import httpx
import time
import json
import jwt
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), '..', 'config', '.env')
        env_file_encoding = 'utf-8'
        extra = 'ignore'


settings = Settings()

# Basic configuration
BASE_URL = "http://localhost:8000"
CUSTOMER_EMAIL = f"customer_{int(time.time())}@example.com"

CUSTOMER_DATA = {
    "email": CUSTOMER_EMAIL,
    "password": "strongpassword123",
    "first_name": "John",
    "last_name": "Doe",
}
CHEF_DATA = {
    "email": "chef@example.com",
    "password": "chefpassword",
    "first_name": "Gordon",
    "last_name": "Ramsay",
    "role": "chef"
}
WAITER_REGISTER_DATA = {
    "email": "waiter@example.com",
    "password": "waiterpassword",
    "first_name": "Adam",
    "last_name": "Smith",
    "role": "waiter"
}
WAITER_DATA = {
    "username": "waiter@example.com",
    "password": "waiterpassword"
}

session_state = {}


def generate_qr_code_jwt(table_id: int) -> str:
    payload = {"table_id": table_id}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)


def run_demo():
    # PART 0 - Staff registration
    print("Staff registration (Chef and Waiter)")
    httpx.post(f"{BASE_URL}/auth/register", json=CHEF_DATA)
    httpx.post(f"{BASE_URL}/auth/register", json=WAITER_REGISTER_DATA)
    print("[INFO] Staff users created or already exist.")

    # PART 1 - Client

    # Step 1 - Registration
    print("Client registration")
    response = httpx.post(f"{BASE_URL}/auth/register", json=CUSTOMER_DATA)
    response.raise_for_status()
    print(response)

    # Step 2 - Logging in
    print("Client logging in")
    login_data = {"username": CUSTOMER_DATA["email"], "password": CUSTOMER_DATA["password"]}
    response = httpx.post(f"{BASE_URL}/auth/jwt/login", data=login_data)
    response.raise_for_status()
    session_state['customer_token'] = response.json()['access_token']
    print(f"\n[INFO] Client token saved to session state")

    # Step 3 - Scanning QR code
    print("Client scanning QR code (table 12)")
    headers = {"Authorization": f"Bearer {session_state['customer_token']}"}
    qr_jwt = generate_qr_code_jwt(table_id=12)
    qr_data = {"code": qr_jwt}
    response = httpx.post(f"{BASE_URL}/order/scan_qr", headers=headers, json=qr_data)
    response.raise_for_status()
    print(response)

    # Step 4 - Placing an order with payment
    print("Client placing an order")
    order_data = {
        "items": [{"item_id": 1, "quantity": 1}, {"item_id": 2, "quantity": 1}],
        "payment_method": "online"
    }
    response = httpx.post(f"{BASE_URL}/order", headers=headers, json=order_data)
    response.raise_for_status()
    session_state['order_id'] = response.json()['order_id']
    print(f"\n[INFO] Created an order with ID: {session_state['order_id']}")
    print(response)

    # PART 2 - System and staff

    # Step 5 - Fetch Payment Link
    print("Fetching payment link...")
    payment_link = None
    for i in range(50):
        time.sleep(2)
        try:
            headers = {"Authorization": f"Bearer {session_state['customer_token']}"}
            response = httpx.get(f"{BASE_URL}/payment/{session_state['order_id']}/link", headers=headers)
            if response.status_code == 200:
                payment_link = response.json().get("payment_link")
                print(f"\n[SUCCESS] Got PayU payment link:")
                print(f"---------> {payment_link} <---------")
                break
        except httpx.HTTPStatusError as e:
            if e.response.status_code != 404:
                raise e  # Reraise unexpected errors
        print(f"Attempt {i + 1}/50: Payment link not ready yet.")

    if not payment_link:
        print("\n[FATAL] Could not retrieve payment link. Aborting.")
        return

    # Step 6 - Wait for Payment and Verify Status by Polling
    print("\nNow, open the link above in a browser and complete the test payment (or cancel it).")
    print("The script will now poll every 5 seconds to check the order status...")

    final_status = None
    for i in range(12):
        print(f"Polling attempt {i + 1}/12...")
        time.sleep(5)

        headers = {"Authorization": f"Bearer {session_state['customer_token']}"}
        response = httpx.get(f"{BASE_URL}/order/my", headers=headers)

        if response.status_code == 200:
            response_data = response.json()
            order_summary = next(
                (o for o in response_data.get('orders', []) if o.get('order_id') == session_state['order_id']), None)

            if order_summary:
                status = order_summary.get("status")
                if status == 'paid':
                    print(f"\n[SUCCESS] Order {session_state['order_id']} has been paid!")
                    final_status = 'paid'
                    break
                elif status == 'cancelled':
                    print(
                        f"\n[COMPENSATION SUCCESS] Payment failed/cancelled, and order {session_state['order_id']} was correctly cancelled.")
                    final_status = 'cancelled'
                    break
        elif response.status_code != 404:
            response.raise_for_status()

    if not final_status:
        print("\n[FAILURE] Timeout: Order status did not change to 'paid' or 'cancelled' within 60 seconds.")
        return

    if final_status == 'cancelled':
        return

    # print("\nNow, open the link above in a browser and complete the test payment.")
    # print("The script will now poll every 5 seconds to check if the order appears for the staff...")
    #
    # order_visible_for_staff = False
    # with httpx.Client() as client:
    #     chef_login_data = {"username": CHEF_DATA["email"], "password": CHEF_DATA["password"]}
    #     response = client.post(f"{BASE_URL}/auth/jwt/login", data=chef_login_data)
    #     response.raise_for_status()
    #     session_state['chef_token'] = response.json()['access_token']
    #     chef_headers = {"Authorization": f"Bearer {session_state['chef_token']}"}
    #
    #     for i in range(12):  # Max 60 seconds
    #         print(f"Polling attempt {i + 1}/12...")
    #         response = client.get(f"{BASE_URL}/staff/orders", headers=chef_headers)
    #         response.raise_for_status()
    #         staff_orders = response.json()
    #
    #         current_order = next((order for order in staff_orders if order['order_id'] == session_state['order_id']), None)
    #
    #         if current_order and current_order.get('status') == 'paid':
    #             print(f"\n[SUCCESS] Order {session_state['order_id']} appeared in staff view with 'paid' status!")
    #             order_visible_for_staff = True
    #             break
    #         time.sleep(5)
    #
    # if not order_visible_for_staff:
    #     print("\n[FAILURE] Timeout: Order did not appear for staff within 60 seconds.")
    #     return

    with httpx.Client() as client:
        # Step X - Chef logging in
        print("Chef logging in")
        chef_login_data = {"username": CHEF_DATA["email"], "password": CHEF_DATA["password"]}
        response = client.post(f"{BASE_URL}/auth/jwt/login", data=chef_login_data)
        response.raise_for_status()
        session_state['chef_token'] = response.json()['access_token']
        chef_headers = {"Authorization": f"Bearer {session_state['chef_token']}"}
        print("\n[INFO] Chef token saved to session state.")

        # Steps 7-8 - Chef
        print("Chef changing status to 'in_progress'")
        status_update_data = {"new_status": "in_progress"}
        response = client.put(f"{BASE_URL}/staff/orders/{session_state['order_id']}/status", headers=chef_headers,
                              json=status_update_data)
        response.raise_for_status()
        print(response)

        print("Chef changing status to 'ready'")
        status_update_data = {"new_status": "ready"}
        response = client.put(f"{BASE_URL}/staff/orders/{session_state['order_id']}/status", headers=chef_headers,
                              json=status_update_data)
        response.raise_for_status()
        print(response)

        # Step 9 - Waiter logging in
        print("Waiter logging in")
        waiter_login_data = {"username": WAITER_DATA["username"], "password": WAITER_DATA["password"]}
        response = client.post(f"{BASE_URL}/auth/jwt/login", data=waiter_login_data)
        response.raise_for_status()
        session_state['waiter_token'] = response.json()['access_token']
        print(f"\n[INFO] Waiter token saved to session state")
        print(response)

        # Steps 10-11 - Waiter
        waiter_headers = {"Authorization": f"Bearer {session_state['waiter_token']}"}
        print("Waiter checks for ready orders")
        response = client.get(f"{BASE_URL}/staff/orders", headers=waiter_headers)
        response.raise_for_status()
        print(response)

        print("Waiter delievers order and changes status to 'delivered'")
        status_update_data = {"new_status": "delivered"}
        response = client.put(f"{BASE_URL}/staff/orders/{session_state['order_id']}/status", headers=waiter_headers,
                              json=status_update_data)
        response.raise_for_status()
        print(response)

    # PART 3 - Final verification

    # Step 12 - Client verifies final status
    print("Client verifies final status")
    response = httpx.get(f"{BASE_URL}/order/my", headers=headers)
    response.raise_for_status()
    print(response)

    response_data = response.json()
    final_orders_list = response_data.get('orders', [])
    final_order_found = any(item['order_id'] == session_state['order_id'] for item in final_orders_list)

    if final_order_found:
        print("\n[SUCCESS] Full flow finished successfully (Final order state verified)")
    else:
        print("\n[FAILURE] Full flow did not finish successfully (Final order not found)")


if __name__ == "__main__":
    try:
        run_demo()
    except httpx.HTTPStatusError as e:
        print(f"\n[ERROR] Server error: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        print(f"\n[ERROR] API communication error: {e}")