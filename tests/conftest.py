"""
Pytest configuration and shared fixtures.
"""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)


@pytest.fixture
def sample_repo(temp_dir):
    """Create a sample repository structure for testing."""
    # Create sample files
    (temp_dir / "src").mkdir()
    (temp_dir / "src" / "main.py").write_text("""
def hello():
    print("Hello, World!")

class User:
    def __init__(self, name):
        self.name = name
""")
    
    (temp_dir / "README.md").write_text("# Sample Repo")
    
    return temp_dir


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
    
    # Create text file
    (repo / "README.md").write_text("# Test Repository")
    
    # Create a subdirectory
    src_dir = repo / "src"
    src_dir.mkdir()
    (src_dir / "utils.py").write_text("""
def multiply(x, y):
    return x * y
""")
    
    return repo


@pytest.fixture
def mock_db(temp_dir):
    """Create a mock database for testing."""
    from codesearch.storage.db import Database
    
    db_path = temp_dir / "test.db"
    db = Database(db_path)
    db.connect()
    db.initialize_schema()
    
    yield db
    
    db.close()
