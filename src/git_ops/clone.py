"""Git clone operations using fully async subprocess.

This version uses asyncio.create_subprocess_exec() instead of asyncio.to_thread()
for better performance and true async I/O without blocking the thread pool.
"""

import asyncio
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


async def run_git_command(
    args: list[str],
    cwd: Optional[str] = None,
    timeout: int = 30
) -> tuple[int, str, str]:
    """
    Run a git command asynchronously using asyncio subprocess.
    
    This is the core async function that replaces subprocess.run() calls.
    It uses asyncio.create_subprocess_exec() for true async I/O.
    
    Args:
        args: Command arguments (e.g., ["git", "status"])
        cwd: Working directory for the command
        timeout: Timeout in seconds
        
    Returns:
        Tuple of (returncode, stdout, stderr)
        
    Raises:
        asyncio.TimeoutError: If command times out
    """
    try:
        # Create async subprocess
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        
        # Wait for completion with timeout
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )
        
        return (
            process.returncode,
            stdout.decode('utf-8', errors='replace'),
            stderr.decode('utf-8', errors='replace')
        )
        
    except asyncio.TimeoutError:
        # Kill the process if it times out
        if process.returncode is None:
            process.kill()
            await process.wait()
        raise


async def get_current_branch(repo_path: Path) -> str:
    """
    Get the current branch name in a git repository.
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        Current branch name or "unknown"
    """
    try:
        returncode, stdout, stderr = await run_git_command(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(repo_path),
            timeout=5
        )
        
        if returncode == 0:
            return stdout.strip()
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
    Clone a GitHub repository to a local directory using async subprocess.
    
    This version uses asyncio.create_subprocess_exec() for true async I/O,
    which is more efficient than asyncio.to_thread() as it doesn't consume
    thread pool resources and provides better concurrency.
    
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
        # Execute git clone using fully async subprocess
        # This doesn't block the event loop or consume thread pool resources
        returncode, stdout, stderr = await run_git_command(
            cmd,
            cwd=None,  # Clone operations don't need a cwd
            timeout=300  # 5 minute timeout
        )
        
        if returncode != 0:
            error_msg = stderr.strip() if stderr else stdout.strip()
            
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
        current_branch = await get_current_branch(repo_path)
        
        # Format next steps with project detection
        next_steps = format_next_steps(repo_path, repo, current_branch)
        
        return success_response({
            "local_repo_path": str(repo_path),
            "remote_url_used": clone_url,
            "current_branch": current_branch,
            "next_steps": next_steps
        })
        
    except asyncio.TimeoutError:
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


async def get_git_status(repo_path: str) -> Dict[str, Any]:
    """
    Get git status for a repository using async subprocess.
    
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
        returncode, stdout, stderr = await run_git_command(
            ["git", "rev-parse", "--git-dir"],
            cwd=str(path),
            timeout=5
        )
        
        if returncode != 0:
            return {"error": "Not a git repository"}
        
        # Get current branch
        branch = await get_current_branch(path)
        
        # Get status
        returncode, stdout, stderr = await run_git_command(
            ["git", "status", "--porcelain"],
            cwd=str(path),
            timeout=5
        )
        
        has_changes = bool(stdout.strip())
        
        return {
            "is_git_repo": True,
            "current_branch": branch,
            "has_uncommitted_changes": has_changes,
            "status_summary": stdout.strip() if has_changes else "Working tree clean"
        }
        
    except asyncio.TimeoutError:
        return {"error": "Git command timed out"}
    except Exception as e:
        return {"error": str(e)}


async def check_repo_has_uncommitted_changes(repo_path: str) -> bool:
    """
    Quick check if repository has uncommitted changes.
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        True if there are uncommitted changes, False otherwise
    """
    try:
        returncode, stdout, stderr = await run_git_command(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            timeout=5
        )
        
        return returncode == 0 and bool(stdout.strip())
    except Exception:
        return False


async def get_remote_url(repo_path: str, remote: str = "origin") -> Optional[str]:
    """
    Get the remote URL for a git repository.
    
    Args:
        repo_path: Path to the git repository
        remote: Remote name (default: "origin")
        
    Returns:
        Remote URL or None if not found
    """
    try:
        returncode, stdout, stderr = await run_git_command(
            ["git", "remote", "get-url", remote],
            cwd=repo_path,
            timeout=5
        )
        
        if returncode == 0:
            return stdout.strip()
    except Exception:
        pass
    
    return None