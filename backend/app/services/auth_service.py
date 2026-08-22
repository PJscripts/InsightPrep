from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import RegisterRequest


def register_user(db: Session, data: RegisterRequest) -> User:
    existing_user = db.scalar(select(User).where(User.email == data.email))

    if existing_user:
        raise ValueError("Email is already registered")

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    user = db.scalar(select(User).where(User.email == email))

    if user is None:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user
