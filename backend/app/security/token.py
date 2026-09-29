from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings


def create_access_token(
    user_id: int,
    username: str,
    role: str,
) -> str:
    """
    Create a JWT access token for an authenticated CareSphere user.
    """

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def decode_access_token(token: str) -> dict | None:
    """
    Decode and validate a CareSphere JWT access token.

    Returns the decoded payload when valid.
    Returns None when the token is invalid or expired.
    """

    try:
        return jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except jwt.PyJWTError:
        return None