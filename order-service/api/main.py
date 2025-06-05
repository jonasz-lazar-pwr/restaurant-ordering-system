# === api/main.py ===

"""Main application entrypoint for the Order Service.

This file initializes the FastAPI application, configures RabbitMQ consumers
on service startup, and includes all relevant routers and middleware.
"""

import aio_pika
from fastapi import FastAPI
from contextlib import asynccontextmanager

from api.models import OrderStatus
from api.core.config import settings
from api.core.middleware import add_middleware
from api.routes.scan import router as scan_router
from api.routes.order import router as order_router
from api.consumers.order_event_handlers import get_handler_for_status

background_tasks = []


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan context for startup and shutdown routines.

    This function initializes the connection to RabbitMQ,
    sets up queue consumers for selected order statuses, and
    gracefully shuts down the connection on application termination.

    Args:
        _app (FastAPI): The FastAPI application instance.
    """
    global background_tasks

    print("Starting up Order Service...")

    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()

    statuses_to_handle = [
        OrderStatus.paid,
        # Add additional statuses here if needed
    ]

    for status in statuses_to_handle:
        queue_name = f"order.{status.value}"
        queue = await channel.declare_queue(queue_name, durable=True)
        handler = get_handler_for_status(status)

        await queue.consume(handler)
        print(f"Listening on queue '{queue_name}'...")

    yield

    print("Shutting down Order Service...")
    for task in background_tasks:
        task.cancel()

    await connection.close()


app = FastAPI(
    title="Order Service",
    description="Order Service API for managing orders and payments.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Apply global middleware
add_middleware(app)


@app.get(
    "/order/health",
    summary="Health check",
    description="Returns a simple health status of the Order Service.",
    tags=["Health"]
)
def health_check():
    """Returns health status of the service."""
    return {"status": "ok"}


# Register routers
app.include_router(scan_router, prefix="/order", tags=["Scan"])
app.include_router(order_router, prefix="/order", tags=["Order"])
