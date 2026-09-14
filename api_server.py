import logging
import os
import asyncio
import secrets
from urllib.parse import urlencode

import httpx
import uvicorn
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from starlette.middleware.sessions import SessionMiddleware

import bot_set
from bot_set import bot
from db.crud import add_custom_role_to_user, create_custom_role, delete_custom_role, delete_custom_role_channel, get_channels_by_guild, get_custom_role_channel, get_custom_roles, get_users_by_role, remove_custom_role_from_user, rename_custom_role


DISCORD_API = "https://discord.com/api/v10"
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:3022/api/auth/callback")
FRONTEND_URL = os.getenv("DASHBOARD_URL", "http://localhost:3022")
SESSION_SECRET = os.getenv("DASHBOARD_SESSION_SECRET", "change-me-in-production")

app = FastAPI(title="Nora Bot Dashboard API")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, same_site="lax", https_only=False)
logger = logging.getLogger(__name__)


def run_on_bot_loop(coroutine):
    """APIスレッドからDiscord Botのイベントループ上で処理を実行する。"""
    bot_loop = bot_set.bot_loop
    if bot_loop is None or not bot_loop.is_running():
        raise RuntimeError("Discord Botのイベントループが起動していません。")
    future = asyncio.run_coroutine_threadsafe(coroutine, bot_loop)
    return future.result(timeout=20)


class CustomRolePayload(BaseModel):
    name: str


class CustomRoleUserPayload(BaseModel):
    userId: int
    userName: str | None = None


class CustomChannelPayload(BaseModel):
    name: str


async def _rename_discord_channel(guild_id: int, channel_id: int, name: str) -> str:
    discord_guild = bot.get_guild(guild_id)
    discord_channel = discord_guild.get_channel(channel_id) if discord_guild else None
    if discord_channel is None:
        raise LookupError("Discord上のチャンネルが見つかりません。")
    await discord_channel.edit(name=name, reason="Dashboard channel rename")
    return discord_channel.name


async def _delete_discord_channel(guild_id: int, channel_id: int) -> None:
    discord_guild = bot.get_guild(guild_id)
    discord_channel = discord_guild.get_channel(channel_id) if discord_guild else None
    if discord_channel is None:
        raise LookupError("Discord上のチャンネルが見つかりません。")
    await discord_channel.delete(reason="Dashboard channel delete")


def _can_manage_guild(request: Request, guild_id: int) -> bool:
    return "user" in request.session and any(
        str(guild.get("id")) == str(guild_id) for guild in request.session.get("guilds", [])
    )


@app.get("/api/auth/discord")
async def discord_login(request: Request):
    if not CLIENT_ID or not CLIENT_SECRET:
        return JSONResponse({"detail": "DISCORD_CLIENT_ID と DISCORD_CLIENT_SECRET を設定してください。"}, status_code=500)

    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds",
        "state": state,
    }
    return RedirectResponse(f"https://discord.com/oauth2/authorize?{urlencode(params)}")


@app.get("/api/auth/callback")
async def discord_callback(request: Request, code: str | None = None, state: str | None = None):
    if not code or not state or not secrets.compare_digest(state, request.session.pop("oauth_state", "")):
        return JSONResponse({"detail": "OAuth2の状態を確認できませんでした。もう一度ログインしてください。"}, status_code=400)

    async with httpx.AsyncClient(timeout=15) as client:
        token_response = await client.post(
            f"{DISCORD_API}/oauth2/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token_response.is_error:
            return JSONResponse({"detail": "Discordとの認証に失敗しました。"}, status_code=400)

        token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        user_response, guilds_response = await _fetch_discord_data(client, headers)
        if user_response.is_error or guilds_response.is_error:
            return JSONResponse({"detail": "Discordのユーザー情報を取得できませんでした。"}, status_code=400)

    # Botのキャッシュが準備できてから、Botが参加しているサーバーを判定する。
    if not bot.is_ready():
        await bot.wait_until_ready()
    bot_guild_ids = {str(guild.id) for guild in bot.guilds}
    manageable_guilds = [
        {
            "id": guild["id"],
            "name": guild["name"],
            "iconUrl": f"https://cdn.discordapp.com/icons/{guild['id']}/{guild['icon']}.png?size=128" if guild.get("icon") else None,
            "memberCount": guild.get("approximate_member_count"),
        }
        for guild in guilds_response.json()
        if guild["id"] in bot_guild_ids and (int(guild.get("permissions", 0)) & (0x8 | 0x20))
    ]
    user = user_response.json()
    request.session["user"] = {
        "id": user["id"],
        "username": user.get("global_name") or user["username"],
        "avatarUrl": f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png?size=128" if user.get("avatar") else None,
    }
    request.session["guilds"] = manageable_guilds
    return RedirectResponse(FRONTEND_URL)


async def _fetch_discord_data(client: httpx.AsyncClient, headers: dict[str, str]):
    return await client.get(f"{DISCORD_API}/users/@me", headers=headers), await client.get(
        f"{DISCORD_API}/users/@me/guilds?with_counts=true", headers=headers
    )


@app.get("/api/auth/session")
async def auth_session(request: Request):
    if "user" not in request.session:
        return JSONResponse(None)
    return {"user": request.session["user"], "guilds": request.session.get("guilds", [])}


@app.post("/api/auth/logout")
async def auth_logout(request: Request):
    request.session.clear()
    return {"ok": True}


@app.get("/api/guilds/{guild_id}/dashboard")
async def guild_dashboard(request: Request, guild_id: int):
    """ログインユーザーが管理できるサーバーのカスタムロール情報を返す。"""
    if "user" not in request.session:
        return JSONResponse({"detail": "ログインが必要です。"}, status_code=401)

    if not _can_manage_guild(request, guild_id):
        return JSONResponse({"detail": "このサーバーを管理する権限がありません。"}, status_code=403)

    roles = get_custom_roles(guild_id)
    channels = get_channels_by_guild(guild_id)
    role_names = {role.id: role.role_name for role in roles}
    role_user_counts = {role.id: len(get_users_by_role(guild_id, role.role_name)) for role in roles}
    discord_guild = bot.get_guild(guild_id)

    channel_items = []
    for channel in channels:
        discord_channel = discord_guild.get_channel(channel.channel_id) if discord_guild else None
        channel_items.append({
            "id": str(channel.channel_id),
            "name": discord_channel.name if discord_channel else f"チャンネル {channel.channel_id}",
            "categoryName": discord_channel.category.name if discord_channel and discord_channel.category else "カテゴリなし",
            "customRoleName": role_names.get(channel.custom_role_id, "削除済みロール"),
            "customRoleId": channel.custom_role_id,
            "userCount": role_user_counts.get(channel.custom_role_id, 0),
        })

    return {
        "customRoleCount": len(roles),
        "customRoles": [{"id": role.id, "name": role.role_name} for role in roles],
        "customRoleChannelCount": len(channel_items),
        "channels": channel_items,
    }


@app.patch("/api/guilds/{guild_id}/custom-channels/{channel_id}")
async def rename_dashboard_custom_channel(request: Request, guild_id: int, channel_id: int, payload: CustomChannelPayload):
    if "user" not in request.session:
        return JSONResponse({"detail": "ログインが必要です。"}, status_code=401)
    if not _can_manage_guild(request, guild_id):
        return JSONResponse({"detail": "このサーバーを管理する権限がありません。"}, status_code=403)
    name = payload.name.strip()
    if not name:
        return JSONResponse({"detail": "チャンネル名を入力してください。"}, status_code=400)
    record = get_custom_role_channel(guild_id, channel_id)
    if record is None:
        return JSONResponse({"detail": "カスタムロール用チャンネルが見つかりません。"}, status_code=404)
    try:
        new_name = run_on_bot_loop(_rename_discord_channel(guild_id, channel_id, name))
    except Exception as exc:
        logger.exception("Failed to rename custom channel %s in guild %s", channel_id, guild_id)
        return JSONResponse({"detail": f"チャンネル名を変更できませんでした: {exc}"}, status_code=502)
    return {"ok": True, "id": str(channel_id), "name": new_name}


@app.delete("/api/guilds/{guild_id}/custom-channels/{channel_id}")
async def delete_dashboard_custom_channel(request: Request, guild_id: int, channel_id: int):
    if "user" not in request.session:
        return JSONResponse({"detail": "ログインが必要です。"}, status_code=401)
    if not _can_manage_guild(request, guild_id):
        return JSONResponse({"detail": "このサーバーを管理する権限がありません。"}, status_code=403)
    record = get_custom_role_channel(guild_id, channel_id)
    if record is None:
        return JSONResponse({"detail": "カスタムロール用チャンネルが見つかりません。"}, status_code=404)
    try:
        run_on_bot_loop(_delete_discord_channel(guild_id, channel_id))
    except Exception as exc:
        logger.exception("Failed to delete custom channel %s in guild %s", channel_id, guild_id)
        return JSONResponse({"detail": f"チャンネルを削除できませんでした: {exc}"}, status_code=502)
    delete_custom_role_channel(channel_id)
    return {"ok": True, "id": str(channel_id)}


@app.post("/api/guilds/{guild_id}/custom-roles")
async def create_dashboard_custom_role(request: Request, guild_id: int, payload: CustomRolePayload):
    if "user" not in request.session:
        return JSONResponse({"detail": "ログインが必要です。"}, status_code=401)
    if not _can_manage_guild(request, guild_id):
        return JSONResponse({"detail": "このサーバーを管理する権限がありません。"}, status_code=403)
    role_name = payload.name.strip()
    if not role_name:
        return JSONResponse({"detail": "ロール名を入力してください。"}, status_code=400)
    if any(role.role_name.casefold() == role_name.casefold() for role in get_custom_roles(guild_id)):
        return JSONResponse({"detail": "同じ名前のカスタムロールが既に存在します。"}, status_code=409)
    try:
        role = create_custom_role(guild_id, role_name)
    except IntegrityError:
        return JSONResponse({"detail": "同じ名前のカスタムロールが既に存在します。"}, status_code=409)
    return {"id": role.id, "name": role.role_name}


@app.patch("/api/guilds/{guild_id}/custom-roles/{role_id}")
async def rename_dashboard_custom_role(request: Request, guild_id: int, role_id: int, payload: CustomRolePayload):
    if "user" not in request.session:
        return JSONResponse({"detail": "ログインが必要です。"}, status_code=401)
    if not _can_manage_guild(request, guild_id):
        return JSONResponse({"detail": "このサーバーを管理する権限がありません。"}, status_code=403)
    role_name = payload.name.strip()
    roles = get_custom_roles(guild_id)
    role = next((item for item in roles if item.id == role_id), None)
    if role is None:
        return JSONResponse({"detail": "カスタムロールが見つかりません。"}, status_code=404)
    if not role_name:
        return JSONResponse({"detail": "ロール名を入力してください。"}, status_code=400)
    if any(item.id != role_id and item.role_name.casefold() == role_name.casefold() for item in roles):
        return JSONResponse({"detail": "同じ名前のカスタムロールが既に存在します。"}, status_code=409)
    try:
        updated = rename_custom_role(guild_id, role_id, role_name)
    except IntegrityError:
        return JSONResponse({"detail": "同じ名前のカスタムロールが既に存在します。"}, status_code=409)
    return {"id": updated.id, "name": updated.role_name}


@app.delete("/api/guilds/{guild_id}/custom-roles/{role_id}")
async def delete_dashboard_custom_role(request: Request, guild_id: int, role_id: int):
    if "user" not in request.session:
        return JSONResponse({"detail": "ログインが必要です。"}, status_code=401)
    if not _can_manage_guild(request, guild_id):
        return JSONResponse({"detail": "このサーバーを管理する権限がありません。"}, status_code=403)
    role = next((item for item in get_custom_roles(guild_id) if item.id == role_id), None)
    if role is None:
        return JSONResponse({"detail": "カスタムロールが見つかりません。"}, status_code=404)
    delete_custom_role(guild_id, role.role_name)
    return {"ok": True}


def _find_dashboard_role(guild_id: int, role_id: int):
    return next((item for item in get_custom_roles(guild_id) if item.id == role_id), None)


@app.get("/api/guilds/{guild_id}/custom-roles/{role_id}/users")
async def custom_role_users(request: Request, guild_id: int, role_id: int):
    if "user" not in request.session:
        return JSONResponse({"detail": "ログインが必要です。"}, status_code=401)
    if not _can_manage_guild(request, guild_id):
        return JSONResponse({"detail": "このサーバーを管理する権限がありません。"}, status_code=403)
    role = _find_dashboard_role(guild_id, role_id)
    if role is None:
        return JSONResponse({"detail": "カスタムロールが見つかりません。"}, status_code=404)

    assigned_records = get_users_by_role(guild_id, role.role_name)
    discord_guild = bot.get_guild(guild_id)
    member_by_id = {
        int(user.discord_user_id): discord_guild.get_member(int(user.discord_user_id))
        for user in assigned_records
    } if discord_guild else {}
    def member_data(member, fallback_id: int, fallback_name: str):
        return {
            "id": str(member.id) if member else str(fallback_id),
            "name": member.display_name if member else fallback_name,
            "avatarUrl": str(member.display_avatar.url) if member else None,
        }

    assigned = [
        member_data(member_by_id.get(int(user.discord_user_id)), int(user.discord_user_id), user.user_name)
        for user in assigned_records
    ]
    assigned.sort(key=lambda user: user["name"].casefold())
    return {"role": {"id": role.id, "name": role.role_name}, "assignedUsers": assigned}


@app.get("/api/guilds/{guild_id}/custom-roles/{role_id}/users/search")
async def search_custom_role_users(
    request: Request,
    guild_id: int,
    role_id: int,
    q: str = Query(default="", max_length=80),
    limit: int = Query(default=25, ge=1, le=25),
):
    if "user" not in request.session:
        return JSONResponse({"detail": "ログインが必要です。"}, status_code=401)
    if not _can_manage_guild(request, guild_id):
        return JSONResponse({"detail": "このサーバーを管理する権限がありません。"}, status_code=403)
    role = _find_dashboard_role(guild_id, role_id)
    if role is None:
        return JSONResponse({"detail": "カスタムロールが見つかりません。"}, status_code=404)
    query = q.strip().casefold()
    assigned_ids = {int(user.discord_user_id) for user in get_users_by_role(guild_id, role.role_name)}
    discord_guild = bot.get_guild(guild_id)
    if discord_guild is None:
        return {"users": []}
    users = [
        {"id": str(member.id), "name": member.display_name, "avatarUrl": str(member.display_avatar.url)}
        for member in discord_guild.members
        if not member.bot and int(member.id) not in assigned_ids and (not query or query in member.display_name.casefold() or query in member.name.casefold())
    ]
    users.sort(key=lambda user: user["name"].casefold())
    return {"users": users[:limit]}


@app.post("/api/guilds/{guild_id}/custom-roles/{role_id}/users")
async def add_dashboard_custom_role_user(request: Request, guild_id: int, role_id: int, payload: CustomRoleUserPayload):
    if "user" not in request.session:
        return JSONResponse({"detail": "ログインが必要です。"}, status_code=401)
    if not _can_manage_guild(request, guild_id):
        return JSONResponse({"detail": "このサーバーを管理する権限がありません。"}, status_code=403)
    role = _find_dashboard_role(guild_id, role_id)
    if role is None:
        return JSONResponse({"detail": "カスタムロールが見つかりません。"}, status_code=404)
    try:
        add_custom_role_to_user(guild_id, role.role_name, payload.userId, payload.userName)
    except ValueError as error:
        return JSONResponse({"detail": str(error)}, status_code=409)
    return {"ok": True}


@app.delete("/api/guilds/{guild_id}/custom-roles/{role_id}/users/{user_id}")
async def remove_dashboard_custom_role_user(request: Request, guild_id: int, role_id: int, user_id: int):
    if "user" not in request.session:
        return JSONResponse({"detail": "ログインが必要です。"}, status_code=401)
    if not _can_manage_guild(request, guild_id):
        return JSONResponse({"detail": "このサーバーを管理する権限がありません。"}, status_code=403)
    role = _find_dashboard_role(guild_id, role_id)
    if role is None:
        return JSONResponse({"detail": "カスタムロールが見つかりません。"}, status_code=404)
    try:
        remove_custom_role_from_user(guild_id, role.role_name, user_id)
    except ValueError as error:
        return JSONResponse({"detail": str(error)}, status_code=404)
    return {"ok": True}


def run_api():
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("API_PORT", "8000")), log_level="info")
