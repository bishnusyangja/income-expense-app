from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    address: str = Field(min_length=1, max_length=500)
    phone: str = Field(min_length=7, max_length=32, pattern=r"^[0-9+\-().\s]+$")
    password: str = Field(min_length=8, max_length=72)

    @field_validator("first_name", "last_name", "address")
    @classmethod
    def require_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("This field cannot be blank")
        return value.strip()

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        phone = value.strip()
        digits = "".join(char for char in phone if char.isdigit())
        if len(digits) < 7:
            raise ValueError("Enter a valid phone number")
        return phone

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not value or value.strip() != value:
            raise ValueError("Password cannot start or end with spaces")
        return value

    @model_validator(mode="after")
    def password_must_differ_from_email(self) -> Self:
        if self.password.lower() == str(self.email).lower():
            raise ValueError("Password cannot be the same as email")
        return self


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
