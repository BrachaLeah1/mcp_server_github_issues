"""API functions for automated PR and fork operations."""

import os
from typing import Dict, Any, Optional

from ..github.client import GitHubClient
from ..config import GITHUB_TOKEN, ErrorCode
from ..utils.errors import error_response, success_response
from ..utils.redact import redact_token


async def create_pull_request_automated(
    repo: str,
    head: str,
    base: str,
    title: str,
    body: str = "",
    draft: bool = False,
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a pull request via GitHub API.
    
    Args:
        repo: Repository in "owner/repo" format
        head: Branch name or "username:branch" for forks
        base: Base branch to merge into
        title: PR title
        body: PR description
        draft: Whether to create as draft PR
        token: GitHub personal access token (optional, uses env if not provided)
        
    Returns:
        Standardized response with PR details
    """
    # Get token from parameter or environment
    auth_token = token or GITHUB_TOKEN
    
    if not auth_token:
        return error_response(
            ErrorCode.INVALID_INPUT,
            "GitHub token required for PR creation",
            {
                "message": "Please provide a token or set GITHUB_TOKEN environment variable",
                "documentation": "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token"
            }
        )
    
    # Validate inputs
    if not all([repo, head, base, title]):
        return error_response(
            ErrorCode.INVALID_INPUT,
            "Missing required parameters",
            {
                "required": ["repo", "head", "base", "title"],
                "message": "All of repo, head, base, and title are required"
            }
        )
    
    try:
        client = GitHubClient()
        result = await client.create_pull_request(
            token=auth_token,
            repo=repo,
            head=head,
            base=base,
            title=title,
            body=body,
            draft=draft
        )
        
        return success_response({
            "pr_url": result["pr_url"],
            "pr_number": result["pr_number"],
            "message": f"Pull request #{result['pr_number']} created successfully"
        })
        
    except Exception as e:
        # Ensure token is not in error message
        error_msg = redact_token(str(e))
        return error_response(
            ErrorCode.PR_CREATION_FAILED,
            f"Failed to create pull request: {error_msg}",
            {}
        )


async def fork_repository_automated(
    repo: str,
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fork a repository via GitHub API.
    
    Args:
        repo: Repository in "owner/repo" format
        token: GitHub personal access token (optional, uses env if not provided)
        
    Returns:
        Standardized response with fork details
    """
    # Get token from parameter or environment
    auth_token = token or GITHUB_TOKEN
    
    if not auth_token:
        return error_response(
            ErrorCode.INVALID_INPUT,
            "GitHub token required for forking",
            {
                "message": "Please provide a token or set GITHUB_TOKEN environment variable",
                "documentation": "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token"
            }
        )
    
    # Validate input
    if not repo or "/" not in repo:
        return error_response(
            ErrorCode.INVALID_INPUT,
            "Invalid repository format",
            {
                "expected": "owner/repo",
                "received": repo
            }
        )
    
    try:
        client = GitHubClient()
        result = await client.fork_repository(
            token=auth_token,
            repo=repo
        )
        
        return success_response({
            "fork_full_name": result["fork_full_name"],
            "clone_url": result["clone_url"],
            "ssh_url": result["ssh_url"],
            "message": f"Repository forked successfully to {result['fork_full_name']}"
        })
        
    except Exception as e:
        # Ensure token is not in error message
        error_msg = redact_token(str(e))
        return error_response(
            ErrorCode.FORK_FAILED,
            f"Failed to fork repository: {error_msg}",
            {}
        )
