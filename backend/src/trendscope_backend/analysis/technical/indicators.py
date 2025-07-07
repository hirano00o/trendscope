"""Technical indicators calculation module.

This module provides functions and classes for calculating various technical
analysis indicators used in stock market analysis.
"""

from decimal import Decimal

import numpy as np
import pandas as pd

from trendscope_backend.data.models import StockData, TechnicalIndicators


def calculate_sma(prices: pd.Series, window: int) -> pd.Series:
    """Calculate Simple Moving Average (SMA).

    Computes the simple moving average over a specified window period.
    The SMA is the arithmetic mean of prices over the window period.

    Args:
        prices: Price series data
        window: Number of periods for the moving average

    Returns:
        Series containing SMA values, with NaN for insufficient data periods

    Raises:
        ValueError: If window size is not positive

    Example:
        >>> prices = pd.Series([10, 12, 14, 16, 18])
        >>> sma = calculate_sma(prices, window=3)
        >>> print(sma.iloc[2])  # First valid SMA value
        12.0
    """
    if window <= 0:
        raise ValueError("Window size must be positive")

    if len(prices) == 0:
        return pd.Series([], dtype=float)

    return prices.rolling(window=window, min_periods=window).mean()


def calculate_ema(prices: pd.Series, span: int) -> pd.Series:
    """Calculate Exponential Moving Average (EMA).

    Computes the exponential moving average which gives more weight
    to recent prices. Uses pandas ewm with span parameter.

    Args:
        prices: Price series data
        span: Span parameter for exponential smoothing

    Returns:
        Series containing EMA values

    Raises:
        ValueError: If span is not positive

    Example:
        >>> prices = pd.Series([10, 12, 14, 16, 18])
        >>> ema = calculate_ema(prices, span=3)
        >>> print(ema.iloc[-1])  # Most recent EMA value
    """
    if span <= 0:
        raise ValueError("Span must be positive")

    if len(prices) == 0:
        return pd.Series([], dtype=float)

    return prices.ewm(span=span, adjust=False).mean()


def calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI).

    The RSI is a momentum oscillator that measures the speed and magnitude
    of price changes. RSI oscillates between 0 and 100.

    Args:
        prices: Price series data
        window: Period for RSI calculation (default 14)

    Returns:
        Series containing RSI values (0-100), with NaN for insufficient data

    Raises:
        ValueError: If window size is not positive

    Example:
        >>> prices = pd.Series([10, 11, 10, 12, 11, 13, 12, 14])
        >>> rsi = calculate_rsi(prices, window=6)
        >>> print(f"RSI: {rsi.iloc[-1]:.2f}")
    """
    if window <= 0:
        raise ValueError("Window size must be positive")

    if len(prices) == 0:
        return pd.Series([], dtype=float)

    if len(prices) < window + 1:
        return pd.Series([np.nan] * len(prices), index=prices.index)

    # Calculate price changes
    delta = prices.diff()

    # Separate gains and losses
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)

    # Calculate average gains and losses
    avg_gains = gains.rolling(window=window, min_periods=window).mean()
    avg_losses = losses.rolling(window=window, min_periods=window).mean()

    # Calculate RS (Relative Strength)
    rs = avg_gains / avg_losses

    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_macd(
    prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD (Moving Average Convergence Divergence).

    MACD is a trend-following momentum indicator that shows the relationship
    between two moving averages of a security's price.

    Args:
        prices: Price series data
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line EMA period (default 9)

    Returns:
        Tuple containing (MACD line, Signal line, Histogram)

    Raises:
        ValueError: If parameters are invalid

    Example:
        >>> prices = pd.Series(range(1, 31))
        >>> macd_line, signal_line, histogram = calculate_macd(prices)
        >>> print(f"MACD: {macd_line.iloc[-1]:.4f}")
    """
    if fast <= 0 or slow <= 0 or signal <= 0:
        raise ValueError("All periods must be positive")

    if fast >= slow:
        raise ValueError("Fast period must be less than slow period")

    if len(prices) == 0:
        empty_series = pd.Series([], dtype=float)
        return empty_series, empty_series, empty_series

    if len(prices) < slow:
        nan_series = pd.Series([np.nan] * len(prices), index=prices.index)
        return nan_series, nan_series, nan_series

    # Calculate fast and slow EMAs
    ema_fast = calculate_ema(prices, span=fast)
    ema_slow = calculate_ema(prices, span=slow)

    # Calculate MACD line
    macd_line = ema_fast - ema_slow

    # Calculate signal line (EMA of MACD line)
    signal_line = calculate_ema(macd_line, span=signal)

    # Calculate histogram (MACD - Signal)
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    prices: pd.Series, window: int = 20, num_std: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands.

    Bollinger Bands consist of a middle band (SMA) and two outer bands
    that are standard deviations away from the middle band.

    Args:
        prices: Price series data
        window: Period for SMA and standard deviation calculation (default 20)
        num_std: Number of standard deviations for bands (default 2.0)

    Returns:
        Tuple containing (Upper band, Middle band, Lower band)

    Raises:
        ValueError: If parameters are invalid

    Example:
        >>> prices = pd.Series([10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20])
        >>> upper, middle, lower = calculate_bollinger_bands(prices, window=5)
        >>> print(f"Upper: {upper.iloc[-1]:.2f}, Lower: {lower.iloc[-1]:.2f}")
    """
    if window <= 0:
        raise ValueError("Window size must be positive")

    if num_std <= 0:
        raise ValueError("Standard deviation multiplier must be positive")

    if len(prices) == 0:
        empty_series = pd.Series([], dtype=float)
        return empty_series, empty_series, empty_series

    # Calculate middle band (SMA)
    middle_band = calculate_sma(prices, window)

    # Calculate standard deviation
    std_dev = prices.rolling(window=window, min_periods=window).std()

    # Calculate upper and lower bands
    upper_band = middle_band + (std_dev * num_std)
    lower_band = middle_band - (std_dev * num_std)

    return upper_band, middle_band, lower_band


class TechnicalIndicatorCalculator:
    """Calculator class for technical indicators.

    Provides methods to calculate various technical indicators from stock data
    and combine them into a comprehensive analysis.

    Example:
        >>> calculator = TechnicalIndicatorCalculator()
        >>> indicators = calculator.calculate_all_indicators(stock_data)
        >>> print(f"RSI: {indicators.rsi}")
    """

    def __init__(self) -> None:
        """Initialize the technical indicator calculator."""
        pass

    def _extract_prices(self, stock_data: list[StockData]) -> pd.Series:
        """Extract closing prices from stock data.

        Args:
            stock_data: List of stock data points

        Returns:
            Series of closing prices indexed by date

        Raises:
            ValueError: If stock data is empty or None
        """
        if stock_data is None:
            raise ValueError("Stock data cannot be None")

        if not stock_data:
            raise ValueError("Stock data cannot be empty")

        # Extract closing prices and create pandas Series
        prices = []
        dates = []

        for data_point in stock_data:
            prices.append(float(data_point.close))
            dates.append(data_point.date)

        return pd.Series(prices, index=dates)

    def calculate_sma(self, stock_data: list[StockData], window: int) -> Decimal | None:
        """Calculate Simple Moving Average for stock data.

        Args:
            stock_data: List of stock data points
            window: Window size for SMA calculation

        Returns:
            Latest SMA value or None if insufficient data

        Example:
            >>> calculator = TechnicalIndicatorCalculator()
            >>> sma = calculator.calculate_sma(stock_data, window=20)
        """
        prices = self._extract_prices(stock_data)

        if len(prices) < window:
            return None

        sma_series = calculate_sma(prices, window)
        sma_dropna = sma_series.dropna()
        latest_sma = sma_dropna.iloc[-1] if not sma_dropna.empty else None

        return Decimal(str(latest_sma)) if latest_sma is not None else None

    def calculate_ema(self, stock_data: list[StockData], span: int) -> Decimal | None:
        """Calculate Exponential Moving Average for stock data.

        Args:
            stock_data: List of stock data points
            span: Span for EMA calculation

        Returns:
            Latest EMA value or None if insufficient data
        """
        prices = self._extract_prices(stock_data)

        if len(prices) == 0:
            return None

        ema_series = calculate_ema(prices, span)
        latest_ema = ema_series.iloc[-1] if len(ema_series) > 0 else None

        return Decimal(str(latest_ema)) if latest_ema is not None else None

    def calculate_rsi(
        self, stock_data: list[StockData], window: int = 14
    ) -> Decimal | None:
        """Calculate Relative Strength Index for stock data.

        Args:
            stock_data: List of stock data points
            window: Window size for RSI calculation

        Returns:
            Latest RSI value or None if insufficient data
        """
        prices = self._extract_prices(stock_data)

        if len(prices) < window + 1:
            return None

        rsi_series = calculate_rsi(prices, window)
        rsi_dropna = rsi_series.dropna()
        latest_rsi = rsi_dropna.iloc[-1] if not rsi_dropna.empty else None

        return Decimal(str(latest_rsi)) if latest_rsi is not None else None

    def calculate_macd(
        self,
        stock_data: list[StockData],
        fast: int = 12,
        slow: int = 26,
        signal_period: int = 9,
    ) -> tuple[Decimal | None, Decimal | None]:
        """Calculate MACD for stock data.

        Args:
            stock_data: List of stock data points
            fast: Fast EMA period
            slow: Slow EMA period
            signal_period: Signal line EMA period

        Returns:
            Tuple of (MACD line value, Signal line value) or (None, None)
        """
        prices = self._extract_prices(stock_data)

        if len(prices) < max(slow, signal_period) + 1:
            return None, None

        macd_line, signal_line, _ = calculate_macd(prices, fast, slow, signal_period)

        macd_dropna = macd_line.dropna()
        signal_dropna = signal_line.dropna()
        latest_macd = macd_dropna.iloc[-1] if not macd_dropna.empty else None
        latest_signal = signal_dropna.iloc[-1] if not signal_dropna.empty else None

        return (
            Decimal(str(latest_macd)) if latest_macd is not None else None,
            Decimal(str(latest_signal)) if latest_signal is not None else None,
        )

    def calculate_bollinger_bands(
        self, stock_data: list[StockData], window: int = 20, num_std: float = 2.0
    ) -> tuple[Decimal | None, Decimal | None]:
        """Calculate Bollinger Bands for stock data.

        Args:
            stock_data: List of stock data points
            window: Window size for calculation
            num_std: Number of standard deviations

        Returns:
            Tuple of (Upper band, Lower band) or (None, None)
        """
        prices = self._extract_prices(stock_data)

        if len(prices) < window:
            return None, None

        upper_band, _, lower_band = calculate_bollinger_bands(prices, window, num_std)

        upper_dropna = upper_band.dropna()
        lower_dropna = lower_band.dropna()
        latest_upper = upper_dropna.iloc[-1] if not upper_dropna.empty else None
        latest_lower = lower_dropna.iloc[-1] if not lower_dropna.empty else None

        return (
            Decimal(str(latest_upper)) if latest_upper is not None else None,
            Decimal(str(latest_lower)) if latest_lower is not None else None,
        )

    def calculate_all_indicators(
        self, stock_data: list[StockData]
    ) -> TechnicalIndicators:
        """Calculate all technical indicators for stock data.

        Computes SMA (20, 50), EMA (12, 26), RSI, MACD, and Bollinger Bands
        and returns them in a TechnicalIndicators model.

        Args:
            stock_data: List of stock data points

        Returns:
            TechnicalIndicators model with calculated values

        Raises:
            ValueError: If stock data is invalid
            TypeError: If stock data is wrong type

        Example:
            >>> calculator = TechnicalIndicatorCalculator()
            >>> indicators = calculator.calculate_all_indicators(stock_data)
            >>> print(f"SMA 20: {indicators.sma_20}")
        """
        if stock_data is None:
            raise ValueError("Stock data cannot be None")

        if not isinstance(stock_data, list):
            raise TypeError("Stock data must be a list")

        # Calculate all indicators
        sma_20 = self.calculate_sma(stock_data, window=20)
        sma_50 = self.calculate_sma(stock_data, window=50)
        ema_12 = self.calculate_ema(stock_data, span=12)
        ema_26 = self.calculate_ema(stock_data, span=26)
        rsi = self.calculate_rsi(stock_data, window=14)
        macd, macd_signal = self.calculate_macd(
            stock_data, fast=12, slow=26, signal_period=9
        )
        bollinger_upper, bollinger_lower = self.calculate_bollinger_bands(
            stock_data, window=20, num_std=2.0
        )

        return TechnicalIndicators(
            sma_20=sma_20,
            sma_50=sma_50,
            ema_12=ema_12,
            ema_26=ema_26,
            rsi=rsi,
            macd=macd,
            macd_signal=macd_signal,
            bollinger_upper=bollinger_upper,
            bollinger_lower=bollinger_lower,
        )
