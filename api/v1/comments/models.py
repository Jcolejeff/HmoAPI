from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, BIGINT
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from datetime import datetime
from api.db.database import Base

from api.v1.files.models import File


class Comment(Base):
    __tablename__ = "comments"

    id = Column(BIGINT, primary_key=True, autoincrement=True, index=True)
    content = Column(LONGTEXT, nullable=False)
    author = Column(BIGINT, ForeignKey(
        'users.id', ondelete='CASCADE'), index=True, nullable=False)
    organization_id = Column(BIGINT, ForeignKey(
        'organizations.id', ondelete="CASCADE"), index=True, nullable=False)
    table_name = Column(String(225), nullable=False, index=True)
    record_id = Column(BIGINT, nullable=False, index=True)
    parent_id = Column(BIGINT, ForeignKey("comments.id"), nullable=True)
    is_edited = Column(Boolean, default=False)
    date_created = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, default=datetime.now)

    replies = relationship("Comment", backref="parent", remote_side=[id])
    creator = relationship("User", backref="author", viewonly=True)

    files = relationship(
        File.__name__,
        # can't use the `EntityNameEnum` because of circular import
        primaryjoin=f"and_(Comment.id==foreign(File.entity_id), File.entity_name == 'comment')",
        backref="comment_files",
        viewonly=True,
    )
