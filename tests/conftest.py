# tests/conftest.py

"""
Test configuration setup.

Ensures the parent `tests/` directory is added to `sys.path` so that
shared modules (e.g., `config.py`) can be properly imported in all test files.
"""

import sys
from pathlib import Path

# Append the root "tests" directory to the module search path
sys.path.append(str(Path(__file__).resolve().parent))
