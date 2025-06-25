import requests
import json
from .exceptions import TokenError, PayUError, OrderError
from api.core.config import settings

# import logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

class PayUClient:
    def __init__(self):
        self.token_url = f"{settings.PAYU_SANDBOX_URL}pl/standard/user/oauth/authorize"
        self.session = requests.Session()
        self.access_token = None

    def authenticate(self):
        auth_data = {
            "grant_type": "client_credentials",
            "client_id": settings.PAYU_CLIENT_ID,
            "client_secret": settings.PAYU_CLIENT_SECRET
        }
        response = self.session.post(self.token_url, data=auth_data)
        response.raise_for_status()  # Check for HTTP error

        if response.status_code != 200:
            raise TokenError(f"Authenticate error: {response.text}")
        
        self.access_token = response.json().get("access_token")
        if not self.access_token:
            raise TokenError("No token in response")
        return self.access_token
    
    def _auth_headers(self):
        if not self.access_token:
            self.authenticate()
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }
    
    def get_payment_methods(self):
        url = f"{settings.PAYU_SANDBOX_URL}api/v2_1/paymethods"
        response = self.session.get(url, headers=self._auth_headers())
        response.raise_for_status()  # Check for HTTP error

        if response.status_code != 200:
            raise PayUError(f"Error getting payment methods: {response.text}")
        return response.json()
    
    def create_order(self, order_data):
        url = f"{settings.PAYU_SANDBOX_URL}api/v2_1/orders"
        # if allow_redirects=False then you get json as response
        # else you get html - redirected
        response = self.session.post(url, headers=self._auth_headers(), json=order_data, allow_redirects=False)
        response.raise_for_status()  # Check for HTTP error

        if response.status_code != 302 and response.status_code != 201:
            raise OrderError(f"Error creating an order: {response.text}")
        return response.json()

    def get_order_status(self, order_id):
        url = f"{settings.PAYU_SANDBOX_URL}api/v2_1/orders/{order_id}"
        response = self.session.get(url, headers=self._auth_headers())
        response.raise_for_status()  # Check for HTTP error

        if response.status_code != 200:
            raise OrderError(f"Error checking order status: {response.text}")
        return response.json()
    
    def cancel_order(self, order_id):
        url = f"{settings.PAYU_SANDBOX_URL}api/v2_1/orders/{order_id}"
        response = self.session.delete(url, headers=self._auth_headers())
        response.raise_for_status()  # Check for HTTP error

        if response.status_code != 200:
            raise OrderError(f"Error canceling the order: {response.text}")
        return response.json()

    def refund_order(self, order_id, refund_data):
        url = f"{settings.PAYU_SANDBOX_URL}api/v2_1/orders/{order_id}/refunds"

        # logger.debug(f"Refund data: {refund_data}")
        # logger.debug(f"With header: {self._auth_headers()}")

        response = self.session.post(url, headers=self._auth_headers(), json=refund_data)
        response.raise_for_status()  # Check for HTTP error

        if response.status_code != 200:
            raise PayUError(f"Error creating a refund: {response.text}")
        return response.json()