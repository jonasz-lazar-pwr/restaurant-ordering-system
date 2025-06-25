# === api/models/base.py ===

"""Base class for SQLAlchemy ORM models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class inherited by all ORM models in the project."""
    pass
