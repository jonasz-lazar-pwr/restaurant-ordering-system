# api/models/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime
from .base import Base
from api.core.config import settings

class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = {"schema": settings.PAYMENT_SERVICE_DB_SCHEMA}

    id = Column(Integer, primary_key=True, index=True)
    # order_id = Column(String, unique=True, index=True, nullable=False)
    payu_order_id = Column(String, unique=True, nullable=False)
    amount = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    status = Column(String, nullable=False, default="NEW")
    table_number = Column(String, nullable=False)
    user_id = Column(String, nullable=False)