"""Data models for GitHub API responses."""

from typing import List, Optional, Any, Dict
from datetime import datetime


class IssueSearchResult:
    """Represents a GitHub issue search result."""
    
    def __init__(self, data: Dict[str, Any]):
        self.repo = data.get("repository_url", "").split("/repos/")[-1] if "repository_url" in data else ""
        self.number = data.get("number", 0)
        self.title = data.get("title", "")
        self.url = data.get("html_url", "")
        self.labels = [label.get("name", "") for label in data.get("labels", [])]
        self.comments = data.get("comments", 0)
        self.created_at = data.get("created_at", "")
        self.updated_at = data.get("updated_at", "")
        self.state = data.get("state", "open")
        self.body = data.get("body", "")
        self.score = data.get("score", 0)
    
    def get_snippet(self, max_length: int = 200) -> str:
        """Get a short snippet of the issue body."""
        if not self.body:
            return "(No description)"
        
        body = self.body.strip()
        if len(body) <= max_length:
            return body
        
        return body[:max_length] + "..."
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "repo": self.repo,
            "number": self.number,
            "title": self.title,
            "url": self.url,
            "labels": self.labels,
            "comments": self.comments,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "snippet": self.get_snippet(),
            "state": self.state
        }


class IssueDetail:
    """Represents detailed information about a GitHub issue."""
    
    def __init__(self, data: Dict[str, Any]):
        self.number = data.get("number", 0)
        self.title = data.get("title", "")
        self.body = data.get("body", "")
        self.url = data.get("html_url", "")
        self.state = data.get("state", "open")
        self.labels = [label.get("name", "") for label in data.get("labels", [])]
        self.assignees = [assignee.get("login", "") for assignee in data.get("assignees", [])]
        self.milestone = data.get("milestone", {}).get("title") if data.get("milestone") else None
        self.created_at = data.get("created_at", "")
        self.updated_at = data.get("updated_at", "")
        self.closed_at = data.get("closed_at")
        self.author = data.get("user", {}).get("login", "")
        self.comments_count = data.get("comments", 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "number": self.number,
            "title": self.title,
            "body": self.body,
            "url": self.url,
            "state": self.state,
            "labels": self.labels,
            "assignees": self.assignees,
            "milestone": self.milestone,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "closed_at": self.closed_at,
            "author": self.author,
            "comments_count": self.comments_count
        }


class Comment:
    """Represents a GitHub issue comment."""
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id", 0)
        self.author = data.get("user", {}).get("login", "")
        self.body = data.get("body", "")
        self.created_at = data.get("created_at", "")
        self.updated_at = data.get("updated_at", "")
        self.url = data.get("html_url", "")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "author": self.author,
            "body": self.body,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "url": self.url
        }


class RepositoryMetadata:
    """Represents GitHub repository metadata."""
    
    def __init__(self, data: Dict[str, Any]):
        self.name = data.get("name", "")
        self.full_name = data.get("full_name", "")
        self.description = data.get("description", "")
        self.default_branch = data.get("default_branch", "main")
        self.language = data.get("language", "")
        self.license = data.get("license", {}).get("name") if data.get("license") else None
        self.stars = data.get("stargazers_count", 0)
        self.forks = data.get("forks_count", 0)
        self.open_issues = data.get("open_issues_count", 0)
        self.clone_url = data.get("clone_url", "")
        self.ssh_url = data.get("ssh_url", "")
        self.topics = data.get("topics", [])
        self.homepage = data.get("homepage", "")
        self.created_at = data.get("created_at", "")
        self.updated_at = data.get("updated_at", "")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "full_name": self.full_name,
            "description": self.description,
            "default_branch": self.default_branch,
            "language": self.language,
            "license": self.license,
            "stars": self.stars,
            "forks": self.forks,
            "open_issues": self.open_issues,
            "clone_url": self.clone_url,
            "ssh_url": self.ssh_url,
            "topics": self.topics,
            "homepage": self.homepage,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
