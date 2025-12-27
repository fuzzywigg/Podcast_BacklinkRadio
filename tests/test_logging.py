"""
Unit tests for logging utilities.
"""

import json
import logging
import os
from io import StringIO
from unittest.mock import patch

import pytest

from hive.utils.logging import (
    BeeLoggerAdapter,
    ColoredFormatter,
    JSONFormatter,
    LogLevel,
    get_bee_logger,
    get_logger,
    log_task_complete,
    log_task_error,
    log_task_start,
)


class TestLogLevel:
    """Tests for LogLevel enum."""

    def test_log_levels_match_stdlib(self) -> None:
        """LogLevel values should match Python logging levels."""
        assert LogLevel.DEBUG.value == logging.DEBUG
        assert LogLevel.INFO.value == logging.INFO
        assert LogLevel.WARNING.value == logging.WARNING
        assert LogLevel.ERROR.value == logging.ERROR
        assert LogLevel.CRITICAL.value == logging.CRITICAL


class TestJSONFormatter:
    """Tests for JSON log formatting."""

    @pytest.fixture
    def json_formatter(self) -> JSONFormatter:
        return JSONFormatter()

    def test_basic_format(self, json_formatter: JSONFormatter) -> None:
        """Should format log record as valid JSON."""
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = json_formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"
        assert data["line"] == 42
        assert "timestamp" in data

    def test_includes_bee_context(self, json_formatter: JSONFormatter) -> None:
        """Should include bee context if present."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.bee_id = "trend_scout_abc123"
        record.bee_type = "trend_scout"

        output = json_formatter.format(record)
        data = json.loads(output)

        assert data["bee_id"] == "trend_scout_abc123"
        assert data["bee_type"] == "trend_scout"

    def test_includes_exception(self, json_formatter: JSONFormatter) -> None:
        """Should include exception info if present."""
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        output = json_formatter.format(record)
        data = json.loads(output)

        assert "exception" in data
        assert "ValueError" in data["exception"]


class TestColoredFormatter:
    """Tests for colored console formatting."""

    @pytest.fixture
    def colored_formatter(self) -> ColoredFormatter:
        return ColoredFormatter()

    def test_includes_color_codes(
            self, colored_formatter: ColoredFormatter) -> None:
        """Should include ANSI color codes."""
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error message",
            args=(),
            exc_info=None,
        )

        output = colored_formatter.format(record)

        # Should contain red color code for ERROR
        assert "\033[31m" in output
        assert "Error message" in output

    def test_includes_bee_id(
            self,
            colored_formatter: ColoredFormatter) -> None:
        """Should include bee_id in output if present."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.bee_id = "test_bee_123"

        output = colored_formatter.format(record)
        assert "test_bee_123" in output


class TestGetLogger:
    """Tests for logger creation."""

    def test_creates_logger_with_prefix(self) -> None:
        """Should create logger with hive prefix."""
        logger = get_logger("test_component")
        assert logger.name == "hive.test_component"

    def test_caches_loggers(self) -> None:
        """Should return same logger for same name."""
        logger1 = get_logger("cached_test")
        logger2 = get_logger("cached_test")
        assert logger1 is logger2


class TestBeeLoggerAdapter:
    """Tests for bee-specific logger adapter."""

    def test_adds_bee_context(self) -> None:
        """Should add bee context to log records."""
        adapter = get_bee_logger("trend_scout", bee_id="trend_scout_abc")

        # Check that extra context is set
        assert adapter.extra["bee_type"] == "trend_scout"
        assert adapter.extra["bee_id"] == "trend_scout_abc"

    def test_without_bee_id(self) -> None:
        """Should work without bee_id."""
        adapter = get_bee_logger("test_bee")
        assert adapter.extra["bee_type"] == "test_bee"
        assert "bee_id" not in adapter.extra


class TestTaskLogging:
    """Tests for task logging convenience functions."""

    @pytest.fixture
    def mock_logger(self) -> logging.Logger:
        """Create a mock logger for testing."""
        logger = logging.getLogger("test_task_logger")
        logger.setLevel(logging.DEBUG)
        return logger

    def test_log_task_start(self, mock_logger: logging.Logger) -> None:
        """Should log task start."""
        with patch.object(mock_logger, "info") as mock_info:
            log_task_start(mock_logger, "test_task", extra_field="value")
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert "test_task" in call_args[0][0]

    def test_log_task_complete(self, mock_logger: logging.Logger) -> None:
        """Should log task completion with duration."""
        with patch.object(mock_logger, "info") as mock_info:
            log_task_complete(mock_logger, "test_task", duration_ms=150.5)
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert "test_task" in call_args[0][0]
            assert "150.5" in call_args[0][0]

    def test_log_task_error(self, mock_logger: logging.Logger) -> None:
        """Should log task error with exception info."""
        error = ValueError("Test error")
        with patch.object(mock_logger, "error") as mock_error:
            log_task_error(mock_logger, "test_task", error)
            mock_error.assert_called_once()
            call_args = mock_error.call_args
            assert "test_task" in call_args[0][0]
            assert call_args[1]["exc_info"] is True
