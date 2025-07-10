"""FastAPI application main module."""

import time
from datetime import UTC, datetime
from typing import Any

import yfinance as yf
from fastapi import FastAPI, HTTPException, Request
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
        "endpoints": [
            "/api/v1/stock/{symbol}", 
            "/api/v1/analysis/{symbol}",
            "/api/v1/comprehensive/{symbol}",
            "/api/v1/historical/{symbol}"
        ],
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

    except ValueError as e:
        # Handle date parsing errors specifically
        error_msg = str(e)
        logger.warning(f"Parameter validation error for {symbol}: {e}")
        
        # Determine error type based on error message
        if "date" in error_msg.lower():
            error_type = "Invalid Parameter"
        else:
            error_type = "Invalid Parameter"
            
        raise HTTPException(
            status_code=400,
            detail={
                "error": error_type,
                "message": error_msg,
                "symbol": symbol,
            },
        ) from e
    except HTTPException:
        # Re-raise HTTPException from analysis module
        raise
    except Exception as e:
        # Handle any other exceptions that weren't caught by analysis module
        error_msg = str(e)
        logger.error(f"Unexpected error in analysis endpoint for {symbol}: {e}", exc_info=True)
        
        # Check if it's a data availability issue
        if ("no data available" in error_msg.lower() or 
            "data not available" in error_msg.lower() or
            "not found" in error_msg.lower()):
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Data Not Available",
                    "message": f"No stock data available for symbol {symbol}",
                    "symbol": symbol,
                },
            ) from e
        # Check if it's an internal calculation error
        elif "internal calculation error" in error_msg.lower():
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Analysis Error",
                    "message": "An error occurred during analysis",
                    "symbol": symbol,
                },
            ) from e
        else:
            # Default to server error
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Analysis Error",
                    "message": "An error occurred during analysis",
                    "symbol": symbol,
                },
            ) from e


# Historical data endpoint
@app.get("/api/v1/historical/{symbol}", tags=["Historical Data"])
async def get_historical_data_endpoint(
    symbol: str,
    period: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Get historical stock price data (OHLCV) for chart display.
    
    Retrieves historical stock price data from yfinance and formats it
    for frontend chart consumption. Supports both predefined periods
    and custom date ranges.
    
    Args:
        symbol: Stock symbol to retrieve data for (e.g., 'AAPL', '7203.T')
        period: Predefined time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        start_date: Custom start date (YYYY-MM-DD format)
        end_date: Custom end date (required if start_date provided)
        
    Returns:
        Dictionary containing historical OHLCV data and metadata
        
    Example:
        GET /api/v1/historical/AAPL?period=1mo
        {
            "success": true,
            "data": {
                "symbol": "AAPL",
                "period": "1mo",
                "data_points": 22,
                "start_date": "2023-12-15",
                "end_date": "2024-01-15",
                "historical_data": [
                    {
                        "date": "2023-12-15",
                        "open": 150.25,
                        "high": 152.75,
                        "low": 149.50,
                        "close": 151.80,
                        "volume": 1234567
                    },
                    ...
                ],
                "metadata": {
                    "current_price": 151.80,
                    "price_change": 5.25,
                    "price_change_percent": 3.58,
                    "average_volume": 1234567,
                    "data_quality": "high",
                    "retrieved_at": "2024-01-15T10:30:00Z"
                }
            }
        }
    """
    from trendscope_backend.api.historical_data import get_historical_data
    from trendscope_backend.api.analysis import parse_date_string
    
    # Parse optional parameters
    parsed_start_date = None
    parsed_end_date = None
    
    try:
        if start_date:
            parsed_start_date = parse_date_string(start_date)
        if end_date:
            parsed_end_date = parse_date_string(end_date)
        
        # Get historical data
        result = await get_historical_data(
            symbol=symbol,
            period=period,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
        )
        
        return result
        
    except ValueError as e:
        # Handle date parsing errors specifically
        error_msg = str(e)
        logger.warning(f"Parameter validation error for historical data {symbol}: {e}")
        
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid Parameter",
                "message": error_msg,
                "symbol": symbol,
            },
        ) from e
    except HTTPException:
        # Re-raise HTTPException from historical_data module
        raise
    except Exception as e:
        # Handle any other exceptions
        error_msg = str(e)
        logger.error(f"Unexpected error in historical data endpoint for {symbol}: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Data Retrieval Error",
                "message": "An error occurred while retrieving historical data",
                "symbol": symbol,
            },
        ) from e


# Comprehensive 6-category analysis endpoint
@app.get("/api/v1/comprehensive/{symbol}", tags=["Comprehensive Analysis"])
async def analyze_stock_comprehensive(
    symbol: str,
    period: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    include_ml: bool = True,
    ml_models: str | None = None,
) -> dict[str, Any]:
    """Perform comprehensive 6-category stock analysis.
    
    Combines technical analysis, pattern recognition, volatility analysis,
    machine learning predictions, fundamental analysis, and integrated scoring
    into a unified analysis report.
    
    Args:
        symbol: Stock symbol to analyze (e.g., 'AAPL', 'GOOGL')
        period: Time period for analysis
            (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        start_date: Custom start date (YYYY-MM-DD format)
        end_date: Custom end date (YYYY-MM-DD format)
        include_ml: Whether to include ML predictions (can be slow, default: true)
        ml_models: Comma-separated ML models to use (random_forest,svm,arima,lstm)
        
    Returns:
        Comprehensive analysis results from all 6 categories
        
    Example:
        GET /api/v1/comprehensive/AAPL?period=3mo&include_ml=true&ml_models=random_forest,svm
        {
            "symbol": "AAPL",
            "analysis_date": "2024-01-15T10:30:00Z",
            "current_price": "182.50",
            "technical_analysis": {...},
            "pattern_analysis": {...},
            "volatility_analysis": {...},
            "ml_predictions": {...},
            "fundamental_analysis": {...},
            "integrated_score": {
                "overall_score": "0.72",
                "confidence_level": "0.85",
                "recommendation": "BUY",
                "risk_assessment": "MODERATE"
            },
            "summary": "Comprehensive analysis shows bullish outlook..."
        }
    """
    from trendscope_backend.api.comprehensive_analysis import get_comprehensive_analysis
    from trendscope_backend.api.analysis import parse_date_string
    
    # Parse optional parameters
    parsed_start_date = None
    parsed_end_date = None
    ml_model_list = None
    
    try:
        if start_date:
            parsed_start_date = parse_date_string(start_date)
        if end_date:
            parsed_end_date = parse_date_string(end_date)
        if ml_models:
            ml_model_list = [model.strip() for model in ml_models.split(",")]
        
        # Perform comprehensive analysis
        result = await get_comprehensive_analysis(
            symbol=symbol,
            period=period,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            include_ml=include_ml,
            ml_models=ml_model_list,
        )
        
        return result
        
    except ValueError as e:
        # Handle date parsing errors specifically
        error_msg = str(e)
        logger.warning(f"Parameter validation error for comprehensive analysis {symbol}: {e}")
        
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid Parameter",
                "message": error_msg,
                "symbol": symbol,
            },
        ) from e
    except HTTPException:
        # Re-raise HTTPException from analysis module
        raise
    except Exception as e:
        # Handle any other exceptions
        error_msg = str(e)
        logger.error(f"Unexpected error in comprehensive analysis for {symbol}: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Analysis Error",
                "message": "An error occurred during comprehensive analysis",
                "symbol": symbol,
            },
        ) from e


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
from fastapi.exceptions import HTTPException as FastAPIHTTPException

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Any) -> JSONResponse:
    """Handle 404 Not Found errors.

    Args:
        request: HTTP request that caused the error
        exc: Exception instance

    Returns:
        JSON response with error details
    """
    # Check if this is a custom HTTPException with detail structure
    if isinstance(exc, FastAPIHTTPException) and isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
        )
    
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

    # Check if this is a custom HTTPException with detail structure
    if isinstance(exc, FastAPIHTTPException) and isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
        )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )
