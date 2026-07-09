"""
File content hashing utilities.
"""

import hashlib
from pathlib import Path


def hash_file_content(file_path: Path) -> str:
    """
    Compute SHA-256 hash of file content.

    Args:
        file_path: Path to the file

    Returns:
        Hex-encoded hash string
    """
    hasher = hashlib.sha256()

    try:
        with open(file_path, "rb") as f:
            # Read in chunks for memory efficiency
            while chunk := f.read(65536):  # 64KB chunks
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        # Return empty hash on error
        return ""


def hash_string(content: str) -> str:
    """
    Compute SHA-256 hash of a string.

    Args:
        content: String content to hash

    Returns:
        Hex-encoded hash string
    """
    hasher = hashlib.sha256()
    hasher.update(content.encode("utf-8"))
    return hasher.hexdigest()
