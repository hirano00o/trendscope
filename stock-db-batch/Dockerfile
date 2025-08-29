# Multi-stage build for Python application
FROM python:3.12-slim AS builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
ADD --chmod=755 https://astral.sh/uv/install.sh /install.sh
RUN /install.sh && rm /install.sh

# Set up working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY src/ ./src/

# Install dependencies using uv
RUN /root/.cargo/bin/uv sync --frozen --no-dev

# Production stage
FROM python:3.12-slim AS production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r stockbatch && useradd -r -g stockbatch stockbatch

# Set up working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy source code
COPY --from=builder /app/src /app/src

# Copy main entry point
COPY main.py /app/

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create data directory and temporary directory
RUN mkdir -p /data /tmp/app && chown stockbatch:stockbatch /data /tmp/app

# Switch to non-root user
USER stockbatch

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Entry point
ENTRYPOINT ["python", "-m", "stock_batch.main"]
