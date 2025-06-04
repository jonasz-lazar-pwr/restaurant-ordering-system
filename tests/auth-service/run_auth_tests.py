# tests/auth-service/run_auth_tests.py

"""
Run all test modules related to the Auth Service.

This script invokes pytest on the current directory, which should contain
unit and integration tests for all endpoints exposed by the Auth Service.
"""

import sys
from pathlib import Path

import pytest


if __name__ == "__main__":
    auth_tests_dir = Path(__file__).parent
    sys.exit(pytest.main([str(auth_tests_dir)]))
