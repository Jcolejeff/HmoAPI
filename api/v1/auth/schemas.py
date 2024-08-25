from pydantic import BaseModel, EmailStr
from api.v1.user.schemas import ShowUser
import enum

class Login(BaseModel):
    email: EmailStr
    password: str

class TokenType(enum.Enum):
    ACCESS = 'access'
    REFRESH = 'refresh'


class Token(BaseModel):
    token: str
    token_type: TokenType


class APIAuth(BaseModel):
    api_key: str
    app_id: str


class APIKEY(BaseModel):
    organization_id: int
    permissions: list


class TokenData(BaseModel):
    id: int
    email: str


class SignUpResponse(BaseModel):
    data: ShowUser
    access_token: str
    refresh_token: str
    token_type: str


class LoginResponse(SignUpResponse):
    pass
