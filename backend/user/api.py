from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.responses import json_response
from user.pymodel import UserCreate, UserResponse
from user.service import create_user, find_user_by_email

router = APIRouter(tags=["users"])


@router.post("/register")
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> JSONResponse:
    if find_user_by_email(db, payload.email):
        return json_response(
            status_code=409,
            message="Registration failed",
            errors={"email": "Email is already registered"},
        )

    user = create_user(db, payload)
    return json_response(
        status_code=201,
        message="User registered successfully",
        data=UserResponse.model_validate(user).model_dump(mode="json"),
    )
