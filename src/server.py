"""GitHub Issue Shepherd MCP Server - Simplified Version.

A local MCP server that helps developers discover GitHub issues,
clone repositories, and create pull requests.

This version uses simple parameters instead of Pydantic models for better
compatibility with AI clients like Cursor.
"""

import json
import logging
import os
from typing import Optional, List
from mcp.server.fastmcp import FastMCP

from src.config import (
    DEFAULT_SEARCH_LIMIT,
    MAX_SEARCH_LIMIT,
    DEFAULT_MAX_COMMENTS,
    DEFAULT_CLONE_METHOD,
    GITHUB_TOKEN
)
from src.utils.logging_config import setup_logging, get_logger
from src.github.client import GitHubClient
from src.github.query_builder import build_search_query, score_result
from src.git_ops.fs_validate import validate_folder_for_clone
from src.git_ops.clone import clone_repository
from src.pr.guidance import generate_pr_checklist
from src.pr.api import create_pull_request_automated, fork_repository_automated
from src.utils.errors import MCPError, RateLimitError, GitHubApiError, success_response, format_success_json, format_error_json

# Setup logging before initializing MCP server
setup_logging(log_level=logging.INFO)
logger = get_logger(__name__)

# Initialize MCP server
mcp = FastMCP("github_issue_shepherd")

logger.info("GitHub Issue Shepherd MCP Server initialized")
if GITHUB_TOKEN:
    logger.info("GitHub token configured")
else:
    logger.warning("No GITHUB_TOKEN set - using unauthenticated API (60 req/hour limit)")


# ============================================================================
# MCP Tools - Simplified with Regular Parameters
# ============================================================================

@mcp.tool(
    name="search_issues",
    annotations={
        "title": "Search GitHub Issues",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def search_issues(
    mode: str,
    repo: Optional[str] = None,
    skills: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
    language: Optional[str] = None,
    difficulty: Optional[str] = None,
    labels: Optional[List[str]] = None,
    state: str = "open",
    sort: str = "relevance",
    limit: int = DEFAULT_SEARCH_LIMIT
) -> str:
    """Search for GitHub issues either in a specific repository or across GitHub.
    
    This tool helps developers discover issues to work on by searching based on:
    - Repository (for focused search)
    - Skills and topics (for broader discovery)
    - Programming language preferences
    - Difficulty level (good-first-issue, easy, medium, hard)
    - Custom labels and state filters
    
    Args:
        mode: 'repo' or 'global'
        repo: Repository name in 'owner/repo' format (required if mode='repo')
        skills: Skills like ['python', 'testing']
        topics: Topics like ['machine-learning']
        language: Programming language filter
        difficulty: 'good-first-issue', 'easy', 'medium', 'hard'
        labels: Additional label filters
        state: 'open', 'closed', or 'all'
        sort: 'relevance', 'created', 'updated', 'comments'
        limit: Maximum results (1-30)
    
    Returns:
        JSON string containing search results
    """
    try:
        logger.info(f"search_issues called: mode={mode}, repo={repo}")
        
        # Validate mode
        if mode not in ["repo", "global"]:
            logger.warning(f"Invalid mode: {mode}")
            return format_error_json(
                code="INVALID_INPUT",
                message="mode must be 'repo' or 'global'",
                hint="Use 'repo' for single repository search or 'global' for across GitHub"
            )
        
        # Validate repo if mode is repo
        if mode == "repo" and not repo:
            logger.warning("repo mode selected but no repo provided")
            return format_error_json(
                code="INVALID_INPUT",
                message="repo is required when mode='repo'",
                hint="Provide repo in 'owner/repo' format"
            )
        
        # Validate repo format
        if repo and '/' not in repo:
            logger.warning(f"Invalid repo format: {repo}")
            return format_error_json(
                code="INVALID_INPUT",
                message="repo must be in 'owner/repo' format",
                hint="Example: 'facebook/react' or 'torvalds/linux'"
            )
        
        # Clamp limit
        limit = max(1, min(limit, MAX_SEARCH_LIMIT))
        
        # Build search query
        query = build_search_query(
            mode=mode,
            repo=repo,
            skills=skills,
            topics=topics,
            language=language,
            difficulty=difficulty,
            labels=labels,
            state=state
        )
        
        logger.debug(f"Search query: {query}")
        
        # Execute search
        client = GitHubClient()
        issues = await client.search_issues(
            query=query,
            sort=sort,
            limit=limit
        )
        
        logger.info(f"Search completed: found {len(issues)} issues")
        
        # Format results with score reasons
        query_params = {
            "mode": mode,
            "repo": repo,
            "skills": skills,
            "topics": topics,
            "language": language,
            "difficulty": difficulty,
            "labels": labels,
            "state": state
        }
        
        results = []
        for issue in issues:
            issue_dict = issue.to_dict()
            issue_dict["score_reason"] = score_result(
                {"title": issue.title, "body": issue.body, "labels": [{"name": l} for l in issue.labels]},
                query_params
            )
            results.append(issue_dict)
        
        response = success_response({
            "results": results,
            "query": query,
            "total_found": len(results)
        })
        
        return format_success_json(response["data"])
        
    except RateLimitError as e:
        logger.error(f"Rate limit exceeded: {e}")
        return e.to_json()
    except MCPError as e:
        logger.error(f"MCP error in search_issues: {e}")
        return e.to_json()
    except Exception as e:
        logger.error(f"Unexpected error in search_issues: {e}", exc_info=True)
        return json.dumps({
            "ok": False,
            "error": {
                "code": "UNEXPECTED_ERROR",
                "message": f"Unexpected error during search: {str(e)}",
                "details": {}
            }
        }, indent=2)


@mcp.tool(
    name="get_issue_details",
    annotations={
        "title": "Get Issue Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def get_issue_details(
    repo: str,
    number: int,
    include_comments: bool = False,
    max_comments: int = DEFAULT_MAX_COMMENTS
) -> str:
    """Get detailed information about a specific GitHub issue.
    
    Fetches complete issue details including title, body, labels, assignees,
    timestamps, and optionally recent comments.
    
    Args:
        repo: Repository in 'owner/repo' format
        number: Issue number
        include_comments: Whether to fetch comments
        max_comments: Maximum comments to include (0-100)
    
    Returns:
        JSON string with issue details
    """
    try:
        logger.info(f"get_issue_details called: repo={repo}, number={number}, include_comments={include_comments}")
        
        # Validate repo format
        if '/' not in repo:
            logger.warning(f"Invalid repo format: {repo}")
            return format_error_json(
                code="INVALID_INPUT",
                message="repo must be in 'owner/repo' format",
                hint="Example: 'facebook/react' or 'torvalds/linux'"
            )
        
        # Validate number
        if number <= 0:
            logger.warning(f"Invalid issue number: {number}")
            return format_error_json(
                code="INVALID_INPUT",
                message="number must be greater than 0",
                hint="Issue number must be a positive integer"
            )
        
        client = GitHubClient()
        
        # Get issue details
        logger.debug(f"Fetching issue {repo}#{number}")
        issue = await client.get_issue(repo, number)
        result = issue.to_dict()
        
        # Get comments if requested
        if include_comments and max_comments > 0:
            logger.debug(f"Fetching {max_comments} comments for {repo}#{number}")
            comments = await client.get_issue_comments(
                repo,
                number,
                max_comments
            )
            result["comments"] = [c.to_dict() for c in comments]
            logger.info(f"Fetched {len(comments)} comments for {repo}#{number}")
        
        logger.info(f"Successfully retrieved issue details for {repo}#{number}")
        return format_success_json(result)
        
    except RateLimitError as e:
        logger.error(f"Rate limit exceeded while fetching {repo}#{number}: {e}")
        return e.to_json()
    except MCPError as e:
        logger.error(f"MCP error in get_issue_details: {e}")
        return e.to_json()
    except Exception as e:
        logger.error(f"Unexpected error fetching issue {repo}#{number}: {e}", exc_info=True)
        return format_error_json(
            code="UNEXPECTED_ERROR",
            message="Failed to fetch issue details",
            context={"error": str(e)}
        )


@mcp.tool(
    name="list_repo_metadata",
    annotations={
        "title": "List Repository Metadata",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def list_repo_metadata(repo: str) -> str:
    """Get metadata and information about a GitHub repository.
    
    Provides helpful context before cloning or working with a repository,
    including default branch, language, license, statistics, and clone URLs.
    
    Args:
        repo: Repository in 'owner/repo' format
    
    Returns:
        JSON string with repository metadata
    """
    try:
        logger.info(f"list_repo_metadata called: repo={repo}")
        
        # Validate repo format
        if '/' not in repo:
            logger.warning(f"Invalid repo format: {repo}")
            return format_error_json(
                code="INVALID_INPUT",
                message="repo must be in 'owner/repo' format",
                hint="Example: 'facebook/react' or 'torvalds/linux'"
            )
        
        logger.debug(f"Fetching metadata for {repo}")
        client = GitHubClient()
        metadata = await client.get_repository(repo)
        
        logger.info(f"Successfully retrieved metadata for {repo}")
        return format_success_json(metadata.to_dict())
        
    except RateLimitError as e:
        logger.error(f"Rate limit exceeded while fetching metadata for {repo}: {e}")
        return e.to_json()
    except MCPError as e:
        logger.error(f"MCP error in list_repo_metadata: {e}")
        return e.to_json()
    except Exception as e:
        logger.error(f"Unexpected error fetching metadata for {repo}: {e}", exc_info=True)
        return format_error_json(
            code="UNEXPECTED_ERROR",
            message="Failed to fetch repository metadata",
            context={"error": str(e)}
        )


@mcp.tool(
    name="prepare_clone",
    annotations={
        "title": "Prepare Folder for Clone",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def prepare_clone(
    target_path: str,
    must_be_empty: bool = True
) -> str:
    """Validate a folder path before cloning a repository.
    
    Checks if the target path exists, is empty (if required), and has
    proper permissions. Creates the directory if it doesn't exist.
    
    Args:
        target_path: Path to validate
        must_be_empty: Whether folder must be empty (default: true)
    
    Returns:
        JSON string with validation results
    """
    try:
        logger.info(f"prepare_clone called: target_path={target_path}, must_be_empty={must_be_empty}")
        
        result = validate_folder_for_clone(
            target_path,
            must_be_empty
        )
        
        if result.get("ok"):
            logger.info(f"Folder validation passed: {target_path}")
            return format_success_json(result.get("data", result))
        else:
            error_info = result.get("error", {})
            logger.warning(f"Folder validation failed for {target_path}: {error_info.get('message')}")
            return format_error_json(
                code=error_info.get("code", "VALIDATION_ERROR"),
                message=error_info.get("message", "Validation failed"),
                context=error_info.get("details", {})
            )
        
    except Exception as e:
        logger.error(f"Unexpected error validating {target_path}: {e}", exc_info=True)
        return format_error_json(
            code="UNEXPECTED_ERROR",
            message="Unexpected error during validation",
            context={"error": str(e)}
        )


@mcp.tool(
    name="clone_repo",
    annotations={
        "title": "Clone Repository",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def clone_repo(
    repo: str,
    target_path: str,
    clone_method: str = DEFAULT_CLONE_METHOD,
    shallow: bool = False,
    branch: Optional[str] = None
) -> str:
    """Clone a GitHub repository to a local directory.
    
    Clones the specified repository using git. The target folder should
    be validated first using prepare_clone. After successful clone,
    provides next steps and setup hints based on detected project type.
    
    Args:
        repo: Repository in 'owner/repo' format
        target_path: Local path to clone into
        clone_method: 'https' or 'ssh' (default: 'https')
        shallow: Whether to do shallow clone (default: false)
        branch: Specific branch to checkout
    
    Returns:
        JSON string with clone results
    """
    try:
        logger.info(f"clone_repo called: repo={repo}, target_path={target_path}, clone_method={clone_method}")
        
        # Validate repo format
        if '/' not in repo:
            logger.warning(f"Invalid repo format: {repo}")
            return format_error_json(
                code="INVALID_INPUT",
                message="repo must be in 'owner/repo' format",
                hint="Example: 'facebook/react' or 'torvalds/linux'"
            )
        
        # Validate clone method
        if clone_method not in ["https", "ssh"]:
            logger.warning(f"Invalid clone method: {clone_method}")
            return format_error_json(
                code="INVALID_INPUT",
                message="clone_method must be 'https' or 'ssh'",
                hint="Use 'https' for password/token auth or 'ssh' for key-based auth"
            )
        
        logger.debug(f"Starting clone of {repo} to {target_path}")
        result = await clone_repository(
            repo=repo,
            target_path=target_path,
            clone_method=clone_method,
            shallow=shallow,
            branch=branch
        )
        
        if result.get("ok"):
            logger.info(f"Successfully cloned {repo} to {target_path}")
            return format_success_json(result.get("data", result))
        else:
            error_info = result.get("error", {})
            logger.error(f"Clone failed for {repo}: {error_info.get('message')}")
            return format_error_json(
                code=error_info.get("code", "CLONE_FAILED"),
                message=error_info.get("message", "Clone operation failed"),
                context=error_info.get("details", {})
            )
        
    except Exception as e:
        logger.error(f"Unexpected error cloning {repo}: {e}", exc_info=True)
        return format_error_json(
            code="UNEXPECTED_ERROR",
            message="Unexpected error during clone",
            context={"error": str(e)}
        )


@mcp.tool(
    name="pr_assistant",
    annotations={
        "title": "Pull Request Creation Assistant",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def pr_assistant(
    local_repo_path: str,
    head_branch: str,
    pr_title: str,
    base_branch: str = "main",
    pr_body: str = "",
    fork_flow: bool = True
) -> str:
    """Get step-by-step guidance for creating a pull request.
    
    Provides comprehensive instructions for creating a PR without requiring
    credentials. Includes commands for testing, pushing, and opening a PR
    via web interface or GitHub CLI.
    
    Args:
        local_repo_path: Path to local repository
        base_branch: Base branch to merge into (default: 'main')
        head_branch: Your branch with changes
        pr_title: Proposed PR title
        pr_body: Proposed PR description
        fork_flow: Whether using fork workflow (default: true)
    
    Returns:
        Markdown-formatted checklist
    """
    try:
        logger.info(f"pr_assistant called: local_repo_path={local_repo_path}, head_branch={head_branch}")
        
        logger.debug(f"Generating PR checklist for {head_branch} -> {base_branch}")
        checklist = await generate_pr_checklist(
            local_repo_path=local_repo_path,
            base_branch=base_branch,
            head_branch=head_branch,
            pr_title=pr_title,
            pr_body=pr_body,
            fork_flow=fork_flow
        )
        
        logger.info(f"Successfully generated PR checklist for {head_branch}")
        return checklist
        
    except Exception as e:
        logger.error(f"Error generating PR guide for {head_branch}: {e}", exc_info=True)
        return f"Error generating PR guide: {str(e)}"


@mcp.tool(
    name="create_pull_request",
    annotations={
        "title": "Create Pull Request (Automated)",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def create_pull_request(
    repo: str,
    head: str,
    base: str,
    title: str,
    body: str = "",
    draft: bool = False,
    token: Optional[str] = None
) -> str:
    """Create a pull request automatically via GitHub API.
    
    Requires a GitHub personal access token (provided or via GITHUB_TOKEN env).
    Creates a PR from your branch to the base branch.
    
    Args:
        repo: Repository in 'owner/repo' format
        head: Branch name or 'username:branch' for forks
        base: Base branch to merge into
        title: PR title
        body: PR description
        draft: Create as draft (default: false)
        token: GitHub PAT (uses env if not provided)
    
    Returns:
        JSON string with PR creation results
    """
    try:
        logger.info(f"create_pull_request called: repo={repo}, head={head}, base={base}, title={title}")
        
        # Validate repo format
        if '/' not in repo:
            logger.warning(f"Invalid repo format: {repo}")
            return format_error_json(
                code="INVALID_INPUT",
                message="repo must be in 'owner/repo' format",
                hint="Example: 'facebook/react' or 'torvalds/linux'"
            )
        
        # Validate title
        if not title or len(title.strip()) == 0:
            logger.warning("Empty PR title provided")
            return format_error_json(
                code="INVALID_INPUT",
                message="title is required and cannot be empty",
                hint="Provide a clear, concise PR title (e.g., 'Fix login redirect bug')"
            )
        
        logger.debug(f"Creating PR: {head} -> {base}")
        result = await create_pull_request_automated(
            repo=repo,
            head=head,
            base=base,
            title=title,
            body=body,
            draft=draft,
            token=token
        )
        
        if result.get("ok"):
            logger.info(f"Successfully created PR in {repo}")
            return format_success_json(result.get("data", result))
        else:
            error_info = result.get("error", {})
            logger.error(f"PR creation failed for {repo}: {error_info.get('message')}")
            return format_error_json(
                code=error_info.get("code", "PR_CREATION_FAILED"),
                message=error_info.get("message", "Failed to create pull request"),
                context=error_info.get("details", {})
            )
        
    except Exception as e:
        logger.error(f"Unexpected error creating PR in {repo}: {e}", exc_info=True)
        return format_error_json(
            code="UNEXPECTED_ERROR",
            message="Unexpected error during PR creation",
            context={"error": str(e)}
        )


@mcp.tool(
    name="fork_repo",
    annotations={
        "title": "Fork Repository (Automated)",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def fork_repo(
    repo: str,
    token: Optional[str] = None
) -> str:
    """Fork a GitHub repository to your account via API.
    
    Requires a GitHub personal access token (provided or via GITHUB_TOKEN env).
    Creates a fork of the specified repository under your account.
    
    Args:
        repo: Repository in 'owner/repo' format
        token: GitHub PAT (uses env if not provided)
    
    Returns:
        JSON string with fork results
    """
    try:
        logger.info(f"fork_repo called: repo={repo}")
        
        # Validate repo format
        if '/' not in repo:
            logger.warning(f"Invalid repo format: {repo}")
            return format_error_json(
                code="INVALID_INPUT",
                message="repo must be in 'owner/repo' format",
                hint="Example: 'facebook/react' or 'torvalds/linux'"
            )
        
        logger.debug(f"Forking {repo} to user account")
        result = await fork_repository_automated(
            repo=repo,
            token=token
        )
        
        if result.get("ok"):
            logger.info(f"Successfully forked {repo}")
            return format_success_json(result.get("data", result))
        else:
            error_info = result.get("error", {})
            logger.error(f"Fork failed for {repo}: {error_info.get('message')}")
            return format_error_json(
                code=error_info.get("code", "FORK_FAILED"),
                message=error_info.get("message", "Failed to fork repository"),
                context=error_info.get("details", {})
            )
        
    except Exception as e:
        logger.error(f"Unexpected error forking {repo}: {e}", exc_info=True)
        return format_error_json(
            code="UNEXPECTED_ERROR",
            message="Unexpected error during fork",
            context={"error": str(e)}
        )


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    mcp.run()