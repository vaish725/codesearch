"""
Integration tests for Phase 2 - Incremental indexing functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from codesearch.storage.db import Database
from codesearch.indexer.indexer import Indexer


@pytest.fixture
def temp_repo():
    """Create a temporary repository for testing."""
    temp_dir = tempfile.mkdtemp()
    repo_path = Path(temp_dir) / "test_repo"
    repo_path.mkdir()

    yield repo_path

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def db():
    """Create a temporary database."""
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_path = Path(db_file.name)
    db_file.close()

    database = Database(db_path)
    database.connect()
    database.initialize_schema()

    yield database

    database.close()
    db_path.unlink()


def test_incremental_no_changes(temp_repo, db):
    """Test that unchanged files are skipped on re-index."""
    # Create initial files
    (temp_repo / "file1.py").write_text("print('hello')\n")
    (temp_repo / "file2.py").write_text("def foo():\n    pass\n")

    indexer = Indexer(db)

    # First index
    stats1 = indexer.index_repository(temp_repo)
    assert stats1["files_new"] == 2
    assert stats1["files_updated"] == 0
    assert stats1["files_unchanged"] == 0
    assert stats1["files_indexed"] == 2

    # Second index (no changes)
    stats2 = indexer.index_repository(temp_repo)
    assert stats2["files_new"] == 0
    assert stats2["files_updated"] == 0
    assert stats2["files_unchanged"] == 2
    assert stats2["files_indexed"] == 0


def test_incremental_file_updated(temp_repo, db):
    """Test that modified files are re-indexed."""
    file_path = temp_repo / "test.py"
    file_path.write_text("print('version 1')\n")

    indexer = Indexer(db)

    # First index
    stats1 = indexer.index_repository(temp_repo)
    assert stats1["files_new"] == 1
    assert stats1["files_updated"] == 0

    # Modify file
    file_path.write_text("print('version 2')\n")

    # Second index
    stats2 = indexer.index_repository(temp_repo)
    assert stats2["files_new"] == 0
    assert stats2["files_updated"] == 1
    assert stats2["files_unchanged"] == 0
    assert stats2["files_indexed"] == 1


def test_incremental_file_added(temp_repo, db):
    """Test that new files are indexed."""
    # Create initial file
    (temp_repo / "file1.py").write_text("print('file1')\n")

    indexer = Indexer(db)

    # First index
    stats1 = indexer.index_repository(temp_repo)
    assert stats1["files_new"] == 1

    # Add new file
    (temp_repo / "file2.py").write_text("print('file2')\n")

    # Second index
    stats2 = indexer.index_repository(temp_repo)
    assert stats2["files_new"] == 1
    assert stats2["files_unchanged"] == 1
    assert stats2["files_indexed"] == 1


def test_incremental_file_deleted(temp_repo, db):
    """Test that deleted files are removed from index."""
    file1 = temp_repo / "file1.py"
    file2 = temp_repo / "file2.py"

    file1.write_text("print('file1')\n")
    file2.write_text("print('file2')\n")

    indexer = Indexer(db)

    # First index
    stats1 = indexer.index_repository(temp_repo)
    assert stats1["files_new"] == 2

    # Check database
    db_stats1 = db.get_stats()
    assert db_stats1["total_files"] == 2

    # Delete file1
    file1.unlink()

    # Second index
    stats2 = indexer.index_repository(temp_repo)
    assert stats2["files_deleted"] == 1
    assert stats2["files_unchanged"] == 1

    # Check database
    db_stats2 = db.get_stats()
    assert db_stats2["total_files"] == 1


def test_incremental_mixed_operations(temp_repo, db):
    """Test a mix of add/update/delete operations."""
    # Initial files
    (temp_repo / "unchanged.py").write_text("# stays the same\n")
    (temp_repo / "to_update.py").write_text("version = 1\n")
    (temp_repo / "to_delete.py").write_text("# will be deleted\n")

    indexer = Indexer(db)

    # First index
    stats1 = indexer.index_repository(temp_repo)
    assert stats1["files_new"] == 3

    # Make changes
    (temp_repo / "to_update.py").write_text("version = 2\n")  # Update
    (temp_repo / "to_delete.py").unlink()  # Delete
    (temp_repo / "new_file.py").write_text("# new file\n")  # Add

    # Second index
    stats2 = indexer.index_repository(temp_repo)
    assert stats2["files_new"] == 1
    assert stats2["files_updated"] == 1
    assert stats2["files_unchanged"] == 1
    assert stats2["files_deleted"] == 1

    # Verify final state
    db_stats = db.get_stats()
    assert db_stats["total_files"] == 3


def test_force_flag_reindexes_all(temp_repo, db):
    """Test that --force flag re-indexes all files."""
    (temp_repo / "file1.py").write_text("print('hello')\n")
    (temp_repo / "file2.py").write_text("print('world')\n")

    indexer = Indexer(db)

    # First index
    stats1 = indexer.index_repository(temp_repo)
    assert stats1["files_new"] == 2

    # Force re-index (no changes made)
    stats2 = indexer.index_repository(temp_repo, force=True)
    assert stats2["files_indexed"] == 2
    assert stats2["files_new"] == 2  # Treated as new in force mode
    assert "files_unchanged" not in stats2 or stats2["files_unchanged"] == 0


def test_incremental_preserves_search(temp_repo, db):
    """Test that search still works after incremental updates."""
    from codesearch.query.search import SearchEngine

    # Create initial file
    (temp_repo / "test.py").write_text("def important_function():\n    pass\n")

    indexer = Indexer(db)
    indexer.index_repository(temp_repo)

    # Search should find it
    search = SearchEngine(db.conn)
    results = search.search("important_function")
    assert len(results) == 1
    assert "important_function" in results[0].snippet

    # Update file
    (temp_repo / "test.py").write_text("def important_function():\n    return 42\n")
    indexer.index_repository(temp_repo)

    # Search should still work with updated content
    results = search.search("return 42")
    assert len(results) == 1
    assert "return 42" in results[0].snippet


def test_hash_comparison_accuracy(temp_repo, db):
    """Test that hash comparison correctly detects changes."""
    file_path = temp_repo / "test.py"

    # Content with same length but different text
    content1 = "x = 1\n"
    content2 = "y = 2\n"

    assert len(content1) == len(content2)  # Same length

    file_path.write_text(content1)

    indexer = Indexer(db)
    stats1 = indexer.index_repository(temp_repo)
    assert stats1["files_new"] == 1

    # Change to different content (same length)
    file_path.write_text(content2)

    stats2 = indexer.index_repository(temp_repo)
    assert stats2["files_updated"] == 1  # Should detect change via hash
    assert stats2["files_unchanged"] == 0


def test_whitespace_only_changes_detected(temp_repo, db):
    """Test that even whitespace-only changes are detected."""
    file_path = temp_repo / "test.py"

    file_path.write_text("def foo():\n    pass\n")

    indexer = Indexer(db)
    stats1 = indexer.index_repository(temp_repo)
    assert stats1["files_new"] == 1

    # Add extra newline
    file_path.write_text("def foo():\n    pass\n\n")

    stats2 = indexer.index_repository(temp_repo)
    assert stats2["files_updated"] == 1


def test_performance_incremental_faster_than_full(temp_repo, db):
    """Test that incremental indexing is faster than full re-index."""
    # Create multiple files
    for i in range(20):
        (temp_repo / f"file{i}.py").write_text(f"def func{i}():\n    pass\n" * 50)

    indexer = Indexer(db)

    # First index
    stats1 = indexer.index_repository(temp_repo)
    time1 = stats1["duration_seconds"]

    # Incremental (no changes) - should be much faster
    stats2 = indexer.index_repository(temp_repo)
    time2 = stats2["duration_seconds"]

    assert stats2["files_unchanged"] == 20
    # Incremental should be faster or equal (both might be <0.01s)
    assert time2 <= time1 or (time1 < 0.01 and time2 < 0.01)
