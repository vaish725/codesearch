"""
Query parser for handling search syntax.

Supports operators like:
- symbol:<name>
- def:<name>
- class:<name>
- import:<module>
- lang:<language>
- path:<pattern>
"""

from dataclasses import dataclass
from typing import Optional, Dict, List
import re


@dataclass
class ParsedQuery:
    """Represents a parsed search query."""
    text_query: str  # Plain text search terms
    symbol_filter: Optional[str] = None
    def_filter: Optional[str] = None
    class_filter: Optional[str] = None
    import_filter: Optional[str] = None
    lang_filter: Optional[str] = None
    path_filter: Optional[str] = None


class QueryParser:
    """
    Parses search queries and extracts filters/operators.
    """
    
    # Pattern for query operators: operator:value
    OPERATOR_PATTERN = re.compile(r'(\w+):([^\s]+)')
    
    def parse(self, query: str) -> ParsedQuery:
        """
        Parse a search query string.
        
        Args:
            query: Raw query string
            
        Returns:
            ParsedQuery object with extracted filters
        """
        filters = {}
        remaining_text = query
        
        # Extract all operators
        for match in self.OPERATOR_PATTERN.finditer(query):
            operator = match.group(1).lower()
            value = match.group(2)
            filters[operator] = value
            # Remove from text query
            remaining_text = remaining_text.replace(match.group(0), "")
        
        # Clean up remaining text
        text_query = " ".join(remaining_text.split())
        
        return ParsedQuery(
            text_query=text_query,
            symbol_filter=filters.get("symbol"),
            def_filter=filters.get("def"),
            class_filter=filters.get("class"),
            import_filter=filters.get("import"),
            lang_filter=filters.get("lang"),
            path_filter=filters.get("path"),
        )
