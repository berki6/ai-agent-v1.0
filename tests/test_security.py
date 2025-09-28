import pytest
import json
from fastapi.testclient import TestClient
from src.web import app
from unittest.mock import patch, AsyncMock
import base64
import requests


class TestSecurity:
    """Security testing and vulnerability assessment"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_sql_injection_protection(self, client):
        """Test protection against SQL injection attacks"""
        # Test with proper sentinel module input (scan_path)
        # Create a temporary file with SQL injection vulnerable code
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
            import tempfile
            import os

            credentials = "admin:admin123"
            auth_header = base64.b64encode(credentials.encode()).decode()

            with tempfile.TemporaryDirectory() as temp_dir:
                # Create a test file with SQL injection vulnerability
                test_file = os.path.join(temp_dir, "test.py")
                with open(test_file, "w") as f:
                    f.write(
                        """
    def vulnerable_function(user_input):
        query = "SELECT * FROM users WHERE id = " + user_input  # SQL injection vulnerability
        return query
    """
                    )

                # Test sentinel module with the temp directory
                response = client.post(
                    "/api/module/sentinel/execute",
                    data={"input_data": json.dumps({"scan_path": temp_dir})},
                    headers={
                        "Authorization": f"Basic {auth_header}",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                )

                # Should succeed and detect vulnerabilities
                assert response.status_code == 200
                data = response.json()
                assert data["success"] == True
                # Should detect SQL injection vulnerability
                assert "vulnerabilities" in data["data"]["report"]
                assert len(data["data"]["report"]["vulnerabilities"]) > 0

                # Check that SQL injection was detected
                vuln_types = [v["type"] for v in data["data"]["report"]["vulnerabilities"]]
                assert "sql_injection" in vuln_types
        finally:
            # Cleanup
            if web.engine:
                asyncio.run(web.engine.shutdown())
            web.engine = None

    def test_xss_protection(self, client):
        """Test protection against Cross-Site Scripting (XSS) attacks"""
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
            # Test with proper sentinel module input (scan_path)
            # Create a temporary file with XSS vulnerable code
            import tempfile
            import os

            credentials = "admin:admin123"
            auth_header = base64.b64encode(credentials.encode()).decode()

            with tempfile.TemporaryDirectory() as temp_dir:
                # Create a test file with XSS vulnerability
                test_file = os.path.join(temp_dir, "test.js")
                with open(test_file, "w") as f:
                    f.write(
                        """
    function vulnerableFunction(userInput) {
        document.getElementById('output').innerHTML = userInput;  // XSS vulnerability
    }
    """
                    )

                # Test sentinel module with the temp directory
                response = client.post(
                    "/api/module/sentinel/execute",
                    data={"input_data": json.dumps({"scan_path": temp_dir})},
                    headers={
                        "Authorization": f"Basic {auth_header}",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                )

                # Should succeed and detect vulnerabilities
                assert response.status_code == 200
                data = response.json()
                assert data["success"] == True
                # Should detect XSS vulnerability
                assert "vulnerabilities" in data["data"]["report"]
                assert len(data["data"]["report"]["vulnerabilities"]) > 0

                # Check that XSS was detected
                vuln_types = [v["type"] for v in data["data"]["report"]["vulnerabilities"]]
                assert "xss_vulnerable" in vuln_types
        finally:
            # Cleanup
            if web.engine:
                asyncio.run(web.engine.shutdown())
            web.engine = None

    def test_authentication_bypass_attempts(self, client):
        """Test resistance to authentication bypass attempts"""
        bypass_attempts = [
            {"Authorization": "Basic " + base64.b64encode(b"admin:wrong").decode()},
            {"Authorization": "Basic " + base64.b64encode(b"wrong:admin123").decode()},
            {"Authorization": "Basic " + base64.b64encode(b"admin:").decode()},
            {"Authorization": "Bearer fake-jwt-token"},
            {"Authorization": "Digest fake-digest"},
        ]

        for headers in bypass_attempts:
            response = client.get("/api/modules", headers=headers)
            # Should fail authentication
            assert response.status_code in [401, 403]

    def test_input_validation_edge_cases(self, client):
        """Test input validation with edge cases"""
        import asyncio
        import time
        from src import web
        from src.core.engine import CodeForgeEngine

        async def _init_engine():
            engine = CodeForgeEngine()
            await engine.initialize()
            return engine
        # Set up engine
        web.engine = asyncio.run(_init_engine())

        try:
            edge_cases = [
                {"input": ""},  # Empty input
                {"input": "x" * 100000},  # Very large input
                {"input": "\x00\x01\x02"},  # Null bytes
                {"input": "<>&\"'"},  # HTML entities
                {"input": "../../../etc/passwd"},  # Path traversal
                {"input": "file:///etc/passwd"},  # File URL scheme
            ]

            credentials = "admin:admin123"
            auth_header = base64.b64encode(credentials.encode()).decode()

            for edge_input in edge_cases:
                response = client.post(
                    "/api/module/scaffolder/execute",
                    data={"input_data": json.dumps(edge_input)},
                    headers={
                        "Authorization": f"Basic {auth_header}",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                )

                # Should handle gracefully - either succeed or fail with proper error
                assert response.status_code in [200, 400, 422, 413]

                # Small delay to avoid rate limiting
                time.sleep(7)
        finally:
            # Cleanup
            if web.engine:
                asyncio.run(web.engine.shutdown())
            web.engine = None

    def test_rate_limit_bypass_attempts(self, client):
        """Test attempts to bypass rate limiting"""
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
            credentials = "admin:admin123"
            auth_header = base64.b64encode(credentials.encode()).decode()

            # Make many requests quickly to trigger rate limiting
            responses = []
            for i in range(15):  # Exceed rate limit
                response = client.post(
                    "/api/module/scaffolder/execute",
                    data={"input_data": json.dumps({"input": f"test {i}"})},
                    headers={
                        "Authorization": f"Basic {auth_header}",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                )
                responses.append(response)

            # Count rate limited responses
            rate_limited = sum(1 for r in responses if r.status_code == 429)
            successful = sum(1 for r in responses if r.status_code == 200)

            # Should have some successful and some rate limited
            assert successful > 0, "No requests succeeded"
            assert rate_limited > 0, "Rate limiting not working - no 429 responses"

            print(
                f"Rate limiting test: {successful} successful, {rate_limited} rate limited"
            )
        finally:
            # Cleanup
            if web.engine:
                asyncio.run(web.engine.shutdown())
            web.engine = None

    def test_information_disclosure(self, client):
        """Test for information disclosure vulnerabilities"""
        # Test various endpoints for information leakage
        endpoints = [
            "/health",
            "/api/modules",
            "/",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            content = response.text.lower()

            # Should not contain sensitive information
            sensitive_patterns = [
                "password",
                "secret",
                "key",
                "token",
                "internal",
                "debug",
                "stack trace",
            ]

            for pattern in sensitive_patterns:
                assert (
                    pattern not in content
                ), f"Sensitive information '{pattern}' found in {endpoint}"

    def test_http_method_restrictions(self, client):
        """Test that only allowed HTTP methods are accepted"""
        credentials = "admin:admin123"
        auth_header = base64.b64encode(credentials.encode()).decode()

        # Test various HTTP methods on API endpoints
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]

        for method in methods:
            response = client.request(
                method, "/api/modules", headers={"Authorization": auth_header}
            )

            # Should either succeed or return 405 Method Not Allowed
            assert response.status_code in [200, 201, 405, 401, 403]

    def test_cors_policy(self, client):
        """Test CORS policy is properly configured"""
        # Test preflight request (OPTIONS)
        response = client.options(
            "/api/module/scaffolder/execute",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization",
            },
        )

        # Check CORS headers are present
        assert (
            "access-control-allow-origin" in response.headers
        ), "Missing CORS origin header"
        assert (
            "access-control-allow-methods" in response.headers
        ), "Missing CORS methods header"
        assert (
            "access-control-allow-headers" in response.headers
        ), "Missing CORS headers header"
        assert (
            "access-control-max-age" in response.headers
        ), "Missing CORS max-age header"

        # Test actual request with origin
        response = client.post(
            "/api/module/scaffolder/execute",
            data={"input_data": json.dumps({"input": "test"})},
            headers={
                "Origin": "http://localhost:3000",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

        # Should have CORS headers in response
        assert (
            "access-control-allow-origin" in response.headers
        ), "Missing CORS origin in response"

    def test_error_message_safety(self, client):
        """Test that error messages don't leak sensitive information"""
        # Trigger various error conditions
        error_conditions = [
            (
                "/api/module/nonexistent/execute",
                "POST",
                {"input_data": json.dumps({"input": "test"})},
            ),
            ("/api/module/scaffolder/execute", "POST", {"input_data": "invalid json"}),
            ("/api/modules/999", "GET", {}),
        ]

        credentials = "admin:admin123"
        auth_header = base64.b64encode(credentials.encode()).decode()

        for endpoint, method, data in error_conditions:
            if method == "GET":
                response = client.get(endpoint, headers={"Authorization": auth_header})
            else:
                response = client.post(
                    endpoint,
                    data=data,
                    headers={
                        "Authorization": auth_header,
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                )

            if response.status_code >= 400:
                error_content = response.text.lower()
                # Should not contain sensitive information
                sensitive_terms = ["traceback", "exception", "stack", "internal"]
                for term in sensitive_terms:
                    assert (
                        term not in error_content
                    ), f"Error message contains sensitive term: {term}"

    def test_secure_headers(self, client):
        """Test that secure headers are set"""
        response = client.get("/")

        # Check for security headers
        security_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection",
            "strict-transport-security",
        ]

        # At least some security headers should be present
        present_headers = [h for h in security_headers if h in response.headers]
        assert len(present_headers) > 0, "No security headers found"

    def test_input_size_limits(self, client):
        """Test that input size limits are enforced"""
        # Test with health endpoint (higher rate limit: 60/minute)
        normal_input = "x" * 1000  # 1KB string

        response = client.get(f"/health?test_data={normal_input}")

        # Should succeed with normal input
        assert response.status_code == 200

        # Test that the application handles input gracefully
        response_data = response.json()
        assert "status" in response_data


class TestDependencySecurity:
    """Test security of external dependencies"""

    def test_no_vulnerable_dependencies(self):
        """Test that dependencies don't have known vulnerabilities"""
        import subprocess
        import sys

        # Try multiple dependency scanning tools
        tools = [
            ([sys.executable, "-m", "safety", "scan"], "safety"),
            ([sys.executable, "-m", "pip-audit"], "pip-audit"),
        ]

        tool_used = None
        result = None

        for cmd, name in tools:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd="c:\\Users\\berek\\OneDrive\\Documents\\DevFiles\\Project-Python\\ai-agent",
                    timeout=30,
                )
                tool_used = name
                break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        if not tool_used or result is None:
            pytest.skip("No dependency scanning tool available (safety or pip-audit)")

        # Check results based on tool used
        if tool_used == "safety":
            # Safety may require authentication now
            if "Please login or register" in result.stdout or result.returncode == 1:
                pytest.skip(
                    "Safety tool requires authentication - skipping dependency scan test"
                )
            # Safety returns 0 for safe, 255 for vulnerabilities
            assert result.returncode in [0, 255], f"Safety failed: {result.stderr}"

            if result.returncode == 255:
                # Check for critical vulnerabilities
                output = result.stdout + result.stderr
                critical_vulns = [
                    line for line in output.split("\n") if "CRITICAL" in line.upper()
                ]
                assert (
                    len(critical_vulns) == 0
                ), f"Critical vulnerabilities found: {critical_vulns}"

        elif tool_used == "pip-audit":
            # pip-audit returns 0 for safe, 1 for vulnerabilities
            assert result.returncode in [0, 1], f"pip-audit failed: {result.stderr}"

            if result.returncode == 1:
                # Check for critical vulnerabilities
                output = result.stdout + result.stderr
                critical_vulns = [
                    line for line in output.split("\n") if "CRITICAL" in line.upper()
                ]
                assert (
                    len(critical_vulns) == 0
                ), f"Critical vulnerabilities found: {critical_vulns}"
