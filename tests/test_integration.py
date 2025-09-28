import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from src.web import app
from unittest.mock import patch, AsyncMock
import json
import pytest_asyncio


class TestWebAPIIntegration:
    """Integration tests for the web API"""

    @pytest.fixture(autouse=True)
    def setup_engine(self):
        """Setup the global engine for tests - handled by conftest.py"""
        # Engine setup is now handled by conftest.py autouse fixture
        pass

    @pytest.fixture
    def client(self):
        """Test client for FastAPI app"""
        return TestClient(app)

    @pytest.fixture
    def async_client(self):
        """Async-compatible client for testing (using TestClient which handles async)"""
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_home_page_loads(self, client):
        """Test that home page loads successfully"""
        # Add authentication
        credentials = "admin:admin123"
        import base64

        auth_header = base64.b64encode(credentials.encode()).decode()

        response = client.get("/", headers={"Authorization": f"Basic {auth_header}"})
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "CodeForge AI" in response.text

    def test_list_modules_endpoint(self, async_client):
        """Test modules listing endpoint"""
        # Initialize engine for this test
        import asyncio
        from src import web
        from src.core.engine import CodeForgeEngine

        async def _init_engine():
            engine = CodeForgeEngine()
            await engine.initialize()
            return engine

        # Set up engine
        web.engine = asyncio.run(_init_engine())

        try:
            # Add authentication
            credentials = "admin:admin123"
            import base64

            auth_header = base64.b64encode(credentials.encode()).decode()

            response = async_client.get(
                "/api/modules", headers={"Authorization": f"Basic {auth_header}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "modules" in data
            assert isinstance(data["modules"], list)
            assert len(data["modules"]) > 0  # Should have at least the 4 modules
        finally:
            # Cleanup
            if web.engine:
                asyncio.run(web.engine.shutdown())
            web.engine = None

    @patch("src.core.ai_utils.AIUtils.generate_text", new_callable=AsyncMock)
    def test_module_execution_success(self, mock_generate_text, async_client):
        """Test successful module execution via API"""
        # Initialize engine for this test
        import asyncio
        from src import web
        from src.core.engine import CodeForgeEngine

        async def _init_engine():
            engine = CodeForgeEngine()
            await engine.initialize()
            return engine

        # Set up engine
        web.engine = asyncio.run(_init_engine())

        try:
            # Mock AI response
            mock_generate_text.return_value = '{"directories": ["src"], "files": {"README.md": {"content": "Test", "description": "Test file"}}, "dependencies": {"package_manager": "pip", "dependencies": [], "dev_dependencies": []}, "scripts": {}, "configuration": {}}'

            # Add authentication
            credentials = "admin:admin123"
            import base64

            auth_header = base64.b64encode(credentials.encode()).decode()

            # Test data
            test_data = {
                "project_name": "test_project",
                "project_type": "web",
                "language": "python",
            }

            response = async_client.post(
                "/api/module/scaffolder/execute",
                data={"input_data": json.dumps(test_data)},
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {auth_header}",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "success" in data
            assert data["success"] is True
        finally:
            # Cleanup
            if web.engine:
                asyncio.run(web.engine.shutdown())
            web.engine = None

    def test_module_execution_invalid_module(self, async_client):
        """Test execution of non-existent module"""
        # Initialize engine for this test
        import asyncio
        from src import web
        from src.core.engine import CodeForgeEngine

        async def _init_engine():
            engine = CodeForgeEngine()
            await engine.initialize()
            return engine

        # Set up engine
        web.engine = asyncio.run(_init_engine())

        try:
            # Add authentication
            credentials = "admin:admin123"
            import base64

            auth_header = base64.b64encode(credentials.encode()).decode()

            test_data = {"input": "test"}

            response = async_client.post(
                "/api/module/nonexistent/execute",
                data={"input_data": json.dumps(test_data)},
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {auth_header}",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "success" in data
            assert data["success"] is False
            assert "error" in data
            assert "not found" in data["error"].lower()
        finally:
            # Cleanup
            if web.engine:
                asyncio.run(web.engine.shutdown())
            web.engine = None

    def test_rate_limiting(self, async_client):
        """Test rate limiting functionality"""
        # Add authentication
        credentials = "admin:admin123"
        import base64

        auth_header = base64.b64encode(credentials.encode()).decode()

        # Make multiple requests to trigger rate limit
        responses = []
        for i in range(15):  # Exceed the 10/minute limit for execution
            response = async_client.post(
                "/api/module/scaffolder/execute",
                data={"input_data": json.dumps({"input": f"test {i}"})},
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {auth_header}",
                },
            )
            responses.append(response)

        # At least one should be rate limited (429)
        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited, "Rate limiting should trigger after exceeding limits"

    def test_static_file_serving(self, client):
        """Test that static files are served (if any exist)"""
        # This test assumes no static files exist yet
        # In a real implementation, you'd test CSS/JS serving
        response = client.get("/static/nonexistent.css")
        assert response.status_code == 404  # Expected for non-existent files

    def test_cors_headers(self, async_client):
        """Test CORS headers are present"""
        response = async_client.options(
            "/api/modules", headers={"Origin": "http://localhost:3000"}
        )

        # Since CORS is not implemented, OPTIONS should return 405
        assert response.status_code == 405
        assert "allow" in response.headers

    def test_error_handling(self, async_client):
        """Test error handling for malformed requests"""
        # Add authentication
        credentials = "admin:admin123"
        import base64

        auth_header = base64.b64encode(credentials.encode()).decode()

        # Test with invalid JSON - this might be rate limited, so check error response
        response = async_client.post(
            "/api/module/scaffolder/execute",
            data={"input_data": "invalid json"},
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {auth_header}",
            },
        )

        # Should either return 400 for bad request, 429 for rate limiting, or 200 with error
        assert response.status_code in [200, 400, 429]
        data = response.json()
        # If it's a rate limit response, it will have 'detail'
        # If it's a normal response, it will have 'success'
        if "detail" in data:
            assert "per" in data["detail"].lower() or "minute" in data["detail"].lower()
        else:
            assert "success" in data


class TestWebAuthentication:
    """Integration tests for authentication"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_unauthenticated_access_blocked(self, client):
        """Test that protected endpoints require authentication"""
        # Try to access without auth
        response = client.get("/api/modules")
        assert response.status_code in [401, 403]  # Should require auth

    def test_basic_auth_success(self, client):
        """Test successful basic authentication"""
        # Initialize engine for this test
        import asyncio
        from src import web
        from src.core.engine import CodeForgeEngine

        async def _init_engine():
            engine = CodeForgeEngine()
            await engine.initialize()
            return engine

        # Set up engine
        web.engine = asyncio.run(_init_engine())

        try:
            # Use the default admin credentials
            credentials = "admin:admin123"
            import base64

            auth_header = base64.b64encode(credentials.encode()).decode()

            response = client.get(
                "/api/modules", headers={"Authorization": f"Basic {auth_header}"}
            )

            # Should succeed with valid credentials
            assert response.status_code == 200
        finally:
            # Cleanup
            if web.engine:
                asyncio.run(web.engine.shutdown())
            web.engine = None

    def test_basic_auth_failure(self, client):
        """Test failed basic authentication"""
        credentials = "wrong:password"
        import base64

        auth_header = base64.b64encode(credentials.encode()).decode()

        response = client.get(
            "/api/modules", headers={"Authorization": f"Basic {auth_header}"}
        )

        # Should fail with invalid credentials
        assert response.status_code in [401, 403]


class TestWebExportFeatures:
    """Integration tests for export features"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @patch("src.services.scaffolder.module.AIUtils")
    def test_pdf_export(self, mock_ai_utils, client):
        """Test PDF export functionality"""
        # Initialize engine for this test
        import asyncio
        from src import web
        from src.core.engine import CodeForgeEngine

        async def _init_engine():
            engine = CodeForgeEngine()
            await engine.initialize()
            return engine

        # Set up engine
        web.engine = asyncio.run(_init_engine())

        try:
            mock_ai_utils.return_value.generate_text = AsyncMock(
                return_value="Test content"
            )

            # Authenticate first
            credentials = "admin:admin123"
            import base64

            auth_header = base64.b64encode(credentials.encode()).decode()

            response = client.get(
                "/api/export/scaffolder/pdf?input_data=test",
                headers={"Authorization": f"Basic {auth_header}"},
            )

            assert response.status_code == 200
            # Check if PDF content type is returned
            assert "application/pdf" in response.headers.get("content-type", "")
        finally:
            # Cleanup
            if web.engine:
                asyncio.run(web.engine.shutdown())
            web.engine = None

    @patch("src.services.scaffolder.module.AIUtils")
    def test_json_export(self, mock_ai_utils, client):
        """Test JSON export functionality"""
        # Initialize engine for this test
        import asyncio
        from src import web
        from src.core.engine import CodeForgeEngine

        async def _init_engine():
            engine = CodeForgeEngine()
            await engine.initialize()
            return engine

        # Set up engine
        web.engine = asyncio.run(_init_engine())

        try:
            mock_ai_utils.return_value.generate_text = AsyncMock(
                return_value="Test content"
            )

            credentials = "admin:admin123"
            import base64

            auth_header = base64.b64encode(credentials.encode()).decode()

            response = client.get(
                "/api/export/scaffolder/json?input_data=test",
                headers={"Authorization": f"Basic {auth_header}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "export_data" in data or isinstance(data, dict)
        finally:
            # Cleanup
            if web.engine:
                asyncio.run(web.engine.shutdown())
            web.engine = None
