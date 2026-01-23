# Examples

This directory contains example scripts demonstrating how to use codesearch.

## Available Examples

### `basic_usage.py`
Demonstrates basic codesearch functionality:
- Database initialization
- Repository indexing
- Text search queries
- Symbol-aware queries

**Run:**
```bash
python examples/basic_usage.py
```

### Future Examples (Coming Soon)

- `advanced_queries.py` - Complex query patterns
- `incremental_indexing.py` - Incremental update examples
- `custom_filters.py` - Custom filtering and ranking
- `api_integration.py` - API server usage (Phase 7+)

## Integration in Your Code

```python
from codesearch.storage.db import Database
from codesearch.query.parser import QueryParser
from codesearch.config import get_db_path

# Initialize
db = Database(get_db_path())
db.connect()

# Parse a query
parser = QueryParser()
parsed = parser.parse("def:main lang:python")

# Execute search (Phase 1+)
# results = search_engine.search(parsed)
```

## Documentation

For complete API documentation, see [docs/architecture.md](../docs/architecture.md).
