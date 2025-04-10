# api/main.py

from fastapi import FastAPI
from api.core.middleware import add_middleware
from api.core.users import fastapi_users
from api.schemas.user import UserRead, UserCreate
from api.core.auth import auth_backend

from fastapi_users.authentication import BearerTransport

app = FastAPI(
    title="Auth Service API",
    description="REST API for auth and user management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware for development
add_middleware(app)

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
    prefix="/users",
    tags=["users"]
)

@app.get(
    "/",
    summary="Health check",
    tags=["Health"]
)
def health_check():
    """Simple health check endpoint that returns 200 OK."""
    return {"status": "ok"}

# @app.get(
#     "/admin/secret",
#     tags=["admin"]
# )
# def get_admin_secret():
#     """Endpoint tavailable only to admin users."""
#     return {"secret": "Top secret info for admins only."}



# @app.post(
#     "/api/register-user",
#     summary="Register a new user",
#     description="Registers a new user using attributes from the validated JWT token.",
#     status_code=201,
#     responses={
#         201: {"description": "User created successfully"},
#         204: {"description": "User already exists"},
#         400: {"description": "Missing required user attributes in token"},
#         401: {"description": "Unauthorized – invalid or missing token"}
#     },
#     tags=["Users"],
#     dependencies=[Depends(JWTBearer())]
# )
# def register_user(
#     payload: dict = Depends(JWTBearer()),
#     db: Session = Depends(get_db)
# ):
#     """
#     Extracts user information from a validated JWT token and registers the user
#     in the db if they don't already exist.
#     """
#     sub = payload.get("sub")
#     email = payload.get("email")
#     first_name = payload.get("given_name")
#     last_name = payload.get("family_name")
#
#     if not sub or not email or not first_name or not last_name:
#         raise HTTPException(status_code=400, detail="Missing required user attributes in token")
#
#     user = db.query(User).filter(User.sub == sub).first()
#     if user:
#         return Response(status_code=status.HTTP_204_NO_CONTENT)
#
#     new_user = User(
#         sub=sub,
#         email=email,
#         first_name=first_name,
#         last_name=last_name
#     )
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
#
#     return {"message": "User created successfully"}
