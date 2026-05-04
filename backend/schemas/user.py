from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    email: EmailStr
    password: str = Field(min_length=8)
    role: bool = False


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=128)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8)
    role: bool | None = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: bool
    last_login: datetime | None

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: bool
    username: str
    user_id: int


class MessageResponse(BaseModel):
    message: str
