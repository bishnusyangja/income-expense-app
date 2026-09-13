from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.auth import create_access_token
from app.database import get_db
from app.responses import json_response
from user.pymodel import UserCreate, UserLogin, UserResponse
from user.service import authenticate_user, create_user, find_user_by_email

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


@router.post("/login")
def login_user(payload: UserLogin, db: Session = Depends(get_db)) -> JSONResponse:
    user = authenticate_user(db, payload.email, payload.password)
    if user is None:
        return json_response(
            status_code=401,
            message="Login failed",
            errors={"email": "Invalid email or password"},
        )

    access_token, expires_at = create_access_token(user)
    return json_response(
        status_code=200,
        message="Login successful",
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "expires_at": expires_at.isoformat(),
            "user": UserResponse.model_validate(user).model_dump(mode="json"),
        },
    )
