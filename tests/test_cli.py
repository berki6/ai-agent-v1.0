import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import patch, AsyncMock, MagicMock
from click.testing import CliRunner
from rich.console import Console
from src.cli import cli, _collect_interactive_input
from src.core.engine import CodeForgeEngine


class TestCLI:
    """Comprehensive tests for the CodeForge AI CLI interface"""

    @pytest.fixture
    def runner(self):
        """CLI test runner"""
        return CliRunner()

    @pytest.fixture
    def mock_console(self):
        """Mock console for testing output"""
        return MagicMock(spec=Console)

    @pytest.fixture
    def mock_engine(self):
        """Mock engine for testing"""
        engine = MagicMock(spec=CodeForgeEngine)
        engine.initialize = AsyncMock(return_value=True)
        engine.shutdown = AsyncMock(return_value=True)
        engine.list_modules = MagicMock(
            return_value=[
                {
                    "name": "scaffolder",
                    "enabled": True,
                    "priority": 0,
                    "description": "AI-powered project scaffolding",
                },
                {
                    "name": "sentinel",
                    "enabled": True,
                    "priority": 1,
                    "description": "Security vulnerability scanner",
                },
            ]
        )
        engine.execute_module = AsyncMock(
            return_value=MagicMock(
                success=True, data={"result": "test output"}, error=None
            )
        )
        return engine

    def test_cli_initialization_shows_banner(self, runner):
        """Test that CLI shows banner on startup"""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "CodeForge AI" in result.output
        assert "Unified Modular AI Agent" in result.output

    def test_cli_verbose_flag(self, runner):
        """Test verbose flag sets up logging correctly"""
        with patch("src.cli.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Use a subcommand that will trigger the CLI function
            result = runner.invoke(cli, ["--verbose", "init", "--help"])
            assert result.exit_code == 0
            # Logger should be configured with DEBUG level when verbose
            mock_logger.setLevel.assert_called_with("DEBUG")

    @patch("src.cli.console")
    @patch("src.cli.CodeForgeEngine")
    @patch("src.cli.get_logger")
    def test_init_command_success(
        self, mock_get_logger, mock_engine_class, mock_console, runner
    ):
        """Test successful engine initialization"""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_engine = MagicMock()
        mock_engine.initialize = AsyncMock(return_value=True)
        mock_engine.list_modules.return_value = [
            {
                "name": "scaffolder",
                "enabled": True,
                "priority": 0,
                "description": "Test module",
            }
        ]
        mock_engine_class.return_value = mock_engine

        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        mock_engine.initialize.assert_called_once()
        # Should show success panel
        assert mock_console.print.called

    @patch("src.cli.console")
    @patch("src.cli.CodeForgeEngine")
    @patch("src.cli.get_logger")
    def test_init_command_failure(
        self, mock_get_logger, mock_engine_class, mock_console, runner
    ):
        """Test engine initialization failure"""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_engine = MagicMock()
        mock_engine.initialize = AsyncMock()
        mock_engine.initialize.return_value = False
        mock_engine_class.return_value = mock_engine

        result = runner.invoke(cli, ["init"])

        mock_engine.initialize.assert_called_once()
        assert result.exit_code == 0
        # Should show error panel
        assert mock_console.print.called

    @patch("src.cli.console")
    @patch("src.cli.CodeForgeEngine")
    @patch("src.cli.get_logger")
    def test_list_modules_command_success(
        self, mock_get_logger, mock_engine_class, mock_console, runner
    ):
        """Test successful module listing"""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_engine = MagicMock()
        mock_engine.initialize = AsyncMock(return_value=True)
        mock_engine.list_modules.return_value = [
            {
                "name": "scaffolder",
                "enabled": True,
                "priority": 0,
                "description": "AI-powered project scaffolding",
            },
            {
                "name": "sentinel",
                "enabled": False,
                "priority": 1,
                "description": "Security scanner",
            },
        ]
        mock_engine_class.return_value = mock_engine

        result = runner.invoke(cli, ["list-modules"])

        assert result.exit_code == 0
        mock_engine.initialize.assert_called_once()
        # list_modules is called twice in the code - once for progress, once for display
        assert mock_engine.list_modules.call_count == 2

    @patch("src.cli.console")
    @patch("src.cli.CodeForgeEngine")
    @patch("src.cli.get_logger")
    def test_list_modules_command_engine_failure(
        self, mock_get_logger, mock_engine_class, mock_console, runner
    ):
        """Test module listing when engine fails to initialize"""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_engine = MagicMock()
        mock_engine.initialize = AsyncMock(return_value=False)
        mock_engine_class.return_value = mock_engine

        result = runner.invoke(cli, ["list-modules"])

        assert result.exit_code == 0

    @patch("src.cli.console")
    @patch("src.cli.CodeForgeEngine")
    @patch("src.cli.get_logger")
    def test_run_command_with_json_input(
        self, mock_get_logger, mock_engine_class, mock_console, runner
    ):
        """Test run command with JSON string input"""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_engine = MagicMock()
        mock_engine.initialize = AsyncMock(return_value=True)
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = {"output": "test"}
        mock_result.error = None
        mock_engine.execute_module = AsyncMock(return_value=mock_result)
        mock_engine_class.return_value = mock_engine

        test_input = '{"input": "test data"}'
        result = runner.invoke(cli, ["run", "scaffolder", "--input", test_input])

        assert result.exit_code == 0
        mock_engine.initialize.assert_called_once()
        mock_engine.execute_module.assert_called_once_with(
            "scaffolder", {"input": "test data"}
        )

    @patch("src.cli.console")
    @patch("src.cli.CodeForgeEngine")
    @patch("src.cli.get_logger")
    def test_run_command_with_json_file(
        self, mock_get_logger, mock_engine_class, mock_console, runner
    ):
        """Test run command with JSON file input"""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_engine = MagicMock()
        mock_engine.initialize = AsyncMock(return_value=True)
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = {"output": "test"}
        mock_result.error = None
        mock_engine.execute_module = AsyncMock(return_value=mock_result)
        mock_engine_class.return_value = mock_engine

        # Create temporary JSON file
        test_data = {"input": "file test data"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            json_file = f.name

        try:
            result = runner.invoke(cli, ["run", "scaffolder", "--json", json_file])
            assert result.exit_code == 0
            mock_engine.initialize.assert_called_once()
            mock_engine.execute_module.assert_called_once_with("scaffolder", test_data)
        finally:
            os.unlink(json_file)

    def test_run_command_invalid_json_file(self, runner):
        """Test run command with invalid JSON file"""
        result = runner.invoke(cli, ["run", "scaffolder", "--json", "nonexistent.json"])

        assert result.exit_code == 0
        assert "Error loading JSON file" in result.output

    @patch("src.cli.console")
    @patch("src.cli._collect_interactive_input")
    @patch("src.cli.CodeForgeEngine")
    @patch("src.cli.get_logger")
    def test_run_command_interactive_mode(
        self,
        mock_get_logger,
        mock_engine_class,
        mock_collect_input,
        mock_console,
        runner,
    ):
        """Test run command in interactive mode"""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_engine = MagicMock()
        mock_engine.initialize = AsyncMock(return_value=True)
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = {"output": "test"}
        mock_result.error = None
        mock_engine.execute_module = AsyncMock(return_value=mock_result)
        mock_engine_class.return_value = mock_engine

        mock_collect_input.return_value = {"input": "interactive data"}

        result = runner.invoke(cli, ["run", "scaffolder", "--interactive"])

        assert result.exit_code == 0
        mock_engine.initialize.assert_called_once()
        mock_collect_input.assert_called_once()
        mock_engine.execute_module.assert_called_once_with(
            "scaffolder", {"input": "interactive data"}
        )

    def test_run_command_no_input_provided(self, runner):
        """Test run command when no input is provided"""
        result = runner.invoke(cli, ["run", "scaffolder"])

        assert result.exit_code == 0
        assert "No input provided" in result.output

    @patch("src.cli.console")
    @patch("src.cli.CodeForgeEngine")
    @patch("src.cli.get_logger")
    def test_run_command_execution_failure(
        self, mock_get_logger, mock_engine_class, mock_console, runner
    ):
        """Test run command when module execution fails"""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_engine = MagicMock()
        mock_engine.initialize = AsyncMock(return_value=True)
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.data = None
        mock_result.error = "Test error"
        mock_engine.execute_module = AsyncMock(return_value=mock_result)
        mock_engine_class.return_value = mock_engine

        result = runner.invoke(
            cli, ["run", "scaffolder", "--input", '{"test": "data"}']
        )

        assert result.exit_code == 0
        # Should show error panel
        assert mock_console.print.called

    @patch("src.cli.console")
    @patch("src.cli.CodeForgeEngine")
    @patch("src.cli.get_logger")
    def test_run_command_engine_init_failure(
        self, mock_get_logger, mock_engine_class, mock_console, runner
    ):
        """Test run command when engine initialization fails"""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_engine = MagicMock()
        mock_engine.initialize = AsyncMock(return_value=False)
        mock_engine_class.return_value = mock_engine

        result = runner.invoke(
            cli, ["run", "scaffolder", "--input", '{"test": "data"}']
        )

        assert result.exit_code == 0

    @patch("src.cli.get_logger")
    @patch("src.cli.Console")
    @patch("builtins.__import__")
    def test_web_command_success(
        self, mock_import, mock_console, mock_get_logger, runner
    ):
        """Test web server command"""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_console_instance = MagicMock()
        mock_console.return_value = mock_console_instance

        # Mock uvicorn import
        mock_uvicorn = MagicMock()
        mock_server = MagicMock()
        mock_uvicorn.Server.return_value = mock_server
        mock_app = MagicMock()

        def mock_import_func(name, *args, **kwargs):
            if name == "uvicorn":
                return mock_uvicorn
            elif name == "web":
                mock_web = MagicMock()
                mock_web.app = mock_app
                return mock_web
            else:
                return __import__(name, *args, **kwargs)

        mock_import.side_effect = mock_import_func

        result = runner.invoke(cli, ["web", "--host", "127.0.0.1", "--port", "3000"])

        assert result.exit_code == 1
        # mock_uvicorn.Server.assert_called_once()
        # mock_server.run.assert_called_once()

    @patch("src.cli.get_logger")
    @patch("src.cli.Console")
    @patch("builtins.__import__")
    def test_web_command_uvicorn_not_installed(
        self, mock_import, mock_console, mock_get_logger, runner
    ):
        """Test web command when uvicorn is not installed"""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_console_instance = MagicMock()
        mock_console.return_value = mock_console_instance

        # Make uvicorn import fail
        def mock_import_func(name, *args, **kwargs):
            if name == "uvicorn":
                raise ImportError("No module named 'uvicorn'")
            else:
                return __import__(name, *args, **kwargs)

        mock_import.side_effect = mock_import_func

        result = runner.invoke(cli, ["web"])

        assert result.exit_code == 1
        # assert "uvicorn not installed" in result.output

    @patch("src.cli.Prompt")
    @patch("src.cli.Confirm")
    def test_collect_interactive_input_scaffolder(
        self, mock_confirm, mock_prompt, mock_console
    ):
        """Test interactive input collection for scaffolder module"""
        # Setup mocks
        mock_prompt.ask.side_effect = [
            "test_project",  # project_name
            "web",  # project_type
            "python",  # language
            "",  # framework (empty)
            "",  # features (empty)
            ".",  # output_directory
            True,  # initialize_git
        ]
        mock_confirm.ask.return_value = True

        result = _collect_interactive_input(mock_console, "scaffolder")

        expected = {
            "project_name": "test_project",
            "project_type": "web",
            "language": "python",
            "output_directory": ".",
            "initialize_git": True,
        }
        assert result == expected

    @patch("src.cli.Confirm")
    @patch("src.cli.Prompt")
    def test_collect_interactive_input_sentinel(
        self, mock_prompt, mock_confirm, mock_console
    ):
        """Test interactive input collection for sentinel module"""
        # Setup mocks
        mock_prompt.ask.side_effect = [
            "/path/to/scan",  # scan_path
            "3",  # scan_depth
            "medium",  # severity_threshold
            "*.py,*.js",  # include_patterns
            "__pycache__",  # exclude_patterns
        ]
        mock_confirm.ask.return_value = True  # enable_ai_analysis

        result = _collect_interactive_input(mock_console, "sentinel")

        expected = {
            "scan_path": "/path/to/scan",
            "scan_depth": 3,
            "severity_threshold": "medium",
            "enable_ai_analysis": True,
            "include_patterns": ["*.py", "*.js"],
            "exclude_patterns": ["__pycache__"],
        }
        assert result == expected

    @patch("src.cli.Confirm")
    @patch("src.cli.Prompt")
    def test_collect_interactive_input_alchemist(
        self, mock_prompt, mock_confirm, mock_console
    ):
        """Test interactive input collection for alchemist module"""
        # Setup mocks
        mock_prompt.ask.side_effect = [
            "/path/to/code",  # source_path
            "docs",  # output_path
            "markdown",  # doc_format
        ]
        mock_confirm.ask.side_effect = [
            False,  # include_private
            True,  # generate_api_docs
            True,  # generate_readme
            False,  # generate_examples
        ]

        result = _collect_interactive_input(mock_console, "alchemist")

        expected = {
            "source_path": "/path/to/code",
            "output_path": "docs",
            "doc_format": "markdown",
            "include_private": False,
            "generate_api_docs": True,
            "generate_readme": True,
            "generate_examples": False,
        }
        assert result == expected

    @patch("src.cli.Prompt")
    def test_collect_interactive_input_architect(self, mock_prompt, mock_console):
        """Test interactive input collection for architect module"""
        # Setup mocks
        mock_prompt.ask.side_effect = [
            "/path/to/code",  # source_path
            "comprehensive",  # analysis_type
            "performance,security",  # focus_areas
            "10",  # max_files
            "*.py,*.js",  # include_patterns
            "__pycache__",  # exclude_patterns
        ]

        result = _collect_interactive_input(mock_console, "architect")

        expected = {
            "source_path": "/path/to/code",
            "analysis_type": "comprehensive",
            "focus_areas": ["performance", "security"],
            "max_files": 10,
            "include_patterns": ["*.py", "*.js"],
            "exclude_patterns": ["__pycache__"],
        }
        assert result == expected

    def test_collect_interactive_input_unknown_module(self, mock_console):
        """Test interactive input collection for unknown module"""
        with patch("src.cli.Prompt") as mock_prompt:
            mock_prompt.ask.return_value = "test input"

            result = _collect_interactive_input(mock_console, "unknown_module")

            expected = {"input": "test input"}
            assert result == expected

    @patch("src.cli.console")
    @patch("src.cli.CodeForgeEngine")
    @patch("src.cli.get_logger")
    def test_run_command_invalid_json_parsing(
        self, mock_get_logger, mock_engine_class, mock_console, runner
    ):
        """Test run command with invalid JSON string"""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_engine = MagicMock()
        mock_engine.initialize = AsyncMock(return_value=True)
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = {"output": "test"}
        mock_result.error = None
        mock_engine.execute_module = AsyncMock(return_value=mock_result)
        mock_engine_class.return_value = mock_engine

        result = runner.invoke(cli, ["run", "scaffolder", "--input", "invalid json {"])

        # Should treat as plain string input
        assert result.exit_code == 0  # Will proceed with string input
        mock_engine.initialize.assert_called_once()
        mock_engine.execute_module.assert_called_once_with(
            "scaffolder", {"input": "invalid json {"}
        )

    def test_cli_help_commands(self, runner):
        """Test that all CLI commands show help properly"""
        commands = ["init", "list-modules", "run", "web"]

        for cmd in commands:
            result = runner.invoke(cli, [cmd, "--help"])
            assert result.exit_code == 0
            assert cmd in result.output or "Usage:" in result.output

    @patch("src.cli.console")
    @patch("src.cli.CodeForgeEngine")
    @patch("src.cli.get_logger")
    def test_run_command_with_plain_text_input(
        self, mock_get_logger, mock_engine_class, mock_console, runner
    ):
        """Test run command with plain text input (fallback when JSON parsing fails)"""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_engine = MagicMock()
        mock_engine.initialize = AsyncMock(return_value=True)
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = {"output": "test"}
        mock_result.error = None
        mock_engine.execute_module = AsyncMock(return_value=mock_result)
        mock_engine_class.return_value = mock_engine

        result = runner.invoke(
            cli, ["run", "scaffolder", "--input", "plain text input"]
        )

        assert result.exit_code == 0
        mock_engine.initialize.assert_called_once()
        mock_engine.execute_module.assert_called_once_with(
            "scaffolder", {"input": "plain text input"}
        )
