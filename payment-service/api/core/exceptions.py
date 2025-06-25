# === api/core/exceptions.py ===

"""Custom exception classes for handling PayU-related errors."""


class PayUError(Exception):
    """Base exception for PayU communication errors."""
    pass


class TokenError(PayUError):
    """Exception raised when obtaining an authentication token fails."""
    pass


class OrderError(PayUError):
    """Exception raised for errors related to PayU order operations."""
    pass
