# api/utils/users.py

from fastapi_users import FastAPIUsers
from api.models.user import User
from api.db.user_manager import get_user_manager
from uuid import UUID
from api.utils.auth import auth_backend


# Main FastAPI Users object that connects all parts
fastapi_users = FastAPIUsers[User, UUID](
    get_user_manager,
    [auth_backend],
)

# Dependency for getting the current logged-in active user
current_active_user = fastapi_users.current_user(active=True)
