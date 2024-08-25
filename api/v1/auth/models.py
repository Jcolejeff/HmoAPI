from sqlalchemy import Boolean, Column, ForeignKey, String, DateTime, BIGINT, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, date
from api.db.database import Base
import passlib.hash as _hash


class BlackListToken(Base):
    __tablename__ = "blacklist_tokens"
    id = Column(BIGINT, primary_key=True, autoincrement=True, index=True)
    created_by = Column(BIGINT, ForeignKey('users.id'), index=True)
    token = Column(String(255), index=True)
    date_created = Column(DateTime, default=datetime.utcnow)


class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(BIGINT, primary_key=True, autoincrement=True, index=True)
    organization_id = Column(BIGINT, ForeignKey(
        "organizations.id"), index=True)
    app_id = Column(String(255), nullable=False, index=True)
    key_hash = Column(Text, nullable=False)
    permissions = Column(JSON, nullable=False)
    active = Column(Boolean, default=1)
    date_created = Column(DateTime, default=datetime.utcnow)

    def verify(self, api_key: str):
        return _hash.sha256_crypt.verify(api_key, self.key_hash)
