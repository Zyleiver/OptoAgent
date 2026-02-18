"""
Unified logging for OptoAgent.

Usage in any module:
    from optoagent.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Hello from %s", __name__)
"""

import logging
import os
import sys

from optoagent.config import LOG_LEVEL, LOGS_DIR


def _ensure_logs_dir() -> None:
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR, exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger with the given name under the 'optoagent' namespace.
    Logs to both stdout and a rotating file in LOGS_DIR.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # already configured

    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-7s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # File handler
    _ensure_logs_dir()
    file_handler = logging.FileHandler(
        os.path.join(LOGS_DIR, "optoagent.log"),
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
