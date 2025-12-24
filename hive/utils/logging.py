"""
Structured Logging for Backlink Broadcast Hive.

Provides consistent, configurable logging across all bees and hive components.
Supports JSON output for production and human-readable output for development.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any


class LogLevel(Enum):
    """Log levels matching Python logging module."""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging in production.

    Outputs logs as JSON objects for easy parsing by log aggregators.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "bee_id"):
            log_data["bee_id"] = record.bee_id
        if hasattr(record, "bee_type"):
            log_data["bee_type"] = record.bee_type
        if hasattr(record, "task_id"):
            log_data["task_id"] = record.task_id
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for human-readable console output.

    Uses ANSI colors for different log levels.
    """

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, "")
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")

        # Build prefix with optional bee_id
        prefix = f"[{timestamp}] [{record.levelname:8}]"
        if hasattr(record, "bee_id"):
            prefix += f" [{record.bee_id}]"

        message = f"{color}{prefix}{self.RESET} {record.getMessage()}"

        # Add exception info if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message


class BeeLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that automatically adds bee context to log messages.

    Usage:
        logger = get_bee_logger("trend_scout", bee_id="trend_scout_abc123")
        logger.info("Found new trend")  # Automatically includes bee context
    """

    def process(
        self, msg: str, kwargs: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Add extra context to log record."""
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


@lru_cache(maxsize=32)
def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with the specified name.

    Args:
        name: Logger name (usually module name or component name)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(f"hive.{name}")

    # Only configure if not already configured
    if not logger.handlers:
        configure_logger(logger)

    return logger


def get_bee_logger(
    bee_type: str,
    bee_id: str | None = None,
) -> BeeLoggerAdapter:
    """
    Get a logger adapter configured for a specific bee.

    Args:
        bee_type: Type of bee (e.g., "trend_scout", "social_poster")
        bee_id: Unique identifier for this bee instance

    Returns:
        Logger adapter with bee context
    """
    logger = get_logger(f"bees.{bee_type}")
    extra = {"bee_type": bee_type}
    if bee_id:
        extra["bee_id"] = bee_id
    return BeeLoggerAdapter(logger, extra)


def configure_logger(logger: logging.Logger) -> None:
    """
    Configure a logger with appropriate handlers and formatters.

    Uses environment variables:
        - LOG_LEVEL: Set log level (default: INFO)
        - LOG_FORMAT: "json" or "text" (default: text)
        - LOG_FILE: Path to log file (optional)
    """
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(level)

    log_format = os.environ.get("LOG_FORMAT", "text").lower()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if log_format == "json":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(ColoredFormatter())

    logger.addHandler(console_handler)

    # File handler (optional)
    log_file = os.environ.get("LOG_FILE")
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(JSONFormatter())  # Always JSON for files
        logger.addHandler(file_handler)


def configure_root_logger() -> None:
    """
    Configure the root hive logger.

    Call this once at application startup.
    """
    root_logger = logging.getLogger("hive")
    root_logger.setLevel(logging.DEBUG)  # Allow all levels, handlers filter

    # Prevent propagation to avoid duplicate logs
    root_logger.propagate = False

    configure_logger(root_logger)


# ─────────────────────────────────────────────────────────────────────────────────
# Convenience functions
# ─────────────────────────────────────────────────────────────────────────────────


def log_task_start(logger: logging.Logger, task_name: str, **kwargs: Any) -> None:
    """Log the start of a task with context."""
    logger.info(f"Starting: {task_name}", extra={"task": task_name, **kwargs})


def log_task_complete(
    logger: logging.Logger,
    task_name: str,
    duration_ms: float,
    **kwargs: Any,
) -> None:
    """Log successful completion of a task."""
    logger.info(
        f"Completed: {task_name} ({duration_ms:.1f}ms)",
        extra={"task": task_name, "duration_ms": duration_ms, **kwargs},
    )


def log_task_error(
    logger: logging.Logger,
    task_name: str,
    error: Exception,
    **kwargs: Any,
) -> None:
    """Log a task error with exception info."""
    logger.error(
        f"Failed: {task_name} - {error!s}",
        extra={"task": task_name, **kwargs},
        exc_info=True,
    )
