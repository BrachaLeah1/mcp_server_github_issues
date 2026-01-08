"""Structured error handling utilities."""

import json
import logging
from typing import Any, Dict, Optional


# Configure module logger
logger = logging.getLogger(__name__)


class MCPError(Exception):
    """Base exception for MCP server errors."""
    
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)
        logger.error(f"MCPError ({code}): {message}", extra={"details": self.details})
    
    def to_dict(self) -> dict:
        """Convert error to standardized dictionary format."""
        return {
            "ok": False,
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }
    
    def to_json(self) -> str:
        """Convert error to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class GitHubApiError(MCPError):
    """Exception for GitHub API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        full_details = details or {}
        if status_code:
            full_details["status_code"] = status_code
        super().__init__("GITHUB_API_ERROR", message, full_details)


class RateLimitError(MCPError):
    """Exception for GitHub API rate limit errors."""
    def __init__(self, reset_at: Optional[int] = None, limit_remaining: int = 0):
        details = {
            "limit_remaining": limit_remaining,
            "hint": "Set GITHUB_TOKEN environment variable for higher rate limits (5000/hr vs 60/hr)"
        }
        if reset_at:
            details["resets_at"] = reset_at
        super().__init__("GITHUB_RATE_LIMIT", "GitHub API rate limit exceeded", details)


class ValidationError(MCPError):
    """Exception for input validation errors."""
    def __init__(self, message: str, field: Optional[str] = None):
        details = {}
        if field:
            details["field"] = field
        super().__init__("VALIDATION_ERROR", message, details)


class GitError(MCPError):
    """Exception for git operation errors."""
    def __init__(self, message: str, command: Optional[str] = None):
        details = {}
        if command:
            details["command"] = command
        super().__init__("GIT_ERROR", message, details)


def success_response(data: Any) -> dict:
    """Create a standardized success response."""
    return {
        "ok": True,
        "data": data
    }


def error_response(code: str, message: str, details: Optional[Dict[str, Any]] = None) -> dict:
    """Create a standardized error response."""
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        }
    }


def format_json_response(data: Any, indent: int = 2) -> str:
    """
    Format a standardized response as JSON string.
    
    Args:
        data: Response dict (typically from success_response or error_response)
        indent: JSON indentation level
        
    Returns:
        JSON-formatted string
    """
    return json.dumps(data, indent=indent)


def format_error_json(code: str, message: str, hint: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Format an error response as JSON string with optional hint and context.
    
    Args:
        code: Error code
        message: Human-readable error message
        hint: Optional hint for resolution
        context: Optional context information
        
    Returns:
        JSON-formatted error string
    """
    error_dict = {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "details": context or {}
        }
    }
    if hint:
        error_dict["error"]["hint"] = hint
    return json.dumps(error_dict, indent=2)


def format_success_json(data: Any) -> str:
    """
    Format a success response as JSON string.
    
    Args:
        data: Data to include in response
        
    Returns:
        JSON-formatted success string
    """
    return json.dumps(success_response(data), indent=2)
