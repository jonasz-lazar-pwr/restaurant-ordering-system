# api/models/models.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base
from ..core.config import settings


class MenuItem(Base):
    __tablename__ = "menu_items"
    __table_args__ = {"schema": settings.ORDER_SERVICE_DB_SCHEMA}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)

class Order(Base):
    __tablename__ = "orders"
    __table_args__ = {"schema": settings.ORDER_SERVICE_DB_SCHEMA}

    id = Column(Integer, primary_key=True, index=True)
    table_number = Column(String, index=True)
    menu_item_id = Column(Integer, ForeignKey(f"{settings.ORDER_SERVICE_DB_SCHEMA}.menu_items.id"))

    menu_item = relationship("MenuItem")
