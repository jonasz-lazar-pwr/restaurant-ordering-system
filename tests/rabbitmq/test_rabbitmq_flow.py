# === tests/rabbitmq/test_rabbitmq_flow.py ===

"""Integration tests for verifying RabbitMQ message flow.

This module simulates:
- Order Service publishing messages to RabbitMQ exchanges.
- Other services publishing events that Order Service would normally consume.
- Queue bindings and message delivery via exchanges and routing keys.
"""

import pytest

from config import (
    PAYMENTS_EXCHANGE_NAME,
    NOTIFICATIONS_EXCHANGE_NAME,
    ROUTING_KEY_PAYMENT_INITIATED,
    ROUTING_KEY_USER_CREATED,
    ROUTING_KEY_ORDER_PAID,
)

from utils import (
    publish_message_to_exchange,
    consume_one_message_from_queue,
    purge_queue_if_exists,
)

# === Simulating outbound messages from Order Service ===

@pytest.mark.asyncio
async def test_order_service_sends_payment_initiated():
    """Simulate: Order Service sends 'payment.initiated' event.

    Verifies that a message is correctly published to the
    'payment.initiated' queue.
    """
    test_order_id = 101
    expected_payload = {"order_id": test_order_id}
    target_queue_name = ROUTING_KEY_PAYMENT_INITIATED  # Same as queue name

    await purge_queue_if_exists(target_queue_name)

    await publish_message_to_exchange(
        exchange_name=PAYMENTS_EXCHANGE_NAME,
        routing_key=ROUTING_KEY_PAYMENT_INITIATED,
        message_body=expected_payload,
    )

    consumed_message = await consume_one_message_from_queue(target_queue_name)

    assert consumed_message is not None, f"No message received on queue {target_queue_name}"
    assert consumed_message == expected_payload


@pytest.mark.asyncio
@pytest.mark.parametrize("test_status, order_id_offset", [
    ("paid", 201),
    ("cancelled", 202),
    ("in_progress", 203),
    ("ready", 204),
    ("delivered", 205),
    ("failed", 206),
])
async def test_order_service_sends_status_notification(test_status: str, order_id_offset: int):
    """Simulate: Order Service sends an order status update event.

    Verifies that the message is routed to the queue 'order.<status>'.

    Args:
        test_status (str): Status name (e.g., 'paid').
        order_id_offset (int): Unique ID used for test isolation.
    """
    test_order_id = order_id_offset
    expected_payload = {
        "order_id": test_order_id,
        "new_status": test_status
    }

    routing_key = f"order.{test_status}"
    target_queue_name = routing_key

    await purge_queue_if_exists(target_queue_name)

    await publish_message_to_exchange(
        exchange_name=NOTIFICATIONS_EXCHANGE_NAME,
        routing_key=routing_key,
        message_body=expected_payload,
    )

    consumed_message = await consume_one_message_from_queue(target_queue_name)

    assert consumed_message is not None, f"No message received on queue {target_queue_name}"
    assert consumed_message == expected_payload


# === Simulating inbound messages to Order Service ===

@pytest.mark.asyncio
async def test_order_service_reacts_to_order_paid_event():
    """Simulate: Order Service receives 'order.paid' event.

    Verifies that the message would be consumed from the queue,
    indicating that Order Service could react (e.g., update DB or notify).
    This test does not verify DB operations – only message flow.
    """
    simulated_order_id = 301
    payload = {"order_id": simulated_order_id, "new_status": "paid"}
    target_queue_name = ROUTING_KEY_ORDER_PAID

    await purge_queue_if_exists(target_queue_name)

    await publish_message_to_exchange(
        exchange_name=NOTIFICATIONS_EXCHANGE_NAME,
        routing_key=target_queue_name,
        message_body=payload,
    )

    consumed_message = await consume_one_message_from_queue(target_queue_name, timeout=10)

    assert consumed_message is not None, f"No 'order.paid' event received on queue {target_queue_name}"
    assert consumed_message.get("order_id") == simulated_order_id


@pytest.mark.asyncio
async def test_notification_exchange_routes_user_created_event():
    """Test that 'user.created' event is routed properly.

    Publishes a 'user.created' message and checks that it reaches
    the queue with the same name.
    """
    test_user_id = "user_abc_123"
    expected_payload = {
        "user_id": test_user_id,
        "event_type": "user_created"
    }

    target_queue_name = ROUTING_KEY_USER_CREATED

    await purge_queue_if_exists(target_queue_name)

    await publish_message_to_exchange(
        exchange_name=NOTIFICATIONS_EXCHANGE_NAME,
        routing_key=target_queue_name,
        message_body=expected_payload,
    )

    consumed_message = await consume_one_message_from_queue(target_queue_name)

    assert consumed_message is not None, f"No message received on queue {target_queue_name}"
    assert consumed_message == expected_payload
