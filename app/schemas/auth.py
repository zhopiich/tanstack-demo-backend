from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class LoginBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class AuthUser(BaseModel):
    id: str = Field(pattern=r"^c[a-z0-9]{24}$")
    name: str
    email: EmailStr
    role: Literal["admin", "reviewer"]


class AuthResponse(BaseModel):
    token: str
    user: AuthUser


class CurrentUserResponse(BaseModel):
    data: AuthUser
