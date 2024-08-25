from fastapi import status
from fastapi.exceptions import HTTPException

class Messages:
    REFERENCED_RECORD_NOT_FOUND = "Referenced record does not exist. Confirm that a record with this ID exists in the specified table",

messages = Messages()

class ReferencedRecordNotFound(HTTPException):
    def __init__(self, detail: str = None) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail if detail else messages.REFERENCED_RECORD_NOT_FOUND,
            headers=None,
        )
