from pydantic import BaseModel, model_validator, EmailStr
from typing import Optional
from datetime import datetime
from api.utils.string import is_empty_string, EmptyStringException
from api.v1.user.models import User
from api.db.database import SessionLocal
from fastapi import HTTPException, status
from api.core import responses
from typing import Any, List, Optional


class UserRole(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class OrgUser(BaseModel):
    organization_id: int
    role: UserRole

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    unique_id: Optional[str] = None
    date_created: Optional[datetime] = datetime.utcnow()
    last_updated: Optional[datetime] = datetime.utcnow()
    class Config:
        from_attributes = True


class CreateUser(UserBase):
    password: str

    class Config:
        from_attributes = True

    # validate email not in use

    @model_validator(mode='before')
    @classmethod
    def validate_email(cls, values):
        email = values.get("email")

        with SessionLocal() as db:
            user_email = db.query(User).filter(User.email == email).first()
            if user_email:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=responses.EMAIL_IN_USE)

        return values


class ShowUser(UserBase):
    id: int
    user_orgs: Optional[List[OrgUser]] = None
    is_deleted: Optional[bool] = None

    class Config:
        from_attributes = True
