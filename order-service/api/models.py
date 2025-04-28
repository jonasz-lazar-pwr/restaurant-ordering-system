from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class MenuItem(Base):
    __tablename__ = "menu_items"
    __table_args__ = {"schema": "order_service"}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)

class Order(Base):
    __tablename__ = "orders"
    __table_args__ = {"schema": "order_service"}

    id = Column(Integer, primary_key=True, index=True)
    table_number = Column(String, index=True)
    menu_item_id = Column(Integer, ForeignKey("order_service.menu_items.id"))

    menu_item = relationship("MenuItem")
