from fastapi import Depends, Cookie, APIRouter, Depends, status
from sqlalchemy.orm import Session
from api.v1.user import schemas as user_schema
from api.v1.organization import schemas as org_schema
from api.db.database import get_db
from api.v1.user.services import UserService
from api.v1.organization.services import OrganizationService
from api.core.dependencies.user import is_authenticated, is_org_member
from api.utils import paginator

app = APIRouter(tags=["Users"])


@app.get("/user", status_code=status.HTTP_200_OK)
async def get_user(
    user: user_schema.User = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    """
        Returns an authenticated user information
    """
    print(user)
    return user


@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    user: user_schema.User = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    """
        This endpoint deletes a user from the db. (Soft delete)

        Returns message: User deleted successfully.
    """

    deleted_user = UserService.delete(db=db, id=user_id)

    return {"message": "User deleted successfully."}


@app.get("/users/{user_id}/invites", status_code=status.HTTP_200_OK)
async def get_user_invites(
    user_id: int,
    size: int = 20,
    page: int = 1,
    user: user_schema.ShowUser = Depends(is_authenticated),
    db: Session = Depends(get_db),
):

    page_size = 20 if size < 1 or size > 20 else size
    page_number = 1 if page <= 0 else page
    offset = paginator.off_set(page=page_number, size=page_size)

    invites, total = await OrganizationService.get_user_invites(db=db, email=user.email)

    pointers = paginator.page_urls(
        page=page_number,
        size=page_size,
        count=total,
        endpoint=f'/users/{user_id}/invites',
    )

    response = paginator.build_paginated_response(
        page=page_number,
        size=page_size,
        total=total,
        pointers=pointers,
        items=list(map(
            (lambda invite: org_schema.ShowOrganizationInvite.model_validate(invite)), invites))
    )

    return response


@app.post("/users/roles", status_code=status.HTTP_200_OK)
async def create_user_roles(
    user: user_schema.ShowUser = Depends(is_org_member),
    db: Session = Depends(get_db)
):
    """
     Endpoint to create custom roles for users mixing permissions.

     Returns created role

    """
    pass
