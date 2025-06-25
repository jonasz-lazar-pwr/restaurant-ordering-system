# === api/services/payu.py ===

"""PayU API client for handling payment operations.

Provides methods to authenticate, fetch payment methods, create orders,
check status, cancel orders, and process refunds via PayU REST API.
"""

import requests

from api.core.config import settings
from api.core.exceptions import TokenError, PayUError, OrderError


class PayUClient:
    """Client to interact with the PayU sandbox API."""

    def __init__(self):
        """Initialize the client with token URL and HTTP session."""
        self.token_url = f"{settings.PAYU_SANDBOX_URL}pl/standard/user/oauth/authorize"
        self.session = requests.Session()
        self.access_token = None

    def authenticate(self) -> str:
        """Authenticate with PayU and retrieve an access token.

        Raises:
            TokenError: If token retrieval fails or token is missing.

        Returns:
            str: Access token string.
        """
        auth_data = {
            "grant_type": "client_credentials",
            "client_id": settings.PAYU_CLIENT_ID,
            "client_secret": settings.PAYU_CLIENT_SECRET,
        }
        response = self.session.post(self.token_url, data=auth_data)
        response.raise_for_status()

        if response.status_code != 200:
            raise TokenError(f"Authenticate error: {response.text}")

        self.access_token = response.json().get("access_token")
        if not self.access_token:
            raise TokenError("No token in response")

        return self.access_token

    def _auth_headers(self) -> dict:
        """Build authentication headers for API requests.

        Returns:
            dict: Headers containing the access token.
        """
        if not self.access_token:
            self.authenticate()
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

    def get_payment_methods(self) -> dict:
        """Fetch available PayU payment methods.

        Raises:
            PayUError: If the API returns a non-200 status.

        Returns:
            dict: JSON response containing payment methods.
        """
        url = f"{settings.PAYU_SANDBOX_URL}api/v2_1/paymethods"
        response = self.session.get(url, headers=self._auth_headers())
        response.raise_for_status()

        if response.status_code != 200:
            raise PayUError(f"Error getting payment methods: {response.text}")
        return response.json()

    def create_order(self, order_data: dict) -> dict:
        """Create a new PayU payment order.

        Args:
            order_data (dict): Payment details payload.

        Raises:
            OrderError: If the order could not be created.

        Returns:
            dict: JSON response with order details.
        """
        url = f"{settings.PAYU_SANDBOX_URL}api/v2_1/orders"
        response = self.session.post(
            url,
            headers=self._auth_headers(),
            json=order_data,
            allow_redirects=False,
        )
        response.raise_for_status()

        if response.status_code not in (201, 302):
            raise OrderError(f"Error creating an order: {response.text}")
        return response.json()

    def get_order_status(self, order_id: str) -> dict:
        """Check the current status of an existing order.

        Args:
            order_id (str): PayU order ID.

        Raises:
            OrderError: If the status request fails.

        Returns:
            dict: JSON response with order status.
        """
        url = f"{settings.PAYU_SANDBOX_URL}api/v2_1/orders/{order_id}"
        response = self.session.get(url, headers=self._auth_headers())
        response.raise_for_status()

        if response.status_code != 200:
            raise OrderError(f"Error checking order status: {response.text}")
        return response.json()

    def cancel_order(self, order_id: str) -> dict:
        """Cancel an existing order.

        Args:
            order_id (str): PayU order ID.

        Raises:
            OrderError: If cancellation fails.

        Returns:
            dict: JSON response confirming cancellation.
        """
        url = f"{settings.PAYU_SANDBOX_URL}api/v2_1/orders/{order_id}"
        response = self.session.delete(url, headers=self._auth_headers())
        response.raise_for_status()

        if response.status_code != 200:
            raise OrderError(f"Error canceling the order: {response.text}")
        return response.json()

    def refund_order(self, order_id: str, refund_data: dict) -> dict:
        """Request a refund for an existing order.

        Args:
            order_id (str): PayU order ID.
            refund_data (dict): JSON payload with refund details.

        Raises:
            PayUError: If refund creation fails.

        Returns:
            dict: JSON response confirming refund.
        """
        url = f"{settings.PAYU_SANDBOX_URL}api/v2_1/orders/{order_id}/refunds"
        response = self.session.post(
            url, headers=self._auth_headers(), json=refund_data
        )
        response.raise_for_status()

        if response.status_code != 200:
            raise PayUError(f"Error creating a refund: {response.text}")
        return response.json()
