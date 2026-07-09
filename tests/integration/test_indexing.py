"""
Integration tests for indexing workflow.
"""

import pytest

from codesearch.storage.db import Database
from codesearch.indexer.indexer import Indexer


@pytest.fixture
def test_repo(tmp_path):
    """Create a test repository with sample files."""
    repo = tmp_path / "test_repo"
    repo.mkdir()

    # Create Python file
    (repo / "main.py").write_text("""
def hello():
    print("Hello, World!")

class User:
    def __init__(self, name):
        self.name = name

    def greet(self):
        return f"Hello, {self.name}"
""")

    # Create JavaScript file
    (repo / "app.js").write_text("""
function calculate(a, b) {
    return a + b;
}

class App {
    constructor() {
        this.name = "MyApp";
    }
}
""")

    # Create text file that should be skipped
    (repo / "README.md").write_text("# Test Repository")

    # Create a subdirectory
    src_dir = repo / "src"
    src_dir.mkdir()
    (src_dir / "utils.py").write_text("""
def multiply(x, y):
    return x * y
""")

    return repo


@pytest.mark.integration
def test_index_repository(test_repo, tmp_path):
    """Test indexing a repository."""
    # Create database
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.connect()
    db.initialize_schema()

    # Create indexer
    indexer = Indexer(db)

    # Index the repository
    stats = indexer.index_repository(test_repo)

    # Verify statistics
    assert stats["files_scanned"] > 0
    assert stats["files_indexed"] >= 3  # Python, JS, and markdown files
    assert stats["chunks_created"] > 0
    assert stats["duration_seconds"] >= 0

    # Verify database contents
    db_stats = db.get_stats()
    assert db_stats["total_files"] >= 3
    assert "python" in db_stats["files_by_language"]
    assert "javascript" in db_stats["files_by_language"]

    db.close()


@pytest.mark.integration
def test_index_nonexistent_repo(tmp_path):
    """Test indexing a non-existent repository."""
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.connect()
    db.initialize_schema()

    indexer = Indexer(db)

    with pytest.raises(FileNotFoundError):
        indexer.index_repository(tmp_path / "nonexistent")

    db.close()


@pytest.mark.integration
def test_index_with_exclusions(test_repo, tmp_path):
    """Test that excluded directories are skipped."""
    # Add node_modules directory (should be excluded)
    node_modules = test_repo / "node_modules"
    node_modules.mkdir()
    (node_modules / "package.js").write_text("// Should be excluded")

    # Create database and index
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.connect()
    db.initialize_schema()

    indexer = Indexer(db)
    indexer.index_repository(test_repo)

    # Verify node_modules was excluded
    cursor = db.conn.execute("SELECT path FROM files WHERE path LIKE '%node_modules%'")
    assert cursor.fetchone() is None

    db.close()
