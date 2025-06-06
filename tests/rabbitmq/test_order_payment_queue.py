# === tests/rabbitmq/test_order_payment_queue.py ===

"""Integration test: Order Service → Payment Queue (RabbitMQ).

This test simulates the publishing of a full payment payload by the Order Service.
It verifies that the message is received correctly in the RabbitMQ queue intended
for the Payment Service.

Assumptions:
    - Default RabbitMQ exchange is used.
    - Routing key equals queue name (direct publishing).
"""

import pytest

from config import PAYMENT_QUEUE
from utils import (
    publish_message_to_queue,
    purge_queue_if_exists,
    consume_one_message_from_queue,
)


@pytest.mark.asyncio
async def test_order_service_sends_payment_payload():
    """Test that a complete payment payload is published and received.

    Simulates Order Service sending a full payment payload to the Payment Queue.
    The test ensures that:
        - The queue is cleared before the test.
        - A sample payload is published.
        - The message is correctly received and parsed from the queue.

    Raises:
        AssertionError: If the payload is not received or does not match.
    """
    test_payload = {
        "notifyUrl": "https://example.com/notify",
        "customerIp": "127.0.0.1",
        "description": "Order #123 for table 5",
        "currencyCode": "PLN",
        "totalAmount": "5000",
        "buyer": {
            "email": "test@example.com",
            "phone": "123456789",
            "firstName": "Jon",
            "lastName": "Doe",
            "language": "pl"
        },
        "products": [
            {"name": "Burger", "unitPrice": "2500", "quantity": "1"},
            {"name": "Fries", "unitPrice": "2500", "quantity": "1"}
        ]
    }

    await purge_queue_if_exists(PAYMENT_QUEUE)
    await publish_message_to_queue(PAYMENT_QUEUE, test_payload)
    consumed = await consume_one_message_from_queue(PAYMENT_QUEUE)

    assert consumed is not None, "No message received from the payment queue."
    assert consumed == test_payload, "Received payload does not match the sent payload."
