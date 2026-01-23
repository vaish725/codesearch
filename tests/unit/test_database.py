"""
Unit tests for database operations.
"""

import pytest
from pathlib import Path
import tempfile

from codesearch.storage.db import Database


@pytest.mark.unit
def test_database_initialization(tmp_path):
    """Test database initialization."""
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.connect()
    db.initialize_schema()
    
    # Check that tables were created
    cursor = db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]
    
    assert "files" in tables
    assert "symbols" in tables
    assert "fts_code" in tables
    assert "index_metadata" in tables
    
    db.close()


@pytest.mark.unit
def test_database_stats_empty(tmp_path):
    """Test stats on empty database."""
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.connect()
    db.initialize_schema()
    
    stats = db.get_stats()
    
    assert stats["total_files"] == 0
    assert stats["total_symbols"] == 0
    assert stats["db_size_bytes"] > 0  # Database file exists
    
    db.close()


@pytest.mark.unit
def test_database_clear_index(tmp_path):
    """Test clearing the index."""
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.connect()
    db.initialize_schema()
    
    # Insert some test data
    db.conn.execute(
        "INSERT INTO files (path, language, mtime, size_bytes, content_hash) VALUES (?, ?, ?, ?, ?)",
        ("test.py", "python", 12345, 100, "abcd1234")
    )
    db.conn.commit()
    
    # Clear index
    db.clear_index()
    
    # Verify data is cleared
    stats = db.get_stats()
    assert stats["total_files"] == 0
    
    db.close()


@pytest.mark.unit
def test_database_context_manager(tmp_path):
    """Test database context manager."""
    db_path = tmp_path / "test.db"
    
    with Database(db_path) as db:
        db.initialize_schema()
        stats = db.get_stats()
        assert stats["total_files"] == 0
    
    # Connection should be closed
    # (No easy way to verify without accessing internals)
