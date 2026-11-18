import bcrypt
from sqlalchemy import or_
from sqlalchemy.orm import Session

from user.dbmodels import User
from user.pymodel import UserCreate


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def find_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(or_(User.email == email, User.username == email)).first()


def _hash_bytes(hashed_password: str | bytes) -> bytes:
    if isinstance(hashed_password, bytes):
        return hashed_password
    return hashed_password.encode("utf-8")


def verify_password(password: str, hashed_password: str | bytes) -> bool:
    if not password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), _hash_bytes(hashed_password))
    except (ValueError, TypeError):
        return False


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = find_user_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user


def create_user(db: Session, payload: UserCreate) -> User:
    user = User(
        username=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        address=payload.address,
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
