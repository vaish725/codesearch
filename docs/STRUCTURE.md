# Project Structure

This document explains the optimized folder structure of codesearch.

## 📁 Root Structure

```
codesearch/                          # Root project directory
├── codesearch/                      # Main package (flat, not src/)
│   ├── __init__.py                 # Package initialization
│   ├── cli.py                      # CLI entry point
│   ├── config.py                   # Configuration settings
│   ├── log.py                      # Logging utilities
│   │
│   ├── indexer/                    # Indexing subsystem
│   │   ├── __init__.py
│   │   ├── scanner.py              # File scanner
│   │   ├── hasher.py               # Content hashing
│   │   ├── language.py             # Language detection
│   │   ├── fts.py                  # FTS chunking
│   │   └── symbols/                # Symbol extractors
│   │       ├── __init__.py
│   │       ├── python_ast.py       # Python AST parser
│   │       └── treesitter_js.py    # JS/TS Tree-sitter
│   │
│   ├── query/                      # Query subsystem
│   │   ├── __init__.py
│   │   ├── parser.py               # Query parser
│   │   └── search.py               # Search engine + hybrid ranking
│   │
│   ├── storage/                    # Storage subsystem
│   │   ├── __init__.py
│   │   ├── db.py                   # Database manager
│   │   ├── schema.sql              # SQL schema
│   │   └── migrations.py           # Schema migrations
│   │
│   └── utils/                      # Utilities
│       ├── __init__.py
│       ├── text.py                 # Text processing
│       └── snippets.py             # Snippet extraction
│
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── conftest.py                 # Shared fixtures
│   ├── unit/                       # Unit tests
│   │   ├── __init__.py
│   │   ├── test_query_parser.py
│   │   └── test_scanner.py
│   └── integration/                # Integration tests
│       └── __init__.py
│
├── examples/                       # Usage examples
│   ├── README.md
│   └── basic_usage.py
│
├── scripts/                        # Development scripts
│   ├── setup_dev.sh               # Dev environment setup
│   ├── run_tests.sh               # Test runner
│   └── benchmark.sh               # Benchmark runner
│
├── benchmarks/                     # Performance benchmarks
│   └── README.md
│
├── docs/                          # Documentation
│   ├── architecture.md            # Architecture guide
│   └── STRUCTURE.md               # This file
│
├── pyproject.toml                 # Project metadata
├── MANIFEST.in                    # Package manifest
├── Makefile                       # Development tasks
├── README.md                      # Project overview
├── CONTRIBUTING.md                # Contribution guide
├── CHANGELOG.md                   # Version history
├── LICENSE                        # MIT License
├── .gitignore                     # Git ignore rules
└── .codesearchignore             # Indexing ignore rules
```

## 🎯 Design Principles

### 1. Flat Package Structure (Not `src/`)

**Why we use `codesearch/` instead of `src/codesearch/`:**

✅ **Simpler imports:**
```python
from codesearch.query.parser import QueryParser  # Clean
# vs
from src.codesearch.query.parser import QueryParser  # Extra nesting
```

✅ **Better for development:**
- Direct imports work without PYTHONPATH manipulation
- IDE autocomplete works better
- Testing is simpler

✅ **Modern Python standard:**
- Poetry, Hatch, and other modern tools prefer flat layout
- Aligns with most popular Python projects

### 2. Separated Test Types

```
tests/
├── unit/           # Fast, isolated tests
└── integration/    # Slower, system tests
```

**Benefits:**
- Run fast tests frequently during development
- Run integration tests in CI/CD
- Clear organization by test type

### 3. Subsystem Organization

Each major component has its own directory:

- **`indexer/`**: All indexing logic (scanning, parsing, symbol extraction)
- **`query/`**: All query processing (parsing, searching, ranking)
- **`storage/`**: All database interaction (schema, queries, migrations)
- **`utils/`**: Shared utilities (text, snippets, helpers)

**Why:**
- Clear separation of concerns
- Easy to navigate
- Scales well as project grows
- Each subsystem can be tested independently

### 4. Developer-Friendly Scripts

```
scripts/
├── setup_dev.sh    # One command setup
├── run_tests.sh    # Test with coverage
└── benchmark.sh    # Performance testing
```

**Benefits:**
- Standardized workflows
- Easy onboarding for new contributors
- Executable scripts (chmod +x)

### 5. Comprehensive Documentation

```
docs/
├── architecture.md  # System design
└── STRUCTURE.md     # This file
```

Plus root-level docs:
- `README.md`: User-facing overview
- `CONTRIBUTING.md`: Developer guide
- `CHANGELOG.md`: Version history

## 📊 Subsystem Breakdown

### Indexer Subsystem

```
indexer/
├── scanner.py       # File traversal, exclusions
├── hasher.py        # Content hashing (SHA-256)
├── language.py      # Detect language by extension
├── fts.py           # FTS chunking logic
└── symbols/         # AST/Tree-sitter parsers
```

**Responsibilities:**
- Scan repository files
- Detect programming languages
- Extract symbols (classes, functions, etc.)
- Prepare content for FTS indexing

### Query Subsystem

```
query/
├── parser.py        # Parse query syntax
└── search.py        # Execute searches + hybrid scoring
```

**Responsibilities:**
- Parse user queries (operators, filters)
- Execute FTS and SQL queries
- Rank results with hybrid scoring
- Format output

### Storage Subsystem

```
storage/
├── db.py            # SQLite connection manager
├── schema.sql       # Database schema
└── migrations.py    # Schema versioning
```

**Responsibilities:**
- Database initialization
- Schema management
- Query execution
- Data persistence

## 🔧 Development Workflow

### Setup
```bash
./scripts/setup_dev.sh
```

### Testing
```bash
make test              # All tests
make test-unit         # Fast tests only
make test-int          # Integration tests
make coverage          # With coverage report
```

### Formatting
```bash
make format            # Auto-format code
make lint              # Check formatting
```

### Common Tasks
```bash
make help              # List all commands
make clean             # Remove artifacts
make benchmark         # Run performance tests
```

## 📦 Package Distribution

### Files Included in Distribution

Controlled by `MANIFEST.in`:
- Source code (`codesearch/`)
- SQL schema files
- Documentation (`docs/`)
- License and readme

### Files Excluded

Via `.gitignore`:
- Bytecode (`__pycache__`, `*.pyc`)
- Virtual environments (`venv/`)
- Build artifacts (`dist/`, `build/`)
- Test artifacts (`.pytest_cache/`, `.coverage`)
- IDE files (`.vscode/`, `.idea/`)

## 🎨 Code Organization Best Practices

### Module Size
- Keep modules under 500 lines when possible
- Split large modules into submodules
- Use clear, descriptive names

### Import Style
```python
# Standard library
import os
from pathlib import Path

# Third-party
import pytest

# Local imports
from codesearch.config import DEFAULT_EXCLUDE_DIRS
from codesearch.query.parser import QueryParser
```

### File Naming
- Snake_case for all files: `query_parser.py`
- Matching class names: `QueryParser` in `parser.py`
- Test prefix: `test_parser.py`

## 🚀 Scaling Considerations

As the project grows:

### When to Add New Subdirectories
- **5+ related modules** → Create subdirectory
- **Complex feature** → Separate subsystem
- **Multiple implementations** → Strategy pattern with subdirectory

### When to Split Modules
- **>500 lines** → Consider splitting
- **Multiple responsibilities** → Separate concerns
- **Hard to test** → Extract dependencies

### When to Add New Subsystems
- **Major feature area** → New top-level directory
- **Clear boundaries** → Independent subsystem
- **Reusable component** → Separate module

## 📚 References

This structure follows:
- [PEP 8](https://peps.python.org/pep-0008/) - Style Guide
- [Python Packaging Guide](https://packaging.python.org/)
- Modern Python project best practices
- Popular open-source Python projects (FastAPI, httpx, pytest)

## ❓ FAQ

**Q: Why not use `src/` layout?**
A: Flat layout is simpler, aligns with modern tools, and provides better DX.

**Q: Why separate unit and integration tests?**
A: Enables running fast tests frequently, slower tests in CI.

**Q: Why shell scripts instead of Python scripts?**
A: Shell scripts are universal, don't require Python imports, work before setup.

**Q: Why Makefile?**
A: Common interface, familiar to developers, works cross-platform with make.

---

**Last Updated:** Phase 0 Restructuring - January 22, 2026
