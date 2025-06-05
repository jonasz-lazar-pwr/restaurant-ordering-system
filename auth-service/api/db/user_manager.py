# api/db/user_manager.py

from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users import BaseUserManager, UUIDIDMixin
from api.models.user import User
from api.core.config import settings
from api.db.session import async_session
from uuid import UUID


# Custom user manager with token secrets
class UserManager(UUIDIDMixin, BaseUserManager[User, UUID]):
    reset_password_token_secret = settings.JWT_SECRET_KEY
    verification_token_secret = settings.JWT_SECRET_KEY


# Dependency to inject the user manager
async def get_user_manager():
    async with async_session() as session:
        yield UserManager(SQLAlchemyUserDatabase(session, User))
