from fastapi import status
from fastapi.exceptions import HTTPException


class CommentMessages:
    COMMENT_NOT_FOUND = "Comment not found",
    PARENT_COMMENT_NOT_FOUND = "Parent comment not found",
    REFERENCED_RECORD_NOT_FOUND = "Referenced record does not exist. Confirm that a record with this ID exists in the specified table",
    NOT_AUTHORIZED = "Not authorized to modify this comment"


messages = CommentMessages()

class CommentNotFoundException(HTTPException):
    def __init__(self, detail: str = None) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail if detail else messages.COMMENT_NOT_FOUND,
            headers=None,
        )

class ParentCommentNotFoundException(HTTPException):
    def __init__(self, detail: str = None) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail if detail else messages.PARENT_COMMENT_NOT_FOUND,
            headers=None,
        )

class ReferencedRecordNotFound(HTTPException):
    def __init__(self, detail: str = None) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail if detail else messages.REFERENCED_RECORD_NOT_FOUND,
            headers=None,
        )

class NotAuthorizedException(HTTPException):
    def __init__(self, detail: str = None) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail if detail else messages.NOT_AUTHORIZED,
            headers=None,
        )
