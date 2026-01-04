"""Configuration and constants for the GitHub Issue Shepherd MCP server."""

import os
from typing import Optional

# GitHub API Configuration
GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")

# Rate Limits
DEFAULT_SEARCH_LIMIT = 10
MAX_SEARCH_LIMIT = 30
DEFAULT_MAX_COMMENTS = 10

# Pagination
DEFAULT_PAGE_SIZE = 30

# Git Configuration
DEFAULT_CLONE_METHOD = "https"
DEFAULT_BRANCH = "main"

# Filesystem
DEFAULT_MUST_BE_EMPTY = True

# Error Codes
class ErrorCode:
    """Standardized error codes for consistent error handling."""
    NOT_EMPTY = "NOT_EMPTY"
    GIT_NOT_FOUND = "GIT_NOT_FOUND"
    GITHUB_RATE_LIMIT = "GITHUB_RATE_LIMIT"
    HTTP_ERROR = "HTTP_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INVALID_PATH = "INVALID_PATH"
    GITHUB_NOT_FOUND = "GITHUB_NOT_FOUND"
    GITHUB_FORBIDDEN = "GITHUB_FORBIDDEN"
    CLONE_FAILED = "CLONE_FAILED"
    FORK_FAILED = "FORK_FAILED"
    PR_CREATION_FAILED = "PR_CREATION_FAILED"

# GitHub API Headers
def get_github_headers() -> dict:
    """Get GitHub API headers with optional authentication."""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers
