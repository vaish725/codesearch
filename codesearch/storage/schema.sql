-- Database schema for codesearch
-- SQLite with FTS5 for full-text search

-- Files table: metadata for indexed files
CREATE TABLE IF NOT EXISTS files (
    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    language TEXT,
    mtime INTEGER NOT NULL,
    size_bytes INTEGER NOT NULL,
    content_hash TEXT NOT NULL
);

-- Index for language filtering
CREATE INDEX IF NOT EXISTS idx_files_language ON files(language);

-- Index for path lookups
CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);

-- Symbols table: extracted symbols from AST parsing
CREATE TABLE IF NOT EXISTS symbols (
    symbol_id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,  -- class, function, method, import
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    signature TEXT,
    extra_json TEXT,  -- Optional JSON for additional metadata
    FOREIGN KEY (file_id) REFERENCES files(file_id) ON DELETE CASCADE
);

-- Indexes for symbol queries
CREATE INDEX IF NOT EXISTS idx_symbols_name_kind ON symbols(name, kind);
CREATE INDEX IF NOT EXISTS idx_symbols_file_id ON symbols(file_id);
CREATE INDEX IF NOT EXISTS idx_symbols_kind ON symbols(kind);

-- FTS5 table for full-text search
-- Using chunked approach for better performance
CREATE VIRTUAL TABLE IF NOT EXISTS fts_code USING fts5(
    file_id UNINDEXED,
    chunk_id UNINDEXED,
    content,
    start_line UNINDEXED,
    end_line UNINDEXED,
    tokenize='porter unicode61'
);

-- Metadata table for tracking index state
CREATE TABLE IF NOT EXISTS index_metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);
