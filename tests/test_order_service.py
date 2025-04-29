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

@pytest.fixture
def create_order():
    with httpx.Client(base_url=BASE_URL) as client:
        client.post("/scan_qr/", json={"code": "stolik_1"})
        client.post("/order/", json={"qr_code": "stolik_1", "item_id": 1})

def test_scan_qr(qr_data):
    with httpx.Client(base_url=BASE_URL) as client:
        response = client.post("/scan_qr/", json=qr_data)
        assert response.status_code == 200
        data = response.json()
        assert "menu" in data
        assert len(data["menu"]) > 0
        assert "message" in data


def test_order_item(order_data):
    with httpx.Client(base_url=BASE_URL) as client:
        response = client.post("/scan_qr/", json={"code": order_data["qr_code"]})
        assert response.status_code == 200

        response = client.post("/order/", json=order_data)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert f"Ordered Pizza Margherita for table {order_data['qr_code']} successfully!" in data["message"]

def test_get_orders(create_order):
    with httpx.Client(base_url=BASE_URL) as client:
        response = client.get("/orders/stolik_1")

        assert response.status_code == 200
        data = response.json()
        assert "table" in data
        assert data["table"] == "stolik_1"
        assert "orders" in data
        assert len(data["orders"]) > 0
        assert data["orders"][0]["name"] == "Pizza Margherita"