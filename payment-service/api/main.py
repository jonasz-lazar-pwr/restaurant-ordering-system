# === api/main.py ===

"""Main entrypoint for the Payment Service.

Initializes the FastAPI app, registers middleware, and routes.
The RabbitMQ consumer for payment requests has been replaced by a synchronous endpoint.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.routes.payment import router as payment_router
from api.core.middleware import add_middleware
from api.services.payu import PayUClient
from api.workers.consumer import start_payment_consumer
from api.workers.refund_consumer import start_refund_consumer
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    print("Starting payment-service...")
    payment_consumer_task = asyncio.create_task(start_payment_consumer())
    refund_consumer_task = asyncio.create_task(start_refund_consumer())
    yield
    print("Shutting down payment-service...")
    payment_consumer_task.cancel()

# Initialize FastAPI app
app = FastAPI(
    title="Payment Service",
    description="Handles PayU payments via synchronous API calls.",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Initialize PayU client
payu_client = PayUClient()

# Apply global middleware (e.g., CORS)
add_middleware(app)

@app.get(
    "/payment/health",
    summary="Health check",
    description="Returns a simple health status of the Payment Service.",
    tags=["Health"],
)
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

# Register payment-related routes
app.include_router(payment_router, prefix="/payment", tags=["Payment"])