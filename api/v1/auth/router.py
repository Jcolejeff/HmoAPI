from datetime import timedelta
from typing import Union

from api.core import responses
from api.core.dependencies.user import is_authenticated, is_org_member
from api.db.database import get_db
from api.v1.auth import schemas as auth_schema
from api.v1.auth.services import Auth
from api.v1.emails.services import EmailService
from api.v1.user import schemas as user_schema
from api.v1.user.models import User as UserModel
from api.v1.user.services import UserService
from decouple import config
from fastapi import (APIRouter, BackgroundTasks, Cookie, Depends,
                     HTTPException, Request, Response, status)
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

ACCESS_TOKEN_EXPIRE_MINUTES = int(config('ACCESS_TOKEN_EXPIRE_MINUTES'))
JWT_REFRESH_EXPIRY = int(config('JWT_REFRESH_EXPIRY'))
IS_REFRESH_TOKEN_SECURE = True if config(
    'PYTHON_ENV') == "production" else False


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = APIRouter(tags=["Auth"])


@app.post("/auth/signup", status_code=status.HTTP_201_CREATED, response_model=auth_schema.SignUpResponse)
async def signup(
    response: Response,
    user: user_schema.CreateUser,
    db: Session = Depends(get_db)
):
    """
    Endpoint to create a user

    Returns: Created User.
    """
    user_service = UserService()
    created_user = user_service.create(user=user, db=db)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = Auth.create_access_token(
        data={"id": created_user.id}, db=db, expires_delta=access_token_expires
    )

    refresh_token = Auth.create_refresh_token(
        data={"id": created_user.id}, db=db)

    refresh_expiry_in_seconds = int(
        timedelta(days=JWT_REFRESH_EXPIRY).total_seconds())

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=refresh_expiry_in_seconds,
        secure=True,
        httponly=True,
        samesite="strict",
        path="/"
    )

    return auth_schema.SignUpResponse(**{
        "data": user_schema.ShowUser.model_validate(created_user),
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    })


@app.post("/auth/login", status_code=status.HTTP_200_OK, response_model=auth_schema.LoginResponse)
async def login_for_access_token(
    response: Response,
    data: auth_schema.Login,
    background_task: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    LOGIN

    Returns: Logged in User and access token.
    """

    auth_service = Auth()
    user = auth_service.authenticate_user(
        email=data.email, password=data.password, db=db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=responses.INVALID_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"id": user.id}, db=db, expires_delta=access_token_expires
    )

    refresh_token = auth_service.create_refresh_token(
        data={"id": user.id}, db=db)
    refresh_expiry_in_seconds = int(
        timedelta(days=JWT_REFRESH_EXPIRY).total_seconds())

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=refresh_expiry_in_seconds,
        secure=True,
        httponly=True,
        samesite="strict",
        path="/"
    )

    return auth_schema.LoginResponse(**{
        "data": user_schema.ShowUser.model_validate(user),
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    })


@app.get("/auth/refresh-access-token", status_code=status.HTTP_200_OK)
async def refresh_access_token(
    response: Response,
    refresh_token: Union[str, None] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    """Refreshes an access_token with the issued refresh_token
    Parameters
        ----------
        refresh_token : str, None
            The refresh token sent in the cookie by the client (default is None)

        Raises
        ------
        UnauthorizedError
            If the refresh token is None.
    """

    if refresh_token is None:
        raise HTTPException(
            detail="Log in to authenticate user",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    valid_refresh_token = Auth.verify_refresh_token(refresh_token, db)

    refresh_expiry_in_seconds = int(
        timedelta(days=JWT_REFRESH_EXPIRY).total_seconds())
    access_token_expiry_in_seconds = int(
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES).total_seconds())

    if valid_refresh_token.email is None:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=refresh_expiry_in_seconds,
            secure=IS_REFRESH_TOKEN_SECURE,
            httponly=True,
            samesite="strict",
        )

        print("refresh failed")
    else:
        user = (
            db.query(UserModel)
            .filter(UserModel.id == valid_refresh_token.id)
            .first()
        )

        access_token = Auth.create_access_token(
            {"id": valid_refresh_token.id}, db
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=refresh_expiry_in_seconds,
            secure=IS_REFRESH_TOKEN_SECURE,
            httponly=True,
            samesite="strict",
        )

    # Access token expires in 15 mins,
    return {
        "user": user_schema.ShowUser.model_validate(user),
        "access_token": access_token,
        "expires_in": access_token_expiry_in_seconds
    }


@app.post("/auth/logout", status_code=status.HTTP_200_OK)
async def logout_user(
    request: Request,
    response: Response,
    user: user_schema.User = Depends(is_authenticated),
    db: Session = Depends(get_db),
):
    """
        This endpoint logs out an authenticated user.

        Returns message: User logged out successfully.
    """

    authService = Auth()
    access_token = request.headers.get('Authorization')

    logout = authService.logout(token=access_token, user=user, db=db)

    response.set_cookie(
        key="refresh_token",
        max_age="0",
        secure=True,
        httponly=True,
        samesite="strict",
    )

    return {"message": "User logged out successfully."}


@app.post("/auth/create-api-key", status_code=status.HTTP_201_CREATED)
async def api_key(
    payload: auth_schema.APIKEY,
    user: user_schema.ShowUser = Depends(is_authenticated),
    db: Session = Depends(get_db)
):
    """Endpoint to create a view once API key"""

    api_key, app_id, permissions = Auth.create_api_key(
        payload.organization_id, permissions=payload.permissions, db=db)

    return {"API key": api_key, "App ID": app_id, "permissions": permissions}
