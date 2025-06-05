# === tests/utils.py ===
"""Utility functions for integration tests involving RabbitMQ and user identity."""

import uuid
import json
import aio_pika

from config import RABBITMQ_URL


def generate_unique_user() -> tuple[str, str]:
    """Generate a unique email and password for test user registration.

    Returns:
        tuple[str, str]: A tuple containing (email, password).
    """
    unique_id = uuid.uuid4().hex[:8]
    email = f"user_{unique_id}@test.com"
    password = "StrongTestPassword123!"
    return email, password


async def publish_message_to_exchange(
    exchange_name: str, routing_key: str, message_body: dict
) -> None:
    """Publish a message to a RabbitMQ exchange with the specified routing key.

    Assumes the exchange exists (e.g., defined via RabbitMQ definitions).

    Args:
        exchange_name (str): Name of the RabbitMQ exchange.
        routing_key (str): Routing key to use for message delivery.
        message_body (dict): The JSON-serializable message payload.
    """
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.get_exchange(exchange_name, ensure=False)
        await exchange.publish(
            aio_pika.Message(body=json.dumps(message_body).encode()),
            routing_key=routing_key
        )


async def consume_one_message_from_queue(
    queue_name: str, timeout: int = 7
) -> dict | None:
    """Consume a single message from the specified RabbitMQ queue.

    Acknowledges the message upon receipt and returns its decoded payload.

    Args:
        queue_name (str): The name of the queue to consume from.
        timeout (int): Timeout in seconds for message availability.

    Returns:
        dict | None: Parsed JSON message body, or None if no message was received.
    """
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        queue = await channel.get_queue(queue_name, ensure=False)
        try:
            incoming_message: aio_pika.abc.AbstractIncomingMessage = await queue.get(
                timeout=timeout, fail=False
            )
            if incoming_message:
                await incoming_message.ack()
                return json.loads(incoming_message.body.decode())
            return None
        except Exception:
            return None


async def purge_queue_if_exists(queue_name: str) -> None:
    """Purge all messages from the specified queue if it exists.

    Args:
        queue_name (str): The name of the queue to purge.

    Notes:
        Logs a warning if the queue does not exist or cannot be accessed.
    """
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        try:
            queue = await channel.get_queue(queue_name, ensure=False)
            await queue.purge()
            print(f"Purged queue: {queue_name}")
        except aio_pika.exceptions.ChannelClosedOnStartup:
            print(f"Queue {queue_name} does not exist or cannot be accessed, skipping purge.")
        except Exception as e:
            print(f"Error purging queue {queue_name}: {e}")
