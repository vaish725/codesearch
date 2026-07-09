"""
Logging utilities for codesearch.
"""

import logging
import sys


def setup_logger(name: str = "codesearch", level: int = logging.INFO) -> logging.Logger:
    """
    Set up and configure a logger.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    # Format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


# Create default logger
logger = setup_logger()
