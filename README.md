# GitHub Issue Shepherd - MCP Server

A Model Context Protocol (MCP) server that helps developers discover GitHub issues to work on, clone repositories, and create pull requests with guided assistance.

## Features

- 🔍 **Smart Issue Discovery**: Search for issues in specific repositories or across GitHub
- 🏷️ **Skill-Based Matching**: Find issues matching your skills and interests
- 📦 **Safe Repository Cloning**: Validate paths and clone repositories with confidence
- 📝 **PR Creation Guidance**: Step-by-step instructions for creating pull requests
- 🤖 **Optional Automation**: Automated PR creation and forking with GitHub API
- 🛡️ **Security First**: Token redaction and safe filesystem operations

## Installation

### Prerequisites

- Python 3.10 or higher
- Git installed and in PATH
- (Optional) GitHub personal access token for higher rate limits and automation

### Setup

1. **Clone or download this repository**:
```bash
git clone https://github.com/BrachaLeah1/mcp_server_github_issues.git
cd mcp_server_github_issues
```

2. **Create and Activate a virtual environment**:
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Unix/MacOS
source venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -e .
```

4. **(Optional) Set up GitHub token**:
```bash
# On Unix/MacOS
export GITHUB_TOKEN=your_github_token_here

# On Windows (Command Prompt)
set GITHUB_TOKEN=your_github_token_here

# On Windows (PowerShell)
$env:GITHUB_TOKEN="your_github_token_here"
```

To create a GitHub token:
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a descriptive name
4. Select scopes: `repo`, `workflow` (for automation features)
5. Click "Generate token" and copy it

## Testing via MCP Inspector
```bash
npx @modelcontextprotocol/inspector python src/server.py
```

## Running the Server

The server runs using stdio transport (standard input/output):

```bash
python -m src.server
```

Or directly:

```bash
python src/server.py
```

## ⚙️ MCP Client Configuration

This server is compatible with any **MCP-compatible code agent**.  
Add it to your client’s MCP configuration file and restart the client.

---

### Example: Cursor IDE

1. Press `Ctrl + Shift + P`
2. Open **Cursor Settings**
3. Navigate to **Tools & MCP**
4. Add a new MCP server with the following configuration:

```json
{
  "mcpServers": {
    "mcp_github_issues": {
      "command": "C:/absolute/path/to/mcp_server_github_issues/venv/Scripts/python.exe",
      "args": [
        "C:/absolute/path/to/mcp_server_github_issues/src/server.py"
      ],
      "cwd": "C:/absolute/path/to/mcp_server_github_issues",
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

## Available Tools

### 1. discover_repository

Discover popular, well-established GitHub repositories to contribute to. Use this when you don't have a specific repository in mind but want to find quality projects matching your interests.

**Filters repositories by**:
- **Minimum 1000 stars** (strong indicator of 100+ contributors and active maintenance)
- **Active projects only** (excludes archived/abandoned repositories)
- **Public repositories**

**Parameters**:
- `language`: Programming language filter (e.g., "python", "javascript", "rust")
- `topics`: List of project topics (e.g., ["machine-learning", "data-science"])
- `sort`: Sort order - "stars" (default), "forks", or "updated"
- `limit`: Maximum repositories to return (1-30, default: 10)

**Returns**: List of repositories with:
- Name, URL, description
- Star count and language
- Topics, last update time
- Open issues count

**Example**:
```json
{
  "language": "python",
  "topics": ["machine-learning"],
  "sort": "stars",
  "limit": 5
}
```

**Use Cases**:
- "I want to contribute to a Python project but don't know which one"
- "Show me popular JavaScript web frameworks to learn from"
- "Find active data science projects to contribute to"

---

### 2. search_issues

Search for GitHub issues in a specific repository. Use after discovering a repository with `discover_repository`.

**Parameters**:
- `repo`: Repository name in "owner/repo" format (required)
- `skills`: List of skills/keywords (e.g., ["python", "testing", "documentation"])
- `topics`: List of topics (e.g., ["machine-learning", "web-development"])
- `language`: Programming language filter
- `difficulty`: Issue difficulty ("good-first-issue", "easy", "medium", "hard")
- `labels`: Additional labels to filter by
- `state`: "open", "closed", or "all"
- `sort`: "relevance", "created", "updated", or "comments"
- `limit`: Maximum results (1-30, default: 10)

**Example**:
```json
{
  "repo": "openvinotoolkit/openvino",
  "difficulty": "good-first-issue",
  "limit": 10
}
```

### 3. get_issue_details

Get detailed information about a specific issue.

**Parameters**:
- `repo`: Repository in "owner/repo" format
- `number`: Issue number
- `include_comments`: Whether to include comments (default: false)
- `max_comments`: Maximum comments to include (default: 10)

**Example**:
```json
{
  "repo": "facebook/react",
  "number": 12345,
  "include_comments": true,
  "max_comments": 5
}
```

### 4. list_repo_metadata

Get comprehensive repository metadata and contribution guide pointers.

This tool provides helpful context **before working with a repository**, including:
- Repository statistics (stars, forks, watchers)
- Default branch and primary language
- License information
- Clone URLs for HTTPS and SSH
- **Pointers to contribution guidelines** (CONTRIBUTING.md, CODE_OF_CONDUCT.md, DEVELOPMENT.md, etc.)

**Key Feature: Contribution Guidance Pointers**:
The response includes a `contribution_guides` section that lists common documentation files to review:
- **CONTRIBUTING.md** - How to contribute and PR process
- **CODE_OF_CONDUCT.md** - Community standards and expectations
- **DEVELOPMENT.md** - Setup and development information
- **DEVELOPERS.md** - Alternative development guide
- **.github/CONTRIBUTING.md** - GitHub-specific guide

This helps developers understand the project's standards **before making changes**.

**Parameters**:
- `repo`: Repository in "owner/repo" format

**Example**:
```json
{
  "repo": "microsoft/vscode"
}
```

**Response Includes**:
```json
{
  "success": true,
  "repo_name": "vscode",
  "owner": "microsoft",
  "stars": 156000,
  "language": "TypeScript",
  "contribution_guides": {
    "message": "Review these files to understand how to contribute to this project",
    "common_files": {
      "CONTRIBUTING.md": "https://github.com/microsoft/vscode/blob/main/CONTRIBUTING.md",
      "CODE_OF_CONDUCT.md": "https://github.com/microsoft/vscode/blob/main/CODE_OF_CONDUCT.md",
      "DEVELOPMENT.md": "https://github.com/microsoft/vscode/blob/main/DEVELOPMENT.md"
    }
  }
}
```

### 5. prepare_clone

Validate a folder path before cloning.

**Parameters**:
- `target_path`: Path to validate (absolute or relative)
- `must_be_empty`: Whether folder must be empty (default: true)

**Example**:
```json
{
  "target_path": "/home/user/projects/new-repo",
  "must_be_empty": true
}
```

### 6. clone_repo

Clone a repository to a local directory - **USER CONFIRMATION REQUIRED**.

⚠️ **CRITICAL**: User must explicitly confirm before cloning. Do NOT assume a path.

**Parameters**:
- `repo`: Repository in "owner/repo" format
- `target_path`: Local path to clone into (user must specify this)
- `confirmed`: Must be `true` to proceed (default: `false`) - **REQUIRED SECURITY CHECKPOINT**
- `clone_method`: "https" or "ssh" (default: "https")
- `shallow`: Whether to do shallow clone (default: false)
- `branch`: Specific branch to checkout (optional)

**Required Workflow**:
1. Present user with two options:
   - **Option A**: Clone to a specific path they provide
   - **Option B**: Clone to current workspace
2. Get explicit user confirmation: "Do you want to proceed? (yes/no)"
3. Only if user confirms, call `clone_repo` with `confirmed=true`

**Example - After User Confirms**:
```json
{
  "repo": "torvalds/linux",
  "target_path": "/home/user/projects/linux",
  "confirmed": true,
  "clone_method": "https",
  "shallow": true
}
```

**Without Confirmation (will return error)**:
```json
{
  "repo": "torvalds/linux",
  "target_path": "/home/user/projects/linux",
  "confirmed": false
}
```
Returns error: `CONFIRMATION_REQUIRED`

### 7. pr_assistant

Get step-by-step guidance for creating a pull request, with emphasis on reviewing the repository's **contribution guidelines**.

**Key Features**:
- Step-by-step instructions for creating a PR
- Git commands for testing, committing, and pushing changes
- Guidance on using GitHub web interface or CLI
- **IMPORTANT**: Directs you to review CONTRIBUTING.md, CODE_OF_CONDUCT.md, and other contribution guidelines
- Troubleshooting tips for common issues

**Why Contribution Guidelines Matter**:
The guidance **emphasizes checking the repository's contribution guidelines** (CONTRIBUTING.md, CODE_OF_CONDUCT.md, DEVELOPMENT.md) because:
- Different projects have different requirements for code format, testing, and documentation
- Following guidelines ensures your PR will be accepted on the first review
- Some projects require specific commit message formats or branch naming conventions
- Code of conduct compliance is essential for maintainers

**Parameters**:
- `local_repo_path`: Path to local repository
- `base_branch`: Base branch to merge into (default: "main")
- `head_branch`: Your branch with changes
- `pr_title`: Proposed PR title
- `pr_body`: Proposed PR description
- `fork_flow`: Whether using fork workflow (default: true)

**Example**:
```json
{
  "local_repo_path": "/home/user/projects/my-repo",
  "base_branch": "main",
  "head_branch": "feature/my-improvement",
  "pr_title": "Add new feature X",
  "pr_body": "This PR adds feature X which solves issue #123",
  "fork_flow": true
}
```

**Sample Output Includes**:
```
## ⚠️ IMPORTANT: Review Contribution Guidelines

Before creating your PR, check the repository's contribution guidelines:

1. Look for these files in the repository:
   - **CONTRIBUTING.md** - Contribution process and standards
   - **CODE_OF_CONDUCT.md** - Community standards and behavior
   - **DEVELOPMENT.md** - Setup and development instructions
   
2. These files explain:
   - How to format code and commit messages
   - Testing requirements
   - Documentation standards
   - PR review process
```

### 8. create_pull_request (Optional - Requires Token)

Automatically create a pull request via GitHub API.

**Parameters**:
- `repo`: Repository in "owner/repo" format
- `head`: Branch name or "username:branch" for forks
- `base`: Base branch to merge into
- `title`: PR title
- `body`: PR description (optional)
- `draft`: Create as draft (default: false)
- `token`: GitHub PAT (optional, uses GITHUB_TOKEN env if not provided)

**Example**:
```json
{
  "repo": "facebook/react",
  "head": "myusername:fix-bug",
  "base": "main",
  "title": "Fix rendering bug in component",
  "body": "Fixes #12345",
  "draft": false
}
```

### 9. fork_repo (Optional - Requires Token)

Fork a repository to your account.

**Parameters**:
- `repo`: Repository in "owner/repo" format
- `token`: GitHub PAT (optional, uses GITHUB_TOKEN env if not provided)

**Example**:
```json
{
  "repo": "microsoft/vscode"
}
```

## Environment Variables

- `GITHUB_TOKEN`: GitHub personal access token (optional but recommended)
  - Increases rate limits from 60 to 5000 requests/hour
  - Required for `create_pull_request` and `fork_repo` tools
  - Get one at: https://github.com/settings/tokens

## Logging

The server includes structured logging to help with debugging and monitoring.

### Default Behavior

By default, the server logs at `INFO` level to stdout:

```
2025-01-09 14:23:45,123 - src.server - INFO - GitHub Issue Shepherd MCP Server initialized
2025-01-09 14:23:45,124 - src.server - INFO - GitHub token configured
2025-01-09 14:23:46,234 - src.github.client - INFO - Searching GitHub issues: python good-first-issue...
```

### Enable Debug Logging

To see detailed debug information (including HTTP requests and parameter details):

```bash
# Set environment variable
export PYTHONUNBUFFERED=1
export DEBUG=1

# Run server with debug logging
python src/server.py
```

Or modify the server initialization in `src/server.py`:

```python
from src.utils.logging_config import setup_logging
import logging

setup_logging(log_level=logging.DEBUG)
```

### Log to File (Optional)

To save logs to a file in addition to stdout:

```python
from src.utils.logging_config import setup_logging
import logging

setup_logging(
    log_level=logging.INFO,
    log_file="github_shepherd.log"
)
```

**What gets logged**:
- Server startup and configuration
- Search queries and result counts
- API requests and responses
- Rate limit status and warnings
- All errors with full context
- Git operation execution and results

## Rate Limits

GitHub API has rate limits to prevent abuse:

### Limits

| Scenario | Limit |
|----------|-------|
| **Without token** | 60 requests/hour |
| **With token** | 5,000 requests/hour |
| **Authenticated search** | 30 requests/minute |

### What Happens When Limit is Exceeded

1. **Tools return standardized error response**:
   ```json
   {
     "ok": false,
     "error": {
       "code": "GITHUB_RATE_LIMIT",
       "message": "GitHub API rate limit exceeded",
       "hint": "Set GITHUB_TOKEN environment variable for higher rate limits (5000/hr vs 60/hr)",
       "details": {
         "limit_remaining": 0,
         "resets_at": 1673280000
       }
     }
   }
   ```

2. **Server logs a warning**:
   ```
   WARNING - Approaching GitHub API rate limit: 6/5000 remaining
   ERROR - Rate limit exceeded. Reset at: 1673280000
   ```

3. **Operations are paused** - retry after reset time

### How to Resolve

**Immediate**: Wait for the rate limit to reset (hourly for unauthenticated, 1 minute for search)

**Permanent**: Set up a GitHub token
1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. Select scopes: `repo`, `workflow` (if using automation)
4. Copy and set as environment variable:
   ```bash
   export GITHUB_TOKEN=ghp_your_token_here
   ```
5. Restart the server

**Monitor**: Check server logs for rate limit warnings and adjust search patterns if needed

## Typical Workflow

### Option 1: You Don't Have a Repository in Mind Yet

1. **Discover popular repositories** matching your interests:
```json
{
  "language": "python",
  "topics": ["machine-learning"],
  "sort": "stars",
  "limit": 10
}
```
This shows you well-maintained projects (1000+ stars, 100+ contributors, active).

2. **Choose a repository** from the results and proceed to step 3 in Option 2

### Option 2: You Already Know Which Repository to Work On

1. **Find an issue to work on** in that repository:
```json
{
  "repo": "owner/repo",
  "skills": ["python", "testing"],
  "difficulty": "good-first-issue",
  "limit": 10
}
```

2. **Get issue details**:
```json
{
  "repo": "owner/repo",
  "number": 123,
  "include_comments": true
}
```

3. **Check repository metadata**:
```json
{
  "repo": "owner/repo"
}
```

4. **Prepare a folder**:
```json
{
  "target_path": "/home/user/dev/new-project",
  "must_be_empty": true
}
```

5. **Clone the repository**:
```json
{
  "repo": "owner/repo",
  "target_path": "/home/user/dev/new-project",
  "clone_method": "https"
}
```

6. **Make your changes** (outside MCP - use your IDE/editor)

7. **Get PR creation guidance**:
```json
{
  "local_repo_path": "/home/user/dev/new-project",
  "base_branch": "main",
  "head_branch": "fix/issue-123",
  "pr_title": "Fix issue #123",
  "pr_body": "This fixes the bug described in #123"
}
```

8. **Optionally create PR automatically** (if you have a token):
```json
{
  "repo": "owner/repo",
  "head": "yourname:fix/issue-123",
  "base": "main",
  "title": "Fix issue #123",
  "body": "Fixes #123"
}
```

## Contributing to Open Source: Understanding Repository Guidelines

### Why Repository Guidelines Matter

Before making changes to any repository, it's **critical** to understand that project's specific contribution requirements. Different projects have different standards for:

- **Code Style & Format**: Python vs JavaScript vs Go have different conventions
- **Testing Requirements**: Some require 100% coverage, others don't have tests yet
- **Commit Message Format**: Some enforce specific prefixes like `fix:` or `feat:`
- **PR Review Process**: Some have multiple reviewers, others are more lenient
- **Documentation Standards**: Some require docs for every change, others don't
- **Community Standards**: Code of Conduct expectations vary widely

### How This Server Helps

This MCP server includes **built-in guidance for finding and reviewing contribution guidelines**:

1. **`list_repo_metadata`** provides direct links to:
   - CONTRIBUTING.md - Contribution process
   - CODE_OF_CONDUCT.md - Community standards
   - DEVELOPMENT.md - Development setup
   - Other contributor resources

2. **`pr_assistant`** emphasizes checking guidelines **before** creating a PR, with a dedicated section:
   ```
   ## ⚠️ IMPORTANT: Review Contribution Guidelines
   
   Before creating your PR, check the repository's contribution guidelines:
   
   1. Look for these files in the repository:
      - CONTRIBUTING.md
      - CODE_OF_CONDUCT.md
      - DEVELOPMENT.md
   
   2. These files explain:
      - How to format code and commit messages
      - Testing requirements
      - Documentation standards
      - PR review process
   ```

### Best Practice Workflow

```
1. discover_repository() or identify repo you want to work on
2. list_repo_metadata()  ← Review contribution guides here
3. search_issues()       ← Find an issue to work on
4. get_issue_details()   ← Understand the problem
5. clone_repo()          ← Only after understanding requirements
6. [Make your changes locally in your editor]
7. pr_assistant()        ← Reviews guidelines again before PR
8. create_pull_request() ← Create PR
```

**Key Principle**: Always read the contribution guidelines before modifying code. This prevents wasted time on PRs that won't be accepted due to format or style issues.

## Troubleshooting

### Git not found

**Error**: `Git is not installed or not found in PATH`

**Solution**: 
1. Install Git from https://git-scm.com/downloads
2. Ensure Git is in your system PATH
3. Restart your terminal/shell
4. Verify with: `git --version`

### Rate limit exceeded

**Error**: `GitHub API rate limit exceeded`

**Solution**:
1. Set up a GitHub personal access token
2. Export it as `GITHUB_TOKEN` environment variable
3. Restart the MCP server
4. Unauthenticated: 60 requests/hour
5. Authenticated: 5000 requests/hour

### Directory not empty

**Error**: `Directory is not empty`

**Solution**:
1. Choose a different, empty directory
2. Or manually clear the directory
3. Or use `must_be_empty: false` (use with caution)

### Permission denied

**Error**: `Permission denied: Cannot write to directory`

**Solution**:
1. Check directory permissions
2. Choose a directory where you have write access
3. On Unix/Mac, use: `chmod +w /path/to/directory`

### Clone failed - Repository not found

**Error**: `Repository not found or inaccessible`

**Solution**:
1. Verify the repository name is correct (owner/repo format)
2. Check if the repository is private and you have access
3. If using SSH, ensure your SSH keys are set up correctly
4. For private repos, use HTTPS with token or set up SSH keys

## Testing

Run the test suite:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/
```

## Project Structure

```
mcp_github_issue_shepherd/
├── pyproject.toml          # Project configuration
├── README.md               # This file
├── src/
│   ├── server.py           # Main MCP server
│   ├── config.py           # Configuration and constants
│   ├── github/
│   │   ├── client.py       # GitHub API client
│   │   ├── query_builder.py  # Search query builder
│   │   └── models.py       # Data models
│   ├── git_ops/
│   │   ├── clone.py        # Git clone operations
│   │   └── fs_validate.py  # Filesystem validation
│   ├── pr/
│   │   ├── guidance.py     # PR creation guidance
│   │   └── api.py          # Automated PR/fork operations
│   └── utils/
│       ├── errors.py       # Error handling
│       ├── logging_config.py  # Logging configuration for the MCP server
│       ├── redact.py       # Token redaction
│       └── detect_project.py  # Project type detection
└── tests/
    ├── test_query_builder.py
    ├── test_mcp_tools.py
    ├── test_fs_validate.py
    ├── test_rate_limiting.py
    └── test_redact.py
```

## Security & Safety

- ✅ Tokens are never logged or exposed in error messages
- ✅ Filesystem operations validate paths and permissions
- ✅ Cloning defaults to empty directories only
- ✅ No automatic code execution or file modification
- ✅ All destructive operations require explicit confirmation

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Search existing GitHub issues
3. Create a new issue with details about your problem

## Acknowledgments

- Uses [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) for testing.
- Uses [GitHub REST API](https://docs.github.com/en/rest)
- Inspired by the need to make open source contribution easier
