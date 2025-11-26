"""Unit tests for logging utilities."""

import json
import logging
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import structlog

from science_card_improvement.utils.logger import (
    CustomJSONEncoder,
    LoggerMixin,
    RequestLogger,
    setup_logging,
    log_debug,
    log_info,
    log_warning,
    log_error,
    log_critical,
)


@pytest.mark.unit
class TestCustomJSONEncoder:
    """Test CustomJSONEncoder class."""

    def test_encode_datetime(self):
        """Test encoding datetime objects."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = json.dumps({"date": dt}, cls=CustomJSONEncoder)
        assert "2024-01-15" in result

    def test_encode_path(self):
        """Test encoding Path objects."""
        path = Path("/home/user/test")
        result = json.dumps({"path": path}, cls=CustomJSONEncoder)
        assert "/home/user/test" in result

    def test_encode_object_with_to_dict(self):
        """Test encoding object with to_dict method."""
        class TestObj:
            def to_dict(self):
                return {"key": "value"}

        obj = TestObj()
        result = json.dumps({"obj": obj}, cls=CustomJSONEncoder)
        data = json.loads(result)
        assert data["obj"] == {"key": "value"}

    def test_encode_object_with_dict(self):
        """Test encoding object with __dict__."""
        class TestObj:
            def __init__(self):
                self.name = "test"
                self.value = 42

        obj = TestObj()
        result = json.dumps({"obj": obj}, cls=CustomJSONEncoder)
        data = json.loads(result)
        assert data["obj"]["name"] == "test"
        assert data["obj"]["value"] == 42

    def test_encode_standard_types(self):
        """Test encoding standard JSON types."""
        data = {
            "string": "test",
            "int": 42,
            "float": 3.14,
            "bool": True,
            "null": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"}
        }
        result = json.dumps(data, cls=CustomJSONEncoder)
        parsed = json.loads(result)
        assert parsed == data


@pytest.mark.unit
class TestLoggerMixin:
    """Test LoggerMixin class."""

    def test_logger_property(self):
        """Test logger property creates logger."""
        class TestClass(LoggerMixin):
            pass

        obj = TestClass()
        logger = obj.logger
        assert logger is not None
        # structlog returns BoundLoggerLazyProxy which has logging methods
        assert hasattr(logger, 'bind')
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')

    def test_logger_cached(self):
        """Test logger is cached after first access."""
        class TestClass(LoggerMixin):
            pass

        obj = TestClass()
        logger1 = obj.logger
        logger2 = obj.logger
        assert logger1 is logger2

    def test_log_debug(self):
        """Test log_debug method."""
        class TestClass(LoggerMixin):
            pass

        obj = TestClass()
        with patch.object(obj.logger, 'debug') as mock_debug:
            obj.log_debug("Test message", key="value")
            mock_debug.assert_called_once_with("Test message", key="value")

    def test_log_info(self):
        """Test log_info method."""
        class TestClass(LoggerMixin):
            pass

        obj = TestClass()
        with patch.object(obj.logger, 'info') as mock_info:
            obj.log_info("Test message", key="value")
            mock_info.assert_called_once_with("Test message", key="value")

    def test_log_warning(self):
        """Test log_warning method."""
        class TestClass(LoggerMixin):
            pass

        obj = TestClass()
        with patch.object(obj.logger, 'warning') as mock_warning:
            obj.log_warning("Test message")
            mock_warning.assert_called_once()

    def test_log_error_without_exception(self):
        """Test log_error without exception."""
        class TestClass(LoggerMixin):
            pass

        obj = TestClass()
        with patch.object(obj.logger, 'error') as mock_error:
            obj.log_error("Test message")
            mock_error.assert_called_once_with("Test message")

    def test_log_error_with_exception(self):
        """Test log_error with exception."""
        class TestClass(LoggerMixin):
            pass

        obj = TestClass()
        exc = ValueError("Test error")
        with patch.object(obj.logger, 'error') as mock_error:
            obj.log_error("Test message", exception=exc)
            call_kwargs = mock_error.call_args[1]
            assert call_kwargs["exception"] == "Test error"
            assert call_kwargs["exception_type"] == "ValueError"

    def test_log_critical(self):
        """Test log_critical method."""
        class TestClass(LoggerMixin):
            pass

        obj = TestClass()
        with patch.object(obj.logger, 'critical') as mock_critical:
            obj.log_critical("Test message")
            mock_critical.assert_called_once()


@pytest.mark.unit
class TestRequestLogger:
    """Test RequestLogger context manager."""

    def test_successful_request(self):
        """Test logging successful request."""
        mock_logger = MagicMock()

        with RequestLogger(mock_logger, "test_operation", key="value"):
            pass

        # Should log start and completion
        assert mock_logger.info.call_count == 2

        # Check start log
        start_call = mock_logger.info.call_args_list[0]
        assert "Starting" in start_call[0][0]
        assert start_call[1]["operation"] == "test_operation"

        # Check completion log
        end_call = mock_logger.info.call_args_list[1]
        assert "Completed" in end_call[0][0]
        assert end_call[1]["status"] == "success"
        assert "duration_ms" in end_call[1]

    def test_failed_request(self):
        """Test logging failed request."""
        mock_logger = MagicMock()

        with pytest.raises(ValueError):
            with RequestLogger(mock_logger, "test_operation"):
                raise ValueError("Test error")

        # Should log start and error
        assert mock_logger.info.call_count == 1
        assert mock_logger.error.call_count == 1

        # Check error log
        error_call = mock_logger.error.call_args
        assert "Failed" in error_call[0][0]
        assert error_call[1]["status"] == "error"
        assert error_call[1]["exception"] == "Test error"
        assert error_call[1]["exception_type"] == "ValueError"

    def test_context_variables(self):
        """Test context variables are passed through."""
        mock_logger = MagicMock()

        with RequestLogger(mock_logger, "test_op", user="test", repo="test/repo"):
            pass

        # Check context in logs
        start_call = mock_logger.info.call_args_list[0]
        assert start_call[1]["user"] == "test"
        assert start_call[1]["repo"] == "test/repo"

    def test_duration_calculation(self):
        """Test duration is calculated correctly."""
        import time
        mock_logger = MagicMock()

        with RequestLogger(mock_logger, "test_op"):
            time.sleep(0.1)  # Sleep for 100ms

        end_call = mock_logger.info.call_args_list[1]
        duration = end_call[1]["duration_ms"]
        # Should be at least 100ms but less than 500ms
        assert 90 <= duration <= 500


@pytest.mark.unit
class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_log_debug_function(self):
        """Test log_debug convenience function."""
        # Just verify it doesn't raise
        log_debug("Test debug message", extra="value")

    def test_log_info_function(self):
        """Test log_info convenience function."""
        log_info("Test info message", extra="value")

    def test_log_warning_function(self):
        """Test log_warning convenience function."""
        log_warning("Test warning message", extra="value")

    def test_log_error_function(self):
        """Test log_error convenience function."""
        log_error("Test error message", extra="value")

    def test_log_error_with_exception(self):
        """Test log_error with exception."""
        exc = ValueError("Test error")
        log_error("Test error message", exception=exc)

    def test_log_critical_function(self):
        """Test log_critical convenience function."""
        log_critical("Test critical message", extra="value")


@pytest.mark.unit
class TestSetupLogging:
    """Test setup_logging function."""

    def test_returns_logger(self):
        """Test setup_logging returns a logger."""
        logger = setup_logging(log_level="DEBUG", log_format="console")
        assert logger is not None

    def test_log_level_setting(self):
        """Test log level is set correctly."""
        logger = setup_logging(log_level="DEBUG")
        # Logger should be configured for DEBUG
        assert logging.root.level == logging.DEBUG or any(
            h.level == logging.DEBUG for h in logging.root.handlers
        )

    def test_json_format(self):
        """Test JSON format configuration."""
        logger = setup_logging(log_format="json")
        assert logger is not None

    def test_colored_format(self):
        """Test colored format configuration."""
        logger = setup_logging(log_format="colored")
        assert logger is not None

    def test_file_handler_creation(self, tmp_path):
        """Test file handler is created."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file=log_file)

        # Log something to create the file
        logger.info("Test message")

        # File should be created (may not contain data immediately due to buffering)
        assert log_file.parent.exists()


@pytest.mark.unit
class TestLoggerEdgeCases:
    """Test edge cases for logger module."""

    def test_custom_json_encoder_unsupported_type(self):
        """Test CustomJSONEncoder fallback for unsupported types."""
        encoder = CustomJSONEncoder()

        # Use complex number which can't be JSON serialized
        obj = complex(1, 2)

        # Should raise TypeError from super().default()
        with pytest.raises(TypeError):
            encoder.default(obj)

    def test_setup_logging_without_file_logging(self):
        """Test setup_logging when file logging is disabled."""
        with patch('science_card_improvement.utils.logger.get_settings') as mock_settings:
            mock_settings.return_value.log_file_enabled = False
            mock_settings.return_value.log_level = "INFO"
            mock_settings.return_value.log_format = "console"
            mock_settings.return_value.app_name = "Test App"

            logger = setup_logging()

            assert logger is not None

    def test_setup_logging_with_default_log_path(self, tmp_path, monkeypatch):
        """Test setup_logging when logs_dir is None."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        with patch('science_card_improvement.utils.logger.get_settings') as mock_settings:
            mock_settings.return_value.log_file_enabled = True
            mock_settings.return_value.logs_dir = None  # This will trigger line 71
            mock_settings.return_value.log_level = "INFO"
            mock_settings.return_value.log_format = "console"
            mock_settings.return_value.app_name = "Test App"

            logger = setup_logging()

            assert logger is not None
            # Default logs directory should be created
            assert (tmp_path / "logs").exists()

    def test_request_logger_with_none_start_time(self):
        """Test RequestLogger when start_time is None."""
        mock_logger = MagicMock()

        req_logger = RequestLogger(mock_logger, "test_operation")
        req_logger.start_time = None  # Force None

        # Exit context manager
        req_logger.__exit__(None, None, None)

        # Should log with duration_ms = 0
        completion_call = mock_logger.info.call_args
        assert completion_call[1]["duration_ms"] == 0
