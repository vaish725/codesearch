"""
Code snippet extraction and formatting.
"""

from typing import Optional, Tuple


def extract_snippet(content: str, line_number: int, context_lines: int = 2) -> Tuple[str, int, int]:
    """
    Extract a code snippet around a specific line.

    Args:
        content: Full file content
        line_number: Target line number (1-indexed)
        context_lines: Number of lines before/after to include

    Returns:
        Tuple of (snippet, start_line, end_line)
    """
    lines = content.splitlines()

    # Calculate range
    start_line = max(1, line_number - context_lines)
    end_line = min(len(lines), line_number + context_lines)

    # Extract lines (convert to 0-indexed for list access)
    snippet_lines = lines[start_line - 1 : end_line]
    snippet = "\n".join(snippet_lines)

    return snippet, start_line, end_line


def format_snippet(snippet: str, start_line: int, highlight_line: Optional[int] = None) -> str:
    """
    Format a snippet with line numbers.

    Args:
        snippet: Code snippet
        start_line: Starting line number
        highlight_line: Line to highlight (optional)

    Returns:
        Formatted snippet with line numbers
    """
    lines = snippet.splitlines()
    formatted_lines = []

    for i, line in enumerate(lines):
        line_num = start_line + i
        prefix = ">" if line_num == highlight_line else " "
        formatted_lines.append(f"{prefix} {line_num:4d} | {line}")

    return "\n".join(formatted_lines)


def get_line_from_content(content: str, line_number: int) -> str:
    """
    Get a specific line from content.

    Args:
        content: Full file content
        line_number: Line number (1-indexed)

    Returns:
        The line content, or empty string if out of range
    """
    lines = content.splitlines()

    if 1 <= line_number <= len(lines):
        return lines[line_number - 1]

    return ""
