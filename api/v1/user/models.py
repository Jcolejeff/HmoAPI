from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, BIGINT
from sqlalchemy.orm import relationship
from datetime import datetime, date
from api.db.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(BIGINT, primary_key=True, autoincrement=True, index=True)
    unique_id = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String(500), index=True, nullable=False)
    password = Column(String(500), nullable=False)
    date_created = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, default=datetime.now)
    is_deleted = Column(Boolean, default=False)

    user_orgs = relationship(
        "OrganizationUser", 
        primaryjoin="and_(User.id == OrganizationUser.user_id, OrganizationUser.is_deleted == False)",
        backref="user_orgs", 
        viewonly=True)
