"""Integration tests for MCP server tools.

These tests work with both the Pydantic-based and simplified parameter versions.
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, AsyncMock, patch


# Test if we can import the server
def test_server_imports():
    """Test that the server module imports successfully."""
    try:
        from src.server import mcp
        assert mcp is not None
        assert mcp.name == "github_issue_shepherd"
    except ImportError as e:
        pytest.fail(f"Failed to import server: {e}")


# Test search_issues tool with mock GitHub client
@pytest.mark.asyncio
async def test_search_issues_repo_mode():
    """Test search_issues in repo mode (only mode supported now)."""
    from src.server import search_issues
    from src.github.models import IssueSearchResult
    
    # Mock the GitHubClient
    with patch('src.server.GitHubClient') as MockClient:
        mock_client = MockClient.return_value
        
        # Create mock issue
        mock_issue_data = {
            "repository_url": "https://api.github.com/repos/test/repo",
            "number": 123,
            "title": "Test Issue",
            "html_url": "https://github.com/test/repo/issues/123",
            "labels": [{"name": "good first issue"}],
            "comments": 5,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-02T00:00:00Z",
            "state": "open",
            "body": "Test body"
        }
        
        mock_issue = IssueSearchResult(mock_issue_data)
        mock_client.search_issues = AsyncMock(return_value=[mock_issue])
        
        # Test the tool with required repo parameter
        result = await search_issues(
            repo="test/repo",
            skills=["python"],
            difficulty="good-first-issue",
            limit=10
        )
        
        # Parse and verify result
        result_data = json.loads(result)
        assert result_data["ok"] is True
        assert len(result_data["data"]["results"]) == 1
        assert result_data["data"]["results"][0]["number"] == 123


@pytest.mark.asyncio
async def test_search_issues_with_filters():
    """Test search_issues with various filters."""
    from src.server import search_issues
    from src.github.models import IssueSearchResult
    
    with patch('src.server.GitHubClient') as MockClient:
        mock_client = MockClient.return_value
        
        mock_issue_data = {
            "repository_url": "https://api.github.com/repos/facebook/react",
            "number": 456,
            "title": "React Issue",
            "html_url": "https://github.com/facebook/react/issues/456",
            "labels": [{"name": "bug"}],
            "comments": 3,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-02T00:00:00Z",
            "state": "open",
            "body": "React bug description"
        }
        
        mock_issue = IssueSearchResult(mock_issue_data)
        mock_client.search_issues = AsyncMock(return_value=[mock_issue])
        
        result = await search_issues(
            repo="facebook/react",
            difficulty="good-first-issue",
            limit=10
        )
        
        result_data = json.loads(result)
        assert result_data["ok"] is True
        assert result_data["data"]["results"][0]["repo"] == "facebook/react"


@pytest.mark.asyncio
async def test_search_issues_missing_repo():
    """Test search_issues without repo parameter (now required)."""
    from src.server import search_issues
    
    result = await search_issues(
        repo="",
        limit=10
    )
    
    result_data = json.loads(result)
    assert result_data["ok"] is False
    assert "INVALID_INPUT" in result_data["error"]["code"]
    assert "owner/repo" in result_data["error"]["message"]


@pytest.mark.asyncio
async def test_get_issue_details():
    """Test get_issue_details tool."""
    from src.server import get_issue_details
    from src.github.models import IssueDetail
    
    with patch('src.server.GitHubClient') as MockClient:
        mock_client = MockClient.return_value
        
        mock_issue_data = {
            "number": 123,
            "title": "Test Issue",
            "body": "Issue description",
            "html_url": "https://github.com/test/repo/issues/123",
            "state": "open",
            "labels": [{"name": "bug"}],
            "assignees": [],
            "milestone": None,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-02T00:00:00Z",
            "closed_at": None,
            "user": {"login": "testuser"},
            "comments": 5
        }
        
        mock_issue = IssueDetail(mock_issue_data)
        mock_client.get_issue = AsyncMock(return_value=mock_issue)
        
        result = await get_issue_details(
            repo="test/repo",
            number=123,
            include_comments=False
        )
        
        result_data = json.loads(result)
        assert result_data["ok"] is True
        assert result_data["data"]["number"] == 123
        assert result_data["data"]["title"] == "Test Issue"


@pytest.mark.asyncio
async def test_get_issue_details_invalid_repo():
    """Test get_issue_details with invalid repo format."""
    from src.server import get_issue_details
    
    result = await get_issue_details(
        repo="invalid_repo",  # Missing slash
        number=123
    )
    
    result_data = json.loads(result)
    assert result_data["ok"] is False
    assert "owner/repo" in result_data["error"]["message"].lower()


@pytest.mark.asyncio
async def test_list_repo_metadata():
    """Test list_repo_metadata tool."""
    from src.server import list_repo_metadata
    from src.github.models import RepositoryMetadata
    
    with patch('src.server.GitHubClient') as MockClient:
        mock_client = MockClient.return_value
        
        mock_repo_data = {
            "name": "react",
            "full_name": "facebook/react",
            "description": "A JavaScript library",
            "default_branch": "main",
            "language": "JavaScript",
            "license": {"name": "MIT"},
            "stargazers_count": 10000,
            "forks_count": 2000,
            "open_issues_count": 500,
            "clone_url": "https://github.com/facebook/react.git",
            "ssh_url": "git@github.com:facebook/react.git",
            "topics": ["javascript", "react", "library"],
            "homepage": "https://react.dev",
            "created_at": "2013-05-24T16:15:54Z",
            "updated_at": "2025-01-01T00:00:00Z"
        }
        
        mock_metadata = RepositoryMetadata(mock_repo_data)
        mock_client.get_repository = AsyncMock(return_value=mock_metadata)
        
        result = await list_repo_metadata(repo="facebook/react")
        
        result_data = json.loads(result)
        assert result_data["ok"] is True
        assert result_data["data"]["full_name"] == "facebook/react"
        assert result_data["data"]["language"] == "JavaScript"


@pytest.mark.asyncio
async def test_prepare_clone():
    """Test prepare_clone tool."""
    from src.server import prepare_clone
    import tempfile
    import os
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test with empty directory
        result = await prepare_clone(
            target_path=tmpdir,
            must_be_empty=True
        )
        
        result_data = json.loads(result)
        assert result_data["ok"] is True
        assert "OK" in result_data["data"]["status"]
        
        # Create a file to make it non-empty
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        
        # Test with non-empty directory
        result = await prepare_clone(
            target_path=tmpdir,
            must_be_empty=True
        )
        
        result_data = json.loads(result)
        assert result_data["ok"] is False
        assert "NOT_EMPTY" in result_data["error"]["code"]


@pytest.mark.asyncio
async def test_clone_repo_requires_confirmation():
    """Test clone_repo requires explicit confirmation."""
    from src.server import clone_repo
    
    # Call without confirmed=true
    result = await clone_repo(
        repo="test/repo",
        target_path="/tmp/test",
        confirmed=False  # Not confirmed
    )
    
    result_data = json.loads(result)
    assert result_data["ok"] is False
    assert result_data["error"]["code"] == "CONFIRMATION_REQUIRED"


@pytest.mark.asyncio
async def test_clone_repo_invalid_repo():
    """Test clone_repo with invalid repo format."""
    from src.server import clone_repo
    
    result = await clone_repo(
        repo="invalid",  # Missing slash
        target_path="/tmp/test",
        confirmed=True,  # Must include confirmation
        clone_method="https"
    )
    
    result_data = json.loads(result)
    assert result_data["ok"] is False
    assert "owner/repo" in result_data["error"]["message"].lower()


@pytest.mark.asyncio
async def test_clone_repo_invalid_method():
    """Test clone_repo with invalid clone method."""
    from src.server import clone_repo
    
    result = await clone_repo(
        repo="test/repo",
        target_path="/tmp/test",
        confirmed=True,  # Must include confirmation
        clone_method="ftp"  # Invalid
    )
    
    result_data = json.loads(result)
    assert result_data["ok"] is False
    assert "clone_method" in result_data["error"]["message"].lower()


@pytest.mark.asyncio
async def test_pr_assistant():
    """Test pr_assistant tool."""
    from src.server import pr_assistant
    
    result = await pr_assistant(
        local_repo_path="/tmp/test-repo",
        head_branch="feature/test",
        pr_title="Test PR",
        base_branch="main",
        pr_body="Test description"
    )
    
    # Should return markdown guide
    assert isinstance(result, str)
    assert "Pull Request Creation Guide" in result
    assert "feature/test" in result
    assert "Test PR" in result


@pytest.mark.asyncio
async def test_create_pull_request_invalid_repo():
    """Test create_pull_request with invalid repo."""
    from src.server import create_pull_request
    
    result = await create_pull_request(
        repo="invalid",
        head="test-branch",
        base="main",
        title="Test PR"
    )
    
    result_data = json.loads(result)
    assert result_data["ok"] is False
    assert "owner/repo" in result_data["error"]["message"].lower()


@pytest.mark.asyncio
async def test_create_pull_request_empty_title():
    """Test create_pull_request with empty title."""
    from src.server import create_pull_request
    
    result = await create_pull_request(
        repo="test/repo",
        head="test-branch",
        base="main",
        title=""
    )
    
    result_data = json.loads(result)
    assert result_data["ok"] is False
    assert "title" in result_data["error"]["message"].lower()


@pytest.mark.asyncio
async def test_fork_repo_invalid_repo():
    """Test fork_repo with invalid repo format."""
    from src.server import fork_repo
    
    result = await fork_repo(repo="invalid")
    
    result_data = json.loads(result)
    assert result_data["ok"] is False
    assert "owner/repo" in result_data["error"]["message"].lower()


# Test that all tools are registered
def test_all_tools_registered():
    """Test that all 8 tools are registered with the MCP server."""
    from src.server import mcp
    
    # Get the list of tools - this depends on FastMCP's internal structure
    # We check that the decorator has been applied
    assert hasattr(mcp, '_tool_manager') or hasattr(mcp, 'list_tools')
    
    # The tools should be defined as functions
    from src import server
    assert hasattr(server, 'search_issues')
    assert hasattr(server, 'get_issue_details')
    assert hasattr(server, 'list_repo_metadata')
    assert hasattr(server, 'prepare_clone')
    assert hasattr(server, 'clone_repo')
    assert hasattr(server, 'pr_assistant')
    assert hasattr(server, 'create_pull_request')
    assert hasattr(server, 'fork_repo')


# Performance test
@pytest.mark.asyncio
async def test_search_performance():
    """Test that search_issues completes in reasonable time."""
    from src.server import search_issues
    from src.github.models import IssueSearchResult
    import time
    
    with patch('src.server.GitHubClient') as MockClient:
        mock_client = MockClient.return_value
        mock_client.search_issues = AsyncMock(return_value=[])
        
        start = time.time()
        result = await search_issues(
            repo="python/cpython",
            skills=["python"],
            limit=10
        )
        duration = time.time() - start
        
        # Should complete in less than 1 second (with mocked client)
        assert duration < 1.0
        
        result_data = json.loads(result)
        assert result_data["ok"] is True


# Test discover_repository tool
@pytest.mark.asyncio
async def test_discover_repository_no_filters():
    """Test discover_repository with no language/topic filters."""
    from src.server import discover_repository
    
    with patch('httpx.AsyncClient') as MockAsyncClient:
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {
                    "full_name": "python/cpython",
                    "html_url": "https://github.com/python/cpython",
                    "description": "The Python programming language",
                    "stargazers_count": 60000,
                    "language": "C",
                    "topics": ["python", "interpreter"],
                    "updated_at": "2025-01-09T00:00:00Z",
                    "open_issues_count": 50
                },
                {
                    "full_name": "torvalds/linux",
                    "html_url": "https://github.com/torvalds/linux",
                    "description": "Linux kernel source tree",
                    "stargazers_count": 185000,
                    "language": "C",
                    "topics": ["kernel", "linux"],
                    "updated_at": "2025-01-09T00:00:00Z",
                    "open_issues_count": 100
                }
            ]
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        
        MockAsyncClient.return_value = mock_client_instance
        
        result = await discover_repository()
        
        result_data = json.loads(result)
        assert result_data["ok"] is True
        assert len(result_data["data"]["repositories"]) == 2
        assert result_data["data"]["repositories"][0]["name"] == "python/cpython"
        assert result_data["data"]["repositories"][0]["stars"] == 60000
        assert result_data["data"]["criteria"]["min_stars"] == 1000


@pytest.mark.asyncio
async def test_discover_repository_with_language():
    """Test discover_repository filtered by language."""
    from src.server import discover_repository
    
    with patch('httpx.AsyncClient') as MockAsyncClient:
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {
                    "full_name": "tensorflow/tensorflow",
                    "html_url": "https://github.com/tensorflow/tensorflow",
                    "description": "An Open Source Machine Learning Framework",
                    "stargazers_count": 185000,
                    "language": "Python",
                    "topics": ["machine-learning", "deep-learning"],
                    "updated_at": "2025-01-09T00:00:00Z",
                    "open_issues_count": 800
                }
            ]
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        
        MockAsyncClient.return_value = mock_client_instance
        
        result = await discover_repository(language="python")
        
        result_data = json.loads(result)
        assert result_data["ok"] is True
        assert len(result_data["data"]["repositories"]) == 1
        assert result_data["data"]["repositories"][0]["language"] == "Python"
        assert result_data["data"]["criteria"]["language"] == "python"


@pytest.mark.asyncio
async def test_discover_repository_with_topics():
    """Test discover_repository filtered by topics."""
    from src.server import discover_repository
    
    with patch('httpx.AsyncClient') as MockAsyncClient:
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {
                    "full_name": "scikit-learn/scikit-learn",
                    "html_url": "https://github.com/scikit-learn/scikit-learn",
                    "description": "scikit-learn: machine learning in Python",
                    "stargazers_count": 60000,
                    "language": "Python",
                    "topics": ["machine-learning", "python"],
                    "updated_at": "2025-01-09T00:00:00Z",
                    "open_issues_count": 400
                }
            ]
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        
        MockAsyncClient.return_value = mock_client_instance
        
        result = await discover_repository(topics=["machine-learning"])
        
        result_data = json.loads(result)
        assert result_data["ok"] is True
        assert len(result_data["data"]["repositories"]) == 1
        assert "machine-learning" in result_data["data"]["repositories"][0]["topics"]
        assert result_data["data"]["criteria"]["topics"] == ["machine-learning"]


@pytest.mark.asyncio
async def test_discover_repository_limit():
    """Test discover_repository respects the limit parameter."""
    from src.server import discover_repository
    
    with patch('httpx.AsyncClient') as MockAsyncClient:
        # Return 5 items but request limit of 3
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {
                    "full_name": f"org{i}/repo{i}",
                    "html_url": f"https://github.com/org{i}/repo{i}",
                    "description": f"Repo {i}",
                    "stargazers_count": 5000 + i * 1000,
                    "language": "Python",
                    "topics": ["test"],
                    "updated_at": "2025-01-09T00:00:00Z",
                    "open_issues_count": 100
                }
                for i in range(5)
            ]
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        
        MockAsyncClient.return_value = mock_client_instance
        
        result = await discover_repository(limit=3)
        
        result_data = json.loads(result)
        assert result_data["ok"] is True
        assert len(result_data["data"]["repositories"]) == 3
        assert result_data["data"]["count"] == 3


@pytest.mark.asyncio
async def test_discover_repository_error_handling():
    """Test discover_repository error handling."""
    from src.server import discover_repository
    
    with patch('httpx.AsyncClient') as MockAsyncClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.get = AsyncMock(side_effect=Exception("API Error"))
        
        MockAsyncClient.return_value = mock_client_instance
        
        result = await discover_repository()
        
        result_data = json.loads(result)
        assert result_data["ok"] is False
        assert result_data["error"]["code"] == "DISCOVERY_ERROR"
        assert "Failed to discover repositories" in result_data["error"]["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])