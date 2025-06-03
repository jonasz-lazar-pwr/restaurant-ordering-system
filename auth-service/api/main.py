# api/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.core.middleware import add_middleware
from api.core.users import fastapi_users
from api.schemas.user import UserRead, UserCreate
from api.core.auth import auth_backend
from fastapi_users.authentication import BearerTransport

@asynccontextmanager
async def lifespan(_app: FastAPI):
    print("Starting up Auth Service...")
    yield
    print("Shutting down Auth Service...")

app = FastAPI(
    title="Auth Service",
    description="Auth Service for managing user authentication and registration.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Apply global middleware
add_middleware(app)

@app.get(
    "/auth/health",
    summary="Health check",
    description="Basic health check endpoint",
    tags=["Health"]
)
def health_check():
    """Simple health check endpoint that returns 200 OK."""
    return {"status": "ok"}

# Define bearer transport
bearer_transport = BearerTransport(tokenUrl="/auth/jwt/login")

# Register authentication routes using custom JWT backend
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"]
)

# Register registration routes
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"]
)

# Register user management routes
app.include_router(
    fastapi_users.get_users_router(UserRead, UserCreate),
    prefix="/auth/users",
    tags=["users"]
)
