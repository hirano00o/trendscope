"""Tests for stock data fetching functionality."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from trendscope_backend.data.stock_data import (
    DataUnavailableError,
    InvalidSymbolError,
    StockDataError,
    StockDataFetcher,
)


class TestStockDataFetcher:
    """Test cases for StockDataFetcher class."""

    def test_stock_data_fetcher_init_default(self) -> None:
        """Test StockDataFetcher initialization with default values."""
        fetcher = StockDataFetcher()
        assert fetcher.cache_enabled is True
        assert fetcher.cache_ttl == 300  # 5 minutes default
        assert fetcher.max_retries == 3

    def test_stock_data_fetcher_init_with_params(self) -> None:
        """Test StockDataFetcher initialization with custom parameters."""
        fetcher = StockDataFetcher(cache_enabled=False, cache_ttl=600, max_retries=5)
        assert fetcher.cache_enabled is False
        assert fetcher.cache_ttl == 600
        assert fetcher.max_retries == 5

    def test_validate_symbol_valid(self) -> None:
        """Test symbol validation with valid symbols."""
        fetcher = StockDataFetcher()
        # Should not raise any exception
        fetcher.validate_symbol("AAPL")
        fetcher.validate_symbol("GOOGL")
        fetcher.validate_symbol("MSFT")

    def test_validate_symbol_invalid_empty(self) -> None:
        """Test symbol validation with empty symbol."""
        fetcher = StockDataFetcher()
        with pytest.raises(InvalidSymbolError, match="Symbol cannot be empty"):
            fetcher.validate_symbol("")

    def test_validate_symbol_invalid_none(self) -> None:
        """Test symbol validation with None symbol."""
        fetcher = StockDataFetcher()
        with pytest.raises(InvalidSymbolError, match="Symbol cannot be None"):
            fetcher.validate_symbol(None)

    def test_validate_symbol_invalid_too_long(self) -> None:
        """Test symbol validation with too long symbol."""
        fetcher = StockDataFetcher()
        long_symbol = "A" * 21  # 21 characters
        with pytest.raises(InvalidSymbolError, match="Symbol too long"):
            fetcher.validate_symbol(long_symbol)

    def test_validate_symbol_invalid_characters(self) -> None:
        """Test symbol validation with invalid characters."""
        fetcher = StockDataFetcher()
        with pytest.raises(
            InvalidSymbolError, match="Symbol contains invalid characters"
        ):
            fetcher.validate_symbol("AAP@L")

    @patch("yfinance.Ticker")
    def test_fetch_stock_data_success(self, mock_ticker: Mock) -> None:
        """Test successful stock data fetching."""
        # Mock successful yfinance data
        mock_data = pd.DataFrame(
            {
                "Open": [150.0, 151.0, 152.0],
                "High": [155.0, 156.0, 157.0],
                "Low": [148.0, 149.0, 150.0],
                "Close": [153.0, 154.0, 155.0],
                "Volume": [1000000, 1100000, 1200000],
            },
            index=pd.date_range("2023-01-01", periods=3, freq="D"),
        )

        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_ticker_instance

        fetcher = StockDataFetcher()
        result = fetcher.fetch_stock_data("AAPL", period="1mo")

        assert result is not None
        assert len(result) == 3
        assert list(result.columns) == ["Open", "High", "Low", "Close", "Volume"]
        mock_ticker.assert_called_once_with("AAPL")

    @patch("yfinance.Ticker")
    def test_fetch_stock_data_empty_data(self, mock_ticker: Mock) -> None:
        """Test fetching stock data when no data is available."""
        # Mock empty DataFrame
        mock_data = pd.DataFrame()

        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_ticker_instance

        fetcher = StockDataFetcher()
        with pytest.raises(DataUnavailableError, match="No data available"):
            fetcher.fetch_stock_data("INVALID", period="1mo")

    @patch("yfinance.Ticker")
    def test_fetch_stock_data_yfinance_exception(self, mock_ticker: Mock) -> None:
        """Test handling of yfinance exceptions."""
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.side_effect = Exception("Network error")
        mock_ticker.return_value = mock_ticker_instance

        fetcher = StockDataFetcher()
        with pytest.raises(StockDataError, match="Failed to fetch stock data"):
            fetcher.fetch_stock_data("AAPL", period="1mo")

    @patch("yfinance.Ticker")
    def test_fetch_stock_data_with_date_range(self, mock_ticker: Mock) -> None:
        """Test fetching stock data with specific date range."""
        mock_data = pd.DataFrame(
            {
                "Open": [150.0, 151.0],
                "High": [155.0, 156.0],
                "Low": [148.0, 149.0],
                "Close": [153.0, 154.0],
                "Volume": [1000000, 1100000],
            },
            index=pd.date_range("2023-01-01", periods=2, freq="D"),
        )

        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_ticker_instance

        fetcher = StockDataFetcher()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 2)

        result = fetcher.fetch_stock_data("AAPL", start=start_date, end=end_date)

        assert result is not None
        assert len(result) == 2
        mock_ticker_instance.history.assert_called_once_with(
            start=start_date, end=end_date
        )

    @patch("yfinance.Ticker")
    def test_fetch_stock_data_with_cache(self, mock_ticker: Mock) -> None:
        """Test stock data fetching with caching enabled."""
        mock_data = pd.DataFrame(
            {
                "Open": [150.0],
                "High": [155.0],
                "Low": [148.0],
                "Close": [153.0],
                "Volume": [1000000],
            },
            index=pd.date_range("2023-01-01", periods=1, freq="D"),
        )

        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_ticker_instance

        fetcher = StockDataFetcher(cache_enabled=True, cache_ttl=300)

        # First call should fetch from API
        result1 = fetcher.fetch_stock_data("AAPL", period="1d")
        assert result1 is not None

        # Second call should use cache (no additional API call)
        result2 = fetcher.fetch_stock_data("AAPL", period="1d")
        assert result2 is not None

        # Should only be called once due to caching
        mock_ticker.assert_called_once_with("AAPL")

    def test_fetch_stock_data_cache_disabled(self) -> None:
        """Test stock data fetching with caching disabled."""
        fetcher = StockDataFetcher(cache_enabled=False)

        # Test that cache is properly disabled
        assert fetcher.cache_enabled is False
        assert len(fetcher._cache) == 0

    def test_clear_cache(self) -> None:
        """Test clearing the cache."""
        fetcher = StockDataFetcher(cache_enabled=True)

        # Add some dummy data to cache
        fetcher._cache["test_key"] = ("test_data", datetime.now())
        assert len(fetcher._cache) == 1

        # Clear cache
        fetcher.clear_cache()
        assert len(fetcher._cache) == 0

    def test_cache_expiry(self) -> None:
        """Test cache expiry functionality."""
        fetcher = StockDataFetcher(cache_enabled=True, cache_ttl=1)  # 1 second TTL

        # Add expired data to cache
        expired_time = datetime.now() - timedelta(seconds=2)
        fetcher._cache["expired_key"] = ("expired_data", expired_time)

        # Check if cache entry is considered expired
        assert fetcher._is_cache_expired("expired_key") is True

        # Add fresh data to cache
        fresh_time = datetime.now()
        fetcher._cache["fresh_key"] = ("fresh_data", fresh_time)

        # Check if cache entry is not expired
        assert fetcher._is_cache_expired("fresh_key") is False

    def test_retry_mechanism(self) -> None:
        """Test retry mechanism for failed requests."""
        fetcher = StockDataFetcher(max_retries=3)

        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker_instance = Mock()
            # First two calls fail, third succeeds
            mock_ticker_instance.history.side_effect = [
                Exception("Network error"),
                Exception("Timeout"),
                pd.DataFrame(
                    {
                        "Open": [150.0],
                        "High": [155.0],
                        "Low": [148.0],
                        "Close": [153.0],
                        "Volume": [1000000],
                    },
                    index=pd.date_range("2023-01-01", periods=1, freq="D"),
                ),
            ]
            mock_ticker.return_value = mock_ticker_instance

            result = fetcher.fetch_stock_data("AAPL", period="1d")
            assert result is not None
            assert len(result) == 1

            # Should have made 3 calls (2 failures + 1 successful)
            assert mock_ticker_instance.history.call_count == 3

    def test_get_stock_info_success(self) -> None:
        """Test successful stock info retrieval."""
        with patch("yfinance.Ticker") as mock_ticker:
            mock_info = {
                "longName": "Apple Inc.",
                "symbol": "AAPL",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "marketCap": 2500000000000,
                "currency": "USD",
            }

            mock_ticker_instance = Mock()
            mock_ticker_instance.info = mock_info
            mock_ticker.return_value = mock_ticker_instance

            fetcher = StockDataFetcher()
            result = fetcher.get_stock_info("AAPL")

            assert result == mock_info
            assert result["longName"] == "Apple Inc."
            assert result["symbol"] == "AAPL"

    def test_get_stock_info_failure(self) -> None:
        """Test stock info retrieval failure."""
        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker_instance = Mock()
            mock_ticker_instance.info = {}  # Empty info indicates failure
            mock_ticker.return_value = mock_ticker_instance

            fetcher = StockDataFetcher()
            with pytest.raises(StockDataError, match="Failed to fetch stock info"):
                fetcher.get_stock_info("INVALID")


class TestStockDataExceptions:
    """Test cases for stock data exceptions."""

    def test_stock_data_error_creation(self) -> None:
        """Test StockDataError exception creation."""
        error = StockDataError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_invalid_symbol_error_creation(self) -> None:
        """Test InvalidSymbolError exception creation."""
        error = InvalidSymbolError("Invalid symbol: XYZ")
        assert str(error) == "Invalid symbol: XYZ"
        assert isinstance(error, StockDataError)

    def test_data_unavailable_error_creation(self) -> None:
        """Test DataUnavailableError exception creation."""
        error = DataUnavailableError("No data available for symbol")
        assert str(error) == "No data available for symbol"
        assert isinstance(error, StockDataError)
