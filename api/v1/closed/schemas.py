from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import enum
from api.utils.utils import PaginatedResponse
from api.v1.user.schemas import ShowUser
from api.v1.files.schemas import ShowFile



class ClosedBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
   
    organization_id: int

class ClosedCreate(ClosedBase):
    pass


class ShowClosed(ClosedBase):
    id: int
    date_created: datetime
    last_updated: datetime

   

    class Config:
        from_attributes = True


class ClosedUpdate(BaseModel):
    organization_id: int
    content: str = Field(..., min_length=1, max_length=1000)

class PaginatedClosedsResponse(PaginatedResponse):
    items: list[ShowClosed]