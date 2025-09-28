import pytest
import logging
import tempfile
import os
import asyncio
import time
from unittest.mock import patch, MagicMock
from src.core.logger import get_logger, log_timing


class TestLogger:
    """Tests for the logger module"""

    def test_get_logger_default(self):
        """Test get_logger with default settings"""
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_get_logger_no_name(self):
        """Test get_logger with no name (root logger)"""
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "root"

    @patch("src.core.logger.settings")
    def test_get_logger_with_log_file_warning(self, mock_settings):
        """Test get_logger configures file logging for WARNING+ levels"""
        mock_settings.LOG_LEVEL = "WARNING"
        mock_settings.LOG_FILE = None

        # Create a temporary directory for log files
        with tempfile.TemporaryDirectory() as temp_dir:
            expected_log_file = os.path.join(temp_dir, "log", "error.log")
            os.makedirs(os.path.dirname(expected_log_file), exist_ok=True)

            with patch("src.core.logger.settings") as settings_patch:
                settings_patch.LOG_LEVEL = "WARNING"
                settings_patch.LOG_FILE = None

                logger = get_logger("test_logger")
                assert isinstance(logger, logging.Logger)

    @patch("src.core.logger.settings")
    def test_get_logger_with_log_file_info(self, mock_settings):
        """Test get_logger configures file logging for INFO level"""
        mock_settings.LOG_LEVEL = "INFO"
        mock_settings.LOG_FILE = None

        with patch("src.core.logger.settings") as settings_patch:
            settings_patch.LOG_LEVEL = "INFO"
            settings_patch.LOG_FILE = None

            logger = get_logger("test_logger")
            assert isinstance(logger, logging.Logger)

    @patch("src.core.logger.settings")
    def test_get_logger_custom_log_file(self, mock_settings):
        """Test get_logger with custom log file"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            with patch("src.core.logger.settings") as settings_patch:
                settings_patch.LOG_LEVEL = "INFO"
                settings_patch.LOG_FILE = temp_file_path

                logger = get_logger("test_logger")
                assert isinstance(logger, logging.Logger)

                # Verify log file was created
                assert os.path.exists(temp_file_path)
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    @patch("src.core.logger.settings")
    def test_get_logger_with_sentry(self, mock_settings):
        """Test get_logger initializes Sentry when DSN is provided"""
        mock_settings.SENTRY_DSN = "https://test@test.ingest.sentry.io/test"
        mock_settings.LOG_LEVEL = "INFO"

        with patch("builtins.__import__") as mock_import:
            mock_sentry = MagicMock()
            mock_import.return_value = mock_sentry

            logger = get_logger("test_logger")

            # Verify Sentry was initialized
            mock_sentry.init.assert_called_once_with(
                dsn="https://test@test.ingest.sentry.io/test"
            )

    @patch("src.core.logger.settings")
    def test_get_logger_sentry_import_error(self, mock_settings):
        """Test get_logger handles Sentry import failure gracefully"""
        mock_settings.SENTRY_DSN = "https://test@test.ingest.sentry.io/test"
        mock_settings.LOG_LEVEL = "INFO"

        # Make sentry_sdk import fail
        with patch.dict("sys.modules", {"sentry_sdk": None}):
            logger = get_logger("test_logger")
            # Should not raise exception
            assert isinstance(logger, logging.Logger)

    @patch("src.core.logger.settings")
    def test_get_logger_invalid_log_level(self, mock_settings):
        """Test get_logger falls back to INFO for invalid log level"""
        mock_settings.LOG_LEVEL = "INVALID_LEVEL"

        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)


class TestLogTiming:
    """Tests for the log_timing decorator"""

    @patch("src.core.logger.get_logger")
    def test_log_timing_sync_function(self, mock_get_logger):
        """Test log_timing decorator on synchronous function"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        @log_timing()
        def test_function(x, y=10):
            time.sleep(0.01)  # Small delay to ensure timing > 0
            return x + y

        result = test_function(5, y=3)
        assert result == 8

        # Verify logging was called
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert "[TIMING]" in log_message
        assert "test_function took" in log_message

    @patch("src.core.logger.get_logger")
    def test_log_timing_async_function(self, mock_get_logger):
        """Test log_timing decorator on asynchronous function"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        @log_timing()
        async def async_test_function(x, y=10):
            await asyncio.sleep(0.01)  # Small delay to ensure timing > 0
            return x + y

        async def run_test():
            result = await async_test_function(5, y=3)
            assert result == 8

            # Verify logging was called
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert "[TIMING]" in log_message
            assert "async_test_function took" in log_message

        asyncio.run(run_test())

    @patch("src.core.logger.get_logger")
    def test_log_timing_with_custom_logger(self, mock_get_logger):
        """Test log_timing decorator with custom logger"""
        custom_logger = MagicMock()

        @log_timing(custom_logger)
        def test_function():
            time.sleep(0.01)
            return "done"

        result = test_function()
        assert result == "done"

        # Verify the custom logger was used directly, not get_logger
        custom_logger.info.assert_called_once()
        log_message = custom_logger.info.call_args[0][0]
        assert "[TIMING]" in log_message
        assert "test_function took" in log_message

        # get_logger should not have been called
        mock_get_logger.assert_not_called()

    @patch("src.core.logger.get_logger")
    def test_log_timing_preserves_function_metadata(self, mock_get_logger):
        """Test that log_timing preserves function name, docstring, etc."""
        mock_logger = MagicMock()

        @log_timing()
        def documented_function(x, y=5):
            """This is a test function with documentation."""
            return x * y

        # Check that function metadata is preserved
        assert documented_function.__name__ == "documented_function"
        assert (
            documented_function.__doc__ == "This is a test function with documentation."
        )

        result = documented_function(3, y=4)
        assert result == 12
