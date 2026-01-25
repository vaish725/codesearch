# Web UI Guide

## 🎯 Overview

The CodeSearch Web UI provides a **beginner-friendly, visual interface** for code search. Perfect for:
- Developers new to code search engines
- Teams preferring GUI over CLI
- Quick demos and presentations
- Visual exploration of large codebases

## 🚀 Getting Started

### Installation

```bash
# Install web dependencies
pip install -e ".[web]"
```

### Launch Options

#### Option 1: Quick Start Script (Easiest)
```bash
./start-web-ui.sh
```

#### Option 2: Python Command
```bash
python3 -m codesearch.web.server
```

#### Option 3: Installed Command
```bash
codesearch-web
```

The server will:
1. Start on `http://127.0.0.1:8080`
2. Automatically open your browser
3. Display interactive API docs at `/docs`

## 🔍 Using the Web UI

### Dashboard (Stats Bar)

The top bar shows your index status:
- **Files Indexed**: Total number of files in the database
- **Symbols**: Functions, classes, imports extracted
- **Index Size**: Database size on disk

### Search Tab

**Basic Search:**
1. Type your query in the search box
2. Adjust result count (default: 10)
3. Set context lines (default: 2)
4. Click "Search" or press Enter

**Filter Examples:**
```
def:authenticate          # Find function definitions
class:UserController      # Find class definitions  
import:react              # Find import statements
lang:python               # Filter by language
path:src/                 # Filter by path
```

**Combined Filters:**
```
authenticate lang:python def:        # Python functions with "authenticate"
Database class: lang:typescript      # TypeScript Database classes
pytest import: path:tests/           # pytest imports in tests/
```

### Index Tab

**Index a Repository:**
1. Enter the absolute path (e.g., `/Users/name/projects/myrepo`)
2. Click "Index"
3. Watch real-time progress
4. See detailed stats after completion

**Quick Actions:**
- **Index Current Directory**: Index the codesearch project itself
- **Clear Index**: Remove all indexed data (requires confirmation)

## 🛠️ REST API

The web UI is powered by a FastAPI backend. Access the interactive API documentation:

**API Docs**: http://127.0.0.1:8080/docs

### Endpoints

#### `POST /api/search`
Search the codebase

**Request:**
```json
{
  "query": "def:main",
  "topk": 10,
  "context": 2
}
```

**Response:**
```json
{
  "query": "def:main",
  "total_results": 5,
  "duration_ms": 1.23,
  "results": [
    {
      "file_path": "main.py",
      "line_number": 42,
      "snippet": "def main():",
      "score": 18.5,
      "match_type": "symbol:function",
      "language": "python",
      "symbol_name": "main",
      "symbol_kind": "function"
    }
  ]
}
```

#### `POST /api/index`
Index a repository

**Request:**
```json
{
  "path": "/Users/name/projects/myrepo"
}
```

#### `GET /api/stats`
Get index statistics

**Response:**
```json
{
  "database_path": "/Users/name/.codesearch/index.db",
  "database_size_mb": 2.45,
  "total_files": 127,
  "total_symbols": 892,
  "languages": {
    "python": 85,
    "javascript": 42
  },
  "symbol_types": {
    "function": 456,
    "class": 123,
    "import": 313
  }
}
```

#### `DELETE /api/index`
Clear the entire index

## 🔌 Integration Examples

### Python Script
```python
import requests

# Search
response = requests.post('http://127.0.0.1:8080/api/search', json={
    'query': 'def:main lang:python',
    'topk': 5
})
results = response.json()

for result in results['results']:
    print(f"{result['file_path']}:{result['line_number']}")
    print(f"  {result['snippet']}")
```

### cURL
```bash
# Search
curl -X POST http://127.0.0.1:8080/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "def:authenticate", "topk": 5}'

# Index
curl -X POST http://127.0.0.1:8080/api/index \
  -H "Content-Type: application/json" \
  -d '{"path": "/Users/name/myproject"}'

# Stats
curl http://127.0.0.1:8080/api/stats
```

### JavaScript (Browser)
```javascript
// Search code
async function search(query) {
  const response = await fetch('http://127.0.0.1:8080/api/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, topk: 10, context: 2 })
  });
  return await response.json();
}

// Usage
const results = await search('class:Database');
console.log(`Found ${results.total_results} results in ${results.duration_ms}ms`);
```

## 💡 Tips & Tricks

### Performance
- The web UI uses the same optimized SQLite backend as the CLI
- Queries typically return in <1ms
- The index is shared between CLI and web UI

### Workflow
```bash
# Index via CLI (faster for large repos)
codesearch index ~/projects/big-repo

# Search via Web UI (easier to explore)
codesearch-web
```

### Security
- The server binds to `127.0.0.1` (localhost only)
- No external network access
- Safe for local development

### Customization
Want to customize the UI or add features? The code is simple:
- `codesearch/web/api.py` - FastAPI backend (280 lines)
- `codesearch/web/ui/index.html` - Frontend (single HTML file, ~800 lines)
- `codesearch/web/server.py` - Launch script (60 lines)

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Change the port in codesearch/web/server.py
port = 8081  # or any free port
```

### Dependencies Missing
```bash
pip install -e ".[web]"
```

### Index Not Found
The web UI and CLI share `~/.codesearch/index.db`. If empty:
```bash
codesearch index /path/to/your/code
```

## 🎓 Learning Resources

- **CLI Guide**: See main README.md
- **API Reference**: http://127.0.0.1:8080/docs (while server running)
- **Architecture**: See `docs/architecture.md`
