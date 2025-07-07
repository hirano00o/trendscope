"""Stock data fetching functionality using yfinance."""

import re
import time
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import yfinance as yf

from trendscope_backend.utils.logging import setup_logger

logger = setup_logger(__name__)


class StockDataError(Exception):
    """Base exception for stock data related errors.

    Raised when there are issues with stock data fetching or processing.
    """

    pass


class InvalidSymbolError(StockDataError):
    """Exception raised for invalid stock symbols.

    Raised when a stock symbol doesn't meet validation criteria
    or contains invalid characters.
    """

    pass


class DataUnavailableError(StockDataError):
    """Exception raised when stock data is not available.

    Raised when yfinance returns empty data or no data is found
    for the requested symbol and time period.
    """

    pass


class StockDataFetcher:
    """Stock data fetcher using yfinance library.

    Provides functionality to fetch stock data from Yahoo Finance with
    caching, retry mechanism, and comprehensive error handling.

    Args:
        cache_enabled: Enable/disable caching of fetched data
        cache_ttl: Time-to-live for cached data in seconds
        max_retries: Maximum number of retry attempts for failed requests

    Example:
        >>> fetcher = StockDataFetcher(cache_enabled=True, cache_ttl=300)
        >>> data = fetcher.fetch_stock_data("AAPL", period="1mo")
        >>> print(data.head())
    """

    def __init__(
        self,
        cache_enabled: bool = True,
        cache_ttl: int = 300,
        max_retries: int = 3,
    ) -> None:
        """Initialize StockDataFetcher with configuration options.

        Args:
            cache_enabled: Enable/disable caching of fetched data
            cache_ttl: Time-to-live for cached data in seconds (default: 300)
            max_retries: Maximum number of retry attempts (default: 3)
        """
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.max_retries = max_retries
        self._cache: dict[str, tuple[Any, datetime]] = {}

        logger.info(
            f"StockDataFetcher initialized: cache_enabled={cache_enabled}, "
            f"cache_ttl={cache_ttl}, max_retries={max_retries}"
        )

    def validate_symbol(self, symbol: str | None) -> None:
        """Validate stock symbol format and constraints.

        Args:
            symbol: Stock symbol to validate

        Raises:
            InvalidSymbolError: If symbol is invalid

        Example:
            >>> fetcher = StockDataFetcher()
            >>> fetcher.validate_symbol("AAPL")  # Valid - no exception
            >>> fetcher.validate_symbol("")  # Raises InvalidSymbolError
        """
        if symbol is None:
            raise InvalidSymbolError("Symbol cannot be None")

        if not symbol or symbol.strip() == "":
            raise InvalidSymbolError("Symbol cannot be empty")

        if len(symbol) > 20:
            raise InvalidSymbolError("Symbol too long (max 20 characters)")

        # Check for valid characters (letters, numbers, dots, hyphens)
        if not re.match(r"^[A-Za-z0-9.-]+$", symbol):
            raise InvalidSymbolError("Symbol contains invalid characters")

        logger.debug(f"Symbol validation passed: {symbol}")

    def fetch_stock_data(
        self,
        symbol: str,
        period: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> pd.DataFrame:
        """Fetch stock data for given symbol and time period.

        Args:
            symbol: Stock symbol to fetch data for
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            start: Start date for data fetching
            end: End date for data fetching

        Returns:
            DataFrame with stock data (Open, High, Low, Close, Volume)

        Raises:
            InvalidSymbolError: If symbol is invalid
            DataUnavailableError: If no data is available
            StockDataError: If fetching fails

        Example:
            >>> fetcher = StockDataFetcher()
            >>> data = fetcher.fetch_stock_data("AAPL", period="1mo")
            >>> print(data.columns.tolist())
            ['Open', 'High', 'Low', 'Close', 'Volume']
        """
        self.validate_symbol(symbol)

        # Create cache key
        cache_key = self._create_cache_key(symbol, period, start, end)

        # Check cache if enabled
        if self.cache_enabled and cache_key in self._cache:
            if not self._is_cache_expired(cache_key):
                logger.debug(f"Cache hit for {symbol}")
                return self._cache[cache_key][0]
            else:
                logger.debug(f"Cache expired for {symbol}")
                del self._cache[cache_key]

        # Fetch data with retry mechanism
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching data for {symbol} (attempt {attempt + 1})")

                ticker = yf.Ticker(symbol)

                if period:
                    data = ticker.history(period=period)
                else:
                    data = ticker.history(start=start, end=end)

                if data.empty:
                    raise DataUnavailableError(
                        f"No data available for symbol: {symbol}"
                    )

                # Cache the result if caching is enabled
                if self.cache_enabled:
                    self._cache[cache_key] = (data, datetime.now())
                    logger.debug(f"Data cached for {symbol}")

                logger.info(
                    f"Successfully fetched {len(data)} data points for {symbol}"
                )
                return data

            except Exception as e:
                if isinstance(e, DataUnavailableError | InvalidSymbolError):
                    raise

                logger.warning(f"Attempt {attempt + 1} failed for {symbol}: {str(e)}")

                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)  # Exponential backoff
                else:
                    raise StockDataError(
                        f"Failed to fetch stock data for {symbol}: {str(e)}"
                    ) from e

        raise StockDataError(
            f"Failed to fetch stock data for {symbol} after {self.max_retries} attempts"
        )

    def get_stock_info(self, symbol: str) -> dict[str, Any]:
        """Get stock information and metadata.

        Args:
            symbol: Stock symbol to get info for

        Returns:
            Dictionary containing stock information

        Raises:
            InvalidSymbolError: If symbol is invalid
            StockDataError: If fetching stock info fails

        Example:
            >>> fetcher = StockDataFetcher()
            >>> info = fetcher.get_stock_info("AAPL")
            >>> print(info["longName"])
            'Apple Inc.'
        """
        self.validate_symbol(symbol)

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info:
                raise StockDataError(f"Failed to fetch stock info for {symbol}")

            logger.info(f"Successfully fetched stock info for {symbol}")
            return info

        except Exception as e:
            logger.error(f"Failed to fetch stock info for {symbol}: {str(e)}")
            raise StockDataError(
                f"Failed to fetch stock info for {symbol}: {str(e)}"
            ) from e

    def clear_cache(self) -> None:
        """Clear all cached data.

        Example:
            >>> fetcher = StockDataFetcher()
            >>> fetcher.clear_cache()
            >>> print(len(fetcher._cache))
            0
        """
        self._cache.clear()
        logger.info("Cache cleared")

    def _create_cache_key(
        self,
        symbol: str,
        period: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> str:
        """Create a cache key for the given parameters.

        Args:
            symbol: Stock symbol
            period: Time period
            start: Start date
            end: End date

        Returns:
            Cache key string
        """
        if period:
            return f"{symbol}_{period}"
        else:
            start_str = start.strftime("%Y-%m-%d") if start else "None"
            end_str = end.strftime("%Y-%m-%d") if end else "None"
            return f"{symbol}_{start_str}_{end_str}"

    def _is_cache_expired(self, cache_key: str) -> bool:
        """Check if cache entry is expired.

        Args:
            cache_key: Cache key to check

        Returns:
            True if cache entry is expired, False otherwise
        """
        if cache_key not in self._cache:
            return True

        cached_time = self._cache[cache_key][1]
        expiry_time = cached_time + timedelta(seconds=self.cache_ttl)
        return datetime.now() > expiry_time
