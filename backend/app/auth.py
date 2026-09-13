import os
from datetime import datetime, timedelta, timezone

import jwt

from user.dbmodels import User

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-insecure-jwt-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30


def create_access_token(user: User) -> tuple[str, datetime]:
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(days=JWT_EXPIRE_DAYS)
    token = jwt.encode(
        {
            "sub": str(user.id),
            "email": user.email,
            "iat": int(issued_at.timestamp()),
            "exp": int(expires_at.timestamp()),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    return token, expires_at


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
