from fastapi import Depends, APIRouter, Depends, status
from sqlalchemy.orm import Session
from api.v1.user import schemas as user_schema
from api.db.database import get_db
from api.core.dependencies.user import is_authenticated, is_org_member
from api.v1.groups import schemas as group_schemas
from api.v1.groups.services import GroupService, GroupMemberService, GroupApproverService

from api.utils import paginator


app = APIRouter(tags=["Groups"])


@app.post("/groups", status_code=status.HTTP_201_CREATED, response_model=group_schemas.ShowGroup)
async def create_group(
    payload: group_schemas.CreateGroup,
    db: Session = Depends(get_db),
    user: user_schema.ShowUser = Depends(is_authenticated)
):
    """
        Creates a new group in an organization. 
        This endpoint also does an case-sensitive duplicate check to avoid creating groups with the same names.
    """
    await is_org_member(organization_id=payload.organization_id, user=user, db=db)

    created_group = await GroupService.create(payload=payload, user_id=user.id, db=db)

    return created_group

@app.get("/groups", status_code=status.HTTP_200_OK, response_model=group_schemas.PaginatedGroupsResponse)
async def get_groups(
    organization_id: int,
    db: Session = Depends(get_db),
    user: user_schema.ShowUser = Depends(is_org_member),
    size: int = 20,
    page: int = 1,
):

    page_size = 20 if size < 1 or size > 20 else size
    page_number = 1 if page <= 0 else page
    offset = paginator.off_set(page=page_number, size=page_size)

    groups, total = await GroupService.fetch_all(org_id=organization_id, db=db, size=page_size, offset=offset)

    pointers = paginator.page_urls(
        page=page_number,
        size=page_size,
        count=total,
        endpoint='/groups',
    )

    response = paginator.build_paginated_response(
        page=page_number,
        size=page_size,
        total=total,
        pointers=pointers,
        items=list(map((lambda group: group_schemas.ShowGroup.model_validate(group)), groups)))

    return response


@app.get("/groups/{id}", status_code=status.HTTP_200_OK, response_model=group_schemas.ShowGroup)
async def get_group(
    id: int,
    organization_id: int,
    db: Session = Depends(get_db),
    user: user_schema.ShowUser = Depends(is_org_member)
):
    """
        Retrieves a group in an organization
    """
    group = GroupService.get_organization_group(id=id, organization_id=organization_id, db=db)

    return group


@app.put("/groups/{id}", status_code=status.HTTP_200_OK, response_model=group_schemas.ShowGroup)
async def update_group(
    id: int,
    payload: group_schemas.UpdateGroup,
    db: Session = Depends(get_db),
    user: user_schema.ShowUser = Depends(is_authenticated)
):
    """
        Updates the information about a group in an organization
    """
    await is_org_member(organization_id=payload.organization_id, user=user, db=db)
    
    updated_group = await GroupService.update_organization_group(id=id, payload=payload, db=db)

    return updated_group

@app.delete("/groups/{id}", status_code=status.HTTP_200_OK, response_model=group_schemas.ShowGroup)
async def delete_group(
    id: int,
    organization_id: int,
    db: Session = Depends(get_db),
    user: user_schema.ShowUser = Depends(is_org_member)
):
    """
        Deletes a group in an organization
    """
    deleted_group = await GroupService.delete_organization_group(id=id, organization_id=organization_id, db=db)

    return deleted_group

@app.post("/groups/{id}/members/add", status_code=status.HTTP_201_CREATED, response_model=list[group_schemas.ShowGroupMember])
async def add_group_members(
    id: int,
    payload: group_schemas.AddMembers,
    db: Session = Depends(get_db),
    user: user_schema.ShowUser = Depends(is_authenticated)
):
    """
        Adds a user to a group. 
        
        If the user already exists in the group, it fails gracefully and the group-user relationship object isn't returned as part of the response
    """
    await is_org_member(organization_id=payload.organization_id, user=user, db=db)
    group_member_service = GroupMemberService(group_id=id, organization_id=payload.organization_id, db=db)
    added_members = await group_member_service.add_group_members(member_ids=payload.member_ids)

    return added_members


@app.post("/groups/{id}/members/remove", status_code=status.HTTP_200_OK)
async def remove_group_members(
    id: int,
    payload: group_schemas.AddMembers,
    db: Session = Depends(get_db),
    user: user_schema.ShowUser = Depends(is_authenticated)
):
    await is_org_member(organization_id=payload.organization_id, user=user, db=db)
    
    group_member_service = GroupMemberService(group_id=id, organization_id=payload.organization_id, db=db)
    removed_members = await group_member_service.remove_group_members(member_ids=payload.member_ids)

    return f"User(s) with IDs {payload.member_ids} removed successfully"

@app.get("/groups/{id}/members", status_code=status.HTTP_200_OK, response_model=group_schemas.PaginatedGroupMembersResponse)
async def get_group_members(
    id: int,
    organization_id: int,
    db: Session = Depends(get_db),
    user: user_schema.ShowUser = Depends(is_authenticated),
    size: int = 20,
    page: int = 1,
):
    await is_org_member(organization_id=organization_id, user=user, db=db)

    page_size = 20 if size < 1 or size > 20 else size
    page_number = 1 if page <= 0 else page
    offset = paginator.off_set(page=page_number, size=page_size)
    group_member_service = GroupMemberService(group_id=id, organization_id=organization_id, db=db)

    members, total = await group_member_service.get_group_members(size=page_size, offset=offset)

    pointers = paginator.page_urls(
        page=page_number,
        size=page_size,
        count=total,
        endpoint='/groups/{id}/members',
    )

    response = paginator.build_paginated_response(
        page=page_number,
        size=page_size,
        total=total,
        pointers=pointers,
        items=list(map((lambda member: group_schemas.ShowGroupMember.model_validate(member)), members)))

    return response


@app.post("/groups/{id}/approvers/add", status_code=status.HTTP_201_CREATED, response_model=list[group_schemas.ShowGroupApprover])
async def add_group_approvers(
    id: int,
    payload: group_schemas.AddApprovers,
    db: Session = Depends(get_db),
    user: user_schema.ShowUser = Depends(is_authenticated)
):
    """
        Adds an approver to a group. 
        
        If the approver already exists in the group, it fails gracefully and the group-user relationship object isn't returned as part of the response
    """
    await is_org_member(organization_id=payload.organization_id, user=user, db=db)
    group_approver_service = GroupApproverService(group_id=id, organization_id=payload.organization_id, db=db)
    added_approvers = await group_approver_service.add_group_approvers(approver_ids=payload.approver_ids)

    return added_approvers


@app.post("/groups/{id}/approvers/remove", status_code=status.HTTP_200_OK)
async def remove_group_approvers(
    id: int,
    payload: group_schemas.RemoveApprovers,
    db: Session = Depends(get_db),
    user: user_schema.ShowUser = Depends(is_authenticated)
):
    await is_org_member(organization_id=payload.organization_id, user=user, db=db)
    
    group_approver_service = GroupApproverService(group_id=id, organization_id=payload.organization_id, db=db)
    removed_approvers = await group_approver_service.remove_group_approvers(approver_ids=payload.approver_ids)

    return f"User(s) with IDs {payload.approver_ids} removed successfully"


@app.get("/groups/{id}/approvers", status_code=status.HTTP_200_OK, response_model=group_schemas.PaginatedGroupApproversResponse)
async def get_group_approvers(
    id: int,
    organization_id: int,
    db: Session = Depends(get_db),
    user: user_schema.ShowUser = Depends(is_authenticated),
    size: int = 20,
    page: int = 1,
):
    await is_org_member(organization_id=organization_id, user=user, db=db)

    page_size = 20 if size < 1 or size > 20 else size
    page_number = 1 if page <= 0 else page
    offset = paginator.off_set(page=page_number, size=page_size)
    group_approver_service = GroupApproverService(group_id=id, organization_id=organization_id, db=db)

    approvers, total = await group_approver_service.get_group_approvers(size=page_size, offset=offset)

    pointers = paginator.page_urls(
        page=page_number,
        size=page_size,
        count=total,
        endpoint='/groups/{id}/approvers',
    )

    response = paginator.build_paginated_response(
        page=page_number,
        size=page_size,
        total=total,
        pointers=pointers,
        items=list(map((lambda approver: group_schemas.ShowGroupApprover.model_validate(approver)), approvers)))

    return response
