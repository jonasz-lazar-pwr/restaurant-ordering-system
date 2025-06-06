# === tests/utils.py ===

"""RabbitMQ and identity utilities for integration testing.

This module provides helper functions for:
- Publishing messages to RabbitMQ queues (via default exchange)
- Consuming and parsing messages from queues
- Purging queues before tests
- Generating unique test users

These functions are used in integration tests across services
(e.g., order-service → payment-service / notification-service).

Dependencies:
    - aio_pika: Async RabbitMQ client
    - config.RABBITMQ_URL: Defined AMQP connection URL
"""

import uuid
import json
import aio_pika

from config import RABBITMQ_URL


def generate_unique_user() -> tuple[str, str]:
    """Generate a unique email and password for user registration tests.

    Returns:
        tuple[str, str]: A tuple (email, password) with randomized email address.
    """
    unique_id = uuid.uuid4().hex[:8]
    return f"user_{unique_id}@test.com", "StrongTestPassword123!"


async def publish_message_to_queue(queue_name: str, message_body: dict) -> None:
    """Publish a JSON-serializable message to a RabbitMQ queue.

    Messages are published via the default exchange using the queue name as routing key.

    Args:
        queue_name (str): Name of the RabbitMQ queue (used as routing key).
        message_body (dict): Message payload to serialize and publish.

    Raises:
        aio_pika.exceptions.AMQPException: On connection or publishing error.
    """
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        message = aio_pika.Message(body=json.dumps(message_body).encode())
        await channel.default_exchange.publish(message, routing_key=queue_name)


async def consume_one_message_from_queue(
    queue_name: str, timeout: int = 7
) -> dict | None:
    """Consume a single message from a RabbitMQ queue.

    If a message is available within the timeout window, it is acknowledged
    and returned as a parsed JSON dictionary.

    Args:
        queue_name (str): The name of the queue to consume from.
        timeout (int, optional): Timeout in seconds (default is 7).

    Returns:
        dict | None: Parsed message body if received, else None.

    Raises:
        aio_pika.exceptions.AMQPException: On channel or queue error.
    """
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        queue = await channel.get_queue(queue_name, ensure=False)
        try:
            incoming = await queue.get(timeout=timeout, fail=False)
            if incoming:
                await incoming.ack()
                return json.loads(incoming.body.decode())
        except Exception:
            pass
        return None


async def purge_queue_if_exists(queue_name: str) -> None:
    """Delete all messages from a RabbitMQ queue if it exists.

    This is used to ensure test isolation and clean state for each test case.

    Args:
        queue_name (str): The name of the queue to purge.

    Raises:
        aio_pika.exceptions.AMQPException: On connection or purge failure.
    """
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        try:
            queue = await channel.get_queue(queue_name, ensure=False)
            await queue.purge()
            print(f"[✔] Purged queue: {queue_name}")
        except aio_pika.exceptions.AMQPException as e:
            print(f"[!] AMQP error while purging '{queue_name}': {e}")
        except Exception as e:
            print(f"[!] Unexpected error while purging '{queue_name}': {e}")
