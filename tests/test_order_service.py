# tests/test_order_service.py

import pytest
import httpx

BASE_URL = "http://localhost:8003"

@pytest.fixture
def qr_data():
    return {"code": "stolik_1"}

@pytest.fixture
def order_data():
    return {"qr_code": "stolik_1", "item_id": 1}


@pytest.mark.asyncio
async def test_scan_qr(qr_data):
    """
    Test scanning a valid QR code.
    Should return menu and 200 status.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/scan_qr/", json=qr_data)
        assert response.status_code == 200
        data = response.json()
        assert "menu" in data
        assert len(data["menu"]) > 0
        assert "message" in data


@pytest.mark.asyncio
async def test_order_item(order_data):
    """
    Test placing a valid order after scanning QR.
    Should return 200 and confirmation message.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        await client.post("/scan_qr/", json={"code": order_data["qr_code"]})

        response = await client.post("/order/", json=order_data)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert f"Ordered Pizza Margherita for table {order_data['qr_code']} successfully!" in data["message"]


@pytest.mark.asyncio
async def test_get_orders(qr_data, order_data):
    """
    Test retrieving orders for a specific table.
    Assumes a previous successful order was made.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        await client.post("/scan_qr/", json=qr_data)
        await client.post("/order/", json=order_data)

        response = await client.get(f"/orders/{qr_data['code']}")
        assert response.status_code == 200
        data = response.json()
        assert data["table"] == qr_data["code"]
        assert "orders" in data
        assert len(data["orders"]) > 0
        assert data["orders"][0]["item"] == "Pizza Margherita"


@pytest.mark.asyncio
async def test_order_invalid_item():
    """
    Test ordering an item that doesn't exist.
    Should return 404.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        await client.post("/scan_qr/", json={"code": "stolik_x"})
        response = await client.post("/order/", json={"qr_code": "stolik_x", "item_id": 9999})
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_orders_invalid_table():
    """
    Test retrieving orders for a non-existent table.
    Should return 404.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/orders/non_existing_table")
        assert response.status_code == 404


# @pytest.mark.asyncio
# async def test_scan_qr_invalid_code():
#     """
#     Test scanning an invalid QR code.
#     Should return 400.
#     """
#     async with httpx.AsyncClient(base_url=BASE_URL) as client:
#         response = await client.post("/scan_qr/", json={"code": "not_existing"})
#         assert response.status_code == 400
