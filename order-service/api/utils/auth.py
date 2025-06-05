# === api/utils/auth.py ===

"""
Authentication utilities for extracting user information from JWT tokens.

This module provides helper functions to parse and validate JWT tokens
from the Authorization header of incoming requests.
"""

from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, status

from api.core.config import settings


def extract_user_info(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Extract user information from a JWT Bearer token.

    This function retrieves the Authorization header, validates its format,
    decodes the JWT token using the configured secret, and returns the claims.

    Args:
        authorization (str): The Authorization header, expected in the format "Bearer <token>".

    Returns:
        dict: Decoded JWT payload containing user claims (e.g., 'sub', 'email', 'role').

    Raises:
        HTTPException:
            - 401 if the Authorization header is missing or malformed,
            - 401 if the token is expired or invalid.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header.",
        )

    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid JWT token.",
        )

    return payload
