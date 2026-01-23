#!/bin/bash
# Benchmark runner script

set -e

echo "⚡ Running codesearch benchmarks..."

# Check if benchmarks directory exists
if [ ! -d "benchmarks" ]; then
    echo "❌ Benchmarks directory not found"
    exit 1
fi

# Run benchmarks
python3 benchmarks/run_benchmarks.py

echo ""
echo "✅ Benchmarks complete!"
echo "📊 Results saved in benchmarks/results/"
