from fastapi import HTTPException, status

class RequestMessages:
    REQUEST_NOT_FOUND = "Request not found."
    NOT_ALLOWED_TO_UPDATE_STATUS = "You are not allowed to update the status of this request"
    LOWER_APPROVER_HAS_NOT_APPROVED = "Cannot add approval until all lower approvers have approved"

messages = RequestMessages()

class RequestNotFoundException(HTTPException):
    def __init__(self, detail: str = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail if detail else messages.REQUEST_NOT_FOUND,
            headers=None,
        )

class NotAllowedToUpdateRequestStatusException(HTTPException):
    def __init__(self, detail: str = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail if detail else messages.NOT_ALLOWED_TO_UPDATE_STATUS,
            headers=None,
        )
class LowerApproverHasNotApprovedException(HTTPException):
    def __init__(self, detail: str = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail if detail else messages.LOWER_APPROVER_HAS_NOT_APPROVED,
            headers=None,
        )