# tests/test_auth_service_via_api_gateway.py

import pytest
import httpx

BASE_URL = "http://localhost:8000"

@pytest.fixture
def user_data():
    # Fixture that provides consistent user data for all tests
    return {
        "email": f"testuser_{hash(frozenset(range(10000)))}@example.com",
        "password": "test1234",
        "first_name": "Test",
        "last_name": "User",
        "role": "client"
    }

@pytest.mark.asyncio
async def test_register_user(user_data):
    """
    Test user registration endpoint.
    Should return 201 if user is created,
    or 400 if user already exists.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("api/auth/register", json=user_data)
        assert response.status_code in (201, 400)

        if response.status_code == 201:
            data = response.json()
            assert data["email"] == user_data["email"]

@pytest.mark.asyncio
async def test_login_user(user_data):
    """
    Test user login endpoint.
    Should return access token for valid credentials.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post(
            "api/auth/jwt/login",
            data={
                "username": user_data["email"],
                "password": user_data["password"]
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200
        data = response.json()
        print(data["access_token"])
        assert "access_token" in data

@pytest.mark.asyncio
async def test_get_current_user(user_data):
    """
    Test api/auth/users/me endpoint to retrieve current user info.
    Requires valid JWT in Authorization header.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Login first to get access token
        login_response = await client.post(
            "api/auth/jwt/login",
            data={
                "username": user_data["email"],
                "password": user_data["password"]
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Use token to get current user info
        headers = {"Authorization": f"Bearer {token}"}
        me_response = await client.get("api/auth/users/me", headers=headers)
        assert me_response.status_code == 200
        data = me_response.json()
        assert data["email"] == user_data["email"]
        assert data["role"] == user_data["role"]

@pytest.mark.asyncio
async def test_logout_user(user_data):
    """
    Test logout endpoint.
    Should return 204 No Content when token is valid.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Login first to get access token
        login_response = await client.post(
            "api/auth/jwt/login",
            data={
                "username": user_data["email"],
                "password": user_data["password"]
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Call logout endpoint
        headers = {"Authorization": f"Bearer {token}"}
        logout_response = await client.post("api/auth/jwt/logout", headers=headers)
        assert logout_response.status_code == 204