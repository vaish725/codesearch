"""
Configuration settings for codesearch.
"""

from pathlib import Path
from typing import List


# Default directories to exclude from indexing
DEFAULT_EXCLUDE_DIRS = [
    ".git",
    "node_modules",
    "dist",
    "build",
    "venv",
    "__pycache__",
    ".venv",
    "env",
    ".pytest_cache",
    ".mypy_cache",
    "target",  # Rust
    "bin",
    "obj",  # C#
]

# Default file patterns to exclude
DEFAULT_EXCLUDE_PATTERNS = [
    "*.pyc",
    "*.pyo",
    "*.so",
    "*.dylib",
    "*.dll",
    "*.exe",
    "*.bin",
    "*.lock",
]

# Maximum file size to index (in bytes)
# Default: 2MB
MAX_FILE_SIZE = 2 * 1024 * 1024

# Language mappings by file extension
LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".rs": "rust",
    ".go": "go",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "csharp",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".html": "html",
    ".css": "css",
    ".sql": "sql",
}

# Database location
def get_db_path() -> Path:
    """Get the path to the SQLite database."""
    # Store in user's home directory
    db_dir = Path.home() / ".codesearch"
    db_dir.mkdir(exist_ok=True)
    return db_dir / "index.db"

# Batch size for database commits
DB_BATCH_SIZE = 200

# FTS chunk size (lines per chunk)
FTS_CHUNK_SIZE = 300
