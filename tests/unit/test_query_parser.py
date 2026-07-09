"""
Tests for query parser.
"""

from codesearch.query.parser import QueryParser


def test_parse_simple_text_query():
    """Test parsing a simple text query."""
    parser = QueryParser()
    result = parser.parse("hello world")

    assert result.text_query == "hello world"
    assert result.symbol_filter is None
    assert result.lang_filter is None


def test_parse_query_with_filters():
    """Test parsing query with filters."""
    parser = QueryParser()
    result = parser.parse("authentication lang:python path:auth")

    assert "authentication" in result.text_query
    assert result.lang_filter == "python"
    assert result.path_filter == "auth"


def test_parse_symbol_query():
    """Test parsing symbol queries."""
    parser = QueryParser()
    result = parser.parse("def:process_payment")

    assert result.def_filter == "process_payment"
    assert result.text_query == ""
