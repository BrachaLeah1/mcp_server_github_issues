"""GitHub Issue Shepherd MCP Server - Simplified Version.

A local MCP server that helps developers discover GitHub issues,
clone repositories, and create pull requests.

This version uses simple parameters instead of Pydantic models for better
compatibility with AI clients like Cursor.
"""

import json
from typing import Optional, List
from mcp.server.fastmcp import FastMCP

from src.config import (
    DEFAULT_SEARCH_LIMIT,
    MAX_SEARCH_LIMIT,
    DEFAULT_MAX_COMMENTS,
    DEFAULT_CLONE_METHOD,
    GITHUB_TOKEN
)
from src.github.client import GitHubClient
from src.github.query_builder import build_search_query, score_result
from src.git_ops.fs_validate import validate_folder_for_clone
from src.git_ops.clone import clone_repository
from src.pr.guidance import generate_pr_checklist
from src.pr.api import create_pull_request_automated, fork_repository_automated
from src.utils.errors import MCPError, success_response

# Initialize MCP server
mcp = FastMCP("github_issue_shepherd")


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
        # Validate mode
        if mode not in ["repo", "global"]:
            return json.dumps({
                "ok": False,
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "mode must be 'repo' or 'global'",
                    "details": {}
                }
            }, indent=2)
        
        # Validate repo if mode is repo
        if mode == "repo" and not repo:
            return json.dumps({
                "ok": False,
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "repo is required when mode='repo'",
                    "details": {}
                }
            }, indent=2)
        
        # Validate repo format
        if repo and '/' not in repo:
            return json.dumps({
                "ok": False,
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "repo must be in 'owner/repo' format",
                    "details": {}
                }
            }, indent=2)
        
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
        
        # Execute search
        client = GitHubClient()
        issues = await client.search_issues(
            query=query,
            sort=sort,
            limit=limit
        )
        
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
        
        return json.dumps(response, indent=2)
        
    except MCPError as e:
        return e.to_json()
    except Exception as e:
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
        # Validate repo format
        if '/' not in repo:
            return json.dumps({
                "ok": False,
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "repo must be in 'owner/repo' format",
                    "details": {}
                }
            }, indent=2)
        
        # Validate number
        if number <= 0:
            return json.dumps({
                "ok": False,
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "number must be greater than 0",
                    "details": {}
                }
            }, indent=2)
        
        client = GitHubClient()
        
        # Get issue details
        issue = await client.get_issue(repo, number)
        result = issue.to_dict()
        
        # Get comments if requested
        if include_comments and max_comments > 0:
            comments = await client.get_issue_comments(
                repo,
                number,
                max_comments
            )
            result["comments"] = [c.to_dict() for c in comments]
        
        response = success_response(result)
        return json.dumps(response, indent=2)
        
    except MCPError as e:
        return e.to_json()
    except Exception as e:
        return json.dumps({
            "ok": False,
            "error": {
                "code": "UNEXPECTED_ERROR",
                "message": f"Unexpected error: {str(e)}",
                "details": {}
            }
        }, indent=2)


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
        # Validate repo format
        if '/' not in repo:
            return json.dumps({
                "ok": False,
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "repo must be in 'owner/repo' format",
                    "details": {}
                }
            }, indent=2)
        
        client = GitHubClient()
        metadata = await client.get_repository(repo)
        
        response = success_response(metadata.to_dict())
        return json.dumps(response, indent=2)
        
    except MCPError as e:
        return e.to_json()
    except Exception as e:
        return json.dumps({
            "ok": False,
            "error": {
                "code": "UNEXPECTED_ERROR",
                "message": f"Unexpected error: {str(e)}",
                "details": {}
            }
        }, indent=2)


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
        result = validate_folder_for_clone(
            target_path,
            must_be_empty
        )
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "ok": False,
            "error": {
                "code": "UNEXPECTED_ERROR",
                "message": f"Unexpected error during validation: {str(e)}",
                "details": {}
            }
        }, indent=2)


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
        # Validate repo format
        if '/' not in repo:
            return json.dumps({
                "ok": False,
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "repo must be in 'owner/repo' format",
                    "details": {}
                }
            }, indent=2)
        
        # Validate clone method
        if clone_method not in ["https", "ssh"]:
            return json.dumps({
                "ok": False,
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "clone_method must be 'https' or 'ssh'",
                    "details": {}
                }
            }, indent=2)
        
        result = await clone_repository(
            repo=repo,
            target_path=target_path,
            clone_method=clone_method,
            shallow=shallow,
            branch=branch
        )
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "ok": False,
            "error": {
                "code": "UNEXPECTED_ERROR",
                "message": f"Unexpected error during clone: {str(e)}",
                "details": {}
            }
        }, indent=2)


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
        checklist = generate_pr_checklist(
            local_repo_path=local_repo_path,
            base_branch=base_branch,
            head_branch=head_branch,
            pr_title=pr_title,
            pr_body=pr_body,
            fork_flow=fork_flow
        )
        
        return checklist
        
    except Exception as e:
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
        # Validate repo format
        if '/' not in repo:
            return json.dumps({
                "ok": False,
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "repo must be in 'owner/repo' format",
                    "details": {}
                }
            }, indent=2)
        
        # Validate title
        if not title or len(title.strip()) == 0:
            return json.dumps({
                "ok": False,
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "title is required and cannot be empty",
                    "details": {}
                }
            }, indent=2)
        
        result = await create_pull_request_automated(
            repo=repo,
            head=head,
            base=base,
            title=title,
            body=body,
            draft=draft,
            token=token
        )
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "ok": False,
            "error": {
                "code": "UNEXPECTED_ERROR",
                "message": f"Unexpected error: {str(e)}",
                "details": {}
            }
        }, indent=2)


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
        # Validate repo format
        if '/' not in repo:
            return json.dumps({
                "ok": False,
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "repo must be in 'owner/repo' format",
                    "details": {}
                }
            }, indent=2)
        
        result = await fork_repository_automated(
            repo=repo,
            token=token
        )
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "ok": False,
            "error": {
                "code": "UNEXPECTED_ERROR",
                "message": f"Unexpected error: {str(e)}",
                "details": {}
            }
        }, indent=2)


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    mcp.run()