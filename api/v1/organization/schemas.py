from pydantic import BaseModel, model_validator, EmailStr
from typing import Optional
from datetime import datetime
from api.utils.string import is_empty_string, EmptyStringException
from api.v1.user.schemas import ShowUser
from .models import InviteStatusEnum, RoleEnum


class OrganizationBase(BaseModel):
    name: str
    slug: Optional[str] = None
    created_by: int
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class Role(BaseModel):
    id: int
    organization_id: Optional[int] = None
    name: str
    permissions: list[str]
    date_created: Optional[datetime]
    last_updated: datetime
    is_deleted: bool

    class Config:
        from_attributes = True


class CreateOrganization(OrganizationBase):
    created_by: Optional[int] = None

    @model_validator(mode="after")
    def validate_empty_strings(cls, values):
        if is_empty_string(values.name):
            raise EmptyStringException("organization name cannot be empty")

        return values


class ViewOrganization(OrganizationBase):
    id: int
    creator: ShowUser
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class InviteUserPayload(BaseModel):
    emails: list[EmailStr]


class UpdateInvitePayload(BaseModel):
    status: InviteStatusEnum


class ShowOrganizationInvite(BaseModel):
    id: int
    organization_id: int
    reciever_email: EmailStr
    reciever_id: Optional[int]
    inviter_id: int
    token: str
    status: InviteStatusEnum
    expires_at: datetime
    created_at: datetime
    updated_at: datetime

    organization: ViewOrganization

    class Config:
        from_attributes = True


class ShowOrganizationUser(BaseModel):
    id: int
    organization_id: int
    user_id: int
    role_id: int
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    organization: ViewOrganization
    user: ShowUser
    role: Role

    class Config:
        from_attributes = True
