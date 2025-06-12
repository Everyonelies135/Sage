"""
utils/logger.py

This module provides logging utilities for the Sage application. It includes functions to log events with different levels of severity and a helper to get a consistent named logger.

Functions:
- `get_logger() -> logging.Logger`: Returns the named logger for Sage.
- `log_event(message: str, level: Literal["info", "warning", "error", "debug"] = "info") -> None`: Logs an event with the specified message and severity level.

Usage:
Use this module to log important events, errors, and debugging information throughout the application.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Literal

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "sage.log")
LOGGER_NAME = "sage"

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Configure the named logger only once
_Logger = logging.getLogger(LOGGER_NAME)
_Logger.setLevel(logging.INFO)
if not _Logger.handlers:
    rotating_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3
    )
    rotating_handler.setLevel(logging.INFO)
    rotating_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s — %(levelname)s — %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    )
    _Logger.addHandler(rotating_handler)
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s — %(levelname)s — %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    )
    _Logger.addHandler(console_handler)


def get_logger() -> logging.Logger:
    """
    Returns the named logger for Sage.
    """
    return _Logger


def log_event(
    message: str, level: Literal["info", "warning", "error", "debug"] = "info"
) -> None:
    """
    Logs an event with the specified message and level using the Sage logger.

    Args:
        message (str): The message to log.
        level (Literal["info", "warning", "error", "debug"]): The log level.

    Returns:
        None
    """
    logger = get_logger()
    if level == "info":
        logger.info(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)
    elif level == "debug":
        logger.debug(message)
