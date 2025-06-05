# === tests/auth-service/test_register_user.py ===

"""Tests for the /auth/register endpoint of the Auth Service.

These tests validate the user registration flow using FastAPI Users.
"""

import pytest
import httpx
from config import get_base_url, AUTH_ENDPOINTS
from utils import generate_unique_user

AUTH_BASE_URL = get_base_url("auth-service")


@pytest.mark.asyncio
async def test_register_valid_user():
    """
    Register a valid user and expect 201 Created with user data.

    Expected response:
        HTTP 201 with JSON containing email, first_name, last_name, and role.
    """
    email, password = generate_unique_user()
    payload = {
        "email": email,
        "password": password,
        "first_name": "Test",
        "last_name": "User",
        "role": "client"
    }

    async with httpx.AsyncClient(base_url=AUTH_BASE_URL) as client:
        response = await client.post(AUTH_ENDPOINTS["register"], json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"
    assert data["role"] == "client"


@pytest.mark.asyncio
async def test_register_user_missing_fields():
    """
    Try to register a user with missing required fields.

    Expected response:
        HTTP 422 Unprocessable Entity due to validation errors.
    """
    email, _ = generate_unique_user()
    payload = {
        "email": email
        # Missing: password, first_name, last_name, role
    }

    async with httpx.AsyncClient(base_url=AUTH_BASE_URL) as client:
        response = await client.post(AUTH_ENDPOINTS["register"], json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_user_existing_email():
    """
    Attempt to register a user with an already used email.

    Expected response:
        HTTP 400 or 409 with a detailed error message.
    """
    email, password = generate_unique_user()
    payload = {
        "email": email,
        "password": password,
        "first_name": "John",
        "last_name": "Doe",
        "role": "client"
    }

    async with httpx.AsyncClient(base_url=AUTH_BASE_URL) as client:
        # First registration should succeed
        first = await client.post(AUTH_ENDPOINTS["register"], json=payload)
        assert first.status_code == 201

        # Second registration should fail
        response = await client.post(AUTH_ENDPOINTS["register"], json=payload)

    assert response.status_code in (400, 409)
    assert "detail" in response.json()
