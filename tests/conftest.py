import pytest
import os
from src.core.config import settings


@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["ENVIRONMENT"] = "development"
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["MAX_FILE_SIZE"] = "1048576"  # 1MB for tests
    yield
    # Cleanup if needed
