"""
Search execution engine with hybrid ranking.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import sqlite3

from .parser import QueryParser, ParsedQuery
from ..utils.snippets import extract_snippet, format_snippet
from ..log import logger


# Ranking boost constants
BOOST_EXACT_MATCH = 10.0       # Exact name match
BOOST_DEFINITION = 5.0          # Symbol definition (vs reference)
BOOST_SYMBOL = 3.0              # Any symbol match
BOOST_SIGNATURE = 2.0           # Match in signature
BOOST_EXPORTED = 1.5            # Exported symbol


@dataclass
class SearchResult:
    """Represents a search result with scoring metadata."""
    file_path: str
    line_number: int
    snippet: str
    score: float
    match_type: str = "text"  # text, symbol:function, symbol:class, etc.
    language: Optional[str] = None
    symbol_name: Optional[str] = None
    symbol_kind: Optional[str] = None
    is_definition: bool = True  # Symbol results are definitions by default
    context_lines: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output."""
        result = {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "snippet": self.snippet,
            "score": self.score,
            "match_type": self.match_type,
            "language": self.language,
        }
        
        # Add symbol metadata if available
        if self.symbol_name:
            result["symbol_name"] = self.symbol_name
        if self.symbol_kind:
            result["symbol_kind"] = self.symbol_kind
        if self.context_lines:
            result["context"] = self.context_lines
            
        return result


class SearchEngine:
    """
    Executes search queries against the index.
    """
    
    def __init__(self, db_connection):
        """
        Initialize the search engine.
        
        Args:
            db_connection: Database connection
        """
        self.db = db_connection
        self.parser = QueryParser()
    
    def search(self, query: str, topk: int = 10) -> List[SearchResult]:
        """
        Execute a search query.
        
        Args:
            query: Search query string
            topk: Number of results to return
            
        Returns:
            List of search results
        """
        # Parse the query
        parsed = self.parser.parse(query)
        
        logger.info(f"Executing search: text='{parsed.text_query}', filters={parsed}")
        
        # Check if this is a symbol-only query
        has_symbol_filter = any([
            parsed.def_filter,
            parsed.class_filter,
            parsed.symbol_filter,
            parsed.import_filter
        ])
        
        if has_symbol_filter and not parsed.text_query:
            # Pure symbol query
            return self._execute_symbol_query(parsed, topk)
        elif has_symbol_filter and parsed.text_query:
            # Hybrid: combine symbol and text results
            symbol_results = self._execute_symbol_query(parsed, topk // 2)
            text_results = self._execute_fts_query(parsed, topk // 2)
            # Merge and sort by score
            all_results = symbol_results + text_results
            all_results.sort(key=lambda r: r.score, reverse=True)
            return all_results[:topk]
        elif parsed.text_query:
            # Text-only query
            return self._execute_fts_query(parsed, topk)
        else:
            # No query
            return []
    
    def _execute_symbol_query(self, parsed: ParsedQuery, topk: int) -> List[SearchResult]:
        """
        Execute a symbol-based query.
        
        Args:
            parsed: Parsed query
            topk: Number of results
            
        Returns:
            List of search results
        """
        results = []
        
        # Determine which symbol filter to use
        symbol_filters = []
        
        if parsed.def_filter:
            symbol_filters.append(("function", parsed.def_filter))
            symbol_filters.append(("method", parsed.def_filter))
        
        if parsed.class_filter:
            symbol_filters.append(("class", parsed.class_filter))
        
        if parsed.import_filter:
            symbol_filters.append(("import", parsed.import_filter))
        
        if parsed.symbol_filter:
            # Generic symbol search (any kind)
            symbol_filters.append((None, parsed.symbol_filter))
        
        for kind, name_pattern in symbol_filters:
            sql_parts = ["""
                SELECT 
                    f.path,
                    f.language,
                    s.name,
                    s.kind,
                    s.start_line,
                    s.end_line,
                    s.signature
                FROM symbols s
                JOIN files f ON s.file_id = f.file_id
                WHERE s.name LIKE ?
            """]
            
            params = [f"%{name_pattern}%"]
            
            # Add kind filter if specific
            if kind:
                sql_parts.append("AND s.kind = ?")
                params.append(kind)
            
            # Add language filter
            if parsed.lang_filter:
                sql_parts.append("AND f.language = ?")
                params.append(parsed.lang_filter)
            
            # Add path filter
            if parsed.path_filter:
                sql_parts.append("AND f.path LIKE ?")
                params.append(f"%{parsed.path_filter}%")
            
            sql_parts.append("ORDER BY s.name LIMIT ?")
            params.append(topk)
            
            sql = " ".join(sql_parts)
            
            try:
                cursor = self.db.execute(sql, params)
                rows = cursor.fetchall()
                
                for row in rows:
                    file_path = row[0]
                    language = row[1]
                    symbol_name = row[2]
                    symbol_kind = row[3]
                    start_line = row[4]
                    end_line = row[5]
                    signature = row[6]
                    
                    # Create snippet from signature or name
                    snippet = signature if signature else f"{symbol_kind}: {symbol_name}"
                    
                    # Enhanced scoring with boosts
                    score = self._calculate_symbol_score(
                        symbol_name=symbol_name,
                        symbol_kind=symbol_kind,
                        query_pattern=name_pattern,
                        signature=signature,
                        is_definition=True
                    )
                    
                    result = SearchResult(
                        file_path=file_path,
                        line_number=start_line,
                        snippet=snippet,
                        score=score,
                        match_type=f"symbol:{symbol_kind}",
                        language=language,
                        symbol_name=symbol_name,
                        symbol_kind=symbol_kind,
                        is_definition=True,
                    )
                    results.append(result)
            
            except Exception as e:
                logger.error(f"Symbol query error: {e}")
                continue
        
        # Sort by score and return top results
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:topk]
    
    def _execute_fts_query(self, parsed: ParsedQuery, topk: int) -> List[SearchResult]:
        """
        Execute an FTS query.
        
        Args:
            parsed: Parsed query
            topk: Number of results
            
        Returns:
            List of search results
        """
        # Build the SQL query
        sql_parts = ["""
            SELECT 
                f.path,
                f.language,
                fts.start_line,
                fts.end_line,
                fts.content,
                fts.rowid,
                rank
            FROM fts_code fts
            JOIN files f ON fts.file_id = f.file_id
            WHERE fts_code MATCH ?
        """]
        
        params = [parsed.text_query]
        
        # Add language filter
        if parsed.lang_filter:
            sql_parts.append("AND f.language = ?")
            params.append(parsed.lang_filter)
        
        # Add path filter
        if parsed.path_filter:
            sql_parts.append("AND f.path LIKE ?")
            params.append(f"%{parsed.path_filter}%")
        
        # Add ordering and limit
        sql_parts.append("ORDER BY rank LIMIT ?")
        params.append(topk)
        
        sql = " ".join(sql_parts)
        
        try:
            cursor = self.db.execute(sql, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                file_path = row[0]
                language = row[1]
                start_line = row[2]
                end_line = row[3]
                content = row[4]
                rank = row[6]
                
                # Find the best line to highlight
                # For now, just use the start line
                line_number = start_line
                
                # Extract snippet (simplified for Phase 1)
                snippet = self._extract_snippet_simple(content, line_number - start_line + 1)
                
                result = SearchResult(
                    file_path=file_path,
                    line_number=line_number,
                    snippet=snippet,
                    score=-float(rank),  # FTS rank is negative, convert to positive
                    match_type="text",
                    language=language,
                )
                results.append(result)
            
            logger.info(f"Found {len(results)} results")
            return results
            
        except sqlite3.OperationalError as e:
            logger.error(f"FTS query failed: {e}")
            return []
    
    def _extract_snippet_simple(self, content: str, relative_line: int) -> str:
        """
        Extract a simple snippet from chunk content.
        
        Args:
            content: Chunk content
            relative_line: Line number relative to chunk start
            
        Returns:
            Snippet string
        """
        lines = content.splitlines()
        
        # Get a few lines around the match
        start = max(0, relative_line - 2)
        end = min(len(lines), relative_line + 3)
        
        snippet_lines = lines[start:end]
        return "\n".join(snippet_lines[:5])  # Max 5 lines
    
    def _calculate_symbol_score(
        self,
        symbol_name: str,
        symbol_kind: str,
        query_pattern: str,
        signature: Optional[str],
        is_definition: bool = True
    ) -> float:
        """
        Calculate relevance score for a symbol match with boosts.
        
        Args:
            symbol_name: Name of the symbol
            symbol_kind: Kind of symbol (function, class, etc.)
            query_pattern: The search pattern
            signature: Symbol signature if available
            is_definition: Whether this is a definition (vs reference)
            
        Returns:
            Relevance score (higher is better)
        """
        base_score = 1.0
        
        # Exact match boost
        if query_pattern.lower() == symbol_name.lower():
            base_score += BOOST_EXACT_MATCH
        elif query_pattern.lower() in symbol_name.lower():
            # Partial match
            base_score += BOOST_EXACT_MATCH * 0.5
        
        # Definition boost (symbols are always definitions)
        if is_definition:
            base_score += BOOST_DEFINITION
        
        # Symbol kind boost
        base_score += BOOST_SYMBOL
        
        # Signature presence boost (indicates well-documented symbol)
        if signature:
            base_score += BOOST_SIGNATURE
        
        # Priority by kind
        kind_priority = {
            "class": 2.0,
            "function": 1.5,
            "method": 1.5,
            "import": 1.0,
        }
        base_score += kind_priority.get(symbol_kind, 1.0)
        
        return base_score
    
    def get_enhanced_snippet(
        self,
        file_path: str,
        line_number: int,
        context_lines: int = 2
    ) -> tuple[str, List[str]]:
        """
        Extract enhanced snippet with context lines from actual file.
        
        Args:
            file_path: Path to the file
            line_number: Target line number (1-indexed)
            context_lines: Number of context lines before/after
            
        Returns:
            Tuple of (main_snippet, context_lines_list)
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Calculate range (1-indexed to 0-indexed)
            target_idx = line_number - 1
            start_idx = max(0, target_idx - context_lines)
            end_idx = min(len(lines), target_idx + context_lines + 1)
            
            # Extract lines
            context = []
            main_line = ""
            
            for i in range(start_idx, end_idx):
                line = lines[i].rstrip()
                if i == target_idx:
                    main_line = line
                context.append(f"{i + 1:4d} | {line}")
            
            snippet = main_line if main_line else ""
            
            return snippet, context
            
        except Exception as e:
            logger.warning(f"Could not enhance snippet for {file_path}:{line_number}: {e}")
            return "", []
