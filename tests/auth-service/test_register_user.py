# tests/auth-service/test_register_user.py

"""
Tests for the /auth/register endpoint of the Auth Service.

These tests validate the user registration flow using FastAPI Users.
"""

import pytest
import httpx
import uuid
from config import get_base_url

BASE_URL = get_base_url("auth-service")
REGISTER_ENDPOINT = "/auth/register"


def generate_unique_email() -> str:
    """Generate a unique email address for test user registration."""
    return f"testuser_{uuid.uuid4().hex}@example.com"


@pytest.mark.asyncio
async def test_register_valid_user():
    """Register a valid user and expect 201 Created with returned user data."""
    email = generate_unique_email()
    payload = {
        "email": email,
        "password": "SecureP@ssw0rd",
        "first_name": "Test",
        "last_name": "User",
        "role": "client"
    }

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post(REGISTER_ENDPOINT, json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"
    assert data["role"] == "client"


@pytest.mark.asyncio
async def test_register_user_missing_fields():
    """Try to register a user with missing required fields. Expect 422 Unprocessable Entity."""
    email = generate_unique_email()
    payload = {
        "email": email
        # Missing password, first_name, last_name, role
    }

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post(REGISTER_ENDPOINT, json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_user_existing_email():
    """Try to register a user with an email that already exists. Expect 400 Bad Request."""
    email = generate_unique_email()
    payload = {
        "email": email,
        "password": "InitialPass123!",
        "first_name": "John",
        "last_name": "Doe",
        "role": "client"
    }

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # First registration
        await client.post(REGISTER_ENDPOINT, json=payload)
        # Duplicate registration
        response = await client.post(REGISTER_ENDPOINT, json=payload)

    assert response.status_code in (400, 409)
    data = response.json()
    assert "detail" in data
