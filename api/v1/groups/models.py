from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, BIGINT, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime

from api.db.database import Base, get_db_with_ctx_mgr
from api.v1.requests.models import Request, RequestStatusEnum

class Group(Base):
    __tablename__ = "groups"
    id = Column(BIGINT, primary_key=True, autoincrement=True, index=True)
    organization_id = Column(BIGINT, index=True, nullable=False)
    name = Column(String(255), index=True, nullable=False)
    description = Column(Text(1000))
    parent_group_id = Column(BIGINT, index=True)
    approval_levels = Column(Integer, index=True, default=1)
    created_by = Column(BIGINT, ForeignKey('users.id'), index=True)
    date_created = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    creator = relationship("User", viewonly=True)
    approvers = relationship("GroupApprover", viewonly=True)

    @hybrid_property
    def open_requests_count(self):
        with get_db_with_ctx_mgr() as db:
            number_of_open_requests = (
                db.query(func.count(Request.id))
                .join(GroupMember, GroupMember.member_id == Request.requester_id)
                .filter(
                    Request.status == RequestStatusEnum.PENDING.value, 
                    Request.is_deleted == False, 
                    GroupMember.group_id == self.id,
                    Request.organization_id == self.organization_id
                )
                .scalar()
            )
            
            return number_of_open_requests


class GroupMember(Base):
    __tablename__ = "group_members"
    __table_args__ = (
        UniqueConstraint('group_id', 'member_id'),
    )
    id = Column(BIGINT, primary_key=True, autoincrement=True, index=True)
    group_id = Column(BIGINT, ForeignKey('groups.id'), index=True, nullable=False)
    member_id = Column(BIGINT, ForeignKey('users.id'), index=True, nullable=False)
    date_created = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)

    group = relationship("Group", viewonly=True, backref="group")
    member = relationship("User", viewonly=True, backref="group-members")


class GroupApprover(Base):
    __tablename__ = "group_approvers"
    __table_args__ = (
        UniqueConstraint('group_id', 'approver_id'),
    )
    id = Column(BIGINT, primary_key=True, autoincrement=True, index=True)
    group_id = Column(BIGINT, ForeignKey('groups.id'), index=True, nullable=False)
    approver_id = Column(BIGINT, ForeignKey('users.id'), index=True, nullable=False)
    position = Column(Integer, index=True, default=1)
    date_created = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)

    group = relationship("Group", viewonly=True)
    approver = relationship("User", viewonly=True)
