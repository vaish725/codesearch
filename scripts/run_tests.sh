#!/bin/bash
# Test runner script with coverage

set -e

echo "🧪 Running codesearch tests..."

# Run unit tests with coverage
echo "📊 Running unit tests with coverage..."
pytest tests/unit -v --cov=codesearch --cov-report=term-missing --cov-report=html

# Run integration tests separately
echo "🔗 Running integration tests..."
pytest tests/integration -v

echo ""
echo "✅ All tests passed!"
echo ""
echo "📈 Coverage report generated in htmlcov/index.html"
