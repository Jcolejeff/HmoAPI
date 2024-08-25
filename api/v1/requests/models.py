from sqlalchemy import (
    Boolean, Column, ForeignKey, String,
    DateTime, BIGINT, Date, Text, Float,
    UniqueConstraint, Integer
)
from sqlalchemy.orm import relationship
from datetime import datetime
from api.db.database import Base
import enum


class RequestStatusEnum(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Request(Base):
    __tablename__ = "requests"
    id = Column(BIGINT, primary_key=True, autoincrement=True, index=True)
    organization_id = Column(BIGINT, index=True, nullable=False)
    requester_id = Column(BIGINT, ForeignKey('users.id'), index=True, nullable=False)
    country = Column(String(255), index=True, nullable=False)
    state = Column(String(255), index=True, nullable=False)
    city = Column(String(255), index=True, nullable=False)
    start = Column(Date, index=True, nullable=False)
    end = Column(Date, index=True, nullable=False)
    purpose = Column(Text(1000))
    hotel = Column(String(255), index=True, nullable=False)
    room = Column(String(255), nullable=False)
    rate = Column(Float, index=True)
    meal = Column(Text(1000))
    transport = Column(Text(1000))
    other_requests = Column(Text(1000))
    rejection_reason = Column(Text(1000))
    status = Column(String(255), default=RequestStatusEnum.PENDING.value)
    date_created = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    requester = relationship("User", viewonly=True)
    request_approvals = relationship("RequestApproval", viewonly=True)


class RequestApproval(Base):
    __tablename__ = "request_approvals"
    __table_args__ = (
        UniqueConstraint('request_id', 'approver_id'),
    )
    id = Column(BIGINT, primary_key=True, autoincrement=True, index=True)
    request_id = Column(BIGINT, ForeignKey('requests.id'),
                        index=True, nullable=False)
    approver_id = Column(BIGINT, ForeignKey(
        'users.id'), index=True, nullable=False)
    position = Column(Integer, index=True, default=1)
    status = Column(String(255), default=RequestStatusEnum.PENDING.value)
    date_created = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)

    request = relationship("Request", viewonly=True)
    approver = relationship("User", viewonly=True)
