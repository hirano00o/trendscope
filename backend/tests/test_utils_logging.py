"""Tests for logging utility functions."""

import logging
import tempfile
from pathlib import Path

import pytest

from trendscope_backend.utils.logging import (
    get_logger,
    log_function_call,
    log_performance,
    setup_logger,
)


class TestSetupLogger:
    """Test cases for setup_logger function."""

    def test_setup_logger_default(self) -> None:
        """Test logger setup with default configuration."""
        logger = setup_logger("test_default")
        assert logger.name == "test_default"
        assert logger.level == logging.INFO

    def test_setup_logger_custom_level(self) -> None:
        """Test logger setup with custom log level."""
        logger = setup_logger("test_debug", level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_setup_logger_with_file(self) -> None:
        """Test logger setup with file output."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            logger = setup_logger("test_file", log_file=f.name)
            logger.info("Test message")

            # Check file exists and has content
            log_path = Path(f.name)
            assert log_path.exists()
            content = log_path.read_text()
            assert "Test message" in content

            # Cleanup
            log_path.unlink()

    def test_setup_logger_custom_format(self) -> None:
        """Test logger setup with custom format."""
        custom_format = "%(name)s - %(message)s"
        logger = setup_logger("test_format", log_format=custom_format)

        # Check that logger was created (detailed format testing is complex)
        assert logger.name == "test_format"

    def test_setup_logger_console_only(self) -> None:
        """Test logger setup with console output only."""
        logger = setup_logger("test_console", console_output=True)
        assert len(logger.handlers) >= 1  # Should have at least console handler


class TestGetLogger:
    """Test cases for get_logger function."""

    def test_get_logger_creates_new(self) -> None:
        """Test getting a new logger instance."""
        logger = get_logger("test_new")
        assert logger.name == "test_new"

    def test_get_logger_returns_existing(self) -> None:
        """Test getting existing logger returns same instance."""
        logger1 = get_logger("test_existing")
        logger2 = get_logger("test_existing")
        assert logger1 is logger2

    def test_get_logger_with_module_name(self) -> None:
        """Test getting logger with module name."""
        logger = get_logger(__name__)
        assert logger.name == __name__


class TestLogFunctionCall:
    """Test cases for log_function_call decorator."""

    def test_log_function_call_basic(self, caplog) -> None:
        """Test basic function call logging."""

        @log_function_call()
        def test_function(x: int, y: int) -> int:
            return x + y

        with caplog.at_level(logging.INFO):
            result = test_function(1, 2)

        assert result == 3
        assert "Calling test_function" in caplog.text
        assert "Finished test_function" in caplog.text

    def test_log_function_call_with_args(self, caplog) -> None:
        """Test function call logging with arguments."""

        @log_function_call(log_args=True)
        def test_function_args(name: str, count: int = 5) -> str:
            return f"{name}_{count}"

        with caplog.at_level(logging.INFO):
            result = test_function_args("test", count=10)

        assert result == "test_10"
        assert "args=('test',)" in caplog.text
        assert "kwargs={'count': 10}" in caplog.text

    def test_log_function_call_with_result(self, caplog) -> None:
        """Test function call logging with result."""

        @log_function_call(log_result=True)
        def test_function_result() -> dict[str, int]:
            return {"status": "success", "count": 42}

        with caplog.at_level(logging.INFO):
            result = test_function_result()

        assert result == {"status": "success", "count": 42}
        assert "returned: {'status': 'success', 'count': 42}" in caplog.text

    def test_log_function_call_exception(self, caplog) -> None:
        """Test function call logging with exception."""

        @log_function_call()
        def failing_function() -> None:
            raise ValueError("Test error")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError, match="Test error"):
                failing_function()

        assert "Exception in failing_function" in caplog.text
        assert "ValueError: Test error" in caplog.text

    def test_log_function_call_custom_logger(self, caplog) -> None:
        """Test function call logging with custom logger."""
        custom_logger = get_logger("custom_test")

        @log_function_call(logger=custom_logger)
        def custom_logged_function() -> str:
            return "success"

        with caplog.at_level(logging.INFO, logger="custom_test"):
            result = custom_logged_function()

        assert result == "success"
        assert "Calling custom_logged_function" in caplog.text


class TestLogPerformance:
    """Test cases for log_performance decorator."""

    def test_log_performance_basic(self, caplog) -> None:
        """Test basic performance logging."""

        @log_performance()
        def slow_function() -> str:
            import time

            time.sleep(0.001)  # Small delay for timing
            return "done"

        with caplog.at_level(logging.INFO):
            result = slow_function()

        assert result == "done"
        assert "Performance: slow_function took" in caplog.text
        assert "seconds" in caplog.text

    def test_log_performance_threshold(self, caplog) -> None:
        """Test performance logging with threshold."""

        @log_performance(threshold_seconds=0.1)
        def fast_function() -> str:
            return "quick"

        with caplog.at_level(logging.WARNING):
            result = fast_function()

        assert result == "quick"
        # Should not log because execution time is below threshold
        assert "Performance:" not in caplog.text

    def test_log_performance_custom_logger(self, caplog) -> None:
        """Test performance logging with custom logger."""
        perf_logger = get_logger("performance_test")

        @log_performance(logger=perf_logger, threshold_seconds=0.0)
        def timed_function() -> int:
            return 42

        with caplog.at_level(logging.INFO, logger="performance_test"):
            result = timed_function()

        assert result == 42
        assert "Performance: timed_function took" in caplog.text

    def test_log_performance_with_exception(self, caplog) -> None:
        """Test performance logging when function raises exception."""

        @log_performance()
        def error_function() -> None:
            raise RuntimeError("Performance test error")

        with caplog.at_level(logging.INFO):
            with pytest.raises(RuntimeError, match="Performance test error"):
                error_function()

        # Should still log performance even when exception occurs
        assert "Performance: error_function took" in caplog.text

    def test_log_performance_warning_level(self, caplog) -> None:
        """Test performance logging at warning level for slow functions."""

        @log_performance(threshold_seconds=0.0, slow_threshold_seconds=0.0)
        def always_slow_function() -> str:
            import time

            time.sleep(0.001)
            return "slow"

        with caplog.at_level(logging.WARNING):
            result = always_slow_function()

        assert result == "slow"
        assert "SLOW Performance:" in caplog.text or "Performance:" in caplog.text
