"""Filesystem validation utilities for safe cloning operations."""

import os
from pathlib import Path
from typing import Dict, Any, List
from enum import Enum

from ..config import ErrorCode
from ..utils.errors import error_response, success_response


class ValidationStatus(str, Enum):
    """Status codes for folder validation."""
    OK = "OK"
    NOT_EMPTY = "NOT_EMPTY"
    INVALID_PATH = "INVALID_PATH"
    PERMISSION_DENIED = "PERMISSION_DENIED"


def validate_folder_for_clone(
    target_path: str,
    must_be_empty: bool = True
) -> Dict[str, Any]:
    """
    Validate a folder path for cloning operations.
    
    Args:
        target_path: Path to validate
        must_be_empty: Whether the folder must be empty
        
    Returns:
        Standardized response dictionary with status and details
    """
    try:
        # Resolve and expand the path
        path = Path(target_path).expanduser().resolve()
        
        # Check if path is valid
        if not _is_valid_path(path):
            return error_response(
                ErrorCode.INVALID_PATH,
                f"Invalid path: {target_path}",
                {
                    "provided_path": target_path,
                    "message": "Path contains invalid characters or references"
                }
            )
        
        # Check if path exists
        if not path.exists():
            # Try to create it
            try:
                path.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                return error_response(
                    ErrorCode.PERMISSION_DENIED,
                    f"Permission denied: Cannot create directory at {path}",
                    {
                        "resolved_path": str(path),
                        "message": "You don't have permission to create directories at this location"
                    }
                )
            except Exception as e:
                return error_response(
                    ErrorCode.INVALID_PATH,
                    f"Failed to create directory: {str(e)}",
                    {"resolved_path": str(path)}
                )
        
        # Check if it's a directory
        if not path.is_dir():
            return error_response(
                ErrorCode.INVALID_PATH,
                f"Path exists but is not a directory: {path}",
                {
                    "resolved_path": str(path),
                    "message": "Please provide a directory path, not a file"
                }
            )
        
        # Check write permissions
        if not os.access(path, os.W_OK):
            return error_response(
                ErrorCode.PERMISSION_DENIED,
                f"Permission denied: Cannot write to directory {path}",
                {
                    "resolved_path": str(path),
                    "message": "You don't have write permission for this directory"
                }
            )
        
        # Check if folder is empty (if required)
        if must_be_empty:
            contents = list_directory_contents(path)
            if contents:
                return error_response(
                    ErrorCode.NOT_EMPTY,
                    f"Directory is not empty: {path}",
                    {
                        "resolved_path": str(path),
                        "contents_preview": contents[:10],  # First 10 items
                        "total_items": len(contents),
                        "message": "Please choose an empty directory for cloning or manually clear this directory"
                    }
                )
        
        # All checks passed
        return success_response({
            "status": ValidationStatus.OK,
            "resolved_path": str(path),
            "message": "Path is valid and ready for cloning"
        })
        
    except Exception as e:
        return error_response(
            ErrorCode.INVALID_PATH,
            f"Unexpected error during path validation: {str(e)}",
            {"provided_path": target_path}
        )


def _is_valid_path(path: Path) -> bool:
    """
    Check if a path is valid and safe.
    
    Args:
        path: Path to validate
        
    Returns:
        True if path is valid, False otherwise
    """
    try:
        # Basic validation - check if path can be resolved
        _ = path.resolve()
        
        # Check for suspicious patterns (this is basic, could be enhanced)
        path_str = str(path)
        
        # Disallow paths that try to escape using ".." excessively
        # (normal ".." is fine, but we want to catch malicious patterns)
        parts = path.parts
        dotdot_count = sum(1 for part in parts if part == "..")
        
        # If more than half the parts are "..", it's suspicious
        if dotdot_count > len(parts) / 2:
            return False
        
        return True
        
    except (ValueError, OSError):
        return False


def list_directory_contents(path: Path, max_items: int = 100) -> List[str]:
    """
    List contents of a directory.
    
    Args:
        path: Directory path
        max_items: Maximum items to return
        
    Returns:
        List of filenames/directory names
    """
    try:
        items = []
        for item in path.iterdir():
            items.append(item.name)
            if len(items) >= max_items:
                break
        return sorted(items)
    except Exception:
        return []


def format_validation_result(result: Dict[str, Any]) -> str:
    """
    Format validation result as a human-readable message.
    
    Args:
        result: Validation result dictionary
        
    Returns:
        Formatted message
    """
    if result.get("ok"):
        data = result.get("data", {})
        return f"✓ {data.get('message', 'Path validated successfully')}\nPath: {data.get('resolved_path', 'N/A')}"
    else:
        error = result.get("error", {})
        msg = f"✗ {error.get('message', 'Validation failed')}"
        
        details = error.get("details", {})
        if details.get("resolved_path"):
            msg += f"\nPath: {details['resolved_path']}"
        
        if details.get("contents_preview"):
            msg += f"\n\nDirectory contains {details.get('total_items', 0)} items:"
            for item in details["contents_preview"][:5]:
                msg += f"\n  - {item}"
            if details.get("total_items", 0) > 5:
                msg += f"\n  ... and {details['total_items'] - 5} more"
        
        if details.get("message"):
            msg += f"\n\nSuggestion: {details['message']}"
        
        return msg
