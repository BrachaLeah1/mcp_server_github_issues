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

## Available Tools

### 1. search_issues

Search for GitHub issues to work on.

**Parameters**:
- `mode`: "repo" (search in specific repository) or "global" (search across GitHub)
- `repo`: Repository name in "owner/repo" format (required if mode="repo")
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
  "mode": "repo",
  "repo": "openvinotoolkit/openvino",
  "difficulty": "good-first-issue",
  "limit": 10
}
```

### 2. get_issue_details

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

### 3. list_repo_metadata

Get repository metadata and information.

**Parameters**:
- `repo`: Repository in "owner/repo" format

**Example**:
```json
{
  "repo": "microsoft/vscode"
}
```

### 4. prepare_clone

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

### 5. clone_repo

Clone a repository to a local directory.

**Parameters**:
- `repo`: Repository in "owner/repo" format
- `target_path`: Local path to clone into
- `clone_method`: "https" or "ssh" (default: "https")
- `shallow`: Whether to do shallow clone (default: false)
- `branch`: Specific branch to checkout (optional)

**Example**:
```json
{
  "repo": "torvalds/linux",
  "target_path": "/home/user/projects/linux",
  "clone_method": "https",
  "shallow": true
}
```

### 6. pr_assistant

Get step-by-step guidance for creating a pull request.

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

### 7. create_pull_request (Optional - Requires Token)

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

### 8. fork_repo (Optional - Requires Token)

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

## Typical Workflow

1. **Find an issue to work on**:
```json
{
  "mode": "global",
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
│       ├── redact.py       # Token redaction
│       └── detect_project.py  # Project type detection
└── tests/
    ├── test_query_builder.py
    ├── test_fs_validate.py
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

- Built with [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Uses [GitHub REST API](https://docs.github.com/en/rest)
- Inspired by the need to make open source contribution easier
