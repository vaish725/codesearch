"""
Benchmark harness for codesearch performance testing.

Tests indexing speed and query latency on real repositories.
"""
import sys
import time
import json
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any
import statistics

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from codesearch.storage.db import Database
from codesearch.indexer.indexer import Indexer
from codesearch.query.search import SearchEngine


class BenchmarkResult:
    """Container for benchmark results."""
    
    def __init__(self, repo_name: str, repo_path: str):
        self.repo_name = repo_name
        self.repo_path = repo_path
        self.repo_size_loc = 0
        self.repo_size_mb = 0
        self.file_count = 0
        self.symbol_count = 0
        
        # Indexing metrics
        self.index_time_seconds = 0.0
        self.index_size_mb = 0.0
        
        # Query metrics
        self.query_latencies = []
        self.query_p50_ms = 0.0
        self.query_p95_ms = 0.0
        self.query_p99_ms = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "repo_name": self.repo_name,
            "repo_path": self.repo_path,
            "repo_size_loc": self.repo_size_loc,
            "repo_size_mb": round(self.repo_size_mb, 2),
            "file_count": self.file_count,
            "symbol_count": self.symbol_count,
            "index_time_seconds": round(self.index_time_seconds, 2),
            "index_size_mb": round(self.index_size_mb, 2),
            "query_p50_ms": round(self.query_p50_ms, 2),
            "query_p95_ms": round(self.query_p95_ms, 2),
            "query_p99_ms": round(self.query_p99_ms, 2),
        }


def count_lines_of_code(repo_path: Path) -> Tuple[int, float]:
    """Count lines of code and size in MB."""
    total_lines = 0
    total_bytes = 0
    
    extensions = {'.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs', '.cpp', '.c', '.h'}
    
    for file_path in repo_path.rglob('*'):
        if file_path.is_file() and file_path.suffix in extensions:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    total_lines += len(lines)
                    total_bytes += file_path.stat().st_size
            except Exception:
                continue
    
    return total_lines, total_bytes / (1024 * 1024)


def benchmark_indexing(repo_path: Path, db_path: Path) -> Tuple[float, int, int]:
    """
    Benchmark indexing performance.
    
    Returns: (time_seconds, file_count, symbol_count)
    """
    # Initialize database
    db = Database(db_path)
    db.connect()
    db.initialize_schema()
    
    # Time the indexing
    indexer = Indexer(db)
    
    start_time = time.perf_counter()
    stats = indexer.index_repository(repo_path, force=True)
    end_time = time.perf_counter()
    
    elapsed = end_time - start_time
    
    # Get stats
    db_stats = db.get_stats()
    file_count = db_stats.get('total_files', 0)
    symbol_count = db_stats.get('total_symbols', 0)
    
    db.close()
    
    return elapsed, file_count, symbol_count


def benchmark_queries(db_path: Path, queries: List[str], runs_per_query: int = 10) -> List[float]:
    """
    Benchmark query performance.
    
    Args:
        db_path: Path to the database
        queries: List of query strings to test
        runs_per_query: Number of times to run each query
    
    Returns: List of latencies in milliseconds
    """
    db = Database(db_path)
    db.connect()
    
    search = SearchEngine(db.conn)
    latencies = []
    
    # Warm up
    for query in queries[:3]:
        search.search(query, topk=10)
    
    # Measure
    for query in queries:
        for _ in range(runs_per_query):
            start_time = time.perf_counter()
            results = search.search(query, topk=10)
            end_time = time.perf_counter()
            
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
    
    db.close()
    
    return latencies


def calculate_percentiles(latencies: List[float]) -> Tuple[float, float, float]:
    """Calculate p50, p95, p99 from latencies."""
    if not latencies:
        return 0.0, 0.0, 0.0
    
    sorted_latencies = sorted(latencies)
    n = len(sorted_latencies)
    
    p50 = sorted_latencies[int(n * 0.50)]
    p95 = sorted_latencies[int(n * 0.95)]
    p99 = sorted_latencies[int(n * 0.99)]
    
    return p50, p95, p99


def benchmark_repository(repo_path: Path, queries: List[str]) -> BenchmarkResult:
    """
    Run complete benchmark on a repository.
    
    Args:
        repo_path: Path to repository to benchmark
        queries: List of queries to test
    
    Returns: BenchmarkResult with all metrics
    """
    repo_name = repo_path.name
    print(f"\n{'='*80}")
    print(f"Benchmarking: {repo_name}")
    print(f"{'='*80}")
    
    result = BenchmarkResult(repo_name, str(repo_path))
    
    # Count LOC
    print("📊 Counting lines of code...")
    result.repo_size_loc, result.repo_size_mb = count_lines_of_code(repo_path)
    print(f"   LOC: {result.repo_size_loc:,}")
    print(f"   Size: {result.repo_size_mb:.2f} MB")
    
    # Create temporary database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "benchmark.db"
        
        # Benchmark indexing
        print("\n⏱️  Benchmarking indexing...")
        index_time, file_count, symbol_count = benchmark_indexing(repo_path, db_path)
        result.index_time_seconds = index_time
        result.file_count = file_count
        result.symbol_count = symbol_count
        result.index_size_mb = db_path.stat().st_size / (1024 * 1024)
        
        print(f"   Files indexed: {file_count:,}")
        print(f"   Symbols extracted: {symbol_count:,}")
        print(f"   Time: {index_time:.2f}s")
        print(f"   Index size: {result.index_size_mb:.2f} MB")
        print(f"   Speed: {result.repo_size_loc / index_time:,.0f} LOC/s")
        
        # Benchmark queries
        print("\n🔍 Benchmarking queries...")
        latencies = benchmark_queries(db_path, queries, runs_per_query=10)
        result.query_latencies = latencies
        
        p50, p95, p99 = calculate_percentiles(latencies)
        result.query_p50_ms = p50
        result.query_p95_ms = p95
        result.query_p99_ms = p99
        
        print(f"   Queries tested: {len(queries)}")
        print(f"   Runs per query: 10")
        print(f"   p50 latency: {p50:.2f} ms")
        print(f"   p95 latency: {p95:.2f} ms")
        print(f"   p99 latency: {p99:.2f} ms")
    
    print(f"\n✅ Benchmark complete for {repo_name}")
    
    return result


def get_default_queries() -> List[str]:
    """Get a standard set of queries for benchmarking."""
    return [
        # Text queries
        "function",
        "import",
        "class",
        "async",
        "export",
        # Symbol queries
        "def:main",
        "class:Config",
        "import:os",
        "symbol:parse",
        "symbol:execute",
        # Filtered queries
        "function lang:python",
        "class lang:javascript",
        "import lang:typescript",
    ]


def run_benchmarks(repo_paths: List[Path], output_file: Path = None) -> List[BenchmarkResult]:
    """
    Run benchmarks on multiple repositories.
    
    Args:
        repo_paths: List of repository paths to benchmark
        output_file: Optional path to save results as JSON
    
    Returns: List of BenchmarkResult objects
    """
    queries = get_default_queries()
    results = []
    
    print("🚀 Starting benchmark suite")
    print(f"📁 Repositories: {len(repo_paths)}")
    print(f"🔍 Queries per repo: {len(queries)}")
    
    for repo_path in repo_paths:
        if not repo_path.exists():
            print(f"⚠️  Skipping {repo_path} (not found)")
            continue
        
        try:
            result = benchmark_repository(repo_path, queries)
            results.append(result)
        except Exception as e:
            print(f"❌ Error benchmarking {repo_path}: {e}")
            continue
    
    # Save results
    if output_file and results:
        print(f"\n💾 Saving results to {output_file}")
        with open(output_file, 'w') as f:
            json.dump([r.to_dict() for r in results], f, indent=2)
    
    # Print summary table
    print_summary_table(results)
    
    return results


def print_summary_table(results: List[BenchmarkResult]):
    """Print a formatted summary table of benchmark results."""
    if not results:
        print("\n⚠️  No results to display")
        return
    
    print("\n" + "="*100)
    print("📊 BENCHMARK SUMMARY")
    print("="*100)
    
    # Header
    print(f"{'Repository':<25} {'LOC':>10} {'Files':>8} {'Symbols':>10} "
          f"{'Index (s)':>10} {'p50 (ms)':>10} {'p95 (ms)':>10}")
    print("-"*100)
    
    # Data rows
    for r in results:
        print(f"{r.repo_name:<25} {r.repo_size_loc:>10,} {r.file_count:>8,} {r.symbol_count:>10,} "
              f"{r.index_time_seconds:>10.2f} {r.query_p50_ms:>10.2f} {r.query_p95_ms:>10.2f}")
    
    print("="*100)
    
    # Averages
    if len(results) > 1:
        avg_loc = sum(r.repo_size_loc for r in results) / len(results)
        avg_index_time = sum(r.index_time_seconds for r in results) / len(results)
        avg_p50 = sum(r.query_p50_ms for r in results) / len(results)
        avg_p95 = sum(r.query_p95_ms for r in results) / len(results)
        
        print(f"{'AVERAGE':<25} {avg_loc:>10,.0f} "
              f"{'':>8} {'':>10} {avg_index_time:>10.2f} {avg_p50:>10.2f} {avg_p95:>10.2f}")
        print("="*100)


def main():
    """Main entry point for benchmark script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark codesearch performance")
    parser.add_argument("repos", nargs="+", help="Repository paths to benchmark")
    parser.add_argument("--output", "-o", help="Output JSON file for results")
    parser.add_argument("--queries", nargs="+", help="Custom queries (optional)")
    
    args = parser.parse_args()
    
    # Convert paths
    repo_paths = [Path(p).resolve() for p in args.repos]
    output_file = Path(args.output) if args.output else None
    
    # Run benchmarks
    results = run_benchmarks(repo_paths, output_file)
    
    if not results:
        print("\n❌ No successful benchmarks")
        sys.exit(1)
    
    print("\n✅ All benchmarks complete!")
    sys.exit(0)


if __name__ == "__main__":
    main()
