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

class EntityNameEnum(enum.Enum):
    REQUEST = "request"

class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    table_name: EntityNameEnum
    record_id: int
    parent_id: Optional[int] = None
    organization_id: int

class CommentCreate(CommentBase):
    pass


class ShowComment(CommentBase):
    id: int
    date_created: datetime
    last_updated: datetime

    creator: ShowUser
    files: Optional[list[ShowFile]] = None

    class Config:
        from_attributes = True


class CommentUpdate(BaseModel):
    organization_id: int
    content: str = Field(..., min_length=1, max_length=1000)

class PaginatedCommentsResponse(PaginatedResponse):
    items: list[ShowComment]