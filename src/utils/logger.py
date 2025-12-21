"""
Centralized Logging Configuration

Uses loguru for better logging experience:
- Colored output
- Automatic rotation
- Structured logging
- Performance tracking
"""

import sys
from pathlib import Path
from loguru import logger

from ..config import app_config


def setup_logger() -> None:
    """
    Configure loguru logger with rotation and formatting.

    Creates separate log files for different severity levels.
    """
    # Remove default handler
    logger.remove()

    # Console handler (colored, INFO and above)
    logger.add(
        sys.stderr,
        format=app_config.log_format,
        level=app_config.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )

    # Main log file (all messages)
    logger.add(
        app_config.logs_dir / "app.log",
        format=app_config.log_format,
        level="DEBUG",
        rotation=app_config.log_rotation,
        retention=app_config.log_retention,
        compression="zip",
        encoding="utf-8"
    )

    # Error log file (errors only)
    logger.add(
        app_config.logs_dir / "errors.log",
        format=app_config.log_format,
        level="ERROR",
        rotation=app_config.log_rotation,
        retention=app_config.log_retention,
        compression="zip",
        encoding="utf-8",
        backtrace=True,
        diagnose=True
    )

    # Database log file (for database operations)
    logger.add(
        app_config.logs_dir / "database.log",
        format=app_config.log_format,
        level="DEBUG",
        rotation=app_config.log_rotation,
        retention=app_config.log_retention,
        compression="zip",
        encoding="utf-8",
        filter=lambda record: "database" in record["name"].lower() or "db" in record["extra"]
    )

    logger.info(f"Logger initialized. Log level: {app_config.log_level}")
    logger.info(f"Logs directory: {app_config.logs_dir}")


def get_logger(name: str):
    """
    Get logger instance with specific name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logger.bind(name=name)


# Initialize logger on module import
setup_logger()
