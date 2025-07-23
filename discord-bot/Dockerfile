# Multi-stage Dockerfile for TrendScope Discord Bot
# Stage 1: Build stage
FROM golang:1.21-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git ca-certificates tzdata

# Set working directory
WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the application
# CGO_ENABLED=0 for static binary
# GOOS=linux for Linux target
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o discord-bot ./cmd/discord-bot/

# Stage 2: Final runtime stage
FROM alpine:latest

# Install runtime dependencies
RUN apk --no-cache add ca-certificates tzdata curl

# Create non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -s /bin/sh -u 1000 -G appuser appuser

# Set working directory
WORKDIR /app

# Copy binary from builder stage
COPY --from=builder /app/discord-bot .

# Copy timezone data (needed for cron scheduling)
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo

# Create directory for CSV file
RUN mkdir -p /data && chown appuser:appuser /data

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep discord-bot || exit 1

# Environment variables (can be overridden)
ENV BACKEND_API_URL=http://backend:8000 \
    CSV_PATH=/data/screener_result.csv \
    CRON_SCHEDULE="0 10 * * 1-5" \
    MAX_WORKERS=10 \
    TOP_STOCKS_COUNT=15

# Exposed port (if needed for metrics/health checks in the future)
EXPOSE 8080

# Command to run
CMD ["./discord-bot"]