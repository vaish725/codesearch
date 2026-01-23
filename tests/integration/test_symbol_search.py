"""
Integration tests for Phase 3 - Symbol extraction and search.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from codesearch.storage.db import Database
from codesearch.indexer.indexer import Indexer
from codesearch.query.search import SearchEngine


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


def test_symbol_extraction_during_indexing(temp_repo, db):
    """Test that symbols are extracted during indexing."""
    # Create a Python file with symbols
    (temp_repo / "module.py").write_text("""
import os
from pathlib import Path

class Calculator:
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b

def multiply(x, y):
    return x * y
""")
    
    indexer = Indexer(db)
    stats = indexer.index_repository(temp_repo)
    
    # Check that symbols were extracted
    assert stats["symbols_extracted"] > 0
    
    # Check database
    db_stats = db.get_stats()
    assert db_stats["total_symbols"] > 0
    
    # Should have: 2 imports, 1 class, 2 methods, 1 function = 6 symbols
    assert db_stats["total_symbols"] == 6


def test_search_by_function_name(temp_repo, db):
    """Test searching for a function by name."""
    (temp_repo / "utils.py").write_text("""
def calculate_total(items):
    return sum(items)

def format_output(data):
    return str(data)
""")
    
    indexer = Indexer(db)
    indexer.index_repository(temp_repo)
    
    search = SearchEngine(db.conn)
    results = search.search("def:calculate_total")
    
    assert len(results) > 0
    assert any("calculate_total" in r.snippet for r in results)
    assert any(r.match_type.startswith("symbol:") for r in results)


def test_search_by_class_name(temp_repo, db):
    """Test searching for a class by name."""
    (temp_repo / "models.py").write_text("""
class User:
    def __init__(self, name):
        self.name = name

class Product:
    def __init__(self, title):
        self.title = title
""")
    
    indexer = Indexer(db)
    indexer.index_repository(temp_repo)
    
    search = SearchEngine(db.conn)
    results = search.search("class:User")
    
    assert len(results) > 0
    assert any("User" in r.snippet for r in results)


def test_search_by_import(temp_repo, db):
    """Test searching for imports."""
    (temp_repo / "app.py").write_text("""
import sqlite3
from pathlib import Path
from typing import List, Dict
""")
    
    indexer = Indexer(db)
    indexer.index_repository(temp_repo)
    
    search = SearchEngine(db.conn)
    results = search.search("import:sqlite3")
    
    assert len(results) > 0
    assert any("sqlite3" in r.snippet.lower() for r in results)


def test_search_method_in_class(temp_repo, db):
    """Test searching for methods within classes."""
    (temp_repo / "service.py").write_text("""
class DataService:
    def fetch_data(self, query):
        pass
    
    def save_data(self, data):
        pass
""")
    
    indexer = Indexer(db)
    indexer.index_repository(temp_repo)
    
    search = SearchEngine(db.conn)
    results = search.search("def:fetch_data")
    
    assert len(results) > 0
    # Method should be found
    assert any("fetch_data" in r.snippet for r in results)


def test_symbol_filter_with_text_query(temp_repo, db):
    """Test combining symbol filter with text search."""
    (temp_repo / "handlers.py").write_text("""
def handle_request(request):
    return process(request)

def handle_response(response):
    return format(response)

class RequestHandler:
    def handle(self):
        pass
""")
    
    indexer = Indexer(db)
    indexer.index_repository(temp_repo)
    
    search = SearchEngine(db.conn)
    results = search.search("def:handle request")
    
    # Should find functions with "handle" in name
    assert len(results) > 0


def test_partial_name_matching(temp_repo, db):
    """Test that partial names work."""
    (temp_repo / "math_utils.py").write_text("""
def calculate_sum(numbers):
    return sum(numbers)

def calculate_average(numbers):
    return sum(numbers) / len(numbers)

def calculate_median(numbers):
    return sorted(numbers)[len(numbers) // 2]
""")
    
    indexer = Indexer(db)
    indexer.index_repository(temp_repo)
    
    search = SearchEngine(db.conn)
    results = search.search("def:calculate")
    
    # Should find all three functions
    assert len(results) == 3


def test_symbols_updated_on_file_change(temp_repo, db):
    """Test that symbols are updated when file changes."""
    file_path = temp_repo / "counter.py"
    
    # Initial version
    file_path.write_text("""
def increment(x):
    return x + 1
""")
    
    indexer = Indexer(db)
    indexer.index_repository(temp_repo)
    
    search = SearchEngine(db.conn)
    results = search.search("def:increment")
    assert len(results) == 1
    
    # Update file - rename function
    file_path.write_text("""
def decrement(x):
    return x - 1
""")
    
    indexer.index_repository(temp_repo)
    
    # Old function should not be found
    results = search.search("def:increment")
    assert len(results) == 0
    
    # New function should be found
    results = search.search("def:decrement")
    assert len(results) == 1


def test_symbols_deleted_with_file(temp_repo, db):
    """Test that symbols are deleted when file is deleted."""
    file_path = temp_repo / "temp.py"
    file_path.write_text("""
def temporary_function():
    pass
""")
    
    indexer = Indexer(db)
    indexer.index_repository(temp_repo)
    
    search = SearchEngine(db.conn)
    results = search.search("def:temporary_function")
    assert len(results) == 1
    
    # Delete the file
    file_path.unlink()
    
    indexer.index_repository(temp_repo)
    
    # Symbol should be gone
    results = search.search("def:temporary_function")
    assert len(results) == 0


def test_language_filter_with_symbols(temp_repo, db):
    """Test combining language filter with symbol search."""
    # Create Python and JavaScript files
    (temp_repo / "utils.py").write_text("""
def process_data():
    pass
""")
    
    (temp_repo / "utils.js").write_text("""
function process_data() {
}
""")
    
    indexer = Indexer(db)
    indexer.index_repository(temp_repo)
    
    search = SearchEngine(db.conn)
    results = search.search("def:process_data lang:python")
    
    # Should only find Python file
    assert len(results) > 0
    assert all(r.language == "python" for r in results)


def test_path_filter_with_symbols(temp_repo, db):
    """Test combining path filter with symbol search."""
    (temp_repo / "src").mkdir()
    (temp_repo / "tests").mkdir()
    
    (temp_repo / "src" / "app.py").write_text("""
def main():
    pass
""")
    
    (temp_repo / "tests" / "test_app.py").write_text("""
def test_main():
    pass
""")
    
    indexer = Indexer(db)
    indexer.index_repository(temp_repo)
    
    search = SearchEngine(db.conn)
    results = search.search("def:main path:src")
    
    # Should only find function in src/
    assert len(results) > 0
    assert all("src" in r.file_path for r in results)


def test_generic_symbol_search(temp_repo, db):
    """Test generic symbol: filter that matches any type."""
    (temp_repo / "code.py").write_text("""
import os

class MyClass:
    def my_method(self):
        pass

def my_function():
    pass
""")
    
    indexer = Indexer(db)
    indexer.index_repository(temp_repo)
    
    search = SearchEngine(db.conn)
    results = search.search("symbol:my")
    
    # Should find both class, method, and function
    assert len(results) >= 3


def test_complex_class_hierarchy(temp_repo, db):
    """Test symbol extraction with complex class structures."""
    (temp_repo / "models.py").write_text("""
class Animal:
    def breathe(self):
        pass

class Mammal(Animal):
    def feed_young(self):
        pass

class Dog(Mammal):
    def bark(self):
        print("Woof!")
""")
    
    indexer = Indexer(db)
    stats = indexer.index_repository(temp_repo)
    
    # Should extract 3 classes + methods
    assert stats["symbols_extracted"] >= 6
    
    search = SearchEngine(db.conn)
    results = search.search("class:Dog")
    assert len(results) > 0
    
    # Check that inheritance info is in signature
    dog_result = [r for r in results if "Dog" in r.snippet][0]
    assert "Mammal" in dog_result.snippet


def test_async_function_search(temp_repo, db):
    """Test searching for async functions."""
    (temp_repo / "async_ops.py").write_text("""
async def fetch_data(url):
    pass

async def save_data(data):
    pass

def sync_operation():
    pass
""")
    
    indexer = Indexer(db)
    indexer.index_repository(temp_repo)
    
    search = SearchEngine(db.conn)
    results = search.search("def:fetch_data")
    
    assert len(results) > 0
    # Should include "async" in signature
    assert any("async" in r.snippet for r in results)


def test_no_symbols_for_non_python_files(temp_repo, db):
    """Test that non-Python files don't extract symbols."""
    (temp_repo / "readme.md").write_text("""
# Documentation
def fake_function():
    This is just text, not code
""")
    
    (temp_repo / "data.json").write_text("""
{"function": "not_real"}
""")
    
    indexer = Indexer(db)
    stats = indexer.index_repository(temp_repo)
    
    # No Python files, so no symbols extracted
    assert stats.get("symbols_extracted", 0) == 0
