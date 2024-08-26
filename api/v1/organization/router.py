from fastapi import Depends, APIRouter, Depends, status, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from decouple import config
from api.v1.organization import schemas as organization_schema
from api.db.database import get_db
from api.v1.user.schemas import ShowUser
from api.v1.organization.services import OrganizationService
from api.v1.groups.services import GroupService
from api.v1.groups.schemas import CreateGroup

from api.core.dependencies.user import is_authenticated, is_org_member
from api.utils import paginator

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = APIRouter(tags=["Organizations"])

@app.post("/organizations", status_code=status.HTTP_201_CREATED, response_model=organization_schema.ViewOrganization)
async def create_organization(
    payload: organization_schema.CreateOrganization,
    user: ShowUser = Depends(is_authenticated),
    db: Session = Depends(get_db)
):
    """
    Endpoint to create an organization

    """
    if not payload.created_by:
        payload.created_by = user.id

    created_org = await OrganizationService.create(payload=payload, db=db)

    await GroupService.create(
        user_id=user.id, 
        db=db, 
        payload=CreateGroup(
            organization_id=created_org.id, 
            name=payload.name + " Department",
            member_ids=[user.id], 
            approver_ids=[user.id],
            approval_levels=1
            
        )
    )

    return created_org


@app.get("/organizations", status_code=status.HTTP_200_OK)
async def get_organizations(
    user: ShowUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
    size: int = 20,
    page: int = 1,
):
    """
    Endpoint to retrieve organization info
    """
    page_size = 20 if size < 1 or size > 20 else size
    page_number = 1 if page <= 0 else page
    offset = paginator.off_set(page=page_number, size=page_size)

    # TODO: IMPLEMENT PAGINATION
    orgs, total = await OrganizationService.fetch_all(user_id=user.id, db=db)

    pointers = paginator.page_urls(
        page=page_number,
        size=page_size,
        count=total,
        endpoint='/organizations',
    )

    response = paginator.build_paginated_response(
        page=page_number,
        size=page_size,
        total=total,
        pointers=pointers,
        items=list(map(
            (lambda org: organization_schema.ViewOrganization.model_validate(org)), orgs)),
    )

    return response


@app.get("/organizations/{organization_id}", status_code=status.HTTP_200_OK)
async def get_organization_by_id(
    organization_id: str,
    user: ShowUser = Depends(is_org_member),
    db: Session = Depends(get_db)
):
    """
    Endpoint to get an organization

    """
    organization = await OrganizationService.get(db=db, id=organization_id)

    return organization_schema.ViewOrganization.model_validate(organization)


@app.get("/organizations/{organization_id}/users", status_code=status.HTTP_200_OK)
async def get_organization_users(
    organization_id: int,
    user: ShowUser = Depends(is_org_member),
    db: Session = Depends(get_db)
):

    # call a send invites function that takes in all emails with the organization and the user sending them
    org_users = await OrganizationService.get_organization_users(organization_id=organization_id, db=db)

    # filter failed and successful invites and return response
    return list(map((lambda org_user: organization_schema.ShowOrganizationUser.model_validate(org_user)), org_users))


@app.post("/organizations/{organization_id}/invites", status_code=status.HTTP_200_OK)
async def invite_user(
    organization_id: int,
    background_task: BackgroundTasks,
    payload: organization_schema.InviteUserPayload,
    user: ShowUser = Depends(is_authenticated),
    db: Session = Depends(get_db)
):
    await is_org_member(organization_id=organization_id, db=db, user=user)

    organization = await OrganizationService.get(db=db, id=organization_id)

    # call a send invites function that takes in all emails with the organization and the user sending them
    invite_results = await OrganizationService.send_invites(emails=payload.emails, user=user, organization=organization, db=db, background_task=background_task)

    # filter failed and successful invites and return response
    return invite_results


@app.get("/organizations/{organization_id}/invites", status_code=status.HTTP_200_OK)
async def get_organization_invites(
    organization_id: int,
    search_value: str = None,
    page: int = 1,
    size: int = 50,
    user: ShowUser = Depends(is_org_member),
    db: Session = Depends(get_db)
):

    page_size = 50 if size < 1 or size > 100 else size
    page_number = 1 if page <= 0 else page
    offset = paginator.off_set(page=page_number, size=page_size)

    # call a send invites function that takes in all emails with the organization and the user sending them
    result, count = await OrganizationService.get_organization_invites(organization_id=organization_id, search_value=search_value, offset=offset, limit=page_size, db=db)

    pointers = paginator.page_urls(
        page=page,
        size=page_size,
        count=count,
        endpoint=f"/organizations/{organization_id}/invites",
    )

    response = {
        "page": page_number,
        "size": page_size,
        "total": count,
        "previous_page": pointers["previous"],
        "next_page": pointers["next"],
        "items": result,
    }

    return response


@app.get("/organizations/invites/{invite_token}", status_code=status.HTTP_200_OK)
async def get_invite(
    invite_token: str,
    db: Session = Depends(get_db)
):
    invite = await OrganizationService.get_organization_invite_by_token(db=db, invite_token=invite_token)

    if not invite:
        raise HTTPException(404, detail="Invite not found")

    return invite


@app.put("/organizations/invites/{invite_token}", status_code=status.HTTP_200_OK)
async def update_invite(
    invite_token: str,
    payload: organization_schema.UpdateInvitePayload,
    user: ShowUser = Depends(is_authenticated),
    db: Session = Depends(get_db)
):
    updated_invite = await OrganizationService.update_invite(db=db, invite_token=invite_token, user_id=user.id, status=payload.status)

    return updated_invite
