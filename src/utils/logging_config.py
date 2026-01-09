"""Logging configuration for the MCP server."""

import logging
from typing import Optional


# Log level constants
DEFAULT_LOG_LEVEL = logging.INFO
DEBUG_LOG_LEVEL = logging.DEBUG
PRODUCTION_LOG_LEVEL = logging.WARNING


def setup_logging(log_level: Optional[int] = None, log_file: Optional[str] = None) -> None:
    """
    Configure logging for the MCP server.
    
    Logs are written to a file or suppressed entirely to avoid interfering
    with MCP protocol communication on stdout/stderr.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to. If not provided, logs are suppressed.
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
    
    # Add NullHandler by default (no output to stderr or stdout)
    # This prevents any interference with MCP protocol
    null_handler = logging.NullHandler()
    root_logger.addHandler(null_handler)
    
    # Add file handler if specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception:
            pass  # Silently fail - don't output errors to stderr
    
    # Set specific loggers to WARNING to minimize noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__ from module)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
