# tests/test_auth_gateway.py

import pytest
import httpx

BASE_URL = "http://localhost:8000"

@pytest.fixture
def user_data():
    # Fixture that provides consistent user data for all tests
    return {
        "email": "testuser@example.com",
        "password": "test1234",
        "first_name": "Test",
        "last_name": "User",
        "role": "client"
    }

@pytest.fixture
def admin_user_data():
    # Fixture for an admin user
    return {
        "email": "adminuser@example.com",
        "password": "admin1234",
        "first_name": "Admin",
        "last_name": "User",
        "role": "admin"
    }

async def get_token(client: httpx.AsyncClient, email: str, password: str) -> str:
    """
    Helper function to retrieve JWT token for a given user.
    """
    response = await client.post(
        "/auth/jwt/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.mark.asyncio
async def test_register_user_via_gateway(user_data):
    """
    Test user registration via Kong.
    Should return 201 if user is created,
    or 400 if user already exists.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/auth/register", json=user_data)
        assert response.status_code in (201, 400)

        if response.status_code == 201:
            data = response.json()
            assert data["email"] == user_data["email"]

@pytest.mark.asyncio
async def test_login_user_via_gateway(user_data):
    """
    Test user login via Kong.
    Should return access token for valid credentials.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        token = await get_token(client, user_data["email"], user_data["password"])
        assert token is not None

@pytest.mark.asyncio
async def test_get_current_user_via_gateway(user_data):
    """
    Test /users/me via Kong.
    Requires valid JWT in Authorization header.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        token = await get_token(client, user_data["email"], user_data["password"])
        headers = {"Authorization": f"Bearer {token}"}
        me_response = await client.get("/users/me", headers=headers)
        assert me_response.status_code == 200
        data = me_response.json()
        assert data["email"] == user_data["email"]
        assert data["role"] == user_data["role"]

@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    """
    Test /users/me with an invalid token via Kong.
    Should return 401 Unauthorized.
    """
    fake_token = "Bearer faketoken.invalid.signature"
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        headers = {"Authorization": fake_token}
        response = await client.get("/users/me", headers=headers)
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_logout_user_via_gateway(user_data):
    """
    Test logout via Kong.
    Should return 204 No Content when token is valid.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        token = await get_token(client, user_data["email"], user_data["password"])
        headers = {"Authorization": f"Bearer {token}"}
        logout_response = await client.post("/auth/jwt/logout", headers=headers)
        assert logout_response.status_code == 204

@pytest.mark.asyncio
async def test_logout_user_invalid_token():
    """
    Test /auth/jwt/logout with an invalid token via Kong.
    Should return 401 Unauthorized.
    """
    fake_token = "Bearer faketoken.invalid.signature"
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        headers = {"Authorization": fake_token}
        response = await client.post("/auth/jwt/logout", headers=headers)
        assert response.status_code == 401

# @pytest.mark.asyncio
# async def test_admin_secret_endpoint_allowed_for_admin(admin_user_data):
#     """
#     Test /admin/secret access with admin role via Kong.
#     Should return 200 or 404 (if endpoint not implemented in backend).
#     """
#     async with httpx.AsyncClient(base_url=BASE_URL) as client:
#         await client.post("/auth/register", json=admin_user_data)
#         token = await get_token(client, admin_user_data["email"], admin_user_data["password"])
#         response = await client.get(
#             "/admin/secret", headers={"Authorization": f"Bearer {token}"}
#         )
#         assert response.status_code in (200, 404)
#
# @pytest.mark.asyncio
# async def test_admin_secret_endpoint_denied_for_non_admin(user_data):
#     """
#     Test /admin/secret access with non-admin role via Kong.
#     Should return 403 Forbidden.
#     """
#     async with httpx.AsyncClient(base_url=BASE_URL) as client:
#         await client.post("/auth/register", json=user_data)
#         token = await get_token(client, user_data["email"], user_data["password"])
#         response = await client.get(
#             "/admin/secret", headers={"Authorization": f"Bearer {token}"}
#         )
#         assert response.status_code == 403
