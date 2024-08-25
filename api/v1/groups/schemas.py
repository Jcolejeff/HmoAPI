from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from api.v1.user.schemas import ShowUser
from api.utils.utils import PaginatedResponse


class GroupBase(BaseModel):
    organization_id: int
    name: str
    description: Optional[str] = None
    parent_group_id: Optional[int] = None
    approval_levels: Optional[int] = None

    class Config:
        from_attributes = True


class CreateGroup(GroupBase):

    approver_ids: Optional[list[int]] = None
    member_ids: Optional[list[int]] = None
    approval_levels: Optional[int] = None


class UpdateGroup(GroupBase):
    name: Optional[str] = None


class ShowGroupApprover(BaseModel):
    id: int
    group_id: int
    approver_id: int
    position: int
    approver: ShowUser

    class Config:
        from_attributes = True


class ShowGroup(GroupBase):
    id: int
    created_by: int
    date_created: datetime
    last_updated: datetime
    is_deleted: bool

    creator: ShowUser
    approvers: list[ShowGroupApprover] = None
    open_requests_count: int

    class Config:
        from_attributes = True


class ShowGroupMember(BaseModel):
    id: int
    group_id: int
    member_id: int
    date_created: datetime
    last_updated: datetime

    group: ShowGroup
    member: ShowUser

    class Config:
        from_attributes = True


class ListMembers(BaseModel):
    id: int
    member: ShowUser

    class Config:
        from_attributes = True


class AddMembers(BaseModel):
    organization_id: int
    member_ids: list[int]


class RemoveMembers(AddMembers):
    pass


class AddApprovers(BaseModel):
    organization_id: int
    approver_ids: list[int]


class RemoveApprovers(AddApprovers):
    pass


class PaginatedGroupApproversResponse(PaginatedResponse):
    items: list[ShowGroupApprover]


class PaginatedGroupMembersResponse(PaginatedResponse):
    items: list[ShowGroupMember]


class PaginatedGroupsResponse(PaginatedResponse):
    items: list[ShowGroup]
