# tests/notification-service/run_notification_tests.py

"""Test runner for the Notification Service.

This script discovers and runs all pytest tests located in the
notification-service/ directory.
"""

import sys
from pathlib import Path

import pytest


if __name__ == "__main__":
    notification_tests_dir = Path(__file__).parent
    sys.exit(pytest.main([str(notification_tests_dir)]))