# api/schemas/user.py

from fastapi_users import schemas
from typing import Optional
from uuid import UUID
from api.models.user import UserRole


# Schema used to return user data (read-only)
class UserRead(schemas.BaseUser[UUID]):
    first_name: str
    last_name: str
    role: UserRole


# Schema used when creating a new user (during registration)
class UserCreate(schemas.BaseUserCreate):
    first_name: str
    last_name: str
    role: Optional[UserRole] = UserRole.client