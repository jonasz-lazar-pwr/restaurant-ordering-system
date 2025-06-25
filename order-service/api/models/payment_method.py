# === api/models/payment_method.py ===

"""Enumeration defining supported payment methods for orders."""

import enum


class PaymentMethod(enum.Enum):
    """
    Enum representing available payment methods for an order.

    Attributes:
        online (str): Payment processed through an online gateway.
        cash (str): Payment to be made in cash to the waiter.
    """
    online = "online"
    cash = "cash"
