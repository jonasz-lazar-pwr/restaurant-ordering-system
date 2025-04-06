# api/core/middleware.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def add_middleware(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
