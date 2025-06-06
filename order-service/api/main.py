# === api/main.py ===

"""Main application entrypoint for the Order Service.

This file initializes the FastAPI application, configures RabbitMQ consumers
on service startup, and includes all relevant routers and middleware.
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from api.core.middleware import add_middleware
from api.routes.scan import router as scan_router
from api.routes.order import router as order_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    print("Starting up Order Service...")
    yield
    print("Shutting down Order Service...")


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
