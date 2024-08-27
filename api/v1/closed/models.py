from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, BIGINT
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from datetime import datetime
from api.db.database import Base

from api.v1.files.models import File


class Closed(Base):
    __tablename__ = "closed"

    id = Column(BIGINT, primary_key=True, autoincrement=True, index=True)
    content = Column(LONGTEXT, nullable=False)
    author = Column(BIGINT, ForeignKey(
        'users.id', ondelete='CASCADE'), index=True, nullable=False)
    organization_id = Column(BIGINT, ForeignKey(
        'organizations.id', ondelete="CASCADE"), index=True, nullable=False)
   
    is_edited = Column(Boolean, default=False)
    date_created = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, default=datetime.now)

  

    