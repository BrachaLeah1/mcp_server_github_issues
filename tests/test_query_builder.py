"""Tests for GitHub query builder.

These tests work with both Pydantic and simplified parameter versions.
"""

import pytest
from src.github.query_builder import build_search_query, score_result


def test_build_search_query_repo_mode():
    """Test building a search query for repository mode."""
    query = build_search_query(
        mode="repo",
        repo="facebook/react",
        difficulty="good-first-issue",
        state="open"
    )
    
    assert "is:issue" in query
    assert "is:open" in query
    assert "repo:facebook/react" in query
    assert "good first issue" in query


def test_build_search_query_global_mode():
    """Test building a search query for global mode."""
    query = build_search_query(
        mode="global",
        skills=["python", "testing"],
        topics=["machine-learning"],
        language="python",
        state="open"
    )
    
    assert "is:issue" in query
    assert "is:open" in query
    assert "python" in query
    assert "testing" in query
    assert "machine-learning" in query
    assert "language:python" in query


def test_build_search_query_with_labels():
    """Test building a search query with custom labels."""
    query = build_search_query(
        mode="repo",
        repo="microsoft/vscode",
        labels=["bug", "help-wanted"],
        state="open"
    )
    
    assert 'label:"bug"' in query
    assert 'label:"help-wanted"' in query


def test_build_search_query_difficulty_variations():
    """Test different difficulty levels."""
    # Good first issue
    query1 = build_search_query(mode="global", difficulty="good-first-issue")
    assert "good first issue" in query1
    
    # Easy
    query2 = build_search_query(mode="global", difficulty="easy")
    assert "easy" in query2 or "beginner" in query2
    
    # Medium
    query3 = build_search_query(mode="global", difficulty="medium")
    assert "medium" in query3 or "intermediate" in query3
    
    # Hard
    query4 = build_search_query(mode="global", difficulty="hard")
    assert "hard" in query4 or "advanced" in query4


def test_score_result():
    """Test scoring of search results."""
    issue_data = {
        "title": "Add python support for testing framework",
        "body": "This issue is about adding python support",
        "labels": [
            {"name": "good first issue"},
            {"name": "python"}
        ]
    }
    
    query_params = {
        "difficulty": "good-first-issue",
        "skills": ["python", "testing"],
        "topics": []
    }
    
    reasons = score_result(issue_data, query_params)
    
    assert any("good first issue" in r.lower() for r in reasons)
    assert any("python" in r.lower() for r in reasons)


def test_score_result_no_matches():
    """Test scoring when there are no specific matches."""
    issue_data = {
        "title": "Some random issue",
        "body": "Random content",
        "labels": []
    }
    
    query_params = {
        "difficulty": None,
        "skills": [],
        "topics": []
    }
    
    reasons = score_result(issue_data, query_params)
    
    assert len(reasons) > 0
    assert any("general" in r.lower() for r in reasons)