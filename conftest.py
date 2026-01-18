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
    # Get the project root directory
    project_root = Path(__file__).parent
    test_env_file = project_root / ".env.test"

    # Load .env.test, overriding any existing environment variables
    if test_env_file.exists():
        load_dotenv(test_env_file, override=True)
    else:
        pytest.fail(f".env.test file not found at {test_env_file}")
