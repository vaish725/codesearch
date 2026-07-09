"""
FastAPI REST API for codesearch.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from pathlib import Path
import os

from ..storage.db import Database
from ..query.search import SearchEngine
from ..indexer.indexer import Indexer
from ..config import get_db_path
from ..log import logger


# Pydantic models for API
class SearchRequest(BaseModel):
    query: str = Field(
        ..., description="Search query with filters (def:, class:, import:, lang:, path:)"
    )
    topk: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    context: int = Field(default=0, ge=0, le=10, description="Lines of context around matches")


class SearchResultResponse(BaseModel):
    file_path: str
    line_number: int
    snippet: str
    score: float
    match_type: str
    language: Optional[str] = None
    symbol_name: Optional[str] = None
    symbol_kind: Optional[str] = None
    context_lines: List[str] = []


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResultResponse]
    duration_ms: float


class IndexRequest(BaseModel):
    path: str = Field(..., description="Path to repository or directory to index")


class IndexResponse(BaseModel):
    success: bool
    message: str
    files_scanned: int
    files_new: int
    files_updated: int
    files_deleted: int
    symbols_extracted: int
    duration_seconds: float


class StatsResponse(BaseModel):
    database_path: str
    database_size_mb: float
    total_files: int
    total_symbols: int
    languages: Dict[str, int]
    symbol_types: Dict[str, int]


# Initialize FastAPI app
app = FastAPI(
    title="CodeSearch API",
    description="Local code search engine with symbol awareness",
    version="1.0.0",
)


# Database connection
def get_db():
    """Get database connection."""
    db_path = get_db_path()
    db = Database(db_path)
    conn = db.connect()
    db.initialize_schema()
    return conn


# API Endpoints


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main UI."""
    ui_path = Path(__file__).parent / "ui" / "index.html"
    if ui_path.exists():
        return FileResponse(ui_path)
    return HTMLResponse(
        "<h1>CodeSearch API</h1><p>UI not found. Visit /docs for API documentation.</p>"
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "codesearch"}


@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Execute a search query.

    Supports filters:
    - `def:name` - Find function definitions
    - `class:name` - Find class definitions
    - `import:name` - Find imports
    - `lang:python` - Filter by language
    - `path:src/` - Filter by path
    """
    import time

    start_time = time.time()

    try:
        conn = get_db()
        engine = SearchEngine(conn)

        results = engine.search(request.query, topk=request.topk)

        # Add context if requested
        if request.context > 0:
            for result in results:
                try:
                    file_path = Path(result.file_path)
                    if file_path.exists():
                        with open(file_path, "r", encoding="utf-8") as f:
                            lines = f.readlines()

                        start_line = max(0, result.line_number - request.context - 1)
                        end_line = min(len(lines), result.line_number + request.context)
                        result.context_lines = [
                            f"{i + 1:4d} | {lines[i].rstrip()}" for i in range(start_line, end_line)
                        ]
                except Exception as e:
                    logger.warning(f"Failed to add context for {result.file_path}: {e}")

        duration_ms = (time.time() - start_time) * 1000

        return SearchResponse(
            query=request.query,
            total_results=len(results),
            results=[SearchResultResponse(**r.to_dict()) for r in results],
            duration_ms=round(duration_ms, 2),
        )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/index", response_model=IndexResponse)
async def index_repository(request: IndexRequest):
    """
    Index a repository or directory.
    """
    import time

    start_time = time.time()

    try:
        repo_path = Path(request.path).expanduser().resolve()

        if not repo_path.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: {request.path}")

        db_path = get_db_path()
        db = Database(db_path)
        db.connect()
        db.initialize_schema()

        # Create indexer and run
        indexer = Indexer(db)
        logger.info(f"Indexing repository: {repo_path}")
        stats = indexer.index_repository(repo_path, force=False)

        duration = time.time() - start_time

        return IndexResponse(
            success=True,
            message=f"Successfully indexed {repo_path}",
            files_scanned=stats.get("files_scanned", 0),
            files_new=stats.get("files_new", 0),
            files_updated=stats.get("files_updated", 0),
            files_deleted=stats.get("files_deleted", 0),
            symbols_extracted=stats.get("symbols_extracted", 0),
            duration_seconds=round(duration, 2),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get index statistics.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        db_path = get_db_path()
        db_size = os.path.getsize(db_path) / (1024 * 1024)  # MB

        # Count files
        cursor.execute("SELECT COUNT(*) FROM files")
        total_files = cursor.fetchone()[0]

        # Count symbols
        cursor.execute("SELECT COUNT(*) FROM symbols")
        total_symbols = cursor.fetchone()[0]

        # Count by language
        cursor.execute("""
            SELECT language, COUNT(*) as count
            FROM files
            GROUP BY language
            ORDER BY count DESC
        """)
        languages = {row[0]: row[1] for row in cursor.fetchall()}

        # Count by symbol type
        cursor.execute("""
            SELECT kind, COUNT(*) as count
            FROM symbols
            GROUP BY kind
            ORDER BY count DESC
        """)
        symbol_types = {row[0]: row[1] for row in cursor.fetchall()}

        return StatsResponse(
            database_path=str(db_path),
            database_size_mb=round(db_size, 2),
            total_files=total_files,
            total_symbols=total_symbols,
            languages=languages,
            symbol_types=symbol_types,
        )

    except Exception as e:
        logger.error(f"Stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/index")
async def purge_index():
    """
    Clear the entire index.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM symbols")
        cursor.execute("DELETE FROM fts_code")
        cursor.execute("DELETE FROM files")

        conn.commit()

        return {"success": True, "message": "Index cleared successfully"}

    except Exception as e:
        logger.error(f"Purge failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Mount static files (for CSS, JS)
static_dir = Path(__file__).parent / "ui" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
