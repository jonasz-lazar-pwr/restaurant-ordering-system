# === api/models/menu_item.py ===

"""SQLAlchemy model for menu items in the order service."""

from sqlalchemy import Column, Integer, String, Float
from api.models.base import Base
from api.core.config import settings


class MenuItem(Base):
    """
    Represents a menu item available for ordering.

    Attributes:
        id (int): Unique identifier of the menu item.
        name (str): Name of the dish.
        description (str): Description of the dish.
        price (float): Price of the dish in currency units.
    """
    __tablename__ = "menu_items"
    __table_args__ = {"schema": settings.ORDER_SERVICE_DB_SCHEMA}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
