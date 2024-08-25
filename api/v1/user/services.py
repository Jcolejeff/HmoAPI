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
from api.v1.user import schemas as user_schema
from api.v1.auth.services import Auth
from api.core import responses
from api.core.base.services import Service


SECRET_KEY = config('SECRET_KEY')
ALGORITHM = config("ALGORITHM")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
JWT_REFRESH_EXPIRY = int(config("JWT_REFRESH_EXPIRY"))


class UserService(Service):

    def create(self, user: user_schema.CreateUser, db: Session):
        created_user = UserModel(unique_id=user.unique_id,
                                 first_name=user.first_name,
                                 last_name=user.last_name,
                                 email=user.email,
                                 date_created=user.date_created,
                                 last_updated=user.last_updated,
                                 password=Auth.hash_password(user.password))
        db.add(created_user)
        db.commit()

        return created_user

    @staticmethod
    def fetch(db: Session, id: int = None, unique_id: str = None) -> user_schema.User:
        if id is None and unique_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=responses.ID_OR_UNIQUE_ID_REQUIRED)

        user = db.query(UserModel).filter(UserModel.id == id).filter(
            UserModel.is_deleted == False).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=responses.NOT_FOUND)

        return user

    @staticmethod
    def fetch_all():
        pass

    @staticmethod
    def fetch_by_email(email: str, db: Session) -> user_schema.User:
        user = db.query(UserModel).filter(UserModel.email ==
                                          email, UserModel.is_deleted == False).first()

        return user

    def update(self):
        pass

    @classmethod
    def delete(cls, db: Session, id: int = None, unique_id: str = None) -> user_schema.User:
        user = cls.fetch(id=id, unique_id=unique_id, db=db)
        user.is_deleted = True
        db.commit()
        return user
