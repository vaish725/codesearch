"""
Database migration utilities.

Optional component for future schema changes.
"""

from typing import List
import sqlite3


class Migration:
    """Represents a database migration."""
    
    def __init__(self, version: int, description: str, sql: str):
        """
        Initialize migration.
        
        Args:
            version: Migration version number
            description: Description of the migration
            sql: SQL statements to execute
        """
        self.version = version
        self.description = description
        self.sql = sql


class MigrationManager:
    """
    Manages database schema migrations.
    
    Optional component - will be implemented if needed.
    """
    
    def __init__(self, db_connection: sqlite3.Connection):
        """
        Initialize migration manager.
        
        Args:
            db_connection: Database connection
        """
        self.conn = db_connection
        self._ensure_migrations_table()
    
    def _ensure_migrations_table(self):
        """Create migrations tracking table if it doesn't exist."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                description TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
    
    def get_current_version(self) -> int:
        """Get the current schema version."""
        cursor = self.conn.execute(
            "SELECT MAX(version) FROM schema_migrations"
        )
        result = cursor.fetchone()[0]
        return result if result is not None else 0
    
    def apply_migrations(self, migrations: List[Migration]):
        """
        Apply pending migrations.
        
        Args:
            migrations: List of migrations to apply
        """
        current_version = self.get_current_version()
        
        for migration in migrations:
            if migration.version > current_version:
                print(f"Applying migration {migration.version}: {migration.description}")
                self.conn.executescript(migration.sql)
                self.conn.execute(
                    "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                    (migration.version, migration.description)
                )
                self.conn.commit()
