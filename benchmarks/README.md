# Benchmarks

This directory contains benchmarking scripts and results for codesearch.

## Structure

- `run_benchmarks.py` - Main benchmark runner
- `results/` - Benchmark results (JSON and graphs)
- `test_repos/` - Sample repositories for testing (not committed)

## Running Benchmarks

```bash
# Run all benchmarks
python benchmarks/run_benchmarks.py

# Run specific benchmark
python benchmarks/run_benchmarks.py --repo /path/to/repo
```

## Metrics Tracked

- **Indexing Performance**
  - Total time to index
  - Lines of code per second
  - Index size on disk
  
- **Query Performance**
  - p50, p95, p99 latency
  - Results per query
  - Query types: text, symbol, filtered

## Implementation

Benchmarks will be fully implemented in Phase 6.
