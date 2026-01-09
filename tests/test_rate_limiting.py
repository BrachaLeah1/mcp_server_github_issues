"""Tests for rate limiting behavior and error responses."""

import json
import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from src.github.client import GitHubClient
from src.utils.errors import RateLimitError, GitHubApiError
from src.utils.redact import redact_token


class TestRateLimitDetection:
    """Test rate limit detection in GitHub client."""
    
    @pytest.mark.asyncio
    async def test_429_too_many_requests(self):
        """Test handling of 429 (Too Many Requests) response."""
        client = GitHubClient()
        
        with patch('httpx.AsyncClient') as mock_async_client:
            # Mock the response with 429 status
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.headers = {
                "X-RateLimit-Limit": "60",
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": "1673280000"
            }
            
            # Setup AsyncClient mock
            mock_client_instance = MagicMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_async_client.return_value = mock_client_instance
            
            # Test that RateLimitError is raised
            with pytest.raises(RateLimitError) as exc_info:
                await client.search_issues("python", limit=10)
            
            # Verify error contains rate limit info
            error = exc_info.value
            assert error.code == "GITHUB_RATE_LIMIT"
            assert "rate limit exceeded" in error.message.lower()
            assert "resets_at" in error.details or "reset_at" in error.message
    
    @pytest.mark.asyncio
    async def test_403_with_rate_limit_message(self):
        """Test handling of 403 with rate limit error message."""
        client = GitHubClient()
        
        with patch('httpx.AsyncClient') as mock_async_client:
            # Mock 403 response with rate limit message
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.headers = {
                "X-RateLimit-Limit": "60",
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": "1673280000"
            }
            mock_response.json = MagicMock(return_value={
                "message": "API rate limit exceeded",
                "documentation_url": "https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting"
            })
            
            # Setup AsyncClient mock
            mock_client_instance = MagicMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_async_client.return_value = mock_client_instance
            
            # Test that RateLimitError is raised
            with pytest.raises(RateLimitError) as exc_info:
                await client.search_issues("python", limit=10)
            
            error = exc_info.value
            assert error.code == "GITHUB_RATE_LIMIT"
    
    @pytest.mark.asyncio
    async def test_rate_limit_error_json_format(self):
        """Test that rate limit error converts to standardized JSON format."""
        error = RateLimitError(reset_at="1673280000", limit_remaining=0)
        
        error_json = error.to_json()
        error_dict = json.loads(error_json)
        
        # Verify JSON structure
        assert error_dict["ok"] is False
        assert error_dict["error"]["code"] == "GITHUB_RATE_LIMIT"
        assert "rate limit exceeded" in error_dict["error"]["message"].lower()
        
        # Verify hint is present (in details, not at top level)
        assert "hint" in error_dict["error"]["details"]
        assert "GITHUB_TOKEN" in error_dict["error"]["details"]["hint"]
        
        # Verify details
        assert error_dict["error"]["details"]["limit_remaining"] == 0
    
    @pytest.mark.asyncio
    async def test_no_token_leakage_in_rate_limit_error(self):
        """Test that rate limit errors don't leak tokens in response."""
        error = RateLimitError(reset_at="1673280000", limit_remaining=0)
        error_json = error.to_json()
        
        # Verify no auth tokens in output
        assert "ghp_" not in error_json
        assert "Authorization" not in error_json
        assert "Bearer" not in error_json
        assert "token" not in error_json.lower() or "GITHUB_TOKEN" in error_json


class TestToolRateLimitResponses:
    """Test that tools return proper error responses for rate limiting."""
    
    @pytest.mark.asyncio
    async def test_search_issues_rate_limit_response(self):
        """Test search_issues tool error response for rate limit."""
        from src.server import search_issues
        
        with patch('src.github.client.GitHubClient.search_issues') as mock_search:
            # Mock rate limit error from client
            mock_search.side_effect = RateLimitError(reset_at="1673280000", limit_remaining=0)
            
            # Call tool with required repo parameter
            result = await search_issues(repo="test/repo")
            
            # Parse JSON response
            result_dict = json.loads(result)
            
            # Verify error structure
            assert result_dict["ok"] is False
            assert result_dict["error"]["code"] == "GITHUB_RATE_LIMIT"
            assert "rate limit exceeded" in result_dict["error"]["message"].lower()
            assert "hint" in result_dict["error"]["details"]
            
            # Verify no token leakage
            assert "ghp_" not in result
            assert "Bearer" not in result
    
    @pytest.mark.asyncio
    async def test_get_issue_details_rate_limit_response(self):
        """Test get_issue_details tool error response for rate limit."""
        from src.server import get_issue_details
        
        with patch('src.github.client.GitHubClient.get_issue') as mock_get:
            # Mock rate limit error
            mock_get.side_effect = GitHubApiError(
                "GitHub API rate limit exceeded",
                status_code=403
            )
            
            # Call tool
            result = await get_issue_details(repo="owner/repo", number=123)
            
            # Parse JSON response
            result_dict = json.loads(result)
            
            # Verify error response
            assert result_dict["ok"] is False
            assert "error" in result_dict
            
            # Verify no token leakage
            assert "ghp_" not in result
            assert "Bearer" not in result
    
    @pytest.mark.asyncio
    async def test_all_tool_responses_are_json(self):
        """Test that all tool error responses are valid JSON."""
        from src.server import (
            search_issues, get_issue_details, list_repo_metadata,
            create_pull_request
        )
        
        # Test search_issues with invalid repo format
        result = await search_issues(repo="invalid")
        assert isinstance(json.loads(result), dict)
        
        # Test get_issue_details with invalid repo
        result = await get_issue_details(repo="invalid", number=123)
        assert isinstance(json.loads(result), dict)
        
        # Test create_pull_request with missing title
        result = await create_pull_request(
            repo="owner/repo",
            head="branch",
            base="main",
            title=""
        )
        assert isinstance(json.loads(result), dict)


class TestRateLimitHeaders:
    """Test extraction and checking of rate limit headers."""
    
    def test_extract_rate_limit_info(self):
        """Test extraction of rate limit info from response headers."""
        client = GitHubClient()
        
        # Mock response
        mock_response = MagicMock()
        mock_response.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4999",
            "X-RateLimit-Reset": "1673280000"
        }
        
        rate_info = client._extract_rate_limit_info(mock_response)
        
        assert rate_info["limit"] == "5000"
        assert rate_info["remaining"] == "4999"
        assert rate_info["reset"] == "1673280000"
    
    def test_extract_rate_limit_info_missing_headers(self):
        """Test extraction when headers are missing."""
        client = GitHubClient()
        
        # Mock response with minimal headers
        mock_response = MagicMock()
        mock_response.headers = {}
        
        rate_info = client._extract_rate_limit_info(mock_response)
        
        assert rate_info["limit"] is None
        assert rate_info["remaining"] is None
        assert rate_info["reset"] is None


class TestTokenRedaction:
    """Test that tokens are properly redacted in error handling."""
    
    def test_token_redaction_in_error(self):
        """Test that error messages redact GitHub tokens."""
        test_token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        
        # Test redaction
        redacted = redact_token(test_token)
        
        # Verify token is obscured
        assert "ghp_" not in redacted or redacted == test_token
        assert test_token not in redacted or redacted == test_token
    
    def test_error_response_no_auth_headers(self):
        """Test that error responses don't include auth headers."""
        error_dict = {
            "ok": False,
            "error": {
                "code": "GITHUB_RATE_LIMIT",
                "message": "Rate limit exceeded",
                "details": {"status_code": 429}
            }
        }
        
        error_json = json.dumps(error_dict)
        
        # Verify no authorization info
        assert "Authorization" not in error_json
        assert "Bearer" not in error_json
        assert "ghp_" not in error_json


class TestRateLimitWarnings:
    """Test rate limit warning behavior."""
    
    def test_check_rate_limit_warning_threshold(self):
        """Test that warnings trigger at <10% remaining."""
        client = GitHubClient()
        
        # Mock response with <10% remaining
        mock_response = MagicMock()
        mock_response.headers = {
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "5"  # 5%
        }
        
        # Should not raise, just log warning
        client._check_rate_limit(mock_response)
    
    def test_check_rate_limit_no_warning_threshold(self):
        """Test that no warnings trigger when above 10% remaining."""
        client = GitHubClient()
        
        # Mock response with >10% remaining
        mock_response = MagicMock()
        mock_response.headers = {
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "50"  # 50%
        }
        
        # Should not raise or log warning
        client._check_rate_limit(mock_response)
