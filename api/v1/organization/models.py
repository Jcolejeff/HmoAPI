import enum
from sqlalchemy import Boolean, Column, ForeignKey, String, DateTime, BIGINT, Enum, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from api.db.database import Base
from uuid import uuid4


class RoleEnum(enum.Enum):
    MANAGER = "Manager"
    STAFF = "Staff"
    Logistics = "Logistics"


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(BIGINT, primary_key=True, autoincrement=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(128), nullable=True, unique=True)
    created_by = Column(BIGINT, ForeignKey('users.id'), index=True)
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    creator = relationship("User", backref="org_creator", viewonly=True)


class OrganizationUser(Base):
    __tablename__ = "organization_users"
    __table_args__ = (
        UniqueConstraint('organization_id', 'user_id'),
    )
    id = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    organization_id = Column(BIGINT, ForeignKey(
        "organizations.id"), index=True)
    user_id = Column(BIGINT, ForeignKey("users.id"), index=True)
    role_id = Column(BIGINT, ForeignKey('org_user_roles.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)
    is_deleted = Column(Boolean, default=False)

    user = relationship("User", backref="user_user", viewonly=True)
    organization = relationship(
        "Organization", backref="user_org", viewonly=True)
    role = relationship("Role", backref="org_user_role", viewonly=True)


class InviteStatusEnum(enum.Enum):
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    FAILED = 'failed'
    PENDING = 'pending'
    REVOKED = 'revoked'


class OrganizationInvite(Base):
    __tablename__ = "organization_invites"
    __table_args__ = (
        UniqueConstraint('organization_id', 'reciever_id', 'reciever_email'),
    )
    id = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    organization_id = Column(BIGINT, ForeignKey(
        "organizations.id"), index=True)
    reciever_email = Column(String(191))
    reciever_id = Column(BIGINT, ForeignKey('users.id'),
                         nullable=True)  # for existing user
    inviter_id = Column(BIGINT, ForeignKey("users.id"), index=True)
    token = Column(String(255), default=uuid4().hex)
    status = Column(Enum(InviteStatusEnum))
    expires_at = Column(DateTime, default=datetime.now,
                        index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    organization = relationship(
        "Organization", backref="invite_org", viewonly=True)


class Role(Base):
    __tablename__ = "org_user_roles"
    id = Column(BIGINT, primary_key=True, autoincrement=True, index=True)
    organization_id = Column(BIGINT, ForeignKey(
        "organizations.id"), index=True, nullable=True)
    name = Column(String(255), nullable=False)
    permissions = Column(JSON, nullable=False)
    date_created = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
