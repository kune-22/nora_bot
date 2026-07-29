from sqlalchemy import Column, Integer, String, BigInteger, DateTime, func, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_user_id = Column(BigInteger, unique=True, nullable=False)
    user_name = Column(String(100), nullable=False)

    custom_roles_links = relationship('CustomRoleLink', back_populates='user')


class CustomRole(Base):
    __tablename__ = 'custom_roles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(100), nullable=False)

    user_links = relationship('CustomRoleLink', back_populates='custom_role')


class CustomRoleLink(Base):
    __tablename__ = 'custom_role_links'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    custom_role_id = Column(Integer, ForeignKey('custom_roles.id'), primary_key=True)
    assigned_at = Column(DateTime, server_default=func.now())

    user = relationship('User', back_populates='custom_roles_links')
    custom_role = relationship('CustomRole', back_populates='user_links')