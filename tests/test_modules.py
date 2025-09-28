import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.scaffolder.module import Scaffolder, ProjectScaffolderConfig
from src.services.sentinel.module import Sentinel, VulnerabilitySentinelConfig
from src.services.alchemist.module import Alchemist, DocumentationAlchemistConfig
from src.services.architect.module import Architect, CodeArchitectConfig


class TestScaffolder:
    """Unit tests for Scaffolder module"""

    @pytest.fixture
    def config(self):
        return ProjectScaffolderConfig(
            name="scaffolder",
            project_type="web",
            project_name="test_project",
            language="python",
        )

    @pytest.fixture
    def module(self, config):
        return Scaffolder(config)

    def test_config_validation(self, config):
        """Test configuration validation"""
        assert config.name == "scaffolder"
        assert config.project_type == "web"
        assert config.project_name == "test_project"

    @pytest.mark.asyncio
    async def test_input_validation_valid(self, module):
        """Test valid input validation"""
        valid_input = {
            "project_type": "web",
            "project_name": "my_app",
            "description": "A web application",
            "language": "python",
        }
        assert module.validate_input(valid_input) is True

    @pytest.mark.asyncio
    async def test_input_validation_invalid(self, module):
        """Test invalid input validation"""
        invalid_input = {
            "project_type": "invalid",
            "description": "Missing project name",
        }
        assert module.validate_input(invalid_input) is False

    @pytest.mark.asyncio
    @patch("src.services.scaffolder.module.AIUtils")
    async def test_execute_success(self, mock_ai_utils, module):
        """Test successful module execution"""
        # Mock AI response
        mock_ai_utils.return_value.generate_text = AsyncMock(
            return_value="""
        # Project Structure
        my_project/
        ├── src/
        │   ├── app.py
        │   └── __init__.py
        ├── tests/
        │   └── test_app.py
        ├── requirements.txt
        └── README.md
        """
        )

        input_data = {
            "project_name": "my_project",
            "project_type": "web",
            "language": "python",
            "description": "A simple web app",
        }

        result = await module.execute(input_data)

        assert result.success is True
        assert "structure" in result.data
        assert result.data["project_name"] == "my_project"


class TestSentinel:
    """Unit tests for Sentinel module"""

    @pytest.fixture
    def config(self):
        return VulnerabilitySentinelConfig(
            name="sentinel",
            scan_depth=3,
            severity_threshold="medium",
            scan_path="src",  # Use existing directory
        )

    @pytest.fixture
    def module(self, config):
        return Sentinel(config)

    @pytest.mark.asyncio
    async def test_input_validation_valid(self, module):
        """Test valid input validation"""
        valid_input = {"scan_path": "src", "language": "python"}
        assert module.validate_input(valid_input) is True

    @pytest.mark.asyncio
    async def test_input_validation_invalid(self, module):
        """Test invalid input validation"""
        invalid_input = {
            "language": "python"
            # Missing code
        }
        assert module.validate_input(invalid_input) is False

    @pytest.mark.asyncio
    @patch("src.services.sentinel.module.AIUtils")
    async def test_execute_with_vulnerabilities(self, mock_ai_utils, module):
        """Test vulnerability detection"""
        mock_ai_utils.return_value.analyze_code = AsyncMock(
            return_value="""
        Found 2 vulnerabilities:
        1. SQL Injection in line 5: Use parameterized queries
        2. Hardcoded password in line 10: Use environment variables
        """
        )

        input_data = {
            "scan_path": "src",
            "code": """
            import sqlite3
            def get_user(user_id):
                conn = sqlite3.connect('db.db')
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")  # SQL injection
                return cursor.fetchone()
            """,
            "language": "python",
        }

        result = await module.execute(input_data)

        assert result.success is True
        assert "report" in result.data
        assert "vulnerabilities" in result.data["report"]


class TestAlchemist:
    """Unit tests for Alchemist module"""

    @pytest.fixture
    def config(self):
        return DocumentationAlchemistConfig(name="alchemist", source_path="src")

    @pytest.fixture
    def module(self, config):
        return Alchemist(config)

    @pytest.mark.asyncio
    async def test_input_validation_valid(self, module):
        """Test valid input validation"""
        valid_input = {"source_path": "src", "language": "python"}
        assert module.validate_input(valid_input) is True

    @pytest.mark.asyncio
    @patch("src.services.alchemist.module.AIUtils")
    async def test_execute_documentation_generation(self, mock_ai_utils, module):
        """Test documentation generation"""
        mock_ai_utils.return_value.analyze_code = AsyncMock(
            return_value="""
        # Function: hello

        ## Description
        A simple function that returns 'world'

        ## Parameters
        None

        ## Returns
        str: The string 'world'

        ## Example
        ```python
        result = hello()
        print(result)  # Output: world
        ```
        """
        )

        input_data = {"source_path": "src", "language": "python"}

        result = await module.execute(input_data)

        assert result.success is True
        assert "documentation" in result.data
        assert isinstance(result.data["documentation"], dict)


class TestArchitect:
    """Unit tests for Architect module"""

    @pytest.fixture
    def config(self):
        return CodeArchitectConfig(name="architect", source_path="src")

    @pytest.fixture
    def module(self, config):
        return Architect(config)

    @pytest.mark.asyncio
    async def test_input_validation_valid(self, module):
        """Test valid input validation"""
        valid_input = {
            "source_path": "src",
            "language": "python",
            "context": "simple calculator function",
        }
        assert module.validate_input(valid_input) is True

    @pytest.mark.asyncio
    @patch("src.services.architect.module.AIUtils")
    async def test_execute_architecture_analysis(self, mock_ai_utils, module):
        """Test architecture analysis"""
        mock_ai_utils.return_value.analyze_code = AsyncMock(
            return_value="""
        # Architecture Analysis

        ## Performance Issues
        - Function is simple and efficient
        - No performance bottlenecks identified

        ## Maintainability
        - Code is readable and well-structured
        - Consider adding type hints for better clarity

        ## Recommendations
        1. Add type hints: def calculate(x: int, y: int) -> int:
        2. Add docstring for documentation
        3. Consider input validation
        """
        )

        input_data = {
            "source_path": "src",
            "language": "python",
            "context": "simple calculator",
        }

        result = await module.execute(input_data)

        assert result.success is True
        assert "report" in result.data
        assert "recommendations" in result.data
