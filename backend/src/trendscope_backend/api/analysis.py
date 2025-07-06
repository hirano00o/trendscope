"""Technical analysis API endpoints and utilities.

This module provides REST API endpoints for stock technical analysis
and utility functions for data validation and formatting.
"""

import re
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi import HTTPException

from trendscope_backend.analysis.technical.indicators import (
    TechnicalIndicatorCalculator,
)
from trendscope_backend.data.models import AnalysisRequest, AnalysisResult
from trendscope_backend.data.stock_data import StockDataFetcher
from trendscope_backend.utils.logging import get_logger

logger = get_logger(__name__)

# Valid yfinance periods
VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}

# Valid technical indicators
VALID_INDICATORS = {"sma", "ema", "rsi", "macd", "bollinger"}


def validate_symbol(symbol: str | None) -> str:
    """Validate stock symbol format.

    Args:
        symbol: Stock symbol to validate

    Returns:
        Validated and normalized symbol

    Raises:
        ValueError: If symbol is invalid

    Example:
        >>> validate_symbol("AAPL")
        'AAPL'
        >>> validate_symbol("brk-a")
        'BRK-A'
    """
    if symbol is None:
        raise ValueError("Symbol cannot be None")

    if not symbol or not symbol.strip():
        raise ValueError("Symbol cannot be empty")

    # Convert to uppercase and strip whitespace
    symbol = symbol.strip().upper()

    # Check length
    if len(symbol) > 20:
        raise ValueError("Symbol too long (max 20 characters)")

    # Check for all numeric symbols
    if symbol.isdigit():
        raise ValueError("Symbol cannot be all numbers")

    # Check format (letters, numbers, dots, hyphens)
    if not re.match(r"^[A-Z0-9.-]+$", symbol):
        raise ValueError("Symbol contains invalid characters")

    return symbol


def validate_period(period: str) -> str:
    """Validate time period parameter.

    Args:
        period: Time period string

    Returns:
        Validated period

    Raises:
        ValueError: If period is invalid

    Example:
        >>> validate_period("1mo")
        '1mo'
        >>> validate_period("invalid")
        ValueError: Invalid period
    """
    if period not in VALID_PERIODS:
        raise ValueError(f"Invalid period. Must be one of: {', '.join(VALID_PERIODS)}")

    return period


def validate_indicators(indicators: list[str]) -> list[str]:
    """Validate technical indicators list.

    Args:
        indicators: List of indicator names

    Returns:
        Validated indicators list

    Raises:
        ValueError: If any indicator is invalid

    Example:
        >>> validate_indicators(["sma", "rsi"])
        ['sma', 'rsi']
        >>> validate_indicators(["invalid"])
        ValueError: Invalid indicator
    """
    if not indicators:
        raise ValueError("At least one indicator must be specified")

    for indicator in indicators:
        if indicator not in VALID_INDICATORS:
            raise ValueError(
                f"Invalid indicator '{indicator}'. "
                f"Must be one of: {', '.join(VALID_INDICATORS)}"
            )

    return indicators


def parse_date_string(date_str: str) -> datetime:
    """Parse date string to datetime object.

    Args:
        date_str: Date string in YYYY-MM-DD format

    Returns:
        Parsed datetime object

    Raises:
        ValueError: If date format is invalid

    Example:
        >>> parse_date_string("2023-01-01")
        datetime(2023, 1, 1, 0, 0)
        >>> parse_date_string("invalid")
        ValueError: Invalid date format
    """
    try:
        # Parse date in YYYY-MM-DD format
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d")

        # Check if date is in the future
        if parsed_date.date() > datetime.now(UTC).date():
            raise ValueError("Date cannot be in the future")

        return parsed_date
    except ValueError as e:
        if "time data" in str(e):
            raise ValueError(
                "Invalid date format. Use YYYY-MM-DD format (e.g., 2023-01-01)"
            ) from e
        raise


def format_analysis_response(analysis_result: AnalysisResult) -> dict[str, Any]:
    """Format analysis result for API response.

    Args:
        analysis_result: Analysis result to format

    Returns:
        Formatted response dictionary

    Example:
        >>> result = AnalysisResult(...)
        >>> response = format_analysis_response(result)
        >>> print(response["symbol"])
        'AAPL'
    """
    # Format time series information
    time_series_info = {
        "start_date": analysis_result.time_series.start_date.isoformat() + "Z",
        "end_date": analysis_result.time_series.end_date.isoformat() + "Z",
        "data_points": analysis_result.time_series.data_points,
        "period": analysis_result.time_series.period,
    }

    # Format technical indicators
    indicators = {}
    if analysis_result.indicators.sma_20 is not None:
        indicators["sma_20"] = str(analysis_result.indicators.sma_20)
    if analysis_result.indicators.sma_50 is not None:
        indicators["sma_50"] = str(analysis_result.indicators.sma_50)
    if analysis_result.indicators.ema_12 is not None:
        indicators["ema_12"] = str(analysis_result.indicators.ema_12)
    if analysis_result.indicators.ema_26 is not None:
        indicators["ema_26"] = str(analysis_result.indicators.ema_26)
    if analysis_result.indicators.rsi is not None:
        indicators["rsi"] = str(analysis_result.indicators.rsi)
    if analysis_result.indicators.macd is not None:
        indicators["macd"] = str(analysis_result.indicators.macd)
    if analysis_result.indicators.macd_signal is not None:
        indicators["macd_signal"] = str(analysis_result.indicators.macd_signal)
    if analysis_result.indicators.bollinger_upper is not None:
        indicators["bollinger_upper"] = str(analysis_result.indicators.bollinger_upper)
    if analysis_result.indicators.bollinger_lower is not None:
        indicators["bollinger_lower"] = str(analysis_result.indicators.bollinger_lower)

    return {
        "symbol": analysis_result.symbol,
        "analysis_date": analysis_result.analysis_date.isoformat() + "Z",
        "time_series": time_series_info,
        "indicators": indicators,
        "recommendation": analysis_result.recommendation,
        "probability_up": str(analysis_result.probability_up),
        "confidence_level": str(analysis_result.confidence_level),
    }


async def get_stock_analysis(
    symbol: str,
    period: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    indicators: list[str] | None = None,
) -> dict[str, Any]:
    """Perform stock technical analysis.

    Fetches stock data and calculates technical indicators for analysis.

    Args:
        symbol: Stock symbol to analyze
        period: Time period for analysis (e.g., '1mo', '3mo')
        start_date: Custom start date for analysis
        end_date: Custom end date for analysis
        indicators: List of indicators to calculate

    Returns:
        Analysis results dictionary

    Raises:
        HTTPException: If analysis fails or data unavailable

    Example:
        >>> analysis = await get_stock_analysis("AAPL", period="1mo")
        >>> print(analysis["symbol"])
        'AAPL'
    """
    try:
        # Validate symbol
        symbol = validate_symbol(symbol)
        logger.info(f"Starting analysis for symbol: {symbol}")

        # Set default indicators if not provided
        if indicators is None:
            indicators = ["sma", "ema", "rsi", "macd", "bollinger"]

        # Validate indicators
        indicators = validate_indicators(indicators)

        # Create analysis request
        if period:
            period = validate_period(period)
            request = AnalysisRequest(
                symbol=symbol, period=period, indicators=indicators
            )
        elif start_date and end_date:
            request = AnalysisRequest(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                indicators=indicators,
            )
        else:
            # Default to 1 month period
            request = AnalysisRequest(
                symbol=symbol, period="1mo", indicators=indicators
            )

        # Fetch stock data
        data_fetcher = StockDataFetcher()

        if request.period:
            stock_data = data_fetcher.fetch_stock_data(symbol, period=request.period)
        else:
            stock_data = data_fetcher.fetch_stock_data(
                symbol, start_date=request.start_date, end_date=request.end_date
            )

        if not stock_data:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Data Not Available",
                    "message": f"No stock data available for symbol {symbol}",
                    "symbol": symbol,
                },
            )

        # Calculate technical indicators
        calculator = TechnicalIndicatorCalculator()
        indicators_result = calculator.calculate_all_indicators(stock_data)

        # Create analysis result
        from trendscope_backend.data.models import TimeSeriesData

        time_series = TimeSeriesData(
            symbol=symbol, data=stock_data, period=request.period or "custom"
        )

        # Calculate probability and confidence (simplified logic for now)
        probability_up = calculate_probability(indicators_result)
        confidence_level = calculate_confidence(indicators_result, len(stock_data))

        analysis_result = AnalysisResult(
            symbol=symbol,
            time_series=time_series,
            indicators=indicators_result,
            analysis_date=datetime.now(UTC),
            probability_up=probability_up,
            confidence_level=confidence_level,
        )

        logger.info(
            f"Analysis completed for {symbol}: "
            f"probability={probability_up}, confidence={confidence_level}"
        )

        return format_analysis_response(analysis_result)

    except HTTPException:
        raise
    except ValueError as e:
        error_msg = str(e)
        logger.warning(f"Validation error for {symbol}: {e}")
        
        # Determine error type based on error message
        if "symbol" in error_msg.lower():
            error_type = "Invalid Symbol"
        elif "period" in error_msg.lower():
            error_type = "Invalid Parameter"
        elif "indicator" in error_msg.lower():
            error_type = "Invalid Parameter"  
        elif "date" in error_msg.lower():
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
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Analysis error for {symbol}: {e}", exc_info=True)
        
        # Check if it's a data availability issue first
        if ("no data available" in error_msg.lower() or 
            "not found" in error_msg.lower() or
            "data not available" in error_msg.lower()):
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Data Not Available",
                    "message": f"No stock data available for symbol {symbol}",
                    "symbol": symbol,
                },
            ) from e
        # Check if it's a server error (internal calculation error)
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
            # Default: treat as server error
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Analysis Error",
                    "message": "An error occurred during analysis",
                    "symbol": symbol,
                },
            ) from e


def calculate_probability(indicators: Any) -> Decimal:
    """Calculate probability of price increase based on indicators.

    This is a simplified algorithm that combines multiple indicators
    to estimate the probability of price increase.

    Args:
        indicators: TechnicalIndicators object

    Returns:
        Probability value between 0.0 and 1.0

    Example:
        >>> prob = calculate_probability(indicators)
        >>> print(f"Probability: {prob}")
        Probability: 0.72
    """
    score = Decimal("0.5")  # Start with neutral 50%
    factors = 0

    # RSI analysis (30-70 range is neutral, outside indicates oversold/overbought)
    if indicators.rsi is not None:
        if indicators.rsi < 30:
            score += Decimal("0.1")  # Oversold, likely to go up
        elif indicators.rsi > 70:
            score -= Decimal("0.1")  # Overbought, likely to go down
        factors += 1

    # MACD analysis (positive MACD suggests uptrend)
    if indicators.macd is not None and indicators.macd_signal is not None:
        if indicators.macd > indicators.macd_signal:
            score += Decimal("0.1")  # MACD above signal line
        else:
            score -= Decimal("0.1")  # MACD below signal line
        factors += 1

    # Moving average analysis
    if indicators.sma_20 is not None and indicators.sma_50 is not None:
        if indicators.sma_20 > indicators.sma_50:
            score += Decimal("0.05")  # Short MA above long MA (uptrend)
        else:
            score -= Decimal("0.05")  # Short MA below long MA (downtrend)
        factors += 1

    # EMA analysis
    if indicators.ema_12 is not None and indicators.ema_26 is not None:
        if indicators.ema_12 > indicators.ema_26:
            score += Decimal("0.05")  # Fast EMA above slow EMA
        else:
            score -= Decimal("0.05")  # Fast EMA below slow EMA
        factors += 1

    # Ensure probability is within valid range
    score = max(Decimal("0.0"), min(Decimal("1.0"), score))

    return score


def calculate_confidence(indicators: Any, data_points: int) -> Decimal:
    """Calculate confidence level in the analysis.

    Confidence is based on the number of available indicators
    and the amount of historical data.

    Args:
        indicators: TechnicalIndicators object
        data_points: Number of data points used in analysis

    Returns:
        Confidence level between 0.0 and 1.0

    Example:
        >>> confidence = calculate_confidence(indicators, 30)
        >>> print(f"Confidence: {confidence}")
        Confidence: 0.85
    """
    base_confidence = Decimal("0.5")

    # Count available indicators
    available_indicators = 0
    if indicators.sma_20 is not None:
        available_indicators += 1
    if indicators.sma_50 is not None:
        available_indicators += 1
    if indicators.ema_12 is not None:
        available_indicators += 1
    if indicators.ema_26 is not None:
        available_indicators += 1
    if indicators.rsi is not None:
        available_indicators += 1
    if indicators.macd is not None:
        available_indicators += 1
    if indicators.bollinger_upper is not None:
        available_indicators += 1

    # More indicators = higher confidence
    indicator_boost = Decimal(str(available_indicators * 0.05))

    # More data points = higher confidence
    if data_points >= 50:
        data_boost = Decimal("0.3")
    elif data_points >= 30:
        data_boost = Decimal("0.2")
    elif data_points >= 20:
        data_boost = Decimal("0.1")
    else:
        data_boost = Decimal("0.0")

    confidence = base_confidence + indicator_boost + data_boost

    # Ensure confidence is within valid range
    confidence = max(Decimal("0.1"), min(Decimal("0.95"), confidence))

    return confidence
