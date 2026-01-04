"""Git clone operations using subprocess."""

import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

from ..config import ErrorCode, DEFAULT_CLONE_METHOD
from ..utils.errors import error_response, success_response, MCPError
from ..utils.detect_project import format_next_steps
from .fs_validate import validate_folder_for_clone


def check_git_installed() -> bool:
    """
    Check if git is installed and available.
    
    Returns:
        True if git is available, False otherwise
    """
    return shutil.which("git") is not None


def get_clone_url(repo: str, method: str = "https") -> str:
    """
    Get the appropriate clone URL for a repository.
    
    Args:
        repo: Repository in "owner/repo" format
        method: Clone method ("https" or "ssh")
        
    Returns:
        Clone URL
    """
    if method == "ssh":
        return f"git@github.com:{repo}.git"
    else:
        return f"https://github.com/{repo}.git"


def get_current_branch(repo_path: Path) -> str:
    """
    Get the current branch name in a git repository.
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        Current branch name or "unknown"
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


async def clone_repository(
    repo: str,
    target_path: str,
    clone_method: str = DEFAULT_CLONE_METHOD,
    shallow: bool = False,
    branch: Optional[str] = None,
    skip_validation: bool = False
) -> Dict[str, Any]:
    """
    Clone a GitHub repository to a local directory.
    
    Args:
        repo: Repository in "owner/repo" format
        target_path: Local path to clone into
        clone_method: "https" or "ssh"
        shallow: Whether to do a shallow clone (--depth 1)
        branch: Specific branch to clone (optional)
        skip_validation: Skip folder validation (use with caution)
        
    Returns:
        Standardized response dictionary with clone results
    """
    # Check if git is installed
    if not check_git_installed():
        return error_response(
            ErrorCode.GIT_NOT_FOUND,
            "Git is not installed or not found in PATH",
            {
                "message": "Please install git from https://git-scm.com/downloads",
                "troubleshooting": "Ensure git is in your system PATH after installation"
            }
        )
    
    # Validate folder unless explicitly skipped
    if not skip_validation:
        validation_result = validate_folder_for_clone(target_path, must_be_empty=True)
        if not validation_result.get("ok"):
            return validation_result
        
        # Use the resolved path from validation
        target_path = validation_result["data"]["resolved_path"]
    
    # Build clone command
    clone_url = get_clone_url(repo, clone_method)
    cmd = ["git", "clone"]
    
    if shallow:
        cmd.extend(["--depth", "1"])
    
    if branch:
        cmd.extend(["--branch", branch])
    
    cmd.extend([clone_url, target_path])
    
    try:
        # Execute git clone
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
            
            # Parse common git errors
            if "Repository not found" in error_msg or "could not read" in error_msg:
                return error_response(
                    ErrorCode.CLONE_FAILED,
                    f"Repository not found or inaccessible: {repo}",
                    {
                        "clone_url": clone_url,
                        "message": "Check that the repository name is correct and you have access to it",
                        "git_error": error_msg
                    }
                )
            elif "Permission denied" in error_msg:
                return error_response(
                    ErrorCode.CLONE_FAILED,
                    "Permission denied during clone",
                    {
                        "clone_url": clone_url,
                        "message": "If using SSH, ensure your SSH keys are set up correctly",
                        "git_error": error_msg
                    }
                )
            else:
                return error_response(
                    ErrorCode.CLONE_FAILED,
                    f"Git clone failed: {error_msg}",
                    {
                        "clone_url": clone_url,
                        "git_error": error_msg
                    }
                )
        
        # Get the current branch
        repo_path = Path(target_path).resolve()
        current_branch = get_current_branch(repo_path)
        
        # Format next steps with project detection
        next_steps = format_next_steps(repo_path, repo, current_branch)
        
        return success_response({
            "local_repo_path": str(repo_path),
            "remote_url_used": clone_url,
            "current_branch": current_branch,
            "next_steps": next_steps
        })
        
    except subprocess.TimeoutExpired:
        return error_response(
            ErrorCode.CLONE_FAILED,
            "Clone operation timed out (exceeded 5 minutes)",
            {
                "clone_url": clone_url,
                "message": "The repository might be very large. Try a shallow clone with shallow=true"
            }
        )
    except Exception as e:
        return error_response(
            ErrorCode.CLONE_FAILED,
            f"Unexpected error during clone: {str(e)}",
            {"clone_url": clone_url}
        )


def get_git_status(repo_path: str) -> Dict[str, Any]:
    """
    Get git status for a repository.
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        Dictionary with git status information
    """
    if not check_git_installed():
        return {"error": "Git not installed"}
    
    try:
        path = Path(repo_path).resolve()
        
        # Check if it's a git repository
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return {"error": "Not a git repository"}
        
        # Get current branch
        branch = get_current_branch(path)
        
        # Get status
        result = subprocess.run(
            ["git", "-C", str(path), "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        has_changes = bool(result.stdout.strip())
        
        return {
            "is_git_repo": True,
            "current_branch": branch,
            "has_uncommitted_changes": has_changes,
            "status_summary": result.stdout.strip() if has_changes else "Working tree clean"
        }
        
    except Exception as e:
        return {"error": str(e)}
