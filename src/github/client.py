"""GitHub API client for making HTTP requests."""

import json
from typing import List, Dict, Any, Optional
import httpx

from ..config import GITHUB_API_BASE, get_github_headers, ErrorCode, DEFAULT_PAGE_SIZE
from ..utils.errors import MCPError
from ..utils.redact import safe_error_message
from .models import IssueSearchResult, IssueDetail, Comment, RepositoryMetadata


class GitHubClient:
    """Client for interacting with the GitHub API."""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize the GitHub API client.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.base_url = GITHUB_API_BASE
        self.timeout = timeout
    
    async def search_issues(
        self,
        query: str,
        sort: str = "relevance",
        limit: int = 10
    ) -> List[IssueSearchResult]:
        """
        Search for issues using GitHub search API.
        
        Args:
            query: GitHub search query string
            sort: Sort order (relevance, created, updated, comments)
            limit: Maximum number of results
            
        Returns:
            List of IssueSearchResult objects
            
        Raises:
            MCPError: If the API request fails
        """
        url = f"{self.base_url}/search/issues"
        params = {
            "q": query,
            "sort": sort,
            "per_page": min(limit, 100)  # GitHub max is 100
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=get_github_headers()
                )
                
                if response.status_code == 403:
                    error_data = response.json()
                    if "rate limit" in error_data.get("message", "").lower():
                        raise MCPError(
                            ErrorCode.GITHUB_RATE_LIMIT,
                            "GitHub API rate limit exceeded. Please set GITHUB_TOKEN environment variable for higher limits.",
                            {"documentation": "https://docs.github.com/en/rest/rate-limit"}
                        )
                    raise MCPError(
                        ErrorCode.GITHUB_FORBIDDEN,
                        f"Access forbidden: {error_data.get('message', 'Unknown error')}",
                        {"status_code": 403}
                    )
                
                response.raise_for_status()
                data = response.json()
                
                items = data.get("items", [])[:limit]
                return [IssueSearchResult(item) for item in items]
                
        except httpx.HTTPStatusError as e:
            raise MCPError(
                ErrorCode.HTTP_ERROR,
                safe_error_message(e, "GitHub API request failed"),
                {"status_code": e.response.status_code}
            )
        except httpx.RequestError as e:
            raise MCPError(
                ErrorCode.HTTP_ERROR,
                safe_error_message(e, "Network error while contacting GitHub"),
                {}
            )
    
    async def get_issue(
        self,
        repo: str,
        number: int
    ) -> IssueDetail:
        """
        Get detailed information about a specific issue.
        
        Args:
            repo: Repository in "owner/repo" format
            number: Issue number
            
        Returns:
            IssueDetail object
            
        Raises:
            MCPError: If the API request fails
        """
        url = f"{self.base_url}/repos/{repo}/issues/{number}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=get_github_headers())
                
                if response.status_code == 404:
                    raise MCPError(
                        ErrorCode.GITHUB_NOT_FOUND,
                        f"Issue #{number} not found in repository {repo}",
                        {"repo": repo, "number": number}
                    )
                
                if response.status_code == 403:
                    raise MCPError(
                        ErrorCode.GITHUB_RATE_LIMIT,
                        "GitHub API rate limit exceeded. Please set GITHUB_TOKEN environment variable.",
                        {}
                    )
                
                response.raise_for_status()
                data = response.json()
                
                return IssueDetail(data)
                
        except httpx.HTTPStatusError as e:
            raise MCPError(
                ErrorCode.HTTP_ERROR,
                safe_error_message(e, "Failed to fetch issue details"),
                {"status_code": e.response.status_code}
            )
        except httpx.RequestError as e:
            raise MCPError(
                ErrorCode.HTTP_ERROR,
                safe_error_message(e, "Network error while fetching issue"),
                {}
            )
    
    async def get_issue_comments(
        self,
        repo: str,
        number: int,
        max_comments: int = 10
    ) -> List[Comment]:
        """
        Get comments for a specific issue.
        
        Args:
            repo: Repository in "owner/repo" format
            number: Issue number
            max_comments: Maximum number of comments to return
            
        Returns:
            List of Comment objects
            
        Raises:
            MCPError: If the API request fails
        """
        url = f"{self.base_url}/repos/{repo}/issues/{number}/comments"
        params = {
            "per_page": min(max_comments, 100),
            "sort": "created",
            "direction": "desc"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=get_github_headers()
                )
                
                if response.status_code == 404:
                    # Issue might not exist, but return empty list
                    return []
                
                response.raise_for_status()
                data = response.json()
                
                return [Comment(comment) for comment in data[:max_comments]]
                
        except httpx.HTTPStatusError as e:
            # For comments, we can be more lenient and return empty list
            return []
        except httpx.RequestError as e:
            return []
    
    async def get_repository(self, repo: str) -> RepositoryMetadata:
        """
        Get repository metadata.
        
        Args:
            repo: Repository in "owner/repo" format
            
        Returns:
            RepositoryMetadata object
            
        Raises:
            MCPError: If the API request fails
        """
        url = f"{self.base_url}/repos/{repo}"
        headers = get_github_headers()
        # Add topics preview header
        headers["Accept"] = "application/vnd.github.mercy-preview+json"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 404:
                    raise MCPError(
                        ErrorCode.GITHUB_NOT_FOUND,
                        f"Repository {repo} not found",
                        {"repo": repo}
                    )
                
                response.raise_for_status()
                data = response.json()
                
                return RepositoryMetadata(data)
                
        except httpx.HTTPStatusError as e:
            raise MCPError(
                ErrorCode.HTTP_ERROR,
                safe_error_message(e, "Failed to fetch repository metadata"),
                {"status_code": e.response.status_code}
            )
        except httpx.RequestError as e:
            raise MCPError(
                ErrorCode.HTTP_ERROR,
                safe_error_message(e, "Network error while fetching repository"),
                {}
            )
    
    async def create_pull_request(
        self,
        token: str,
        repo: str,
        head: str,
        base: str,
        title: str,
        body: str = "",
        draft: bool = False
    ) -> Dict[str, Any]:
        """
        Create a pull request via GitHub API.
        
        Args:
            token: GitHub personal access token
            repo: Repository in "owner/repo" format
            head: Branch name or "username:branch" for forks
            base: Base branch to merge into
            title: PR title
            body: PR description
            draft: Whether to create as draft PR
            
        Returns:
            Dictionary with pr_url and pr_number
            
        Raises:
            MCPError: If the API request fails
        """
        url = f"{self.base_url}/repos/{repo}/pulls"
        headers = get_github_headers()
        headers["Authorization"] = f"Bearer {token}"
        
        payload = {
            "title": title,
            "head": head,
            "base": base,
            "body": body,
            "draft": draft
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 422:
                    error_data = response.json()
                    raise MCPError(
                        ErrorCode.PR_CREATION_FAILED,
                        f"Pull request validation failed: {error_data.get('message', 'Unknown error')}",
                        {"errors": error_data.get("errors", [])}
                    )
                
                response.raise_for_status()
                data = response.json()
                
                return {
                    "pr_url": data.get("html_url", ""),
                    "pr_number": data.get("number", 0)
                }
                
        except httpx.HTTPStatusError as e:
            raise MCPError(
                ErrorCode.PR_CREATION_FAILED,
                safe_error_message(e, "Failed to create pull request"),
                {"status_code": e.response.status_code}
            )
        except httpx.RequestError as e:
            raise MCPError(
                ErrorCode.HTTP_ERROR,
                safe_error_message(e, "Network error while creating PR"),
                {}
            )
    
    async def fork_repository(
        self,
        token: str,
        repo: str
    ) -> Dict[str, Any]:
        """
        Fork a repository via GitHub API.
        
        Args:
            token: GitHub personal access token
            repo: Repository in "owner/repo" format
            
        Returns:
            Dictionary with fork_full_name, clone_url, and ssh_url
            
        Raises:
            MCPError: If the API request fails
        """
        url = f"{self.base_url}/repos/{repo}/forks"
        headers = get_github_headers()
        headers["Authorization"] = f"Bearer {token}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers)
                
                if response.status_code == 403:
                    raise MCPError(
                        ErrorCode.FORK_FAILED,
                        "Cannot fork repository. You may not have permission or already have a fork.",
                        {}
                    )
                
                response.raise_for_status()
                data = response.json()
                
                return {
                    "fork_full_name": data.get("full_name", ""),
                    "clone_url": data.get("clone_url", ""),
                    "ssh_url": data.get("ssh_url", "")
                }
                
        except httpx.HTTPStatusError as e:
            raise MCPError(
                ErrorCode.FORK_FAILED,
                safe_error_message(e, "Failed to fork repository"),
                {"status_code": e.response.status_code}
            )
        except httpx.RequestError as e:
            raise MCPError(
                ErrorCode.HTTP_ERROR,
                safe_error_message(e, "Network error while forking repository"),
                {}
            )
