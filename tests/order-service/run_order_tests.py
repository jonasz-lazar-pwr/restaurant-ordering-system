# tests/order-service/run_order_tests.py

"""Test runner for the Order Service.

This script discovers and executes all pytest tests located in the
order-service/ directory.
"""

import sys
from pathlib import Path

import pytest


if __name__ == "__main__":
    order_tests_dir = Path(__file__).parent
    sys.exit(pytest.main([str(order_tests_dir)]))
