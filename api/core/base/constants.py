import enum
from typing import Any
from api.v1.requests.models import Request
from api.v1.comments.models import Comment

class EntityNameEnum(enum.Enum):
    REQUEST = "request"
    COMMENT = "comment"

table_name_to_model_map: dict[EntityNameEnum, Any] = {
    "request": Request,
    "comment": Comment
}