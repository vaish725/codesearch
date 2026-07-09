"""
Unit tests for Python AST symbol extraction.
"""

import pytest
from codesearch.indexer.symbols.python_ast import PythonASTExtractor


@pytest.fixture
def extractor():
    """Create a Python AST extractor."""
    return PythonASTExtractor()


def test_extract_function(extractor):
    """Test extracting a simple function."""
    source = """
def hello_world():
    print("Hello, World!")
"""
    symbols = extractor.extract_from_source(source)

    assert len(symbols) == 1
    assert symbols[0].name == "hello_world"
    assert symbols[0].kind == "function"
    assert symbols[0].start_line == 2
    assert "def hello_world()" in symbols[0].signature


def test_extract_function_with_args(extractor):
    """Test extracting a function with arguments."""
    source = """
def greet(name, age=25):
    return f"Hello {name}, age {age}"
"""
    symbols = extractor.extract_from_source(source)

    assert len(symbols) == 1
    assert symbols[0].name == "greet"
    assert symbols[0].kind == "function"
    assert "name" in symbols[0].signature
    assert "age=..." in symbols[0].signature


def test_extract_async_function(extractor):
    """Test extracting an async function."""
    source = """
async def fetch_data(url):
    return await get(url)
"""
    symbols = extractor.extract_from_source(source)

    assert len(symbols) == 1
    assert symbols[0].name == "fetch_data"
    assert symbols[0].kind == "function"
    assert "async def" in symbols[0].signature


def test_extract_class(extractor):
    """Test extracting a class."""
    source = """
class Person:
    def __init__(self, name):
        self.name = name
"""
    symbols = extractor.extract_from_source(source)

    # Should extract class and method
    assert len(symbols) == 2

    # Check class
    class_symbol = [s for s in symbols if s.kind == "class"][0]
    assert class_symbol.name == "Person"
    assert class_symbol.kind == "class"
    assert "class Person" in class_symbol.signature

    # Check method
    method_symbol = [s for s in symbols if s.kind == "method"][0]
    assert method_symbol.name == "Person.__init__"
    assert method_symbol.kind == "method"


def test_extract_class_with_inheritance(extractor):
    """Test extracting a class with base classes."""
    source = """
class Dog(Animal, Mammal):
    pass
"""
    symbols = extractor.extract_from_source(source)

    assert len(symbols) == 1
    assert symbols[0].name == "Dog"
    assert symbols[0].kind == "class"
    assert "Animal" in symbols[0].signature
    assert "Mammal" in symbols[0].signature


def test_extract_methods(extractor):
    """Test extracting multiple methods from a class."""
    source = """
class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    async def multiply_async(self, a, b):
        return a * b
"""
    symbols = extractor.extract_from_source(source)

    # 1 class + 3 methods
    assert len(symbols) == 4

    methods = [s for s in symbols if s.kind == "method"]
    assert len(methods) == 3

    method_names = {s.name for s in methods}
    assert "Calculator.add" in method_names
    assert "Calculator.subtract" in method_names
    assert "Calculator.multiply_async" in method_names


def test_extract_imports(extractor):
    """Test extracting import statements."""
    source = """
import os
import sys
from pathlib import Path
from typing import List, Dict
"""
    symbols = extractor.extract_from_source(source)

    # 2 regular imports + 1 Path + 2 from typing = 5
    assert len(symbols) == 5

    import_names = {s.name for s in symbols}
    assert "os" in import_names
    assert "sys" in import_names
    assert "pathlib.Path" in import_names
    assert "typing.List" in import_names
    assert "typing.Dict" in import_names


def test_extract_from_import(extractor):
    """Test extracting from...import statements."""
    source = """
from collections import defaultdict
from os.path import join, exists
"""
    symbols = extractor.extract_from_source(source)

    assert len(symbols) == 3
    assert all(s.kind == "import" for s in symbols)

    names = {s.name for s in symbols}
    assert "collections.defaultdict" in names
    assert "os.path.join" in names
    assert "os.path.exists" in names


def test_extract_star_import(extractor):
    """Test extracting from...import * statements."""
    source = """
from utils import *
"""
    symbols = extractor.extract_from_source(source)

    assert len(symbols) == 1
    assert symbols[0].name == "utils.*"
    assert symbols[0].kind == "import"


def test_extract_complex_signature(extractor):
    """Test extracting function with complex signature."""
    source = """
def process(data, *args, verbose=False, **kwargs):
    pass
"""
    symbols = extractor.extract_from_source(source)

    assert len(symbols) == 1
    sig = symbols[0].signature
    assert "data" in sig
    assert "*args" in sig
    assert "verbose=..." in sig
    assert "**kwargs" in sig


def test_nested_functions(extractor):
    """Test that nested functions are extracted (only top-level for now)."""
    source = """
def outer():
    def inner():
        pass
    return inner
"""
    symbols = extractor.extract_from_source(source)

    # Only outer function is extracted (nested functions not supported yet)
    assert len(symbols) >= 1
    function_names = {s.name for s in symbols}
    assert "outer" in function_names


def test_syntax_error_handling(extractor):
    """Test that syntax errors are handled gracefully."""
    source = """
def broken(
    # Missing closing paren
"""
    symbols = extractor.extract_from_source(source)

    # Should return empty list, not crash
    assert symbols == []


def test_empty_source(extractor):
    """Test extracting from empty source."""
    symbols = extractor.extract_from_source("")
    assert symbols == []


def test_line_numbers(extractor):
    """Test that line numbers are correct."""
    source = """
# Line 1

def foo():  # Line 3 (but appears as line 4 due to leading newline)
    pass    # Line 4

class Bar:  # Line 6 (appears as 7)
    def baz(self):  # Line 7 (appears as 8)
        pass  # Line 8
"""
    symbols = extractor.extract_from_source(source)

    foo_symbol = [s for s in symbols if s.name == "foo"][0]
    # Line numbers are 1-indexed from the source string
    assert foo_symbol.start_line == 4  # "def foo():" line
    assert foo_symbol.end_line >= 5

    bar_symbol = [s for s in symbols if s.name == "Bar"][0]
    assert bar_symbol.start_line == 7  # "class Bar:" line
    assert bar_symbol.end_line >= 9

    baz_symbol = [s for s in symbols if s.name == "Bar.baz"][0]
    assert baz_symbol.start_line == 8


def test_real_world_example(extractor):
    """Test with a realistic code example."""
    source = """
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

class UserManager:
    def __init__(self, db_connection):
        self.db = db_connection

    def create_user(self, username: str, email: str) -> int:
        query = "INSERT INTO users (username, email) VALUES (?, ?)"
        cursor = self.db.execute(query, (username, email))
        return cursor.lastrowid

    def get_user(self, user_id: int) -> Optional[dict]:
        query = "SELECT * FROM users WHERE id = ?"
        cursor = self.db.execute(query, (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def validate_email(email: str) -> bool:
    return "@" in email
"""
    symbols = extractor.extract_from_source(source)

    # Should extract: 2 imports, 1 class, 3 methods/functions
    assert len(symbols) >= 5

    # Check we have all the expected types
    kinds = {s.kind for s in symbols}
    assert "import" in kinds
    assert "class" in kinds
    assert "method" in kinds
    assert "function" in kinds

    # Check specific symbols
    names = {s.name for s in symbols}
    assert "UserManager" in names
    assert "UserManager.__init__" in names
    assert "UserManager.create_user" in names
    assert "validate_email" in names
