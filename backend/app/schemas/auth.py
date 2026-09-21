"""Authentication Request and Response Schemas."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class CustomerRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None


class CustomerLoginRequest(BaseModel):
    email: EmailStr
    password: str


class StaffLoginRequest(BaseModel):
    username: str
    password: str


class CustomerResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class StaffResponse(BaseModel):
    id: int
    username: str
    role: str
    branch_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
