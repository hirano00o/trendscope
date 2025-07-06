"""FastAPI application main module."""

import time
from datetime import UTC, datetime
from typing import Any

import yfinance as yf
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from trendscope_backend.utils.logging import get_logger

logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title="TrendScope Backend API",
    description="Stock trend analysis API with technical indicators",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js default development server
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next) -> Any:
    """Log all HTTP requests with timing information.

    Args:
        request: HTTP request object
        call_next: Next middleware or route handler

    Returns:
        HTTP response with added timing headers
    """
    start_time = time.time()

    # Log incoming request
    logger.info(
        f"Incoming request: {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Add timing header
    response.headers["X-Process-Time"] = str(process_time)

    # Log response
    logger.info(
        f"Response: {response.status_code} for {request.method} {request.url.path} "
        f"in {process_time:.4f}s"
    )

    return response


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next) -> Any:
    """Add security headers to all responses.

    Args:
        request: HTTP request object
        call_next: Next middleware or route handler

    Returns:
        HTTP response with security headers
    """
    response = await call_next(request)

    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    return response


def get_health_status() -> dict[str, Any]:
    """Get comprehensive health status of the service and its dependencies.

    Checks the health of the service itself and external dependencies
    like yfinance connectivity.

    Returns:
        Dictionary containing health status information

    Example:
        >>> health = get_health_status()
        >>> print(health["status"])
        'healthy'
        >>> print(health["dependencies"]["yfinance"]["status"])
        'healthy'
    """
    health_data = {
        "status": "healthy",
        "service": "trendscope-backend",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "0.1.0",
        "dependencies": {},
    }

    # Check yfinance connectivity
    try:
        # Quick test to verify yfinance is working
        ticker = yf.Ticker("AAPL")
        # Try to get basic info (this is a lightweight operation)
        info = ticker.info
        if info and len(info) > 0:
            yfinance_status = "healthy"
            yfinance_message = "Connection successful"
        else:
            yfinance_status = "unhealthy"
            yfinance_message = "No data returned"
    except Exception as e:
        yfinance_status = "unhealthy"
        yfinance_message = f"Connection failed: {str(e)}"
        logger.warning(f"yfinance health check failed: {e}")

    health_data["dependencies"]["yfinance"] = {
        "status": yfinance_status,
        "message": yfinance_message,
        "checked_at": datetime.now(UTC).isoformat(),
    }

    return health_data


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, Any]:
    """Health check endpoint for service monitoring.

    Returns comprehensive health information including dependency status.
    This endpoint is used by load balancers, monitoring systems, and
    deployment pipelines to verify service health.

    Returns:
        Health status information including dependencies

    Example:
        GET /health
        {
            "status": "healthy",
            "service": "trendscope-backend",
            "timestamp": "2024-01-15T10:30:00.000Z",
            "version": "0.1.0",
            "dependencies": {
                "yfinance": {
                    "status": "healthy",
                    "message": "Connection successful"
                }
            }
        }
    """
    return get_health_status()


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Root endpoint with basic API information.

    Returns:
        Basic API information and available endpoints

    Example:
        GET /
        {
            "message": "TrendScope Backend API",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health"
        }
    """
    return {
        "message": "TrendScope Backend API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1/",
    }


# API v1 router placeholder
@app.get("/api/v1/", tags=["API v1"])
async def api_v1_root() -> dict[str, Any]:
    """API v1 root endpoint.

    Returns:
        API v1 information and available endpoints

    Example:
        GET /api/v1/
        {
            "message": "TrendScope API v1",
            "version": "1.0",
            "endpoints": ["/api/v1/stock/{symbol}"]
        }
    """
    return {
        "message": "TrendScope API v1",
        "version": "1.0",
        "endpoints": ["/api/v1/stock/{symbol}", "/api/v1/analysis/{symbol}"],
    }


# Technical analysis endpoints
@app.get("/api/v1/analysis/{symbol}", tags=["Technical Analysis"])
async def analyze_stock(
    symbol: str,
    period: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    indicators: str | None = None,
) -> dict[str, Any]:
    """Perform technical analysis on a stock symbol.

    Analyzes stock price data using various technical indicators
    and provides probability-based investment recommendations.

    Args:
        symbol: Stock symbol to analyze (e.g., 'AAPL', 'GOOGL')
        period: Time period for analysis
            (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        start_date: Custom start date (YYYY-MM-DD format)
        end_date: Custom end date (YYYY-MM-DD format)
        indicators: Comma-separated list of indicators (sma,ema,rsi,macd,bollinger)

    Returns:
        Technical analysis results with indicators and recommendation

    Example:
        GET /api/v1/analysis/AAPL?period=1mo&indicators=sma,rsi,macd
        {
            "symbol": "AAPL",
            "analysis_date": "2024-01-15T10:30:00Z",
            "time_series": {...},
            "indicators": {...},
            "recommendation": "BUY",
            "probability_up": "0.72",
            "confidence_level": "0.85"
        }
    """
    from trendscope_backend.api.analysis import get_stock_analysis, parse_date_string

    # Parse optional parameters
    parsed_start_date = None
    parsed_end_date = None
    indicator_list = None

    try:
        if start_date:
            parsed_start_date = parse_date_string(start_date)
        if end_date:
            parsed_end_date = parse_date_string(end_date)
        if indicators:
            indicator_list = [ind.strip() for ind in indicators.split(",")]

        # Perform analysis
        result = await get_stock_analysis(
            symbol=symbol,
            period=period,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            indicators=indicator_list,
        )

        return result

    except Exception:
        # Let the analysis module handle specific error formatting
        raise


# Placeholder for stock analysis endpoint (keeping for backward compatibility)
@app.get("/api/v1/stock/{symbol}", tags=["Stock Analysis"])
async def get_stock_analysis_legacy(symbol: str) -> dict[str, Any]:
    """Get stock analysis for a given symbol (legacy endpoint).

    This endpoint redirects to the new analysis endpoint.
    Use /api/v1/analysis/{symbol} for full functionality.

    Args:
        symbol: Stock symbol to analyze (e.g., 'AAPL', 'GOOGL')

    Returns:
        Redirect to analysis endpoint

    Example:
        GET /api/v1/stock/AAPL
        {
            "message": "Use /api/v1/analysis/{symbol} for full analysis",
            "redirect_url": "/api/v1/analysis/AAPL"
        }
    """
    return {
        "message": "Use /api/v1/analysis/{symbol} for full analysis functionality",
        "redirect_url": f"/api/v1/analysis/{symbol}",
        "symbol": symbol.upper(),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.on_event("startup")
async def startup_event() -> None:
    """Application startup event handler.

    Performs initialization tasks when the application starts.
    This includes logging startup information and any necessary
    service initialization.
    """
    logger.info("TrendScope Backend API starting up...")
    logger.info("FastAPI application initialized successfully")

    # Log configuration
    logger.info(f"API version: {app.version}")
    logger.info("Docs available at: /docs")
    logger.info("Health check available at: /health")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Application shutdown event handler.

    Performs cleanup tasks when the application shuts down.
    This includes logging shutdown information and cleaning up
    any resources.
    """
    logger.info("TrendScope Backend API shutting down...")
    logger.info("Cleanup completed successfully")


# Global exception handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Any) -> JSONResponse:
    """Handle 404 Not Found errors.

    Args:
        request: HTTP request that caused the error
        exc: Exception instance

    Returns:
        JSON response with error details
    """
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested endpoint {request.url.path} was not found",
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )


@app.exception_handler(405)
async def method_not_allowed_handler(request: Request, exc: Any) -> JSONResponse:
    """Handle 405 Method Not Allowed errors.

    Args:
        request: HTTP request that caused the error
        exc: Exception instance

    Returns:
        JSON response with error details
    """
    return JSONResponse(
        status_code=405,
        content={
            "error": "Method Not Allowed",
            "message": f"The method {request.method} is not allowed for "
            f"{request.url.path}",
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Any) -> JSONResponse:
    """Handle 500 Internal Server Error.

    Args:
        request: HTTP request that caused the error
        exc: Exception instance

    Returns:
        JSON response with error details
    """
    logger.error(
        f"Internal server error for {request.method} {request.url.path}: {exc}"
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )
