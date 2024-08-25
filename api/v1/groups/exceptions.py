from fastapi import HTTPException, status

class GroupMessages:
    GROUP_NOT_FOUND = "Group not found."
    DUPLICATE_GROUP_NAME = "A group with this name already exists"
    GROUP_MEMBER_ALREADY_EXISTS = "Group member already exists"
    MEMBER_NOT_FOUND = "Member not found."
    APPROVER_NOT_FOUND = "Approver not found."

messages = GroupMessages()

class GroupNotFoundException(HTTPException):
   def __init__(self, detail: str = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail if detail else messages.GROUP_NOT_FOUND,
            headers=None,
        )

class DuplicateGroupNameException(HTTPException):
   def __init__(self, detail: str = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail if detail else messages.DUPLICATE_GROUP_NAME,
            headers=None,
        )

class GroupMemberAlreadyExistsException(HTTPException):
   def __init__(self, detail: str = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail if detail else messages.GROUP_MEMBER_ALREADY_EXISTS,
            headers=None,
        )

class MemberNotFoundException(HTTPException):
    def __init__(self, detail: str = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail if detail else messages.MEMBER_NOT_FOUND,
            headers=None,
        )

class ApproverNotFoundException(HTTPException):
    def __init__(self, detail: str = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail if detail else messages.APPROVER_NOT_FOUND,
            headers=None,
        )
