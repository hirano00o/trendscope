# Backend Dockerfile for TrendScope
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Create non-root user for security
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash appuser

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/ ./src/
COPY main.py ./

# Create cache directory and set permissions
RUN mkdir -p /tmp/.cache/uv && \
    chown -R appuser:appuser /app /tmp/.cache

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONPATH=/app/src
ENV HOST=0.0.0.0
ENV PORT=8000
ENV UV_CACHE_DIR=/tmp/.cache/uv

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application using uvicorn
CMD ["uv", "run", "uvicorn", "trendscope_backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]