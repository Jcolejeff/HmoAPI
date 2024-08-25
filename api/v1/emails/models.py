from sqlalchemy import (
    Boolean, Column, ForeignKey, String,
    DateTime, BIGINT, Date, Text, Float,
    UniqueConstraint, Integer, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from api.db.database import Base
import enum
from sqlalchemy.dialects.mysql import LONGTEXT


class EmailStatus(enum.Enum):
    SUCCESS = "success"
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"


class Email(Base):
    __tablename__ = "email"
    id = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    organization_id = Column(BIGINT, ForeignKey(
        "organizations.id"), nullable=True, index=True)
    title = Column(Text(1000))
    recipients = Column(JSON, default=[])
    body = Column(LONGTEXT, nullable=False)
    status = Column(String(255), default=EmailStatus.PENDING.value, index=True)
    retries = Column(Integer, default=0)
    date_sent = Column(DateTime, nullable=True)
    priority = Column(Integer, default=1, index=True)
    template_name = Column(String(255))
    date_created = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
