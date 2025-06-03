# api/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.core.middleware import add_middleware
from api.routes import proxy


@asynccontextmanager
async def lifespan(_app: FastAPI):
    print("Starting up API Gateway...")
    yield
    print("Shutting down API Gateway...")

app = FastAPI(
    lifespan=lifespan,
    title="API Gateway",
    description="API Gateway for forwarding requests.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Apply global middleware
add_middleware(app)

@app.get(
    "/health",
    summary="Health check",
    description="Basic health check endpoint",
    tags=["Health"]
)
def health_check():
    return {"status": "ok"}

# Mount routers
app.include_router(proxy.router, prefix="/api")

# app.include_router(auth.router, prefix="/auth", tags=["Auth"])
# app.include_router(order.router, prefix="/order", tags=["Order"])
# app.include_router(payment.router, prefix="/payment", tags=["Payment"])
