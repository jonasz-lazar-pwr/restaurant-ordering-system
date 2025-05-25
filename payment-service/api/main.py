# === api/main.py ===

"""Main entrypoint for the Payment Service.

Initializes the FastAPI app, registers middleware, routes, and starts
the background RabbitMQ consumer for payment messages.
"""

import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI

# from fastapi import FastAPI, HTTPException
# from .core.payu_client import PayUClient
# from .schemas.payment import CreatePaymentRequest, CreateRefundRequest
# from .core.exceptions import PayUError, OrderError
# from .core.config import settings

from api.routes.payment import router as payment_router
from api.core.middleware import add_middleware
from api.services.payu import PayUClient
from api.workers.consumer import start_payment_consumer

consumer_task = None  # Background consumer task


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan context manager.

    Starts the background payment consumer on startup and gracefully shuts
    it down on application shutdown.

    Args:
        _app (FastAPI): The FastAPI application instance.

    Yields:
        None
    """
    global consumer_task
    print("Starting payment-service...")
    consumer_task = asyncio.create_task(start_payment_consumer())
    yield
    print("Shutting down payment-service...")
    if consumer_task:
        consumer_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await consumer_task


# Initialize FastAPI app
app = FastAPI(
    title="Payment Service",
    description="Handles PayU payments triggered from RabbitMQ.",
    version="1.0.0",
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
    """Health check endpoint.

    Returns:
        dict: A simple dictionary with service status.
    """
    return {"status": "ok"}


# Register payment-related routes
app.include_router(payment_router, prefix="/payment", tags=["Payment"])


# @app.post("/payments")
# def create_payment(payment: CreatePaymentRequest):
#     try:
#         order_data = {
#             "notifyUrl": payment.notifyUrl,
#             "customerIp": payment.customerIp,
#             "merchantPosId": settings.PAYU_MERCHANT_POS_ID,
#             "description": payment.description,
#             "currencyCode": payment.currencyCode,
#             "totalAmount": payment.totalAmount,
#             "buyer": payment.buyer.model_dump(),
#             "products": [product.model_dump() for product in payment.products]
#         }
#         response = payu_client.create_order(order_data)
#         return {
#             "orderId": response.get("orderId"),
#             "redirectUri": response.get("redirectUri")
#         }
#     except OrderError as e:
#         raise HTTPException(status_code=502, detail=str(e))

# @app.get("/payments/{order_id}")
# def get_payment_status(order_id: str):
#     try:
#         status = payu_client.get_order_status(order_id)
#         return status
#     except OrderError as e:
#         raise HTTPException(status_code=502, detail=str(e))
    
# @app.delete("/payments/{order_id}")
# def cancel_payment(order_id: str):
#     try:
#         status = payu_client.cancel_order(order_id)
#         return status
#     except OrderError as e:
#         raise HTTPException(status_code=502, detail=str(e))

# @app.post("/payments/{order_id}/refund")
# def refund_payment(order_id: str, refund: CreateRefundRequest):
#     try:
#         refund_data = {
#             "refund": {
#                 "description" : refund.description,
#                 "currencyCode" : refund.currencyCode
#             }
#         }
#         response = payu_client.refund_order(order_id, refund_data)
#         return response
#     except PayUError as e:
#         raise HTTPException(status_code=502, detail=str(e))
