import passlib.hash as _hash
import secrets
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy.sql import or_
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from typing import Annotated, Union
from uuid import uuid4
from decouple import config

from api.v1.auth.models import BlackListToken, APIKey
from api.v1.user.models import User as UserModel
from api.v1.organization.models import Organization
from api.v1.user import schemas as user_schema
from api.v1.auth import schemas as auth_schema
from api.core import responses
from api.core.base.services import Service


SECRET_KEY = config('SECRET_KEY')
ALGORITHM = config("ALGORITHM")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
JWT_REFRESH_EXPIRY = int(config("JWT_REFRESH_EXPIRY"))


class Auth():

    def __init__(self) -> None:
        pass

    @classmethod
    async def get_current_user(cls, token: Annotated[str, Depends(oauth2_scheme)], db: Session) -> user_schema.User:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=responses.COULD_NOT_VALIDATE_CRED,
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            id: str = payload.get("id")
            if id is None:
                raise credentials_exception
            token_data = id
        except JWTError:
            raise credentials_exception
        user = db.query(UserModel).filter(UserModel.id == id).first()
        if user is None:
            raise credentials_exception
        return user

    @classmethod
    def authenticate_user(cls, db: Session, password: str, email: str) -> user_schema.User:
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            return None
        if not cls.verify_password(password, user.password):
            return None
        return user

    @classmethod
    def authenticate_api_key(cls, db: Session, key: str, app_id: str):
        fetched_api = db.query(APIKey).filter(APIKey.app_id == app_id).first()
        if fetched_api is None:
            return None
        if not cls.verify_password(password=key, hashed_password=fetched_api.key_hash):
            return None

        # return org creator - may be changed later
        user = db.query(UserModel).join(Organization, UserModel.id == Organization.created_by).filter(
            Organization.id == fetched_api.organization_id).first()

        return user

    @staticmethod
    def verify_password(password, hashed_password):
        return pwd_context.verify(password, hashed_password)

    @staticmethod
    def hash_password(password) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, db: Session, expires_delta: timedelta = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=30)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        db.commit()

        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict, db: Session) -> str:
        to_encode = data.copy()

        expire = datetime.utcnow() + timedelta(days=int(JWT_REFRESH_EXPIRY))

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

        return encoded_jwt

    @classmethod
    def verify_access_token(cls, token: str, db: Session) -> auth_schema.TokenData:
        try:
            invalid_token = cls.check_token_blacklist(db=db, token=token)
            if invalid_token == True:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=responses.INVALID_CREDENTIALS,
                                    headers={"WWW-Authenticate": "Bearer"})

            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            id: int | None = payload.get("id")

            if id is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=responses.INVALID_CREDENTIALS,
                                    headers={"WWW-Authenticate": "Bearer"})

            user = db.query(UserModel).filter(UserModel.id == id).first()

            if user is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=responses.INVALID_CREDENTIALS,
                                    headers={"WWW-Authenticate": "Bearer"})

            token_data = auth_schema.TokenData(email=user.email, id=id)

            return token_data

        except JWTError as error:
            print(error, 'error')
            raise JWTError(HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired access token",
                                         headers={"WWW-Authenticate": "Bearer"}))

    @classmethod
    def verify_refresh_token(cls, refresh_token: str, db: Session) -> auth_schema.TokenData:
        try:
            if not refresh_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail=responses.EXPIRED)

            payload = jwt.decode(refresh_token, SECRET_KEY,
                                 algorithms=[ALGORITHM])
            id: str | None = payload.get("id")

            if id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=responses.INVALID_CREDENTIALS,
                    headers={"WWW-Authenticate": "Bearer"})

            user = db.query(UserModel).filter(UserModel.id == id).first()

            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail=responses.INVALID_CREDENTIALS)

            token_data = auth_schema.TokenData(email=user.email, id=id)

        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired session",
                                headers={"WWW-Authenticate": "Bearer"})

        return token_data

    @staticmethod
    def check_token_blacklist(token: str, db: Session) -> bool:
        fetched_token = db.query(BlackListToken).filter(
            BlackListToken.token == token).first()

        if fetched_token:
            return True
        else:
            return False

    @staticmethod
    def logout(token: str, user: user_schema.ShowUser, db: Session) -> str:
        blacklist_token = BlackListToken(
            token=token.split(' ')[1],
            created_by=user.id
        )

        db.add(blacklist_token)
        db.commit()

        return token

    @classmethod
    def create_api_key(cls, organization_id: str, permissions: list, db: Session) -> str:
        """ Generate a view once API KEY"""

        api_key = secrets.token_hex(32)
        app_id = secrets.token_hex(10)
        hash = cls.hash_password(api_key)

        created_api_key = APIKey(
            organization_id=organization_id,
            app_id=app_id,
            key_hash=hash,
            permissions=permissions,
        )

        db.add(created_api_key)
        db.commit()

        return (api_key, app_id, permissions)

    @classmethod
    def magic_login(cls, user_id: int, db: Session, expires_delta: timedelta = None):
        data = {"id": user_id}

        jwt = cls.create_access_token(
            data=data, db=db, expires_delta=expires_delta)

        return jwt
