from pydantic import BaseModel, EmailStr, Field
from typing import List

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=4, max_length=72)

class User(UserBase):
    id: int
    roles: str = Field(default="user")

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
