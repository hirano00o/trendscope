"""Tests for technical indicators calculation module."""

from datetime import datetime
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from trendscope_backend.analysis.technical.indicators import (
    TechnicalIndicatorCalculator,
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
)
from trendscope_backend.data.models import StockData


class TestSMACalculation:
    """Test cases for Simple Moving Average (SMA) calculation."""

    def test_calculate_sma_basic(self) -> None:
        """Test basic SMA calculation with valid data."""
        prices = pd.Series([10, 12, 14, 16, 18, 20, 22, 24, 26, 28])
        result = calculate_sma(prices, window=5)

        # First 4 values should be NaN
        assert pd.isna(result.iloc[:4]).all()

        # Fifth value should be mean of first 5 values: (10+12+14+16+18)/5 = 14
        assert result.iloc[4] == 14.0

        # Sixth value should be mean of values 2-6: (12+14+16+18+20)/5 = 16
        assert result.iloc[5] == 16.0

    def test_calculate_sma_insufficient_data(self) -> None:
        """Test SMA calculation with insufficient data points."""
        prices = pd.Series([10, 12, 14])
        result = calculate_sma(prices, window=5)

        # All values should be NaN when we have fewer data points than window
        assert pd.isna(result).all()

    def test_calculate_sma_single_window(self) -> None:
        """Test SMA calculation with window size of 1."""
        prices = pd.Series([10, 12, 14, 16, 18])
        result = calculate_sma(prices, window=1)

        # Window of 1 should return the original values (but as float dtype)
        expected = pd.Series([10.0, 12.0, 14.0, 16.0, 18.0])
        pd.testing.assert_series_equal(result, expected)

    def test_calculate_sma_invalid_window(self) -> None:
        """Test SMA calculation with invalid window size."""
        prices = pd.Series([10, 12, 14, 16, 18])

        with pytest.raises(ValueError, match="Window size must be positive"):
            calculate_sma(prices, window=0)

        with pytest.raises(ValueError, match="Window size must be positive"):
            calculate_sma(prices, window=-1)

    def test_calculate_sma_empty_series(self) -> None:
        """Test SMA calculation with empty price series."""
        prices = pd.Series([], dtype=float)
        result = calculate_sma(prices, window=5)

        assert len(result) == 0


class TestEMACalculation:
    """Test cases for Exponential Moving Average (EMA) calculation."""

    def test_calculate_ema_basic(self) -> None:
        """Test basic EMA calculation with valid data."""
        prices = pd.Series([10.0, 12.0, 14.0, 16.0, 18.0, 20.0])
        result = calculate_ema(prices, span=3)

        # EMA should have same length as input
        assert len(result) == len(prices)

        # First value should equal first price
        assert result.iloc[0] == 10.0

        # Values should generally increase (following trend)
        assert result.iloc[-1] > result.iloc[0]

    def test_calculate_ema_span_validation(self) -> None:
        """Test EMA calculation with invalid span values."""
        prices = pd.Series([10.0, 12.0, 14.0, 16.0, 18.0])

        with pytest.raises(ValueError, match="Span must be positive"):
            calculate_ema(prices, span=0)

        with pytest.raises(ValueError, match="Span must be positive"):
            calculate_ema(prices, span=-1)

    def test_calculate_ema_single_value(self) -> None:
        """Test EMA calculation with single data point."""
        prices = pd.Series([10.0])
        result = calculate_ema(prices, span=3)

        assert len(result) == 1
        assert result.iloc[0] == 10.0

    def test_calculate_ema_empty_series(self) -> None:
        """Test EMA calculation with empty price series."""
        prices = pd.Series([], dtype=float)
        result = calculate_ema(prices, span=3)

        assert len(result) == 0


class TestRSICalculation:
    """Test cases for Relative Strength Index (RSI) calculation."""

    def test_calculate_rsi_basic(self) -> None:
        """Test basic RSI calculation with valid data."""
        # Create price series with clear up and down movements
        prices = pd.Series([10, 11, 12, 11, 10, 11, 12, 13, 14, 13, 12, 13, 14, 15])
        result = calculate_rsi(prices, window=14)

        # RSI should be between 0 and 100
        valid_values = result.dropna()
        assert (valid_values >= 0).all()
        assert (valid_values <= 100).all()

        # First (window-1) values should be NaN
        assert pd.isna(result.iloc[:13]).all()

    def test_calculate_rsi_trending_up(self) -> None:
        """Test RSI calculation with consistently increasing prices."""
        prices = pd.Series(range(1, 21))  # Consistently increasing prices
        result = calculate_rsi(prices, window=14)

        # RSI should be high (closer to 100) for uptrending prices
        final_rsi = result.iloc[-1]
        assert final_rsi > 70  # Typically considered overbought

    def test_calculate_rsi_trending_down(self) -> None:
        """Test RSI calculation with consistently decreasing prices."""
        prices = pd.Series(range(20, 0, -1))  # Consistently decreasing prices
        result = calculate_rsi(prices, window=14)

        # RSI should be low (closer to 0) for downtrending prices
        final_rsi = result.iloc[-1]
        assert final_rsi < 30  # Typically considered oversold

    def test_calculate_rsi_invalid_window(self) -> None:
        """Test RSI calculation with invalid window size."""
        prices = pd.Series([10, 11, 12, 13, 14])

        with pytest.raises(ValueError, match="Window size must be positive"):
            calculate_rsi(prices, window=0)

    def test_calculate_rsi_insufficient_data(self) -> None:
        """Test RSI calculation with insufficient data points."""
        prices = pd.Series([10, 11, 12])
        result = calculate_rsi(prices, window=14)

        # All values should be NaN when we have fewer data points than window
        assert pd.isna(result).all()


class TestMACDCalculation:
    """Test cases for MACD (Moving Average Convergence Divergence) calculation."""

    def test_calculate_macd_basic(self) -> None:
        """Test basic MACD calculation with valid data."""
        prices = pd.Series(
            [
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
                20,
                21,
                22,
                23,
                24,
                25,
                26,
                27,
                28,
                29,
                30,
            ]
        )
        macd_line, signal_line, histogram = calculate_macd(
            prices, fast=12, slow=26, signal=9
        )

        # All components should have same length as input
        assert len(macd_line) == len(prices)
        assert len(signal_line) == len(prices)
        assert len(histogram) == len(prices)

        # Histogram should equal macd_line - signal_line (where both are not NaN)
        valid_mask = ~(pd.isna(macd_line) | pd.isna(signal_line))
        if valid_mask.any():
            pd.testing.assert_series_equal(
                histogram[valid_mask],
                macd_line[valid_mask] - signal_line[valid_mask],
                check_names=False,
            )

    def test_calculate_macd_parameter_validation(self) -> None:
        """Test MACD calculation with invalid parameters."""
        prices = pd.Series([10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20])

        # Fast period must be less than slow period
        with pytest.raises(
            ValueError, match="Fast period must be less than slow period"
        ):
            calculate_macd(prices, fast=26, slow=12, signal=9)

        # Parameters must be positive
        with pytest.raises(ValueError, match="All periods must be positive"):
            calculate_macd(prices, fast=0, slow=26, signal=9)

    def test_calculate_macd_trending_up(self) -> None:
        """Test MACD behavior with uptrending prices."""
        prices = pd.Series(range(1, 51))  # Strong uptrend
        macd_line, signal_line, histogram = calculate_macd(
            prices, fast=12, slow=26, signal=9
        )

        # In an uptrend, MACD line should eventually be above signal line
        valid_macd = macd_line.dropna()
        valid_signal = signal_line.dropna()

        if len(valid_macd) > 10 and len(valid_signal) > 10:
            # Check last few values where both are available
            assert valid_macd.iloc[-1] > valid_signal.iloc[-1]

    def test_calculate_macd_insufficient_data(self) -> None:
        """Test MACD calculation with insufficient data points."""
        prices = pd.Series([10, 11, 12])
        macd_line, signal_line, histogram = calculate_macd(
            prices, fast=12, slow=26, signal=9
        )

        # All values should be NaN when we have insufficient data
        assert pd.isna(macd_line).all()
        assert pd.isna(signal_line).all()
        assert pd.isna(histogram).all()


class TestBollingerBandsCalculation:
    """Test cases for Bollinger Bands calculation."""

    def test_calculate_bollinger_bands_basic(self) -> None:
        """Test basic Bollinger Bands calculation with valid data."""
        prices = pd.Series(
            [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]
        )
        upper_band, middle_band, lower_band = calculate_bollinger_bands(
            prices, window=10, num_std=2
        )

        # All bands should have same length as input
        assert len(upper_band) == len(prices)
        assert len(middle_band) == len(prices)
        assert len(lower_band) == len(prices)

        # Middle band should equal SMA
        sma = calculate_sma(prices, window=10)
        pd.testing.assert_series_equal(middle_band, sma, check_names=False)

        # Upper band should be above middle band (where not NaN)
        valid_mask = ~pd.isna(upper_band)
        if valid_mask.any():
            assert (upper_band[valid_mask] >= middle_band[valid_mask]).all()

        # Lower band should be below middle band (where not NaN)
        if valid_mask.any():
            assert (lower_band[valid_mask] <= middle_band[valid_mask]).all()

    def test_calculate_bollinger_bands_standard_deviation(self) -> None:
        """Test Bollinger Bands with different standard deviation multipliers."""
        prices = pd.Series([10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20])

        # Calculate with 1 std and 2 std
        upper_1std, middle_1std, lower_1std = calculate_bollinger_bands(
            prices, window=5, num_std=1
        )
        upper_2std, middle_2std, lower_2std = calculate_bollinger_bands(
            prices, window=5, num_std=2
        )

        # Middle bands should be the same
        pd.testing.assert_series_equal(middle_1std, middle_2std, check_names=False)

        # 2-std bands should be wider than 1-std bands
        valid_mask = ~pd.isna(upper_1std)
        if valid_mask.any():
            assert (upper_2std[valid_mask] >= upper_1std[valid_mask]).all()
            assert (lower_2std[valid_mask] <= lower_1std[valid_mask]).all()

    def test_calculate_bollinger_bands_parameter_validation(self) -> None:
        """Test Bollinger Bands calculation with invalid parameters."""
        prices = pd.Series([10, 11, 12, 13, 14, 15])

        with pytest.raises(ValueError, match="Window size must be positive"):
            calculate_bollinger_bands(prices, window=0, num_std=2)

        with pytest.raises(
            ValueError, match="Standard deviation multiplier must be positive"
        ):
            calculate_bollinger_bands(prices, window=5, num_std=0)

    def test_calculate_bollinger_bands_insufficient_data(self) -> None:
        """Test Bollinger Bands calculation with insufficient data points."""
        prices = pd.Series([10, 11])
        upper_band, middle_band, lower_band = calculate_bollinger_bands(
            prices, window=5, num_std=2
        )

        # All values should be NaN when we have insufficient data
        assert pd.isna(upper_band).all()
        assert pd.isna(middle_band).all()
        assert pd.isna(lower_band).all()


class TestTechnicalIndicatorCalculator:
    """Test cases for TechnicalIndicatorCalculator class."""

    @pytest.fixture
    def sample_stock_data(self) -> list[StockData]:
        """Create sample stock data for testing."""
        stock_data = []
        base_price = Decimal("100.0")

        for i in range(30):
            # Create realistic OHLCV data with some volatility
            price_change = Decimal(str(np.random.uniform(-2, 2)))
            open_price = base_price + price_change
            high_price = open_price + Decimal(str(abs(np.random.uniform(0, 3))))
            low_price = open_price - Decimal(str(abs(np.random.uniform(0, 3))))
            close_price = open_price + Decimal(str(np.random.uniform(-2, 2)))

            # Ensure price relationships are valid
            high_price = max(high_price, max(open_price, close_price))
            low_price = min(low_price, min(open_price, close_price))

            stock_data.append(
                StockData(
                    symbol="TEST",
                    date=datetime(2024, 1, i + 1),
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=1000000 + int(np.random.uniform(-100000, 100000)),
                )
            )

            base_price = close_price

        return stock_data

    def test_calculator_initialization(self) -> None:
        """Test TechnicalIndicatorCalculator initialization."""
        calculator = TechnicalIndicatorCalculator()

        assert calculator is not None
        assert hasattr(calculator, "calculate_all_indicators")

    def test_calculator_sma_calculation(
        self, sample_stock_data: list[StockData]
    ) -> None:
        """Test SMA calculation through calculator."""
        calculator = TechnicalIndicatorCalculator()

        sma_20 = calculator.calculate_sma(sample_stock_data, window=20)
        sma_50 = calculator.calculate_sma(sample_stock_data, window=50)

        # SMA_20 should have values for data points >= 20
        assert sma_20 is not None

        # SMA_50 should be None due to insufficient data (only 30 points)
        assert sma_50 is None

    def test_calculator_ema_calculation(
        self, sample_stock_data: list[StockData]
    ) -> None:
        """Test EMA calculation through calculator."""
        calculator = TechnicalIndicatorCalculator()

        ema_12 = calculator.calculate_ema(sample_stock_data, span=12)
        ema_26 = calculator.calculate_ema(sample_stock_data, span=26)

        # Both EMAs should have values
        assert ema_12 is not None
        assert ema_26 is not None

    def test_calculator_rsi_calculation(
        self, sample_stock_data: list[StockData]
    ) -> None:
        """Test RSI calculation through calculator."""
        calculator = TechnicalIndicatorCalculator()

        rsi = calculator.calculate_rsi(sample_stock_data, window=14)

        # RSI should have a value
        assert rsi is not None
        assert 0 <= rsi <= 100

    def test_calculator_macd_calculation(
        self, sample_stock_data: list[StockData]
    ) -> None:
        """Test MACD calculation through calculator."""
        calculator = TechnicalIndicatorCalculator()

        macd, signal = calculator.calculate_macd(
            sample_stock_data, fast=12, slow=26, signal_period=9
        )

        # MACD components should have values
        assert macd is not None
        assert signal is not None

    def test_calculator_bollinger_bands_calculation(
        self, sample_stock_data: list[StockData]
    ) -> None:
        """Test Bollinger Bands calculation through calculator."""
        calculator = TechnicalIndicatorCalculator()

        upper, lower = calculator.calculate_bollinger_bands(
            sample_stock_data, window=20, num_std=2
        )

        # Bollinger Bands should have values
        assert upper is not None
        assert lower is not None

    def test_calculator_all_indicators(
        self, sample_stock_data: list[StockData]
    ) -> None:
        """Test calculation of all indicators together."""
        calculator = TechnicalIndicatorCalculator()

        indicators = calculator.calculate_all_indicators(sample_stock_data)

        # Should return TechnicalIndicators model
        assert indicators is not None
        assert hasattr(indicators, "sma_20")
        assert hasattr(indicators, "ema_12")
        assert hasattr(indicators, "rsi")
        assert hasattr(indicators, "macd")
        assert hasattr(indicators, "bollinger_upper")

    def test_calculator_insufficient_data_handling(self) -> None:
        """Test calculator behavior with insufficient data."""
        calculator = TechnicalIndicatorCalculator()

        # Create minimal data set
        minimal_data = [
            StockData(symbol="TEST",
                date=datetime(2024, 1, 1),
                open=Decimal("100.0"),
                high=Decimal("105.0"),
                low=Decimal("95.0"),
                close=Decimal("102.0"),
                volume=1000000,
            )
        ]

        indicators = calculator.calculate_all_indicators(minimal_data)

        # Most indicators should be None due to insufficient data
        assert indicators.sma_20 is None
        assert indicators.sma_50 is None
        assert indicators.rsi is None

    def test_calculator_empty_data_handling(self) -> None:
        """Test calculator behavior with empty data."""
        calculator = TechnicalIndicatorCalculator()

        with pytest.raises(ValueError, match="Stock data cannot be empty"):
            calculator.calculate_all_indicators([])

    def test_calculator_data_validation(self) -> None:
        """Test calculator input data validation."""
        calculator = TechnicalIndicatorCalculator()

        # Test with None input
        with pytest.raises(ValueError, match="Stock data cannot be None"):
            calculator.calculate_all_indicators(None)

        # Test with invalid data type
        with pytest.raises(TypeError):
            calculator.calculate_all_indicators("invalid_data")
