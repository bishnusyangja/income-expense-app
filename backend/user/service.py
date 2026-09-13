import bcrypt
from sqlalchemy import or_
from sqlalchemy.orm import Session

from user.dbmodels import User
from user.pymodel import UserCreate


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def find_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(or_(User.email == email, User.username == email)).first()


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
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
