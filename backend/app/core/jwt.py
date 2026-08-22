from datetime import datetime, timedelta, timezone

import jwt

from app.core.settings import settings

ALGORITHM = "HS256"


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expiration_minutes
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[ALGORITHM],
    )
