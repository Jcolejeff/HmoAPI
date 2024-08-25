from sqlalchemy import Boolean, Column, ForeignKey, String, DateTime, BIGINT
from datetime import datetime
from api.db.database import Base

class ApprovedHotel(Base):
    __tablename__ = "approved_hotels"
    id = Column(BIGINT, primary_key=True, autoincrement=True, index=True)
    organization_id = Column(BIGINT, index=True, nullable=False)
    hotel_name = Column(String(255), index=True, nullable=False)
    country = Column(String(255), index=True, nullable=False)
    state = Column(String(255), index=True, nullable=False)
    city = Column(String(255), index=True, nullable=False)
    created_by = Column(BIGINT, ForeignKey('users.id'), index=True)
    date_created = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
