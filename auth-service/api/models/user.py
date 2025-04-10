# api/models/user.py

from typing import Optional
from sqlalchemy import String, TIMESTAMP, Enum as PgEnum, func
from sqlalchemy.orm import Mapped, mapped_column
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from enum import Enum
from .base import Base
from ..core.config import settings


# Enum for available user roles in the system
class UserRole(str, Enum):
    client = "client"
    waiter = "waiter"
    chef = "chef"
    admin = "admin"


# User model extending FastAPI Users base user table (UUID-based)
class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"
    __table_args__ = {"schema": settings.AUTH_SERVICE_DB_SCHEMA}

    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(PgEnum(UserRole), nullable=False, default=UserRole.client)
    created_at: Mapped[Optional[str]] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[Optional[str]] = mapped_column(TIMESTAMP, onupdate=func.now())
