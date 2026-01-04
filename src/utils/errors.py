"""Structured error handling utilities."""

import json
from typing import Any, Dict, Optional


class MCPError(Exception):
    """Base exception for MCP server errors."""
    
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)
    
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
