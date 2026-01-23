"""
File scanner for traversing repositories.
"""

from pathlib import Path
from typing import List, Set, Iterator
import os


def load_ignore_file(ignore_file: Path) -> Set[str]:
    """
    Load patterns from a .codesearchignore file.
    
    Args:
        ignore_file: Path to ignore file
        
    Returns:
        Set of patterns to ignore
    """
    patterns = set()
    
    if ignore_file.exists():
        try:
            with open(ignore_file, "r") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith("#"):
                        patterns.add(line)
        except Exception:
            pass
    
    return patterns


class FileScanner:
    """
    Scans a repository and yields files to index.
    """
    
    def __init__(
        self,
        root_path: Path,
        exclude_dirs: List[str],
        exclude_patterns: List[str],
        max_file_size: int
    ):
        """
        Initialize the file scanner.
        
        Args:
            root_path: Root directory to scan
            exclude_dirs: Directory names to exclude
            exclude_patterns: File patterns to exclude
            max_file_size: Maximum file size in bytes
        """
        self.root_path = Path(root_path).resolve()
        self.exclude_dirs = set(exclude_dirs)
        self.exclude_patterns = exclude_patterns
        self.max_file_size = max_file_size
        
        # Load .codesearchignore if it exists
        ignore_file = self.root_path / ".codesearchignore"
        if ignore_file.exists():
            custom_patterns = load_ignore_file(ignore_file)
            self.exclude_dirs.update(custom_patterns)
    
    def should_exclude_dir(self, dir_name: str) -> bool:
        """Check if a directory should be excluded."""
        return dir_name in self.exclude_dirs
    
    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if a file should be excluded."""
        # Check against exclude patterns
        filename = file_path.name
        
        for pattern in self.exclude_patterns:
            # Simple glob-style matching
            if pattern.startswith("*."):
                # Extension match
                if filename.endswith(pattern[1:]):
                    return True
            elif pattern in filename:
                # Substring match
                return True
        
        return False
    
    def is_binary_file(self, file_path: Path) -> bool:
        """
        Detect if a file is binary.
        
        Simple heuristic: check for null bytes in first 8KB.
        """
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(8192)
                return b"\x00" in chunk
        except Exception:
            return True
    
    def scan(self) -> Iterator[Path]:
        """
        Scan the repository and yield file paths to index.
        
        Yields:
            Path objects for files to index
        """
        for root, dirs, files in os.walk(self.root_path):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if not self.should_exclude_dir(d)]
            
            for filename in files:
                file_path = Path(root) / filename
                
                # Check if file should be excluded
                if self.should_exclude_file(file_path):
                    continue
                
                # Check file size
                try:
                    if file_path.stat().st_size > self.max_file_size:
                        continue
                except Exception:
                    continue
                
                # Check if binary
                if self.is_binary_file(file_path):
                    continue
                
                yield file_path
