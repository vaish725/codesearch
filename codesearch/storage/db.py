"""
Database connection and management.
"""

import sqlite3
from pathlib import Path
from typing import Optional


class Database:
    """
    Manages SQLite database connection and initialization.
    """

    def __init__(self, db_path: Path):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """
        Open database connection with optimizations.

        Returns:
            Database connection
        """
        if self.conn is None:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row

            # Enable WAL mode for better concurrency
            self.conn.execute("PRAGMA journal_mode=WAL")

            # Performance optimizations
            self.conn.execute("PRAGMA synchronous=NORMAL")
            self.conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
            self.conn.execute("PRAGMA temp_store=MEMORY")

        return self.conn

    def initialize_schema(self):
        """
        Create tables and indexes if they don't exist.
        """
        schema_file = Path(__file__).parent / "schema.sql"

        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")

        with open(schema_file, "r") as f:
            schema_sql = f.read()

        conn = self.connect()
        try:
            conn.executescript(schema_sql)
            conn.commit()

            # Set initial metadata
            conn.execute(
                "INSERT OR REPLACE INTO index_metadata (key, value) VALUES (?, ?)",
                ("schema_version", "1.0"),
            )
            conn.execute(
                "INSERT OR REPLACE INTO index_metadata (key, value) VALUES (?, ?)",
                ("created_at", str(int(Path.home().stat().st_ctime))),
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to initialize schema: {e}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def get_stats(self) -> dict:
        """
        Get index statistics.

        Returns:
            Dictionary with statistics
        """
        conn = self.connect()
        cursor = conn.cursor()

        stats = {}

        # File counts
        cursor.execute("SELECT COUNT(*) FROM files")
        stats["total_files"] = cursor.fetchone()[0]

        # Files by language
        cursor.execute("""
            SELECT language, COUNT(*) as count
            FROM files
            GROUP BY language
            ORDER BY count DESC
        """)
        stats["files_by_language"] = dict(cursor.fetchall())

        # Symbol counts
        cursor.execute("SELECT COUNT(*) FROM symbols")
        stats["total_symbols"] = cursor.fetchone()[0]

        # Symbols by kind
        cursor.execute("""
            SELECT kind, COUNT(*) as count
            FROM symbols
            GROUP BY kind
            ORDER BY count DESC
        """)
        stats["symbols_by_kind"] = dict(cursor.fetchall())

        # Database size
        cursor.execute(
            "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"
        )
        stats["db_size_bytes"] = cursor.fetchone()[0]

        # Metadata
        cursor.execute("SELECT key, value FROM index_metadata")
        stats["metadata"] = dict(cursor.fetchall())

        return stats

    def clear_index(self):
        """Clear all indexed data."""
        conn = self.connect()
        try:
            conn.execute("DELETE FROM symbols")
            conn.execute("DELETE FROM fts_code")
            conn.execute("DELETE FROM files")
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to clear index: {e}")
