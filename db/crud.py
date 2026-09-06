from sqlalchemy.orm import joinedload

from db.crud_base import CRUDBase
from db.database import SessionLocal
from db.models import Channel, CustomRole, CustomRoleLink, Guild, User


guild_crud = CRUDBase(Guild)
user_crud = CRUDBase(User)
custom_role_crud = CRUDBase(CustomRole)
custom_role_link_crud = CRUDBase(CustomRoleLink)
channel_crud = CRUDBase(Channel)


def _ensure_guild(session, guild_id: int) -> None:
    """Guildレコードがなければ作成する。guild_idはDiscordのサーバーID。"""
    if session.get(Guild, guild_id) is None:
        guild = Guild(guild_id=guild_id)
        session.add(guild)
        session.flush()


def create_custom_role(guild_id: int, role_name: str) -> CustomRole:
    """指定サーバーにカスタムロールを作成する。"""
    session = SessionLocal()
    try:
        _ensure_guild(session, guild_id)
        role = CustomRole(guild_id=guild_id, role_name=role_name)
        session.add(role)
        session.commit()
        session.refresh(role)
        return role
    finally:
        session.close()


def get_custom_roles(guild_id: int) -> list[CustomRole]:
    """指定サーバーに属するカスタムロールをすべて取得する。"""
    session = SessionLocal()
    try:
        return session.query(CustomRole).filter(CustomRole.guild_id == guild_id).all()
    finally:
        session.close()


def create_custom_role_channel(
    guild_id: int,
    role_name: str,
    channel_id: int,
) -> Channel:
    """カスタムロール専用として作成したDiscordチャンネルを保存する。"""
    session = SessionLocal()
    try:
        custom_role = session.query(CustomRole).filter(
            CustomRole.guild_id == guild_id,
            CustomRole.role_name == role_name,
        ).first()
        if custom_role is None:
            raise ValueError(f"Role '{role_name}' not found")

        if session.get(Channel, channel_id) is not None:
            raise ValueError(f"Channel '{channel_id}' already exists")

        channel = Channel(
            channel_id=channel_id,
            guild_id=guild_id,
            custom_role_id=custom_role.id,
        )
        session.add(channel)
        session.commit()
        session.refresh(channel)
        return channel
    finally:
        session.close()


def get_channels_by_custom_role(guild_id: int, role_name: str) -> list[Channel]:
    """指定サーバー内のカスタムロールに紐づくチャンネルを取得する。"""
    session = SessionLocal()
    try:
        return (
            session.query(Channel)
            .join(Channel.custom_role)
            .filter(
                Channel.guild_id == guild_id,
                CustomRole.role_name == role_name,
            )
            .all()
        )
    finally:
        session.close()


def get_channels_by_guild(guild_id: int) -> list[Channel]:
    """指定サーバーで記録済みのカスタムロール用チャンネルを取得する。"""
    session = SessionLocal()
    try:
        return session.query(Channel).filter(Channel.guild_id == guild_id).all()
    finally:
        session.close()


def delete_custom_role_channel(channel_id: int) -> bool:
    """削除済みDiscordチャンネルの記録を削除する。"""
    session = SessionLocal()
    try:
        channel = session.get(Channel, channel_id)
        if channel is None:
            return False
        session.delete(channel)
        session.commit()
        return True
    finally:
        session.close()


def get_roles_by_user(guild_id: int, discord_user_id: int) -> list[CustomRole]:
    """指定サーバー内でユーザーが持つカスタムロールを取得する。"""
    session = SessionLocal()
    try:
        user = (
            session.query(User)
            .filter(
                User.guild_id == guild_id,
                User.discord_user_id == discord_user_id,
            )
            .options(joinedload(User.custom_roles_links).joinedload(CustomRoleLink.custom_role))
            .first()
        )
        if user is None:
            return []
        return [link.custom_role for link in user.custom_roles_links]
    finally:
        session.close()


def get_users_by_role(guild_id: int, role_name: str) -> list[User]:
    """指定サーバー内でロールを持つユーザーを取得する。"""
    session = SessionLocal()
    try:
        role = (
            session.query(CustomRole)
            .filter(
                CustomRole.guild_id == guild_id,
                CustomRole.role_name == role_name,
            )
            .options(joinedload(CustomRole.user_links).joinedload(CustomRoleLink.user))
            .first()
        )
        if role is None:
            return []
        return [link.user for link in role.user_links]
    finally:
        session.close()


def add_custom_role_to_user(
    guild_id: int,
    role_name: str,
    discord_user_id: int,
    user_name: str | None = None,
) -> CustomRoleLink:
    """指定サーバーのユーザーに、そのサーバーのカスタムロールを付与する。"""
    session = SessionLocal()
    try:
        custom_role = session.query(CustomRole).filter(
            CustomRole.guild_id == guild_id,
            CustomRole.role_name == role_name,
        ).first()
        if custom_role is None:
            raise ValueError(f"Role '{role_name}' not found")

        user = session.query(User).filter(
            User.guild_id == guild_id,
            User.discord_user_id == discord_user_id,
        ).first()
        if user is None:
            user = User(
                guild_id=guild_id,
                discord_user_id=discord_user_id,
                user_name=user_name or f"User_{discord_user_id}",
            )
            session.add(user)
            session.flush()

        link = session.get(CustomRoleLink, (user.id, custom_role.id))
        if link is not None:
            raise ValueError(f"User already has role '{role_name}'")

        link = CustomRoleLink(user_id=user.id, custom_role_id=custom_role.id)
        session.add(link)
        session.commit()
        return link
    finally:
        session.close()


def remove_custom_role_from_user(
    guild_id: int,
    role_name: str,
    discord_user_id: int,
) -> None:
    """指定サーバーのユーザーからカスタムロールを剥奪する。"""
    session = SessionLocal()
    try:
        custom_role = session.query(CustomRole).filter(
            CustomRole.guild_id == guild_id,
            CustomRole.role_name == role_name,
        ).first()
        if custom_role is None:
            raise ValueError(f"Role '{role_name}' not found")

        user = session.query(User).filter(
            User.guild_id == guild_id,
            User.discord_user_id == discord_user_id,
        ).first()
        if user is None:
            raise ValueError(f"User with discord_user_id {discord_user_id} not found")

        session.query(CustomRoleLink).filter(
            CustomRoleLink.user_id == user.id,
            CustomRoleLink.custom_role_id == custom_role.id,
        ).delete()
        session.commit()
    finally:
        session.close()


def delete_custom_role(guild_id: int, role_name: str) -> None:
    """指定サーバーのロールと関連リンクを削除する。"""
    session = SessionLocal()
    try:
        custom_role = session.query(CustomRole).filter(
            CustomRole.guild_id == guild_id,
            CustomRole.role_name == role_name,
        ).first()
        if custom_role is None:
            raise ValueError(f"Role '{role_name}' not found")

        session.query(CustomRoleLink).filter(
            CustomRoleLink.custom_role_id == custom_role.id
        ).delete()
        session.query(Channel).filter(Channel.custom_role_id == custom_role.id).delete()
        session.delete(custom_role)
        session.commit()
    finally:
        session.close()
