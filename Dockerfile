FROM python:3.11-slim

LABEL maintainer="vaish725"
LABEL description="Codesearch - Local code search engine with symbol awareness"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY codesearch/ ./codesearch/
COPY tests/ ./tests/

# Install codesearch
RUN pip install --no-cache-dir -e .

# Create volume for indexed repositories
VOLUME ["/repos"]

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
ENTRYPOINT ["codesearch"]
CMD ["--help"]
