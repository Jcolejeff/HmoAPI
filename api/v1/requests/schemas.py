from fastapi import HTTPException, status
from pydantic import BaseModel, model_validator
from datetime import datetime, date
from typing import Optional
from api.v1.requests.models import RequestStatusEnum
from api.utils.utils import PaginatedResponse
from api.v1.user.schemas import ShowUser


class RequestBase(BaseModel):
    organization_id: int
    state: str
    city: str
    country: str
    start: date
    end: date
    purpose: str
    hotel: str
    room: str
    rate: float
    meal: Optional[str] = None
    transport: Optional[str] = None
    other_requests: Optional[str] = None
    requester_id: int
    rejection_reason: Optional[str] = None
    status: Optional[str] = RequestStatusEnum.PENDING.value


class CreateRequest(RequestBase):
    status: Optional[RequestStatusEnum] = RequestStatusEnum.PENDING.value

    @model_validator(mode='before')
    @classmethod
    def validate_start_and_end(cls, values):
        start_dt = values.get("start")
        end_dt = values.get("end")

        if start_dt > end_dt:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Start date cannot be farther than end date")

        return values


class RequestApproval(BaseModel):
    id: int
    request_id: int
    approver_id: int
    position: int = 1
    status: RequestStatusEnum
    date_created: datetime
    last_updated: datetime

    approver: ShowUser
    
    class Config:
        from_attributes = True

        
class ShowRequest(RequestBase):
    id: int
    is_deleted: bool
    date_created: datetime
    last_updated: datetime

    requester: ShowUser
    request_approvals: list[RequestApproval] = None

    class Config:
        from_attributes = True


class UpdateRequest(BaseModel):
    organization_id: int
    status: Optional[RequestStatusEnum] = None
    state: Optional[str] = None
    city: Optional[str] = None
    start: Optional[date] = None
    end: Optional[date] = None
    purpose: Optional[str] = None
    hotel: Optional[str] = None
    room: Optional[str] = None
    rate: Optional[float] = None
    meal: Optional[str] = None
    transport: Optional[str] = None
    other_requests: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def validate_start_and_end(cls, values):
        start_dt = values.get("start")
        end_dt = values.get("end")

        if start_dt and end_dt:
            if start_dt > end_dt:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Start date cannot be farther than end date")

        return values


class UpdateRequestApproval(BaseModel):
    status: RequestStatusEnum


class PaginatedRequestsResponse(PaginatedResponse):
    items: list[ShowRequest]
