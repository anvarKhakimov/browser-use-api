"""Logging configuration utility."""

import logging
import sys
from typing import Optional

from app.config import get_settings


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None
) -> None:
    """
    Configure application logging.

    Args:
        log_level: Logging level (defaults to settings)
        log_format: Custom log format (defaults to structured format)
    """
    settings = get_settings()

    # Use provided level or fall back to settings
    level = log_level or settings.log_level
    level = getattr(logging, level.upper(), logging.INFO)

    # Default structured format for Railway/production
    if log_format is None:
        if settings.is_production:
            # Structured format for production (easier to parse in log aggregators)
            log_format = (
                '{"time": "%(asctime)s", "level": "%(levelname)s", '
                '"logger": "%(name)s", "message": "%(message)s", '
                '"module": "%(module)s", "function": "%(funcName)s", '
                '"line": %(lineno)d}'
            )
        else:
            # Human-readable format for development
            log_format = (
                "%(asctime)s - %(name)s - %(levelname)s - "
                "[%(module)s:%(funcName)s:%(lineno)d] - %(message)s"
            )

    # Configure root logger
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set specific loggers
    loggers_config = {
        "app": level,
        "browser_use": logging.INFO,
        "uvicorn": logging.INFO,
        "uvicorn.access": logging.WARNING if settings.is_production else logging.INFO,
        "fastapi": logging.INFO,
    }

    for logger_name, logger_level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(logger_level)

    # Reduce noise from third-party libraries in production
    if settings.is_production:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)

    # Log startup info
    logger = logging.getLogger("app.utils.logger")
    logger.info(
        f"Logging configured: level={logging.getLevelName(level)}, "
        f"environment={settings.environment}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class RequestIdFilter(logging.Filter):
    """Add request ID to log records for tracing."""

    def __init__(self, request_id: Optional[str] = None):
        """Initialize filter with optional request ID."""
        super().__init__()
        self.request_id = request_id

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request_id to the log record."""
        record.request_id = self.request_id or "no-request-id"
        return True