"""Utilities for redacting sensitive information from logs and errors."""

import re
from typing import Any, Dict


def redact_token(text: str) -> str:
    """
    Redact GitHub tokens from text.
    
    Tokens typically start with 'ghp_', 'gho_', 'ghu_', 'ghs_', or 'ghr_'.
    """
    # Redact GitHub tokens
    text = re.sub(r'gh[pousr]_[A-Za-z0-9]{36,}', '***REDACTED***', text)
    
    # Redact Bearer tokens in Authorization headers
    text = re.sub(r'Bearer\s+[A-Za-z0-9_\-\.]+', 'Bearer ***REDACTED***', text)
    
    # Redact generic token patterns
    text = re.sub(r'token["\']?\s*[:=]\s*["\']?[A-Za-z0-9_\-\.]+', 'token: ***REDACTED***', text, flags=re.IGNORECASE)
    
    return text


def redact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively redact sensitive fields from a dictionary.
    
    Redacts common sensitive field names like 'token', 'password', 'secret', etc.
    """
    sensitive_keys = {'token', 'password', 'secret', 'api_key', 'apikey', 'authorization'}
    
    redacted = {}
    for key, value in data.items():
        if key.lower() in sensitive_keys:
            redacted[key] = '***REDACTED***'
        elif isinstance(value, dict):
            redacted[key] = redact_dict(value)
        elif isinstance(value, str):
            redacted[key] = redact_token(value)
        else:
            redacted[key] = value
    
    return redacted


def safe_error_message(error: Exception, context: str = "") -> str:
    """
    Create a safe error message with redacted sensitive information.
    
    Args:
        error: The exception to format
        context: Additional context about where the error occurred
        
    Returns:
        A safe error message with redacted tokens
    """
    error_msg = str(error)
    redacted_msg = redact_token(error_msg)
    
    if context:
        return f"{context}: {redacted_msg}"
    return redacted_msg
