# api/core/auth.py

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi_users.authentication import AuthenticationBackend, BearerTransport
from fastapi_users.authentication.strategy.jwt import JWTStrategy
from api.models.user import User
from api.core.config import settings
from jose import jwt


# Transport: Bearer tokens via Authorization header
bearer_transport = BearerTransport(tokenUrl="/auth/jwt/login")

# Custom JWT Strategy with additional payload (e.g. role)
class CustomJWTStrategy(JWTStrategy):
    async def write_token(self, user: User) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(seconds=self.lifetime_seconds)

        data: Dict[str, Any] = {
            "aud": self.token_audience,
            "exp": expire,
            "sub": str(user.id),
            "role": user.role,
            "iss": settings.JWT_ISSUER,
        }

        return jwt.encode(data, self.secret, algorithm=self.algorithm)


# JWT strategy factory
def get_jwt_strategy() -> CustomJWTStrategy:
    return CustomJWTStrategy(
        secret=settings.SECRET_KEY,
        lifetime_seconds=settings.JWT_LIFETIME_SECONDS,
        token_audience=[settings.JWT_AUDIENCE],
    )


# Authentication backend definition
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)
