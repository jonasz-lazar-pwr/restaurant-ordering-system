# === api/main.py ===

"""
Notification Service main application.

Initializes the FastAPI app, applies middleware, starts background consumers,
and mounts routes for health checks and notification handling.
"""

import asyncio
import contextlib
from contextlib import asynccontextmanager
from fastapi import FastAPI

from api.core.middleware import add_middleware
from api.db.session import engine
from api.workers.consumer import start_notification_consumer


consumer_task = None  # Background task for consuming RabbitMQ messages


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Define startup and shutdown logic for the notification service."""
    global consumer_task

    print("Starting up notification-service...")
    consumer_task = asyncio.create_task(start_notification_consumer())

    yield

    print("Shutting down notification-service...")
    if consumer_task:
        consumer_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await consumer_task

    await engine.dispose()


# Initialize the FastAPI application
app = FastAPI(
    title="Notification Service",
    description="Handles email notifications using SNS and RabbitMQ.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Apply global middleware
add_middleware(app)


@app.get(
    "/notification/health",
    summary="Health check",
    description="Basic health check endpoint",
    tags=["Health"]
)
def health_check():
    """Returns health status of the service."""
    return {"status": "ok"}
