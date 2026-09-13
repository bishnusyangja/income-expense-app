from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _parse_amount(value: object) -> object:
    if value is None or isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        raise ValueError("Enter a valid amount")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Enter a valid amount")


class IncomeCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    note: str | None = Field(default=None, max_length=500)

    @field_validator("title")
    @classmethod
    def require_title(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("This field cannot be blank")
        return title

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        note = value.strip()
        return note or None

    @field_validator("amount", mode="before")
    @classmethod
    def parse_amount(cls, value: object) -> object:
        return _parse_amount(value)

    @model_validator(mode="after")
    def amount_must_be_positive(self) -> Self:
        if self.amount <= 0:
            raise ValueError("Amount must be greater than 0")
        return self


class ExpenditureCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    income_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    note: str | None = Field(default=None, max_length=500)

    @field_validator("title")
    @classmethod
    def require_title(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("This field cannot be blank")
        return title

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        note = value.strip()
        return note or None

    @field_validator("amount", mode="before")
    @classmethod
    def parse_amount(cls, value: object) -> object:
        return _parse_amount(value)

    @model_validator(mode="after")
    def amount_must_be_positive(self) -> Self:
        if self.amount <= 0:
            raise ValueError("Amount must be greater than 0")
        return self


class IncomeResponse(BaseModel):
    id: int
    user_id: int
    title: str
    amount: Decimal
    remaining: Decimal
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ExpenditureResponse(BaseModel):
    id: int
    user_id: int
    income_id: int
    title: str
    amount: Decimal
    note: str | None
    created_at: datetime
    income_remaining: Decimal

    model_config = {"from_attributes": True}
