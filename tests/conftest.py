import pytest
import os
import asyncio
from src.core.config import settings
from src.core.engine import CodeForgeEngine


@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "WARNING"  # Reduce log noise during tests
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["MAX_FILE_SIZE"] = "1048576"  # 1MB for tests
    os.environ["GEMINI_API_KEY"] = "test-api-key"  # Mock API key
    yield
    # Cleanup if needed


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_engine():
    """Setup CodeForgeEngine for testing"""
    import asyncio
    from src import web

    async def _init_engine():
        engine = CodeForgeEngine()
        await engine.initialize()
        return engine

    # Initialize engine synchronously for tests
    web.engine = asyncio.run(_init_engine())
    yield
    # Cleanup
    if web.engine:
        asyncio.run(web.engine.shutdown())
    web.engine = None


@pytest.fixture
def sample_module_input():
    """Sample input data for module testing"""
    return {
        "scaffolder": {
            "project_type": "web",
            "project_name": "test_project",
            "description": "A test web project",
        },
        "sentinel": {"code": "def hello(): return 'world'", "language": "python"},
        "alchemist": {"code": "def hello(): return 'world'", "language": "python"},
        "architect": {
            "code": "def calculate(x, y): return x + y",
            "language": "python",
            "context": "simple calculator function",
        },
    }


@pytest.fixture
def mock_ai_response():
    """Mock AI response for testing"""
    return {
        "success": True,
        "data": {
            "analysis": "Test analysis",
            "recommendations": ["Add type hints", "Add docstring"],
            "structure": {
                "files": ["main.py", "utils.py"],
                "directories": ["src", "tests"],
            },
        },
        "metadata": {
            "execution_time": 1.5,
            "language": "python",
            "timestamp": "2025-09-28T08:30:00Z",
        },
    }


@pytest.fixture
def auth_headers():
    """Authentication headers for testing"""
    import base64

    credentials = "admin:admin123"
    auth_header = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {auth_header}"}


@pytest.fixture
def large_test_input():
    """Large input for performance testing"""
    return {
        "input": "x" * 10000,  # 10KB string
        "description": "y" * 5000,
        "requirements": ["z" * 1000] * 5,
    }


@pytest.fixture
def malicious_inputs():
    """Malicious inputs for security testing"""
    return {
        "sql_injection": [
            {"input": "'; DROP TABLE users; --"},
            {"input": "1' OR '1'='1"},
            {"input": "' UNION SELECT password FROM users --"},
        ],
        "xss": [
            {"input": "<script>alert('XSS')</script>"},
            {"input": "<img src=x onerror=alert('XSS')>"},
            {"input": "javascript:alert('XSS')"},
        ],
        "path_traversal": [
            {"input": "../../../etc/passwd"},
            {"input": "..\\..\\..\\windows\\system32\\config\\sam"},
            {"input": "file:///etc/passwd"},
        ],
    }
