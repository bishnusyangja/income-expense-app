from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    address: str = Field(min_length=1, max_length=500)
    phone: str = Field(min_length=7, max_length=32)
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    username: EmailStr
    first_name: str
    last_name: str
    email: EmailStr
    address: str
    phone: str
    created_at: datetime

    model_config = {"from_attributes": True}
