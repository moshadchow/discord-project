"""JWT token creation and verification."""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from ..config import load_auth_config


def create_access_token(user_id: int, username: str, role: str) -> str:
    """Create a signed JWT access token."""
    config = load_auth_config()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=config.jwt_access_token_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, config.jwt_secret_key, algorithm=config.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token.

    Returns the payload dict on success.
    Raises JWTError on expired or invalid tokens.
    """
    config = load_auth_config()
    return jwt.decode(token, config.jwt_secret_key, algorithms=[config.jwt_algorithm])
