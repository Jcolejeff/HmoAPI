from typing import Union
from api.core.dependencies.custom_oauth import OAuth2PasswordBearer
from fastapi import Depends, Cookie, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import and_
from jose import JWTError, jwt

from api.v1.auth import schemas as auth_schema
from api.v1.user import schemas as user_schema
from api.v1.auth.services import Auth
from api.v1.user.services import UserService
from api.v1.user.models import User as UserModel
from api.v1.auth.models import APIKey
from api.v1.organization.models import OrganizationUser, Role

from api.v1.organization.services import OrganizationService
from api.db.database import get_db
from api.core import responses

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def is_authenticated(
    access_credentials: auth_schema.Token | auth_schema.APIAuth = Depends(oauth2_scheme),
    refresh_token: Union[str, None] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> user_schema.User:
    """
        Dependency to check if a user is authenticated and return the authenticated user.
        If the return value of the `oauth2_scheme` is a refresh token, 
        the value of the refresh token will be the same as the `refresh_token` argument that is read from the cookie here.

        The reason for the `refresh_token` in the argument here is because 
        the `oauth2_scheme` call method can only return one authentication credential even if multiple exist.
        If it returns an expired access token and a refresh token is passed, there won't be any refresh token available in scope
        to attempt to refresh the expired access token. Hence, the need for the `refresh_token` argument here.
    """

    auth_service = Auth()


    if type(access_credentials) == auth_schema.Token:
        if access_credentials.token_type == auth_schema.TokenType.ACCESS:
            try:
                access_token_info = auth_service.verify_access_token(access_credentials.token, db)
            except JWTError as ex:
                refresh_token_info = auth_service.verify_refresh_token(refresh_token, db)

                user = UserService.fetch(id=refresh_token_info.id, db=db)

                return user
        elif access_credentials.token_type == auth_schema.TokenType.REFRESH:
                refresh_token_info = auth_service.verify_refresh_token(refresh_token, db)

                user = UserService.fetch(id=refresh_token_info.id, db=db)

                return user
        
        user = UserService.fetch(id=access_token_info.id, db=db)
        user.app_id = None

    if type(access_credentials) == auth_schema.APIAuth:
        user = auth_service.authenticate_api_key(db=db, key=access_credentials.api_key, app_id=access_credentials.app_id)
        user.app_id = access_credentials.app_id

    return user


async def is_org_member(organization_id: str,
                        user: user_schema.ShowUser = Depends(is_authenticated),
                        db: Session = Depends(get_db),
                        ):

    is_member = await OrganizationService.get_organization_user(user_id=user.id, organization_id=organization_id, db=db)

    if not is_member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=responses.NOT_ORG_MEMBER)

    return user


async def is_permitted(permission: str, organization_id: int, user_id: int, app_id: str, db: Session = Depends(get_db)):

    if app_id is None:
        org_role = (db.query(Role).join(OrganizationUser, Role.id == OrganizationUser.role)
                    .filter(and_(OrganizationUser.user_id == user_id,
                                 OrganizationUser.organization_id == organization_id,
                                 OrganizationUser.is_deleted == False))
                    .first())

        if not org_role:
            return False

        permissions = list(org_role.permissions)

    else:
        key_record = db.query(APIKey).filter(
            APIKey.app_id == app_id, APIKey.active == True).first()

        if not key_record:
            return False

        permissions = list(key_record.permissions)

    if permission in permissions:
        return True
    else:
        return False
