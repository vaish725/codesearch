# Makefile for codesearch development

.PHONY: help install test clean format lint docs

help:
	@echo "Codesearch Development Commands:"
	@echo "  make install    - Install package in development mode"
	@echo "  make test       - Run all tests"
	@echo "  make test-unit  - Run unit tests only"
	@echo "  make test-int   - Run integration tests only"
	@echo "  make coverage   - Run tests with coverage report"
	@echo "  make format     - Format code with black and isort"
	@echo "  make lint       - Run linters (black, isort, mypy)"
	@echo "  make clean      - Clean build artifacts"
	@echo "  make docs       - Generate documentation"
	@echo "  make benchmark  - Run benchmarks"

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit -v -m unit

test-int:
	pytest tests/integration -v -m integration

coverage:
	pytest tests/ -v --cov=codesearch --cov-report=term-missing --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

format:
	black codesearch/ tests/ examples/
	isort codesearch/ tests/ examples/

lint:
	black --check codesearch/ tests/
	isort --check codesearch/ tests/
	mypy codesearch/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docs:
	@echo "Documentation is in docs/ directory"
	@echo "Open docs/architecture.md to view"

benchmark:
	python3 benchmarks/run_benchmarks.py

.DEFAULT_GOAL := help
