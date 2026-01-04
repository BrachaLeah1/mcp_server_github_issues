"""Generate PR creation guidance and instructions."""

from pathlib import Path
from typing import Dict, Any
from ..git_ops.clone import get_git_status


def generate_pr_checklist(
    local_repo_path: str,
    base_branch: str = "main",
    head_branch: str = "",
    pr_title: str = "",
    pr_body: str = "",
    fork_flow: bool = True
) -> str:
    """
    Generate a step-by-step checklist for creating a pull request.
    
    Args:
        local_repo_path: Path to the local repository
        base_branch: Base branch to merge into
        head_branch: Branch containing changes
        pr_title: Proposed PR title
        pr_body: Proposed PR description
        fork_flow: Whether user is working with a fork
        
    Returns:
        Formatted checklist as a string
    """
    checklist = []
    
    # Header
    checklist.append("# Pull Request Creation Guide")
    checklist.append("")
    checklist.append(f"Repository: {local_repo_path}")
    checklist.append(f"Base branch: {base_branch}")
    checklist.append(f"Your branch: {head_branch}")
    checklist.append("")
    
    # Get git status
    git_status = get_git_status(local_repo_path)
    
    if git_status.get("error"):
        checklist.append(f"⚠️  Warning: {git_status['error']}")
        checklist.append("")
    else:
        checklist.append(f"Current branch: {git_status.get('current_branch', 'unknown')}")
        if git_status.get("has_uncommitted_changes"):
            checklist.append("⚠️  You have uncommitted changes")
        else:
            checklist.append("✓ Working tree is clean")
        checklist.append("")
    
    # Step-by-step instructions
    checklist.append("## Step-by-Step Instructions")
    checklist.append("")
    
    # Step 1: Verify branch
    checklist.append("### 1. Verify you're on the correct branch")
    checklist.append("```bash")
    checklist.append(f"cd {local_repo_path}")
    checklist.append("git branch --show-current")
    checklist.append("```")
    checklist.append(f"Expected output: `{head_branch}`")
    checklist.append("")
    
    if git_status.get("current_branch") != head_branch:
        checklist.append("⚠️  You're not on the expected branch! Switch with:")
        checklist.append("```bash")
        checklist.append(f"git checkout {head_branch}")
        checklist.append("```")
        checklist.append("")
    
    # Step 2: Ensure all changes are committed
    checklist.append("### 2. Ensure all changes are committed")
    checklist.append("```bash")
    checklist.append("git status")
    checklist.append("```")
    checklist.append("")
    if git_status.get("has_uncommitted_changes"):
        checklist.append("⚠️  You have uncommitted changes. Commit them:")
        checklist.append("```bash")
        checklist.append("git add .")
        checklist.append('git commit -m "Your commit message"')
        checklist.append("```")
        checklist.append("")
    
    # Step 3: Run tests (if applicable)
    checklist.append("### 3. Run tests (recommended)")
    checklist.append("")
    checklist.append("Before creating a PR, make sure tests pass:")
    checklist.append("```bash")
    checklist.append("# For Python projects:")
    checklist.append("pytest")
    checklist.append("")
    checklist.append("# For Node.js projects:")
    checklist.append("npm test")
    checklist.append("")
    checklist.append("# For other projects, check README or CONTRIBUTING.md")
    checklist.append("```")
    checklist.append("")
    
    # Step 4: Push your branch
    checklist.append("### 4. Push your branch to GitHub")
    checklist.append("")
    if fork_flow:
        checklist.append("Since you're working with a fork:")
        checklist.append("```bash")
        checklist.append(f"git push origin {head_branch}")
        checklist.append("```")
        checklist.append("")
        checklist.append("If this is your first push of this branch:")
        checklist.append("```bash")
        checklist.append(f"git push -u origin {head_branch}")
        checklist.append("```")
    else:
        checklist.append("```bash")
        checklist.append(f"git push origin {head_branch}")
        checklist.append("```")
    checklist.append("")
    
    # Step 5: Create the pull request
    checklist.append("### 5. Create the Pull Request")
    checklist.append("")
    checklist.append("You have two options:")
    checklist.append("")
    
    # Option A: Web interface
    checklist.append("**Option A: Via GitHub Web Interface**")
    checklist.append("")
    checklist.append("1. Go to the repository on GitHub")
    checklist.append("2. Click on 'Pull requests' tab")
    checklist.append("3. Click 'New pull request'")
    if fork_flow:
        checklist.append("4. Set base repository and branch")
        checklist.append(f"5. Set your fork and branch: {head_branch}")
    else:
        checklist.append(f"4. Select base: {base_branch}")
        checklist.append(f"5. Select compare: {head_branch}")
    checklist.append("6. Click 'Create pull request'")
    checklist.append(f"7. Title: {pr_title}")
    if pr_body:
        checklist.append(f"8. Description: {pr_body}")
    checklist.append("")
    
    # Option B: GitHub CLI
    checklist.append("**Option B: Via GitHub CLI (gh)**")
    checklist.append("")
    checklist.append("If you have GitHub CLI installed:")
    checklist.append("```bash")
    if fork_flow:
        checklist.append(f'gh pr create --base {base_branch} --head {head_branch} --title "{pr_title}" --body "{pr_body}"')
    else:
        checklist.append(f'gh pr create --base {base_branch} --title "{pr_title}" --body "{pr_body}"')
    checklist.append("```")
    checklist.append("")
    
    # Additional tips
    checklist.append("## Additional Tips")
    checklist.append("")
    checklist.append("- **Link to the issue**: Mention 'Fixes #123' or 'Closes #123' in your PR description")
    checklist.append("- **Follow contribution guidelines**: Check if the repository has a CONTRIBUTING.md file")
    checklist.append("- **Keep PRs focused**: One PR should address one issue or feature")
    checklist.append("- **Write clear commit messages**: Use present tense, be descriptive")
    checklist.append("- **Update documentation**: If you changed functionality, update relevant docs")
    checklist.append("")
    
    # Troubleshooting
    checklist.append("## Troubleshooting")
    checklist.append("")
    checklist.append("**If push is rejected:**")
    checklist.append("```bash")
    checklist.append("# Pull latest changes from upstream")
    checklist.append(f"git pull origin {base_branch}")
    checklist.append("# Resolve conflicts if any")
    checklist.append("# Push again")
    checklist.append(f"git push origin {head_branch}")
    checklist.append("```")
    checklist.append("")
    checklist.append("**If you need to update your fork:**")
    checklist.append("```bash")
    checklist.append("# Add upstream remote (if not already added)")
    checklist.append("git remote add upstream <original-repo-url>")
    checklist.append("# Fetch upstream changes")
    checklist.append("git fetch upstream")
    checklist.append("# Merge or rebase")
    checklist.append(f"git merge upstream/{base_branch}")
    checklist.append("```")
    checklist.append("")
    
    return "\n".join(checklist)


def generate_quick_pr_guide(
    base_branch: str = "main",
    head_branch: str = "",
    issue_number: int = None
) -> str:
    """
    Generate a quick reference guide for PR creation.
    
    Args:
        base_branch: Base branch to merge into
        head_branch: Branch containing changes
        issue_number: Related issue number (optional)
        
    Returns:
        Quick reference guide
    """
    guide = []
    
    guide.append("# Quick PR Creation Guide")
    guide.append("")
    guide.append("## Essential Commands")
    guide.append("")
    guide.append("```bash")
    guide.append("# 1. Ensure you're on your feature branch")
    guide.append(f"git checkout {head_branch}")
    guide.append("")
    guide.append("# 2. Commit all changes")
    guide.append("git add .")
    guide.append('git commit -m "Description of changes"')
    guide.append("")
    guide.append("# 3. Push to GitHub")
    guide.append(f"git push -u origin {head_branch}")
    guide.append("")
    guide.append("# 4. Create PR via GitHub CLI (if installed)")
    issue_ref = f' --body "Fixes #{issue_number}"' if issue_number else ""
    guide.append(f'gh pr create --base {base_branch} --title "Your PR title"{issue_ref}')
    guide.append("```")
    guide.append("")
    guide.append("Or visit GitHub to create the PR via web interface.")
    guide.append("")
    
    if issue_number:
        guide.append(f"## Link to Issue #{issue_number}")
        guide.append("")
        guide.append(f"Include this in your PR description: `Fixes #{issue_number}` or `Closes #{issue_number}`")
        guide.append("This will automatically close the issue when your PR is merged.")
        guide.append("")
    
    return "\n".join(guide)


def generate_fork_workflow_guide() -> str:
    """
    Generate a guide for the fork workflow.
    
    Returns:
        Fork workflow guide
    """
    guide = []
    
    guide.append("# Fork Workflow Guide")
    guide.append("")
    guide.append("When contributing to repositories you don't have write access to,")
    guide.append("you typically use the fork workflow:")
    guide.append("")
    guide.append("## One-Time Setup")
    guide.append("")
    guide.append("```bash")
    guide.append("# 1. Fork the repository on GitHub (use the Fork button)")
    guide.append("")
    guide.append("# 2. Clone YOUR fork")
    guide.append("git clone https://github.com/YOUR-USERNAME/REPO-NAME.git")
    guide.append("cd REPO-NAME")
    guide.append("")
    guide.append("# 3. Add the original repository as 'upstream'")
    guide.append("git remote add upstream https://github.com/ORIGINAL-OWNER/REPO-NAME.git")
    guide.append("")
    guide.append("# 4. Verify remotes")
    guide.append("git remote -v")
    guide.append("# Should show:")
    guide.append("# origin    -> your fork")
    guide.append("# upstream  -> original repo")
    guide.append("```")
    guide.append("")
    guide.append("## For Each Contribution")
    guide.append("")
    guide.append("```bash")
    guide.append("# 1. Sync with upstream")
    guide.append("git checkout main")
    guide.append("git fetch upstream")
    guide.append("git merge upstream/main")
    guide.append("")
    guide.append("# 2. Create a feature branch")
    guide.append("git checkout -b feature/my-contribution")
    guide.append("")
    guide.append("# 3. Make your changes and commit")
    guide.append("git add .")
    guide.append('git commit -m "Description"')
    guide.append("")
    guide.append("# 4. Push to YOUR fork")
    guide.append("git push -u origin feature/my-contribution")
    guide.append("")
    guide.append("# 5. Create PR on GitHub")
    guide.append("# - Base: original-repo/main")
    guide.append("# - Head: your-fork/feature/my-contribution")
    guide.append("```")
    guide.append("")
    
    return "\n".join(guide)
