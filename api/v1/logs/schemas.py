from pydantic import BaseModel, model_validator
from typing import Optional, Union
from datetime import datetime
from api.utils.string import is_empty_string, EmptyStringException
from api.v1.user.schemas import ShowUser
import enum

class LogAction(enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    ASSIGNED = "assigned"

class LogBase(BaseModel):
    name: Optional[str] = None
    action: LogAction
    message: str
    date: datetime
    entity: str
    entity_id: int
    activity_message: Optional[str] = None

    class Config:
        from_attributes = True