"""Tests for filesystem validation.

These tests are independent of the server parameter format.
"""

import pytest
import tempfile
import os
from pathlib import Path
from src.git_ops.fs_validate import (
    validate_folder_for_clone,
    list_directory_contents,
    ValidationStatus
)


def test_validate_empty_directory():
    """Test validation of an empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = validate_folder_for_clone(tmpdir, must_be_empty=True)
        
        assert result["ok"] is True
        assert result["data"]["status"] == ValidationStatus.OK
        assert Path(tmpdir).resolve() == Path(result["data"]["resolved_path"])


def test_validate_non_empty_directory():
    """Test validation of a non-empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file in the directory
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("test content")
        
        result = validate_folder_for_clone(tmpdir, must_be_empty=True)
        
        assert result["ok"] is False
        assert result["error"]["code"] == "NOT_EMPTY"
        assert "test.txt" in result["error"]["details"]["contents_preview"]


def test_validate_non_empty_directory_allowed():
    """Test validation when non-empty is allowed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file in the directory
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("test content")
        
        result = validate_folder_for_clone(tmpdir, must_be_empty=False)
        
        assert result["ok"] is True


def test_validate_creates_directory():
    """Test that validation creates directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        new_dir = Path(tmpdir) / "new_folder"
        
        result = validate_folder_for_clone(str(new_dir), must_be_empty=True)
        
        assert result["ok"] is True
        assert new_dir.exists()
        assert new_dir.is_dir()


def test_validate_path_expansion():
    """Test that paths with ~ are expanded."""
    home = Path.home()
    result = validate_folder_for_clone("~", must_be_empty=False)
    
    assert result["ok"] is True
    assert str(home) in result["data"]["resolved_path"]


def test_list_directory_contents():
    """Test listing directory contents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some files
        for i in range(5):
            (Path(tmpdir) / f"file{i}.txt").write_text("content")
        
        contents = list_directory_contents(Path(tmpdir))
        
        assert len(contents) == 5
        assert "file0.txt" in contents
        assert "file4.txt" in contents
        assert contents == sorted(contents)  # Should be sorted


def test_list_directory_contents_max_items():
    """Test that max_items is respected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create 20 files
        for i in range(20):
            (Path(tmpdir) / f"file{i}.txt").write_text("content")
        
        contents = list_directory_contents(Path(tmpdir), max_items=10)
        
        assert len(contents) == 10


def test_validate_file_not_directory():
    """Test validation fails when path is a file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"
        file_path.write_text("content")
        
        result = validate_folder_for_clone(str(file_path), must_be_empty=True)
        
        assert result["ok"] is False
        assert result["error"]["code"] == "INVALID_PATH"