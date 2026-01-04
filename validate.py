#!/usr/bin/env python3
"""Validation script to check if all imports work correctly."""

import sys

def validate_imports():
    """Test that all modules can be imported."""
    print("Validating imports...")
    
    errors = []
    
    # Test main server
    try:
        from src import server
        print("✓ Main server module")
    except Exception as e:
        errors.append(f"✗ Main server: {e}")
    
    # Test config
    try:
        from src import config
        print("✓ Config module")
    except Exception as e:
        errors.append(f"✗ Config: {e}")
    
    # Test GitHub modules
    try:
        from src.github import client, models, query_builder
        print("✓ GitHub modules")
    except Exception as e:
        errors.append(f"✗ GitHub modules: {e}")
    
    # Test git operations
    try:
        from src.git_ops import clone, fs_validate
        print("✓ Git operations modules")
    except Exception as e:
        errors.append(f"✗ Git operations: {e}")
    
    # Test PR modules
    try:
        from src.pr import api, guidance
        print("✓ PR modules")
    except Exception as e:
        errors.append(f"✗ PR modules: {e}")
    
    # Test utilities
    try:
        from src.utils import errors, redact, detect_project
        print("✓ Utility modules")
    except Exception as e:
        errors.append(f"✗ Utilities: {e}")
    
    # Test Pydantic models
    try:
        from src.server import (
            SearchIssuesInput,
            GetIssueDetailsInput,
            CloneRepoInput
        )
        print("✓ Pydantic models")
    except Exception as e:
        errors.append(f"✗ Pydantic models: {e}")
    
    # Test MCP server
    try:
        from src.server import mcp
        print("✓ MCP server instance")
    except Exception as e:
        errors.append(f"✗ MCP server: {e}")
    
    if errors:
        print("\n❌ Validation failed with errors:")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print("\n✅ All validations passed!")
        return True


def check_dependencies():
    """Check if required dependencies are installed."""
    print("\nChecking dependencies...")
    
    required = [
        "mcp",
        "httpx",
        "pydantic"
    ]
    
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            missing.append(package)
            print(f"✗ {package} - NOT INSTALLED")
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("Install with: pip install -e .")
        return False
    else:
        print("\n✅ All dependencies installed!")
        return True


def main():
    """Run all validations."""
    print("=" * 60)
    print("GitHub Issue Shepherd - Validation Script")
    print("=" * 60)
    
    deps_ok = check_dependencies()
    print()
    
    if deps_ok:
        imports_ok = validate_imports()
        
        if imports_ok:
            print("\n" + "=" * 60)
            print("🎉 Ready to use!")
            print("=" * 60)
            print("\nNext steps:")
            print("  1. Set GITHUB_TOKEN environment variable (optional)")
            print("  2. Run: python -m src.server")
            print("  3. Check README.md for usage examples")
            return 0
        else:
            return 1
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
