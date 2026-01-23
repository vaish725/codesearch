# Architecture Documentation

## Overview

Codesearch is a local-first code search engine that provides GitHub-scale search capabilities with symbol awareness.

## System Architecture

```
┌─────────────────────────────────────────────────┐
│                    CLI Layer                     │
│              (codesearch command)                │
└─────────────────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
┌────────────────┐         ┌────────────────┐
│    Indexer     │         │     Query      │
│   Components   │         │   Components   │
└────────────────┘         └────────────────┘
        │                           │
        ├─ Scanner                  ├─ Parser
        ├─ Language Detector        ├─ Search Engine
        ├─ Symbol Extractors        ├─ Ranker
        └─ FTS Indexer              └─ Result Formatter
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
┌────────────────┐         ┌────────────────┐
│  Storage Layer │         │  Symbol Store  │
│  (SQLite FTS5) │         │  (SQLite)      │
└────────────────┘         └────────────────┘
```

## Core Components

### 1. Indexer

**Purpose**: Scan repositories and build searchable index

**Components**:
- `FileScanner`: Recursively traverses directories
- `LanguageDetector`: Identifies programming languages
- `SymbolExtractor`: Extracts symbols via AST parsing
- `FTSIndexer`: Populates full-text search tables

**Flow**:
1. Scan repository for files
2. Filter out excluded directories and binary files
3. Detect language for each file
4. Extract symbols (if supported language)
5. Chunk content and index into FTS
6. Store metadata and symbols in database

### 2. Query Engine

**Purpose**: Execute searches and return ranked results

**Components**:
- `QueryParser`: Parses query syntax (filters, operators)
- `SearchEngine`: Executes queries against database
- `ResultRanker`: Applies hybrid ranking strategy

**Flow**:
1. Parse query into filters and text
2. Execute FTS query with filters
3. Execute symbol queries if applicable
4. Merge and rank results
5. Extract snippets
6. Format output

### 3. Storage Layer

**Purpose**: Persistent storage using SQLite

**Tables**:
- `files`: File metadata and hashes
- `symbols`: Extracted symbols with locations
- `fts_code`: Full-text search index (FTS5)
- `index_metadata`: Index state tracking

**Optimizations**:
- WAL mode for concurrency
- Strategic indexes on common queries
- Chunked FTS for better performance

## Data Flow

### Indexing Flow

```
Repository → Scanner → Language Detection → Symbol Extraction
                ↓                                    ↓
          File Metadata → [Database] ← Symbols Store
                ↓
          FTS Indexing → [fts_code table]
```

### Query Flow

```
User Query → Parse Filters → Execute FTS Search
                ↓                     ↓
          Symbol Search         Text Search
                ↓                     ↓
              Merge Results → Rank → Format → Output
```

## Incremental Indexing Strategy

1. **Hash-based Change Detection**
   - Compute SHA-256 of file content
   - Compare with stored hash
   - Re-index only changed files

2. **Update Process**
   - Scan repository
   - For each file:
     - New file → Index
     - Changed file → Delete old + Re-index
     - Deleted file → Remove from DB
   - Report statistics

## Symbol Extraction

### Python (AST-based)

- Uses built-in `ast` module
- Extracts:
  - Classes, functions, methods
  - Imports and import-from statements
  - Signatures with parameters
  - Docstrings (optional)

### JavaScript/TypeScript (Tree-sitter)

- Uses Tree-sitter parser
- Extracts:
  - Function declarations
  - Class declarations
  - Exports (named and default)
  - Import statements

## Ranking Strategy

**Hybrid Ranking Formula**:

```
final_score = fts_base_score 
            + (is_exact_symbol_match × 10)
            + (is_definition × 5)
            + (match_in_signature × 3)
```

**Factors**:
- FTS relevance (BM25-based)
- Symbol match type
- Result location (definitions ranked higher)
- Match context (signature, comment, code)

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Indexing Speed | 200k LOC in <5 min | Initial version |
| Query p50 | <100ms | On warmed cache |
| Query p95 | <300ms | Complex queries |
| Index Size | ~10-20% of source | With symbols |

## Future Enhancements

### Phase 7+ (Stretch)

1. **Reference Finding**
   - Approximate "find all references"
   - Heuristic filtering

2. **Semantic Search**
   - Local embeddings (Ollama)
   - Hybrid retrieval

3. **API Server**
   - FastAPI-based REST API
   - Still local-only

4. **IDE Integration**
   - VS Code extension
   - Real-time search

## Design Decisions

### Why SQLite?

- ✅ Zero-config, embedded database
- ✅ Excellent FTS5 support
- ✅ ACID guarantees
- ✅ Single-file portability
- ✅ Fast for local workloads

### Why AST over Regex?

- ✅ Accurate symbol extraction
- ✅ Understands code structure
- ✅ Handles complex cases
- ❌ Requires per-language parsers

### Why Chunking?

- ✅ Better FTS performance
- ✅ Precise snippet extraction
- ✅ Smaller index updates
- ❌ Slightly more complex

## Testing Strategy

1. **Unit Tests**
   - Query parser
   - Symbol extractors
   - Ranking logic

2. **Integration Tests**
   - End-to-end indexing
   - Query execution
   - Incremental updates

3. **Benchmarks**
   - Real-world repositories
   - Performance regression tracking

## Security Considerations

- ✅ No network calls required
- ✅ Never executes repository code
- ✅ Path sanitization to prevent traversal
- ✅ Safe file reading with error handling
- ✅ Local-only operation

## Development Roadmap

See [PRD](../prd.md) for detailed phase-by-phase implementation plan.

---

*Last updated: Phase 0 - Initial architecture*
