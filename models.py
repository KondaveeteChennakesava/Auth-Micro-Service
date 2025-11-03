from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
    token_type: str = "access"


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50,
                          description="Username")
    email: EmailStr = Field(..., description="Email address")
    full_name: str | None = Field(
        None, max_length=100, description="Full name")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.isalnum() and '_' not in v:
            raise ValueError(
                'Username must contain only alphanumeric characters and underscores')
        return v.lower()


class UserCreate(UserBase):
    password: str = Field(..., min_length=8,
                          max_length=128, description="Password")

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError(
                'Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError(
                'Password must contain at least one lowercase letter')
        return v


class User(UserBase):
    disabled: bool = False

    class Config:
        from_attributes = True


class UserInDB(User):
    id: int
    hashed_password: str

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class MessageResponse(BaseModel):
    message: str
    detail: str | None = None
