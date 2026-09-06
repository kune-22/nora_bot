import asyncio

import discord

from db.crud import get_channels_by_custom_role


MAX_CONCURRENT_UPDATES = 5


async def _set_view_permission(
    guild: discord.Guild,
    channel_id: int,
    member: discord.Member,
    can_view: bool,
    semaphore: asyncio.Semaphore,
) -> bool:
    """1チャンネルに対する閲覧権限だけを更新する。"""
    channel = guild.get_channel(channel_id)
    if not isinstance(channel, discord.abc.GuildChannel):
        return False

    async with semaphore:
        overwrite = channel.overwrites_for(member)
        overwrite.view_channel = can_view
        await channel.set_permissions(
            member,
            overwrite=overwrite,
            reason="Custom role channel permission update",
        )
    return True


async def set_custom_role_channel_access(
    guild: discord.Guild,
    guild_id: int,
    role_name: str,
    member: discord.Member,
    can_view: bool,
    channel_records=None,
) -> tuple[int, int]:
    """ロールに紐づく全チャンネルの閲覧権限を並行更新する。

    Returns:
        (更新できたチャンネル数, 更新に失敗または見つからなかったチャンネル数)
    """
    if channel_records is None:
        # 同期SQLAlchemy処理をイベントループ外で実行する。
        channel_records = await asyncio.to_thread(
            get_channels_by_custom_role,
            guild_id,
            role_name,
        )
    if not channel_records:
        return 0, 0

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_UPDATES)
    results = await asyncio.gather(
        *(
            _set_view_permission(
                guild,
                record.channel_id,
                member,
                can_view,
                semaphore,
            )
            for record in channel_records
        ),
        return_exceptions=True,
    )

    updated_count = sum(result is True for result in results)
    failed_count = len(results) - updated_count
    return updated_count, failed_count


async def grant_custom_role_channel_access(
    guild: discord.Guild,
    guild_id: int,
    role_name: str,
    member: discord.Member,
    channel_records=None,
) -> tuple[int, int]:
    """カスタムロール付与後、そのロール用チャンネルを閲覧可能にする。"""
    return await set_custom_role_channel_access(
        guild,
        guild_id,
        role_name,
        member,
        can_view=True,
        channel_records=channel_records,
    )


async def revoke_custom_role_channel_access(
    guild: discord.Guild,
    guild_id: int,
    role_name: str,
    member: discord.Member,
    channel_records=None,
) -> tuple[int, int]:
    """カスタムロール剥奪後、そのロール用チャンネルを閲覧不可にする。"""
    return await set_custom_role_channel_access(
        guild,
        guild_id,
        role_name,
        member,
        can_view=False,
        channel_records=channel_records,
    )
