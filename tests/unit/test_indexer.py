"""
Unit tests for indexer components.
"""

import pytest
from pathlib import Path

from codesearch.indexer.scanner import FileScanner, load_ignore_file
from codesearch.indexer.language import LanguageDetector
from codesearch.indexer.hasher import hash_file_content, hash_string
from codesearch.indexer.fts import FTSChunker
from codesearch.config import LANGUAGE_MAP


@pytest.mark.unit
def test_file_scanner(tmp_path):
    """Test file scanner."""
    # Create test files
    (tmp_path / "test.py").write_text("print('hello')")
    (tmp_path / "test.js").write_text("console.log('hello')")
    (tmp_path / "README.md").write_text("# README")

    # Create excluded directory
    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()
    (node_modules / "package.js").write_text("// excluded")

    scanner = FileScanner(
        root_path=tmp_path,
        exclude_dirs=["node_modules"],
        exclude_patterns=["*.md"],
        max_file_size=1024 * 1024,
    )

    files = list(scanner.scan())
    file_names = [f.name for f in files]

    assert "test.py" in file_names
    assert "test.js" in file_names
    assert "README.md" not in file_names  # Excluded by pattern
    assert "package.js" not in file_names  # In excluded directory


@pytest.mark.unit
def test_load_ignore_file(tmp_path):
    """Test loading .codesearchignore file."""
    ignore_file = tmp_path / ".codesearchignore"
    ignore_file.write_text("""
# Comment line
node_modules
*.log

# Another comment
build/
""")

    patterns = load_ignore_file(ignore_file)

    assert "node_modules" in patterns
    assert "*.log" in patterns
    assert "build/" in patterns
    assert "# Comment line" not in patterns


@pytest.mark.unit
def test_language_detector():
    """Test language detection."""
    detector = LanguageDetector(LANGUAGE_MAP)

    assert detector.detect(Path("test.py")) == "python"
    assert detector.detect(Path("test.js")) == "javascript"
    assert detector.detect(Path("test.ts")) == "typescript"
    assert detector.detect(Path("test.unknown")) is None

    assert detector.is_supported(Path("test.py")) is True
    assert detector.is_supported(Path("test.unknown")) is False


@pytest.mark.unit
def test_hash_string():
    """Test string hashing."""
    hash1 = hash_string("hello world")
    hash2 = hash_string("hello world")
    hash3 = hash_string("different")

    assert hash1 == hash2  # Same input = same hash
    assert hash1 != hash3  # Different input = different hash
    assert len(hash1) == 64  # SHA-256 hex = 64 chars


@pytest.mark.unit
def test_hash_file_content(tmp_path):
    """Test file content hashing."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    hash1 = hash_file_content(test_file)
    hash2 = hash_file_content(test_file)

    assert hash1 == hash2
    assert len(hash1) == 64


@pytest.mark.unit
def test_fts_chunker():
    """Test FTS chunking."""
    chunker = FTSChunker(chunk_size=3)

    content = "\n".join([f"Line {i}" for i in range(10)])
    chunks = chunker.chunk_content(content)

    assert len(chunks) > 1  # Should be chunked

    # Verify chunk structure
    for chunk_content, start_line, end_line in chunks:
        assert start_line > 0
        assert end_line >= start_line
        assert isinstance(chunk_content, str)


@pytest.mark.unit
def test_fts_chunker_small_content():
    """Test FTS chunker with content smaller than chunk size."""
    chunker = FTSChunker(chunk_size=100)

    content = "Line 1\nLine 2\nLine 3"
    chunks = chunker.chunk_content(content)

    assert len(chunks) == 1
    chunk_content, start_line, end_line = chunks[0]
    assert start_line == 1
    assert end_line == 3
