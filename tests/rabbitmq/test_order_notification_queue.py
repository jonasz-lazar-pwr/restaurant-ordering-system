# === tests/rabbitmq/test_order_notification_queue.py ===

"""Integration test: Order Service → Notification Queue (RabbitMQ).

This test simulates the publishing of order status update messages by the Order Service.
It verifies that each message is correctly received in the notification service queue.

Assumptions:
    - Messages are sent via the default RabbitMQ exchange.
    - Routing key equals queue name (direct-to-queue delivery).
"""

import pytest

from config import NOTIFICATION_QUEUE
from utils import (
    publish_message_to_queue,
    purge_queue_if_exists,
    consume_one_message_from_queue,
)


@pytest.mark.asyncio
@pytest.mark.parametrize("test_status", [
    "pending",
    "paid",
    "in_progress",
    "ready",
    "delivered",
    "cancelled",
    "failed"
])
async def test_order_service_sends_status_notification(test_status: str):
    """Verify that Order Service publishes status update to the notification queue.

    This test clears the notification queue, sends a status update payload,
    and confirms that the message is received and correctly structured.

    Args:
        test_status (str): Status value to simulate (e.g., 'paid', 'ready').

    Raises:
        AssertionError: If message is missing or doesn't match expected payload.
    """
    test_payload = {
        "order_id": 1000 + hash(test_status) % 1000,
        "new_status": test_status,
        "email": f"{test_status}@example.com"
    }

    await purge_queue_if_exists(NOTIFICATION_QUEUE)
    await publish_message_to_queue(NOTIFICATION_QUEUE, test_payload)
    consumed = await consume_one_message_from_queue(NOTIFICATION_QUEUE)

    assert consumed is not None, f"No message received for status '{test_status}'."
    assert consumed == test_payload, f"Mismatch in payload for status '{test_status}'."
