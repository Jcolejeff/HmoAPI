from sqlalchemy import Boolean, Column, ForeignKey, String, DateTime, BIGINT, Text, Enum, Integer
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from datetime import datetime
from api.db.database import Base
import enum


class File(Base):
    __tablename__ = "files"
    id = Column(BIGINT, primary_key=True, autoincrement=True, index=True)
    organization_id = Column(BIGINT, ForeignKey('organizations.id'), index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer)
    entity_id = Column(BIGINT, nullable=False)
    entity_name = Column(String(255), nullable=False)
    url = Column(Text(2000), nullable=False)
    description = Column(LONGTEXT)
    created_at = Column(DateTime,default=datetime.utcnow)
    updated_at = Column(DateTime,default=datetime.utcnow)
    created_by = Column(BIGINT, ForeignKey('users.id'), index=True, nullable=False)

    creator = relationship("User", backref="file_creator", viewonly=True)