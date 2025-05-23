# api/core/auth.py

"""
Authentication core module for the API Gateway.

This module provides JWT (JSON Web Token) verification functionalities.
It includes a custom JWTBearer class for FastAPI dependency injection and
a helper function to verify JWT tokens against configured settings.
"""

from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, ExpiredSignatureError, jwt
from .config import settings


class JWTBearer(HTTPBearer):
    """
    A FastAPI security dependency that extracts and optionally validates a Bearer token.

    This class extends FastAPI's HTTPBearer to be used as a dependency.
    It primarily relies on the base class's behavior to extract credentials.
    The actual token verification logic is handled separately by `verify_jwt_token`.

    Attributes:
        auto_error (bool): If True, an HTTPException is raised if the Authorization
                           header is missing or malformed. Defaults to True.
    """

    def __init__(self, auto_error: bool = True):
        """
        Initializes JWTBearer.

        Args:
            auto_error: If True, automatically raises HTTPException for missing
                        or malformed Authorization headers.
        """
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        """
        Makes the class instance callable as a FastAPI dependency.

        This method is invoked by FastAPI when the dependency is used.
        It calls the parent __call__ method to extract the Bearer token credentials.

        Args:
            request: The incoming FastAPI Request object.

        Returns:
            An HTTPAuthorizationCredentials object if a Bearer token is found and
            `auto_error` is False or the header is valid. Returns None if `auto_error`
            is False and no valid header is found. Raises HTTPException if
            `auto_error` is True and the header is invalid or missing.
        """
        return await super().__call__(request)


def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifies a JWT token and returns its payload if valid.

    This function decodes the JWT using the secret key, algorithm, audience,
    and issuer specified in the application settings.

    Args:
        token: The JWT string to verify.

    Returns:
        A dictionary containing the token's payload if verification is successful
        and the token is not expired.
        Returns None if the token is invalid, expired, or if any other
        verification error occurs.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
        return payload
    except ExpiredSignatureError:
        print("Token has expired.")
        return None
    except JWTError as e:
        print(f"JWT validation error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during JWT validation: {e}")
        return None

jwt_bearer_instance = JWTBearer()