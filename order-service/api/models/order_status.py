# === api/models/order_status.py ===

"""Enumeration defining possible statuses of a customer order."""

import enum


class OrderStatus(enum.Enum):
    """
    Enum representing the various states an order can be in.

    Attributes:
        pending (str): Order created but not yet paid.
        paid (str): Order has been paid and is awaiting preparation.
        in_progress (str): Order is being prepared by the kitchen.
        ready (str): Order is ready for pickup by the waiter.
        delivered (str): Order has been delivered to the customer.
        cancelled (str): Order was cancelled (by user or kitchen).
        failed (str): Order processing failed (e.g., payment issues).
    """
    pending = "pending"
    paid = "paid"
    in_progress = "in_progress"
    ready = "ready"
    delivered = "delivered"
    cancelled = "cancelled"
    failed = "failed"
