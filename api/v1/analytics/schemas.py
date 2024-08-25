from fastapi import HTTPException, status
from pydantic import BaseModel, model_validator
from typing import Optional
from datetime import date

class TopHotelsResponse(BaseModel):
    id: int
    name: str 
    total_requests: Optional[int] = None
    total_spend: Optional[int] = None
    travel_count: Optional[int] = None

    class Config:
        orm_mode = True


class TopDestinationsResponse(TopHotelsResponse):

    class Config:
        orm_mode = True

class TopTravellersResponse(TopHotelsResponse):
    department: Optional[str]

    class Config:
        orm_mode = True

class TopRequestersResponse(TopHotelsResponse):
    department: Optional[str]

    class Config:
        orm_mode = True

class CoworkersResponse(TopHotelsResponse):
    department: Optional[str]

    class Config:
        orm_mode = True


class CreateReport(BaseModel):
    total_requests: Optional[bool] = False
    pending_requests: Optional[bool] = False
    approved_requests: Optional[bool] = False
    top_requesters: Optional[bool] = False
    top_hotels: Optional[bool] = False
    total_spend: Optional[bool] = False
    cancelled_requests: Optional[bool] = False
    total_departments: Optional[bool] = False
    travel_count: Optional[bool] = False
    top_destinations: Optional[bool] = False
    top_travellers: Optional[bool] = False
    organization_id: int
    start_date: date
    end_date: date
    email: str

    @model_validator(mode='before')
    @classmethod
    def validate_start_and_end(cls, values):
        start_dt = values.get("start_date")
        end_dt = values.get("end_date")

        if start_dt and end_dt:
            if start_dt > end_dt:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Start date cannot be farther than end date")

        return values
