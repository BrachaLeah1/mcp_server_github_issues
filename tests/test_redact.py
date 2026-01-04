"""Tests for token redaction utilities.

These tests are independent of the server parameter format.
"""

import pytest
from src.utils.redact import redact_token, redact_dict, safe_error_message


def test_redact_github_token():
    """Test redaction of GitHub tokens."""
    text = "Error with token: ghp_1234567890abcdefghijklmnopqrstuvwxyz"
    redacted = redact_token(text)
    
    assert "ghp_" not in redacted
    assert "***REDACTED***" in redacted
    assert "1234567890" not in redacted


def test_redact_multiple_token_types():
    """Test redaction of different GitHub token types."""
    tokens = [
        "ghp_1234567890abcdefghijklmnopqrstuvwxyz",
        "gho_1234567890abcdefghijklmnopqrstuvwxyz",
        "ghu_1234567890abcdefghijklmnopqrstuvwxyz",
        "ghs_1234567890abcdefghijklmnopqrstuvwxyz",
        "ghr_1234567890abcdefghijklmnopqrstuvwxyz"
    ]
    
    for token in tokens:
        text = f"Token: {token}"
        redacted = redact_token(text)
        assert token not in redacted
        assert "***REDACTED***" in redacted


def test_redact_bearer_token():
    """Test redaction of Bearer tokens in Authorization headers."""
    text = "Authorization: Bearer ghp_abcdefghijklmnopqrstuvwxyz123456"
    redacted = redact_token(text)
    
    assert "Bearer ***REDACTED***" in redacted
    assert "ghp_" not in redacted


def test_redact_token_field():
    """Test redaction of token field assignments."""
    texts = [
        'token: "ghp_1234567890abcdefghijklmnopqrstuvwxyz"',
        "token = ghp_1234567890abcdefghijklmnopqrstuvwxyz",
        "TOKEN: ghp_1234567890abcdefghijklmnopqrstuvwxyz"
    ]
    
    for text in texts:
        redacted = redact_token(text)
        assert "***REDACTED***" in redacted
        assert "ghp_" not in redacted or "1234567890" not in redacted


def test_redact_dict_sensitive_keys():
    """Test redaction of sensitive dictionary keys."""
    data = {
        "token": "ghp_secret123",
        "password": "mypassword",
        "api_key": "key123",
        "normal_field": "public_value"
    }
    
    redacted = redact_dict(data)
    
    assert redacted["token"] == "***REDACTED***"
    assert redacted["password"] == "***REDACTED***"
    assert redacted["api_key"] == "***REDACTED***"
    assert redacted["normal_field"] == "public_value"


def test_redact_dict_nested():
    """Test redaction of nested dictionaries."""
    data = {
        "config": {
            "token": "secret",
            "url": "https://api.github.com"
        },
        "other": "value"
    }
    
    redacted = redact_dict(data)
    
    assert redacted["config"]["token"] == "***REDACTED***"
    assert redacted["config"]["url"] == "https://api.github.com"
    assert redacted["other"] == "value"


def test_redact_dict_preserves_structure():
    """Test that redaction preserves dictionary structure."""
    data = {
        "level1": {
            "level2": {
                "token": "secret",
                "data": "public"
            }
        }
    }
    
    redacted = redact_dict(data)
    
    assert "level1" in redacted
    assert "level2" in redacted["level1"]
    assert redacted["level1"]["level2"]["token"] == "***REDACTED***"
    assert redacted["level1"]["level2"]["data"] == "public"


def test_safe_error_message():
    """Test safe error message creation."""
    error = ValueError("Failed with token: ghp_1234567890abcdefghijklmnopqrstuvwxyz")
    safe_msg = safe_error_message(error, "API call")
    
    assert "ghp_" not in safe_msg
    assert "***REDACTED***" in safe_msg
    assert "API call" in safe_msg


def test_safe_error_message_no_context():
    """Test safe error message without context."""
    error = ValueError("Token ghp_1234567890abcdefghijklmnopqrstuvwxyz is invalid")
    safe_msg = safe_error_message(error)
    
    assert "ghp_" not in safe_msg
    assert "***REDACTED***" in safe_msg


def test_redact_preserves_non_sensitive():
    """Test that non-sensitive content is preserved."""
    text = "This is a normal message without any secrets"
    redacted = redact_token(text)
    
    assert redacted == text


def test_redact_dict_empty():
    """Test redacting an empty dictionary."""
    data = {}
    redacted = redact_dict(data)
    
    assert redacted == {}