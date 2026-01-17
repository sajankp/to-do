"""JWT utility functions for token encoding and decoding."""
from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()
SECRET_KEY = settings.secret_key
PASSWORD_ALGORITHM = settings.password_algorithm


def decode_jwt_token(token: str):
    """Decode a JWT token and return its payload.

    Args:
        token: The JWT token string to decode

    Returns:
        dict: The decoded payload if successful, None if decoding fails
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[PASSWORD_ALGORITHM])
        return payload
    except JWTError:
        return None
