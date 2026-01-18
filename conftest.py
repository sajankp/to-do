"""
Pytest configuration file for shared fixtures.

Note: Python path is configured via pytest.ini (pythonpath = .)
Future fixtures can be added here as needed.
"""

from pathlib import Path

from dotenv import load_dotenv

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
