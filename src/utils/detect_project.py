"""Utilities for detecting project type and providing setup hints."""

from pathlib import Path
from typing import List, Dict, Any


def detect_project_type(repo_path: Path) -> Dict[str, Any]:
    """
    Detect project type based on files in the repository.
    
    Args:
        repo_path: Path to the cloned repository
        
    Returns:
        Dictionary with project_type and setup hints
    """
    hints = []
    project_types = []
    
    # Python project detection
    if (repo_path / "pyproject.toml").exists():
        project_types.append("Python (pyproject.toml)")
        hints.append("Install dependencies: pip install -e .")
    elif (repo_path / "requirements.txt").exists():
        project_types.append("Python (requirements.txt)")
        hints.append("Install dependencies: pip install -r requirements.txt")
    elif (repo_path / "setup.py").exists():
        project_types.append("Python (setup.py)")
        hints.append("Install dependencies: pip install -e .")
    elif (repo_path / "Pipfile").exists():
        project_types.append("Python (Pipenv)")
        hints.append("Install dependencies: pipenv install")
    elif (repo_path / "poetry.lock").exists():
        project_types.append("Python (Poetry)")
        hints.append("Install dependencies: poetry install")
    
    # Node.js project detection
    if (repo_path / "package.json").exists():
        project_types.append("Node.js")
        if (repo_path / "package-lock.json").exists():
            hints.append("Install dependencies: npm install")
        elif (repo_path / "yarn.lock").exists():
            hints.append("Install dependencies: yarn install")
        elif (repo_path / "pnpm-lock.yaml").exists():
            hints.append("Install dependencies: pnpm install")
        else:
            hints.append("Install dependencies: npm install")
    
    # C/C++ project detection
    if (repo_path / "CMakeLists.txt").exists():
        project_types.append("C/C++ (CMake)")
        hints.append("Build: mkdir build && cd build && cmake .. && make")
    elif (repo_path / "Makefile").exists():
        project_types.append("C/C++ (Makefile)")
        hints.append("Build: make")
    
    # Rust project detection
    if (repo_path / "Cargo.toml").exists():
        project_types.append("Rust")
        hints.append("Build: cargo build")
        hints.append("Run tests: cargo test")
    
    # Go project detection
    if (repo_path / "go.mod").exists():
        project_types.append("Go")
        hints.append("Install dependencies: go mod download")
        hints.append("Build: go build")
    
    # Java/Maven project detection
    if (repo_path / "pom.xml").exists():
        project_types.append("Java (Maven)")
        hints.append("Build: mvn clean install")
    elif (repo_path / "build.gradle").exists() or (repo_path / "build.gradle.kts").exists():
        project_types.append("Java (Gradle)")
        hints.append("Build: ./gradlew build")
    
    # Ruby project detection
    if (repo_path / "Gemfile").exists():
        project_types.append("Ruby")
        hints.append("Install dependencies: bundle install")
    
    # Docker detection
    if (repo_path / "Dockerfile").exists():
        hints.append("Docker support detected. Build: docker build -t <image-name> .")
    if (repo_path / "docker-compose.yml").exists() or (repo_path / "docker-compose.yaml").exists():
        hints.append("Docker Compose support detected. Run: docker-compose up")
    
    # General hints
    if (repo_path / "README.md").exists() or (repo_path / "README").exists():
        hints.insert(0, "Read README for setup instructions")
    
    if (repo_path / "CONTRIBUTING.md").exists():
        hints.append("Read CONTRIBUTING.md for contribution guidelines")
    
    # Test detection
    test_dirs = ["test", "tests", "__tests__", "spec"]
    for test_dir in test_dirs:
        if (repo_path / test_dir).exists():
            hints.append(f"Run tests (check README for test commands)")
            break
    
    return {
        "project_types": project_types if project_types else ["Unknown"],
        "setup_hints": hints if hints else ["Check README for setup instructions"]
    }


def format_next_steps(repo_path: Path, repo_name: str, current_branch: str) -> str:
    """
    Format next steps after cloning a repository.
    
    Args:
        repo_path: Path to the cloned repository
        repo_name: Name of the repository (owner/repo)
        current_branch: The current branch checked out
        
    Returns:
        Formatted string with next steps
    """
    detection = detect_project_type(repo_path)
    
    output = f"Repository cloned successfully!\n\n"
    output += f"Repository: {repo_name}\n"
    output += f"Local path: {repo_path}\n"
    output += f"Current branch: {current_branch}\n\n"
    
    if detection["project_types"]:
        output += "Project type(s): " + ", ".join(detection["project_types"]) + "\n\n"
    
    if detection["setup_hints"]:
        output += "Next steps:\n"
        for i, hint in enumerate(detection["setup_hints"], 1):
            output += f"{i}. {hint}\n"
    
    return output
