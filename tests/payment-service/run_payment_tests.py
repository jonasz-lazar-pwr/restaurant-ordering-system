# tests/payment-service/run_payment_tests.py

"""Test runner for the Payment Service.

This script discovers and executes all pytest tests located in the
payment-service/ directory.
"""

import sys
from pathlib import Path

import pytest


if __name__ == "__main__":
    payment_tests_dir = Path(__file__).parent
    sys.exit(pytest.main([str(payment_tests_dir)]))
