"""
Utility functions for authentication.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from config import settings
from jose import jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify if the provided password matches the stored hash.

    Args:
        plain_password (str): The plain text password to verify.
        hashed_password (str): The hashed password to compare against.

    Returns:
        bool: True if the passwords match, False otherwise.
    """
    password_bytes = plain_password.encode("utf-8")
    hashed_password_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)


def get_password_hash(password: str) -> str:
    """
    Generate a hash for the provided password.

    Args:
        password (str): The password to hash.

    Returns:
        str: The hashed password.
    """
    salt = bcrypt.gensalt()
    password_bytes = password.encode("utf-8")
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with the provided data and optional expiration time.

    Args:
        data (dict): The data to include in the token.
        expires_delta (Optional[timedelta], optional): The expiration time for the token.
            Defaults to None, which means the token will expire after 15 minutes.

    Returns:
        str: The generated access token.

    Raises:
        JWTError: If there is an error encoding the token.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt
