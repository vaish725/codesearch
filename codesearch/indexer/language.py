"""
Language detection utilities.
"""

from pathlib import Path
from typing import Optional


class LanguageDetector:
    """
    Detects programming language from file extension.
    """

    def __init__(self, language_map: dict):
        """
        Initialize the language detector.

        Args:
            language_map: Mapping from file extensions to language names
        """
        self.language_map = language_map

    def detect(self, file_path: Path) -> Optional[str]:
        """
        Detect the language of a file.

        Args:
            file_path: Path to the file

        Returns:
            Language name or None if unknown
        """
        suffix = file_path.suffix.lower()
        return self.language_map.get(suffix)

    def is_supported(self, file_path: Path) -> bool:
        """
        Check if a file's language is supported.

        Args:
            file_path: Path to the file

        Returns:
            True if language is supported
        """
        return self.detect(file_path) is not None
