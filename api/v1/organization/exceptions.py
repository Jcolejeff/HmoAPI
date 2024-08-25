from fastapi import status
from fastapi.exceptions import HTTPException


class Messages:
    ORGANIZATION_NOT_FOUND = "Organization not found"
    INVITE_NOT_FOUND = "Organization not found"

messages = Messages()

class OrganizationNotFoundException(HTTPException):
    def __init__(self, detail: str = None) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail if detail else messages.ORGANIZATION_NOT_FOUND,
            headers=None,
        )

class InviteNotFoundException(HTTPException):
    def __init__(self, detail: str = None) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail if detail else messages.INVITE_NOT_FOUND,
            headers=None,
        )