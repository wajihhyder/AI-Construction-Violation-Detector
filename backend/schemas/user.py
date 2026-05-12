from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from models.user import ROLE_ADMIN, ROLE_AUTHORITY, ROLE_DG

RoleName = Literal[ROLE_ADMIN, ROLE_AUTHORITY, ROLE_DG]


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    email: EmailStr
    password: str = Field(min_length=8)
    role_name: RoleName = ROLE_AUTHORITY
    assigned_area: str | None = Field(default=None, min_length=1, max_length=128)


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=128)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8)
    role_name: RoleName | None = None
    assigned_area: str | None = Field(default=None, min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: bool
    role_name: RoleName
    assigned_area: str | None
    last_login: datetime | None

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: bool
    role_name: RoleName
    assigned_area: str | None
    username: str
    user_id: int


class MessageResponse(BaseModel):
    message: str
