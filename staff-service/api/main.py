# api/main.py

"""Entry point for the Staff Service."""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from api.core.middleware import add_middleware
from api.routes.order import router as orders_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    print("Starting up Staff Service...")
    yield
    print("Shutting down Staff Service...")


app = FastAPI(
    title="Staff Service",
    description="Staff Service API for managing staff operations.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Apply global middleware
add_middleware(app)


@app.get(
    "/staff/health",
    summary="Health check",
    description="Basic health check endpoint.",
    tags=["Health"]
)
def health_check():
    """Simple health check endpoint that returns 200 OK."""
    return {"status": "ok"}


# Register routers
app.include_router(orders_router, prefix="/staff", tags=["Order"])
