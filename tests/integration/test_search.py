"""
Integration tests for search functionality.
"""

import pytest

from codesearch.storage.db import Database
from codesearch.indexer.indexer import Indexer
from codesearch.query.search import SearchEngine


@pytest.fixture
def indexed_repo(test_repo, tmp_path):
    """Create and index a test repository."""
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.connect()
    db.initialize_schema()

    indexer = Indexer(db)
    indexer.index_repository(test_repo)

    return db


@pytest.mark.integration
def test_text_search(indexed_repo):
    """Test basic text search."""
    search = SearchEngine(indexed_repo.conn)

    results = search.search("hello", topk=10)

    assert len(results) > 0
    assert any("hello" in r.snippet.lower() for r in results)

    indexed_repo.close()


@pytest.mark.integration
def test_search_with_language_filter(indexed_repo):
    """Test search with language filter."""
    search = SearchEngine(indexed_repo.conn)

    results = search.search("function lang:javascript", topk=10)

    # Should only return JavaScript files
    for result in results:
        assert result.language == "javascript"

    indexed_repo.close()


@pytest.mark.integration
def test_search_with_path_filter(indexed_repo):
    """Test search with path filter."""
    search = SearchEngine(indexed_repo.conn)

    results = search.search("multiply path:utils", topk=10)

    # Should only return files with 'utils' in the path
    for result in results:
        assert "utils" in result.file_path.lower()

    indexed_repo.close()


@pytest.mark.integration
def test_search_no_results(indexed_repo):
    """Test search with no results."""
    search = SearchEngine(indexed_repo.conn)

    results = search.search("nonexistentterm12345", topk=10)

    assert len(results) == 0

    indexed_repo.close()


@pytest.mark.integration
def test_search_topk_limit(indexed_repo):
    """Test that topk limit is respected."""
    search = SearchEngine(indexed_repo.conn)

    results = search.search("def", topk=2)

    assert len(results) <= 2

    indexed_repo.close()
