# api/utils/auth.py

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
            "iss": settings.JWT_ISSUER,
            "role": user.role.value,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email
        }

        return jwt.encode(data, self.secret, algorithm=self.algorithm)


# JWT strategy factory
def get_jwt_strategy() -> CustomJWTStrategy:
    return CustomJWTStrategy(
        secret=settings.JWT_SECRET_KEY,
        lifetime_seconds=settings.JWT_LIFETIME_SECONDS,
        token_audience=[settings.JWT_AUDIENCE],
    )


# Authentication backend definition
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)
