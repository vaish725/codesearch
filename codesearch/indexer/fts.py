"""
Full-text search indexing utilities.
"""

from typing import List, Tuple


class FTSChunker:
    """
    Chunks file content for FTS indexing.
    """
    
    def __init__(self, chunk_size: int = 300):
        """
        Initialize the chunker.
        
        Args:
            chunk_size: Number of lines per chunk
        """
        self.chunk_size = chunk_size
    
    def chunk_content(self, content: str) -> List[Tuple[str, int, int]]:
        """
        Split content into chunks.
        
        Args:
            content: File content as string
            
        Returns:
            List of tuples (chunk_content, start_line, end_line)
        """
        lines = content.splitlines(keepends=True)
        chunks = []
        
        for i in range(0, len(lines), self.chunk_size):
            chunk_lines = lines[i : i + self.chunk_size]
            chunk_content = "".join(chunk_lines)
            start_line = i + 1  # 1-indexed
            end_line = i + len(chunk_lines)
            
            chunks.append((chunk_content, start_line, end_line))
        
        return chunks if chunks else [("", 1, 1)]
