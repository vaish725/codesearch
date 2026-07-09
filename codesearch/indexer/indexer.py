"""
Main indexer orchestration.

Coordinates scanning, language detection, and FTS indexing.
"""

from pathlib import Path
from typing import Any, Dict, Set
import time

from ..storage.db import Database
from ..config import (
    DEFAULT_EXCLUDE_DIRS,
    DEFAULT_EXCLUDE_PATTERNS,
    MAX_FILE_SIZE,
    LANGUAGE_MAP,
    DB_BATCH_SIZE,
    FTS_CHUNK_SIZE,
)
from .scanner import FileScanner
from .language import LanguageDetector
from .hasher import hash_file_content
from .fts import FTSChunker
from .symbols.python_ast import PythonASTExtractor
from .symbols.treesitter_js import JSSymbolExtractor
from ..log import logger


class Indexer:
    """
    Main indexer for codesearch.

    Orchestrates the indexing process:
    1. Scan repository files
    2. Detect languages
    3. Read and chunk content
    4. Index into SQLite FTS
    5. Extract symbols (Python, JavaScript, TypeScript)
    """

    def __init__(self, db: Database):
        """
        Initialize the indexer.

        Args:
            db: Database connection
        """
        self.db = db
        self.language_detector = LanguageDetector(LANGUAGE_MAP)
        self.fts_chunker = FTSChunker(FTS_CHUNK_SIZE)
        self.python_extractor = PythonASTExtractor()
        self.js_extractor = JSSymbolExtractor()

    def _get_existing_files(self, conn) -> Dict[str, tuple]:
        """
        Get all existing files from database with their hashes.

        Args:
            conn: Database connection

        Returns:
            Dict mapping file paths to (file_id, content_hash) tuples
        """
        cursor = conn.execute("SELECT file_id, path, content_hash FROM files")
        return {row[1]: (row[0], row[2]) for row in cursor.fetchall()}

    def _delete_file_from_index(self, conn, file_id: int) -> None:
        """
        Delete a file and all its associated data from the index.

        Args:
            conn: Database connection
            file_id: File ID to delete
        """
        # FTS entries are deleted by trigger
        conn.execute("DELETE FROM fts_code WHERE file_id = ?", (file_id,))
        conn.execute("DELETE FROM symbols WHERE file_id = ?", (file_id,))
        conn.execute("DELETE FROM files WHERE file_id = ?", (file_id,))

    def index_repository(self, repo_path: Path, force: bool = False) -> Dict[str, Any]:
        """
        Index a repository with incremental update support.

        Args:
            repo_path: Path to repository root
            force: If True, re-index all files (ignore hashes)

        Returns:
            Statistics about the indexing operation
        """
        start_time = time.time()
        repo_path = Path(repo_path).resolve()

        if not repo_path.exists():
            raise FileNotFoundError(f"Repository not found: {repo_path}")

        if not repo_path.is_dir():
            raise ValueError(f"Not a directory: {repo_path}")

        logger.info(f"Starting {'full' if force else 'incremental'} index of: {repo_path}")

        # Initialize scanner
        scanner = FileScanner(
            root_path=repo_path,
            exclude_dirs=DEFAULT_EXCLUDE_DIRS,
            exclude_patterns=DEFAULT_EXCLUDE_PATTERNS,
            max_file_size=MAX_FILE_SIZE,
        )

        # Statistics
        stats: Dict[str, Any] = {
            "files_scanned": 0,
            "files_new": 0,
            "files_updated": 0,
            "files_unchanged": 0,
            "files_deleted": 0,
            "files_skipped": 0,
            "files_failed": 0,
            "chunks_created": 0,
        }

        conn = self.db.connect()
        batch_count = 0

        # Get existing files from database (for incremental indexing)
        existing_files = {} if force else self._get_existing_files(conn)
        scanned_paths: Set[str] = set()

        try:
            # Scan and index files
            for file_path in scanner.scan():
                stats["files_scanned"] += 1

                try:
                    # Detect language
                    language = self.language_detector.detect(file_path)
                    if not language:
                        stats["files_skipped"] += 1
                        continue

                    # Read file content
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                    except Exception as e:
                        logger.warning(f"Failed to read {file_path}: {e}")
                        stats["files_failed"] += 1
                        continue

                    # Get file metadata
                    file_stat = file_path.stat()
                    mtime = int(file_stat.st_mtime)
                    size_bytes = file_stat.st_size
                    content_hash = hash_file_content(file_path)

                    # Make path relative to repo root
                    try:
                        rel_path = str(file_path.relative_to(repo_path))
                    except ValueError:
                        rel_path = str(file_path)

                    scanned_paths.add(rel_path)

                    # Check if file needs indexing (incremental logic)
                    is_new = rel_path not in existing_files
                    needs_update = False

                    if not is_new:
                        file_id, old_hash = existing_files[rel_path]
                        needs_update = old_hash != content_hash

                        if not needs_update:
                            # File unchanged, skip indexing
                            stats["files_unchanged"] += 1
                            continue

                    # File is new or changed, index it
                    if is_new:
                        stats["files_new"] += 1
                    else:
                        stats["files_updated"] += 1
                        # Delete old FTS and symbol entries for updated file
                        conn.execute("DELETE FROM fts_code WHERE file_id = ?", (file_id,))
                        conn.execute("DELETE FROM symbols WHERE file_id = ?", (file_id,))

                    # Insert or update file record
                    cursor = conn.execute(
                        """
                        INSERT INTO files (path, language, mtime, size_bytes, content_hash)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(path) DO UPDATE SET
                            language=excluded.language,
                            mtime=excluded.mtime,
                            size_bytes=excluded.size_bytes,
                            content_hash=excluded.content_hash
                        RETURNING file_id
                        """,
                        (rel_path, language, mtime, size_bytes, content_hash),
                    )

                    result = cursor.fetchone()
                    if result:
                        file_id = result[0]
                    else:
                        # Fallback for older SQLite versions without RETURNING
                        cursor = conn.execute(
                            "SELECT file_id FROM files WHERE path = ?", (rel_path,)
                        )
                        file_id = cursor.fetchone()[0]

                    # Chunk content and index into FTS
                    chunks = self.fts_chunker.chunk_content(content)
                    for chunk_id, (chunk_content, start_line, end_line) in enumerate(chunks):
                        conn.execute(
                            """
                            INSERT INTO fts_code (file_id, chunk_id, content, start_line, end_line)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (file_id, chunk_id, chunk_content, start_line, end_line),
                        )
                        stats["chunks_created"] += 1

                    # Extract and store symbols
                    symbols: list = []
                    if language == "python":
                        symbols = self.python_extractor.extract_from_source(content)
                    elif language in ["javascript", "typescript"]:
                        symbols = self.js_extractor.extract_from_source(content)

                    for symbol in symbols:
                        conn.execute(
                            """
                            INSERT INTO symbols
                                (file_id, name, kind, start_line, end_line, signature)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                file_id,
                                symbol.name,
                                symbol.kind,
                                symbol.start_line,
                                symbol.end_line,
                                symbol.signature,
                            ),
                        )
                    stats["symbols_extracted"] = stats.get("symbols_extracted", 0) + len(symbols)

                    batch_count += 1

                    # Commit in batches
                    if batch_count >= DB_BATCH_SIZE:
                        conn.commit()
                        indexed_total = stats["files_new"] + stats["files_updated"]
                        logger.info(
                            f"Indexed {indexed_total} files so far "
                            f"({stats['files_new']} new, {stats['files_updated']} updated)..."
                        )
                        batch_count = 0

                except Exception as e:
                    logger.error(f"Error indexing {file_path}: {e}")
                    stats["files_failed"] += 1
                    continue

            # Handle deleted files (in DB but not scanned)
            if not force:
                for rel_path, (file_id, _) in existing_files.items():
                    if rel_path not in scanned_paths:
                        logger.debug(f"Removing deleted file: {rel_path}")
                        self._delete_file_from_index(conn, file_id)
                        stats["files_deleted"] += 1

            # Final commit
            conn.commit()

            # Calculate duration
            duration = time.time() - start_time
            stats["duration_seconds"] = round(duration, 2)

            # Calculate total indexed (new + updated)
            stats["files_indexed"] = stats["files_new"] + stats["files_updated"]

            # Log summary
            if force:
                logger.info(
                    f"Full indexing complete: {stats['files_indexed']} files "
                    f"indexed in {duration:.2f}s"
                )
            else:
                logger.info(
                    f"Incremental indexing complete in {duration:.2f}s: "
                    f"{stats['files_new']} new, {stats['files_updated']} updated, "
                    f"{stats['files_unchanged']} unchanged, {stats['files_deleted']} deleted"
                )

            return stats

        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Indexing failed: {e}")
