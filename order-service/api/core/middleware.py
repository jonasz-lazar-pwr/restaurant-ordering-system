# api/core/middleware.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.core.config import settings


def add_middleware(app: FastAPI):
    allow_origins = [origin.strip() for origin in settings.CORS_ALLOW_ORIGINS.split(",")]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
