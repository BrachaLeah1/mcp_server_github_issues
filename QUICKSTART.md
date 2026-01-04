# Quick Start Guide

Get started with GitHub Issue Shepherd in 5 minutes!

## Installation

```bash
# 1. Navigate to the project directory
cd mcp_github_issue_shepherd

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install
pip install -e .
```

## Basic Usage

### Example 1: Find Good First Issues in a Specific Repo

```json
{
  "mode": "repo",
  "repo": "facebook/react",
  "difficulty": "good-first-issue",
  "limit": 5
}
```

### Example 2: Search for Python Issues Globally

```json
{
  "mode": "global",
  "skills": ["python", "testing"],
  "difficulty": "easy",
  "limit": 10
}
```

### Example 3: Clone a Repository

First, prepare the folder:
```json
{
  "target_path": "/home/user/projects/my-new-project",
  "must_be_empty": true
}
```

Then clone:
```json
{
  "repo": "facebook/react",
  "target_path": "/home/user/projects/my-new-project",
  "clone_method": "https"
}
```

### Example 4: Get PR Creation Help

```json
{
  "local_repo_path": "/home/user/projects/my-new-project",
  "base_branch": "main",
  "head_branch": "fix/issue-123",
  "pr_title": "Fix bug in component rendering",
  "pr_body": "Fixes #123"
}
```

## Setting Up GitHub Token (Optional but Recommended)

```bash
# Get a token from: https://github.com/settings/tokens
export GITHUB_TOKEN=your_token_here
```

Benefits:
- Rate limit increases from 60/hour to 5000/hour
- Can use automated PR creation
- Can fork repositories automatically

## Common Workflows

### Workflow 1: Find and Start Working on an Issue

1. Search for issues matching your skills
2. Get details of interesting issues
3. Check repository metadata
4. Prepare and clone the repository
5. Make your changes
6. Get PR creation guidance

### Workflow 2: Contributing to a New Project

1. Find the repository
2. List repository metadata (check language, license, etc.)
3. Search for good first issues in that repo
4. Clone and start contributing!

## Tips

- Start with `difficulty: "good-first-issue"` if you're new to a project
- Use `shallow: true` for faster cloning of large repositories
- Always check `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` in the repository
- Link your PR to the issue using "Fixes #123" in the PR description

## Troubleshooting

**Git not found?**
```bash
# Install git
# Then verify:
git --version
```

**Rate limited?**
```bash
# Set up a GitHub token
export GITHUB_TOKEN=your_token
```

**Directory not empty?**
- Choose a different directory
- Or manually clear it
- Or use `must_be_empty: false` (use carefully!)

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check out the [examples](examples/) directory for more use cases
- Run tests: `pytest tests/`

Happy contributing! 🎉
