from sqlalchemy import Column, Integer, String, BigInteger, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Guild(Base):
    __tablename__ = "guilds"
    guild_id = Column(BigInteger, primary_key=True)
    users = relationship("User", back_populates="guild")
    custom_roles = relationship(
        "CustomRole",
        back_populates="guild",
        cascade="all, delete-orphan",
    )
    channels = relationship(
        "Channel",
        back_populates="guild",
        cascade="all, delete-orphan",
    )

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, ForeignKey("guilds.guild_id"), nullable=False)
    discord_user_id = Column(BigInteger, nullable=False)
    user_name = Column(String(100), nullable=False)
    guild = relationship("Guild", back_populates="users")
    custom_roles_links = relationship("CustomRoleLink", back_populates="user")
    __table_args__ = (UniqueConstraint("guild_id", "discord_user_id", name="uq_guild_user"),)

class CustomRole(Base):
    __tablename__ = "custom_roles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, ForeignKey("guilds.guild_id"), nullable=False)
    role_name = Column(String(100), nullable=False)
    guild = relationship("Guild", back_populates="custom_roles")
    user_links = relationship("CustomRoleLink", back_populates="custom_role")
    channels = relationship(
        "Channel",
        back_populates="custom_role",
        cascade="all, delete-orphan",
    )
    __table_args__ = (UniqueConstraint("guild_id", "role_name", name="uq_guild_role_name"),)


class Channel(Base):
    __tablename__ = "channels"

    # DiscordのチャンネルIDを主キーとしてそのまま保存する。
    channel_id = Column(BigInteger, primary_key=True)
    guild_id = Column(BigInteger, ForeignKey("guilds.guild_id"), nullable=False)
    custom_role_id = Column(Integer, ForeignKey("custom_roles.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    guild = relationship("Guild", back_populates="channels")
    custom_role = relationship("CustomRole", back_populates="channels")


class CustomRoleLink(Base):
    __tablename__ = "custom_role_links"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    custom_role_id = Column(Integer, ForeignKey("custom_roles.id"), primary_key=True)
    assigned_at = Column(DateTime, server_default=func.now())
    user = relationship("User", back_populates="custom_roles_links")
    custom_role = relationship("CustomRole", back_populates="user_links")
