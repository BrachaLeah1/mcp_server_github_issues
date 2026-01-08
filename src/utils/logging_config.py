"""Logging configuration for the MCP server."""

import logging
import sys
from typing import Optional


# Log level constants
DEFAULT_LOG_LEVEL = logging.INFO
DEBUG_LOG_LEVEL = logging.DEBUG
PRODUCTION_LOG_LEVEL = logging.WARNING


def setup_logging(log_level: Optional[int] = None, log_file: Optional[str] = None) -> None:
    """
    Configure logging for the MCP server.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to
    """
    if log_level is None:
        log_level = DEFAULT_LOG_LEVEL
    
    # Create formatter with detailed information
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove any existing handlers
    root_logger.handlers.clear()
    
    # Add console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            root_logger.warning(f"Failed to create log file '{log_file}': {e}")
    
    # Set specific loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)  # Reduce noise from httpx
    logging.getLogger("asyncio").setLevel(logging.WARNING)  # Reduce noise from asyncio


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__ from module)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
