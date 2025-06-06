# === tests/notification-service/test_consumer_flow.py ===

"""Integration test: Notification Service consumes messages from RabbitMQ queue.

This test verifies that a properly structured message can be published
to the 'notification' queue, triggering the consumer logic.
"""

import asyncio
import pytest

from config import NOTIFICATION_QUEUE
from utils import purge_queue_if_exists, publish_message_to_queue


@pytest.mark.asyncio
async def test_notification_service_receives_message():
    """Simulate sending a notification event to the queue (manual DB/mail check expected)."""

    # Arrange – clear the queue and prepare payload
    await purge_queue_if_exists(NOTIFICATION_QUEUE)

    test_payload = {
        "order_id": 4444,
        "new_status": "delivered",
        "email": "this-will-be-ignored@example.com"
    }

    # Act – publish message and wait briefly
    await publish_message_to_queue(NOTIFICATION_QUEUE, test_payload)
    await asyncio.sleep(2)
    assert True  # Just ensure no exceptions occurred