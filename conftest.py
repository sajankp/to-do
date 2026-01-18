"""
Pytest configuration file for shared fixtures.

Note: Python path is configured via pytest.ini (pythonpath = .)
Future fixtures can be added here as needed.
"""

from pathlib import Path

import pytest
from dotenv import load_dotenv


@pytest.fixture(scope="session", autouse=True)
def load_test_env():
    """
    Load .env.test file before running tests.

    This ensures tests use a dedicated test environment configuration
    instead of the developer's local .env file.

    The fixture runs automatically (autouse=True) once per test session.
    """
    # Logic to reload if needed, but relying on top-level execution for now
    pass


# Load .env.test immediately when conftest is imported
# This ensures environment variables are set before app modules are imported during collection
project_root = Path(__file__).parent
test_env_file = project_root / ".env.test"

if test_env_file.exists():
    load_dotenv(test_env_file, override=True)
else:
    # We can't easily fail here without stopping everything, but strictly we should.
    # pytest.fail cannot be used at module level easily.
    import sys

    sys.stderr.write(f"CRITICAL: .env.test file not found at {test_env_file}\n")
    sys.exit(1)
