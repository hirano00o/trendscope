# Frontend Dockerfile for TrendScope
FROM oven/bun:1 AS base

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json bun.lock* ./

# Install system dependencies and bun dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN bun install --frozen-lockfile

# Copy source code
COPY . .

# Build the application
RUN bun run build

# Set environment variables
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Start the application
CMD ["bun", "start"]