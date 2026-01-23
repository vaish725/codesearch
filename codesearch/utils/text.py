"""
Text processing utilities.
"""

import re
from typing import List, Tuple


def read_file_safe(file_path: str) -> str:
    """
    Safely read a text file with error handling.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File content as string, or empty string on error
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def truncate_text(text: str, max_length: int = 200) -> str:
    """
    Truncate text to maximum length with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def highlight_match(text: str, match_term: str, start_marker: str = "**", end_marker: str = "**") -> str:
    """
    Highlight matching terms in text.
    
    Args:
        text: Text to highlight
        match_term: Term to highlight
        start_marker: Start marker for highlight
        end_marker: End marker for highlight
        
    Returns:
        Text with highlighted matches
    """
    # Simple case-insensitive highlighting
    pattern = re.compile(re.escape(match_term), re.IGNORECASE)
    return pattern.sub(lambda m: f"{start_marker}{m.group()}{end_marker}", text)


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    return " ".join(text.split())
