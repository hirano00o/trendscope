"""Historical stock data API endpoints.

This module provides REST API endpoints for retrieving historical stock price data
(OHLCV) from yfinance, formatted for frontend chart display.
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import HTTPException, Query

from trendscope_backend.data.models import StockData, TimeSeriesData
from trendscope_backend.data.stock_data import StockDataFetcher
from trendscope_backend.utils.logging import get_logger
from trendscope_backend.api.analysis import validate_symbol, validate_period

logger = get_logger(__name__)


def _convert_dataframe_to_stock_data(df: pd.DataFrame, symbol: str) -> List[StockData]:
    """Convert pandas DataFrame to list of StockData objects.
    
    Args:
        df: DataFrame with OHLCV data (from yfinance)
        symbol: Stock symbol
        
    Returns:
        List of StockData objects
        
    Raises:
        ValueError: If DataFrame structure is invalid
    """
    if df.empty:
        raise ValueError("DataFrame is empty")
    
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    stock_data_list = []
    
    for date_index, row in df.iterrows():
        try:
            # Convert pandas timestamp to datetime
            if hasattr(date_index, 'to_pydatetime'):
                date = date_index.to_pydatetime()
            else:
                date = pd.to_datetime(date_index).to_pydatetime()
            
            stock_data = StockData(
                symbol=symbol,
                date=date,
                open=Decimal(str(row['Open'])),
                high=Decimal(str(row['High'])),
                low=Decimal(str(row['Low'])),
                close=Decimal(str(row['Close'])),
                volume=int(row['Volume'])
            )
            stock_data_list.append(stock_data)
        except Exception as e:
            logger.warning(f"Failed to convert row for {symbol} at {date_index}: {e}")
            continue
    
    if not stock_data_list:
        raise ValueError("No valid stock data could be converted")
    
    logger.info(f"Converted {len(stock_data_list)} data points from DataFrame to StockData objects")
    return stock_data_list


def _format_historical_data_for_api(stock_data_list: List[StockData]) -> List[Dict[str, Any]]:
    """Format stock data list for frontend API consumption.
    
    Converts StockData objects to dictionary format optimized for chart display.
    
    Args:
        stock_data_list: List of StockData objects
        
    Returns:
        List of dictionaries with formatted data for charts
        
    Example:
        >>> formatted_data = _format_historical_data_for_api(stock_data)
        >>> print(formatted_data[0])
        {
            "date": "2024-01-15",
            "open": 150.25,
            "high": 152.75,
            "low": 149.50,
            "close": 151.80,
            "volume": 1234567
        }
    """
    formatted_data = []
    
    for stock_data in stock_data_list:
        formatted_point = {
            "date": stock_data.date.strftime("%Y-%m-%d"),
            "open": float(stock_data.open),
            "high": float(stock_data.high),
            "low": float(stock_data.low),
            "close": float(stock_data.close),
            "volume": stock_data.volume
        }
        formatted_data.append(formatted_point)
    
    # Sort by date to ensure proper chronological order
    formatted_data.sort(key=lambda x: x["date"])
    
    return formatted_data


async def get_historical_data(
    symbol: str,
    period: Optional[str] = Query("1mo", description="Time period (e.g., '1mo', '3mo', '6mo', '1y')"),
    start_date: Optional[datetime] = Query(None, description="Custom start date"),
    end_date: Optional[datetime] = Query(None, description="Custom end date")
) -> Dict[str, Any]:
    """Get historical stock price data (OHLCV) for chart display.
    
    Retrieves historical stock price data from yfinance and formats it
    for frontend chart consumption. Supports both predefined periods
    and custom date ranges.
    
    Args:
        symbol: Stock symbol to retrieve data for (e.g., 'AAPL', '7203.T')
        period: Predefined time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
        start_date: Custom start date (alternative to period)
        end_date: Custom end date (required if start_date provided)
        
    Returns:
        Dictionary containing historical data and metadata
        
    Raises:
        HTTPException: If data retrieval fails or parameters are invalid
        
    Example:
        >>> data = await get_historical_data("AAPL", period="1mo")
        >>> print(len(data["data"]["historical_data"]))
        22
    """
    try:
        # Validate symbol
        symbol = validate_symbol(symbol)
        logger.info(f"Starting historical data retrieval for symbol: {symbol}")
        
        # Validate date/period parameters
        if period and (start_date or end_date):
            raise ValueError("Cannot specify both period and custom date range")
        
        if (start_date or end_date) and not (start_date and end_date):
            raise ValueError("Both start_date and end_date required for custom date range")
        
        if start_date and end_date and start_date >= end_date:
            raise ValueError("start_date must be before end_date")
        
        # Validate period if provided
        if period:
            period = validate_period(period)
        
        # Fetch stock data
        data_fetcher = StockDataFetcher()
        
        if period:
            stock_data_df = data_fetcher.fetch_stock_data(symbol, period=period)
        else:
            stock_data_df = data_fetcher.fetch_stock_data(
                symbol, start_date=start_date, end_date=end_date
            )
        
        if stock_data_df is None or (hasattr(stock_data_df, 'empty') and stock_data_df.empty):
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Data Not Available",
                    "message": f"No historical data available for symbol {symbol}",
                    "symbol": symbol,
                },
            )
        
        logger.info(f"Retrieved {len(stock_data_df)} data points for {symbol}")
        
        # Convert DataFrame to StockData objects
        stock_data_list = _convert_dataframe_to_stock_data(stock_data_df, symbol)
        
        # Format data for API response
        historical_data = _format_historical_data_for_api(stock_data_list)
        
        # Create TimeSeriesData for metadata
        time_series = TimeSeriesData(
            symbol=symbol,
            data=stock_data_list,
            period=period or f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        )
        
        # Calculate additional metrics for metadata
        prices = [float(data.close) for data in stock_data_list]
        current_price = prices[-1] if prices else 0
        price_change = prices[-1] - prices[0] if len(prices) > 1 else 0
        price_change_percent = (price_change / prices[0] * 100) if len(prices) > 1 and prices[0] > 0 else 0
        
        volumes = [data.volume for data in stock_data_list]
        avg_volume = sum(volumes) / len(volumes) if volumes else 0
        
        # Generate response
        response = {
            "symbol": symbol,
            "period": time_series.period,
            "data_points": time_series.data_points,
            "start_date": time_series.start_date.strftime("%Y-%m-%d"),
            "end_date": time_series.end_date.strftime("%Y-%m-%d"),
            "historical_data": historical_data,
            "metadata": {
                "current_price": current_price,
                "price_change": round(price_change, 2),
                "price_change_percent": round(price_change_percent, 2),
                "average_volume": int(avg_volume),
                "data_quality": "high" if len(historical_data) > 20 else "medium" if len(historical_data) > 10 else "low",
                "retrieved_at": datetime.now(UTC).isoformat() + "Z"
            }
        }
        
        logger.info(f"Historical data retrieval completed for {symbol}")
        
        # Return wrapped response for frontend API client compatibility
        return {
            "success": True,
            "data": response
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        error_msg = str(e)
        logger.warning(f"Validation error for {symbol}: {e}")
        
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid Parameter",
                "message": error_msg,
                "symbol": symbol,
            },
        ) from e
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Historical data retrieval error for {symbol}: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Data Retrieval Error",
                "message": "An error occurred while retrieving historical data",
                "symbol": symbol,
            },
        ) from e