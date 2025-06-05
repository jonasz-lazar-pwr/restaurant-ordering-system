# tests/staff-service/run_staff_tests.py

"""Test runner for the Staff Service.

This script discovers and executes all pytest tests located in the
staff-service/ directory.
"""

import sys
from pathlib import Path

import pytest


if __name__ == "__main__":
    staff_tests_dir = Path(__file__).parent
    sys.exit(pytest.main([str(staff_tests_dir)]))
