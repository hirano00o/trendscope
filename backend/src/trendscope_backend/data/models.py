"""Data models and schemas for stock analysis."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator


class StockData(BaseModel):
    """Stock price data for a single time point.

    Represents OHLCV (Open, High, Low, Close, Volume) data for a stock
    at a specific date with comprehensive validation.

    Args:
        symbol: Stock symbol (e.g., 'AAPL', 'GOOGL')
        date: Date for this data point
        open: Opening price
        high: Highest price during the period
        low: Lowest price during the period
        close: Closing price
        volume: Trading volume

    Example:
        >>> stock_data = StockData(
        ...     symbol="AAPL",
        ...     date=datetime(2024, 1, 1),
        ...     open=Decimal("150.00"),
        ...     high=Decimal("155.00"),
        ...     low=Decimal("148.00"),
        ...     close=Decimal("153.00"),
        ...     volume=1000000
        ... )
        >>> print(stock_data.symbol)
        'AAPL'
    """

    symbol: str = Field(..., min_length=1, max_length=20, description="Stock symbol")
    date: datetime = Field(..., description="Date for this data point")
    open: Decimal = Field(..., gt=0, description="Opening price")
    high: Decimal = Field(..., gt=0, description="Highest price")
    low: Decimal = Field(..., gt=0, description="Lowest price")
    close: Decimal = Field(..., gt=0, description="Closing price")
    volume: int = Field(..., ge=0, description="Trading volume")

    @model_validator(mode="after")
    def validate_price_relationships(self) -> "StockData":
        """Validate that price relationships are logically consistent.

        Ensures that:
        - High price is at least as high as open and close prices
        - Low price is at most as low as open and close prices

        Returns:
            Validated StockData instance

        Raises:
            ValueError: If price relationships are invalid
        """
        if self.high < max(self.open, self.close):
            raise ValueError("High price must be >= max(open, close)")

        if self.low > min(self.open, self.close):
            raise ValueError("Low price must be <= min(open, close)")

        return self

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate stock symbol format.

        Args:
            v: Symbol to validate

        Returns:
            Validated symbol in uppercase

        Raises:
            ValueError: If symbol is invalid
        """
        if not v or not v.strip():
            raise ValueError("Symbol cannot be empty")

        # Convert to uppercase and remove whitespace
        symbol = v.strip().upper()

        # Basic format validation (letters, numbers, dots, hyphens)
        import re

        if not re.match(r"^[A-Z0-9.-]+$", symbol):
            raise ValueError("Symbol contains invalid characters")

        return symbol


class StockInfo(BaseModel):
    """Stock information and metadata.

    Contains company information and metadata for a stock symbol.

    Args:
        symbol: Stock symbol
        name: Company name
        sector: Business sector (optional)
        industry: Industry classification (optional)
        market_cap: Market capitalization in USD (optional)
        currency: Trading currency (optional)

    Example:
        >>> stock_info = StockInfo(
        ...     symbol="AAPL",
        ...     name="Apple Inc.",
        ...     sector="Technology",
        ...     market_cap=2500000000000
        ... )
        >>> print(stock_info.name)
        'Apple Inc.'
    """

    symbol: str = Field(..., min_length=1, max_length=20, description="Stock symbol")
    name: str = Field(..., min_length=1, description="Company name")
    sector: str | None = Field(None, description="Business sector")
    industry: str | None = Field(None, description="Industry classification")
    market_cap: int | None = Field(None, ge=0, description="Market cap in USD")
    currency: str | None = Field(None, description="Trading currency")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate stock symbol format."""
        return v.strip().upper()


class TimeSeriesData(BaseModel):
    """Time series collection of stock data points.

    Represents a collection of stock data points over a time period
    with metadata about the time range.

    Args:
        symbol: Stock symbol
        data: List of stock data points
        period: Time period description (e.g., '1mo', '3mo')

    Example:
        >>> data_points = [StockData(...), StockData(...)]
        >>> time_series = TimeSeriesData(
        ...     symbol="AAPL",
        ...     data=data_points,
        ...     period="1mo"
        ... )
        >>> print(time_series.data_points)
        2
    """

    symbol: str = Field(..., min_length=1, max_length=20, description="Stock symbol")
    data: list[StockData] = Field(..., min_length=1, description="Stock data points")
    period: str = Field(..., description="Time period description")

    @computed_field
    @property
    def start_date(self) -> datetime:
        """Get the earliest date in the time series.

        Returns:
            Earliest date from the data points
        """
        return min(point.date for point in self.data)

    @computed_field
    @property
    def end_date(self) -> datetime:
        """Get the latest date in the time series.

        Returns:
            Latest date from the data points
        """
        return max(point.date for point in self.data)

    @computed_field
    @property
    def data_points(self) -> int:
        """Get the number of data points.

        Returns:
            Number of data points in the series
        """
        return len(self.data)

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate stock symbol format."""
        return v.strip().upper()


class TechnicalIndicators(BaseModel):
    """Technical analysis indicators for stock analysis.

    Contains calculated technical indicators like moving averages,
    momentum indicators, and volatility measures.

    Args:
        sma_20: 20-day Simple Moving Average (optional)
        sma_50: 50-day Simple Moving Average (optional)
        ema_12: 12-day Exponential Moving Average (optional)
        ema_26: 26-day Exponential Moving Average (optional)
        rsi: Relative Strength Index (0-100) (optional)
        macd: MACD line value (optional)
        macd_signal: MACD signal line value (optional)
        bollinger_upper: Bollinger Band upper line (optional)
        bollinger_lower: Bollinger Band lower line (optional)

    Example:
        >>> indicators = TechnicalIndicators(
        ...     sma_20=Decimal("152.50"),
        ...     rsi=Decimal("65.5"),
        ...     macd=Decimal("2.45")
        ... )
        >>> print(indicators.rsi)
        Decimal('65.5')
    """

    sma_20: Decimal | None = Field(None, description="20-day Simple Moving Average")
    sma_50: Decimal | None = Field(None, description="50-day Simple Moving Average")
    ema_12: Decimal | None = Field(
        None, description="12-day Exponential Moving Average"
    )
    ema_26: Decimal | None = Field(
        None, description="26-day Exponential Moving Average"
    )
    rsi: Decimal | None = Field(None, ge=0, le=100, description="RSI (0-100)")
    macd: Decimal | None = Field(None, description="MACD line value")
    macd_signal: Decimal | None = Field(None, description="MACD signal line value")
    bollinger_upper: Decimal | None = Field(None, description="Bollinger upper band")
    bollinger_lower: Decimal | None = Field(None, description="Bollinger lower band")


class AnalysisRequest(BaseModel):
    """Request for stock analysis.

    Defines the parameters for requesting stock analysis including
    the time period and which indicators to calculate.

    Args:
        symbol: Stock symbol to analyze
        period: Predefined period (e.g., '1mo', '3mo', '6mo', '1y')
        start_date: Custom start date (alternative to period)
        end_date: Custom end date (required if start_date provided)
        indicators: List of indicators to calculate

    Example:
        >>> request = AnalysisRequest(
        ...     symbol="AAPL",
        ...     period="1mo",
        ...     indicators=["sma", "rsi", "macd"]
        ... )
        >>> print(request.symbol)
        'AAPL'
    """

    symbol: str = Field(..., min_length=1, max_length=20, description="Stock symbol")
    period: str | None = Field(None, description="Time period")
    start_date: datetime | None = Field(None, description="Custom start date")
    end_date: datetime | None = Field(None, description="Custom end date")
    indicators: list[Literal["sma", "ema", "rsi", "macd", "bollinger"]] = Field(
        ..., min_length=1, description="Indicators to calculate"
    )

    @model_validator(mode="after")
    def validate_date_period_logic(self) -> "AnalysisRequest":
        """Validate date and period configuration.

        Ensures that either period OR date range is specified, but not both.
        Also validates that start_date is before end_date when using date range.

        Returns:
            Validated AnalysisRequest instance

        Raises:
            ValueError: If validation fails
        """
        has_period = self.period is not None
        has_dates = self.start_date is not None or self.end_date is not None

        if not has_period and not has_dates:
            raise ValueError("Must specify either period or date range")

        if has_period and has_dates:
            raise ValueError("Cannot specify both period and date range")

        if has_dates:
            if self.start_date is None or self.end_date is None:
                raise ValueError("Both start_date and end_date required for date range")

            if self.start_date >= self.end_date:
                raise ValueError("start_date must be before end_date")

        return self

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate stock symbol format."""
        return v.strip().upper()


class AnalysisResult(BaseModel):
    """Result of stock analysis.

    Contains the analysis results including time series data,
    technical indicators, and probability predictions.

    Args:
        symbol: Stock symbol analyzed
        time_series: Historical stock data used in analysis
        indicators: Calculated technical indicators
        analysis_date: When the analysis was performed
        probability_up: Probability of price increase (0.0-1.0)
        confidence_level: Confidence in the prediction (0.0-1.0)

    Example:
        >>> result = AnalysisResult(
        ...     symbol="AAPL",
        ...     time_series=time_series_data,
        ...     indicators=technical_indicators,
        ...     analysis_date=datetime.now(),
        ...     probability_up=Decimal("0.72"),
        ...     confidence_level=Decimal("0.85")
        ... )
        >>> print(result.recommendation)
        'BUY'
    """

    symbol: str = Field(..., min_length=1, max_length=20, description="Stock symbol")
    time_series: TimeSeriesData = Field(..., description="Historical data used")
    indicators: TechnicalIndicators = Field(..., description="Technical indicators")
    analysis_date: datetime = Field(..., description="Analysis timestamp")
    probability_up: Decimal = Field(
        ..., ge=0, le=1, description="Probability of price increase"
    )
    confidence_level: Decimal = Field(
        ..., ge=0, le=1, description="Confidence in prediction"
    )

    @computed_field
    @property
    def recommendation(self) -> Literal["BUY", "HOLD", "SELL"]:
        """Get investment recommendation based on probability.

        Returns recommendation based on probability thresholds:
        - BUY: probability >= 0.7
        - SELL: probability <= 0.3
        - HOLD: 0.3 < probability < 0.7

        Returns:
            Investment recommendation
        """
        if self.probability_up >= Decimal("0.7"):
            return "BUY"
        elif self.probability_up <= Decimal("0.3"):
            return "SELL"
        else:
            return "HOLD"

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate stock symbol format."""
        return v.strip().upper()


class HistoricalDataPoint(BaseModel):
    """Single historical data point for chart display.

    Represents OHLCV data for a single date, optimized for frontend
    chart consumption with simplified types and consistent formatting.

    Args:
        date: Date in YYYY-MM-DD format
        open: Opening price as float
        high: Highest price as float
        low: Lowest price as float
        close: Closing price as float
        volume: Trading volume as integer

    Example:
        >>> data_point = HistoricalDataPoint(
        ...     date="2024-01-15",
        ...     open=150.25,
        ...     high=152.75,
        ...     low=149.50,
        ...     close=151.80,
        ...     volume=1234567
        ... )
        >>> print(data_point.date)
        '2024-01-15'
    """

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    open: float = Field(..., gt=0, description="Opening price")
    high: float = Field(..., gt=0, description="Highest price")
    low: float = Field(..., gt=0, description="Lowest price")
    close: float = Field(..., gt=0, description="Closing price")
    volume: int = Field(..., ge=0, description="Trading volume")

    @model_validator(mode="after")
    def validate_price_relationships(self) -> "HistoricalDataPoint":
        """Validate that price relationships are logically consistent.

        Ensures that:
        - High price is at least as high as open and close prices
        - Low price is at most as low as open and close prices

        Returns:
            Validated HistoricalDataPoint instance

        Raises:
            ValueError: If price relationships are invalid
        """
        if self.high < max(self.open, self.close):
            raise ValueError("High price must be >= max(open, close)")

        if self.low > min(self.open, self.close):
            raise ValueError("Low price must be <= min(open, close)")

        return self


class HistoricalDataMetadata(BaseModel):
    """Metadata for historical data response.

    Contains additional information about the historical data including
    price changes, volume statistics, and data quality indicators.

    Args:
        current_price: Most recent closing price
        price_change: Absolute price change over the period
        price_change_percent: Percentage price change over the period
        average_volume: Average trading volume over the period
        data_quality: Quality indicator (high/medium/low)
        retrieved_at: Timestamp when data was retrieved

    Example:
        >>> metadata = HistoricalDataMetadata(
        ...     current_price=151.80,
        ...     price_change=5.25,
        ...     price_change_percent=3.58,
        ...     average_volume=1234567,
        ...     data_quality="high",
        ...     retrieved_at="2024-01-15T10:30:00Z"
        ... )
        >>> print(metadata.price_change_percent)
        3.58
    """

    current_price: float = Field(..., gt=0, description="Most recent closing price")
    price_change: float = Field(..., description="Absolute price change over period")
    price_change_percent: float = Field(..., description="Percentage price change")
    average_volume: int = Field(..., ge=0, description="Average trading volume")
    data_quality: Literal["high", "medium", "low"] = Field(..., description="Data quality indicator")
    retrieved_at: str = Field(..., description="Data retrieval timestamp")


class HistoricalDataResponse(BaseModel):
    """Response model for historical data API endpoint.

    Contains historical OHLCV data and metadata for frontend chart display.
    This model is specifically designed for chart consumption with simplified
    data types and consistent formatting.

    Args:
        symbol: Stock symbol
        period: Time period description
        data_points: Number of data points in the response
        start_date: Start date of the data in YYYY-MM-DD format
        end_date: End date of the data in YYYY-MM-DD format
        historical_data: List of historical data points
        metadata: Additional metadata about the data

    Example:
        >>> response = HistoricalDataResponse(
        ...     symbol="AAPL",
        ...     period="1mo",
        ...     data_points=22,
        ...     start_date="2023-12-15",
        ...     end_date="2024-01-15",
        ...     historical_data=[data_point1, data_point2, ...],
        ...     metadata=metadata
        ... )
        >>> print(len(response.historical_data))
        22
    """

    symbol: str = Field(..., min_length=1, max_length=20, description="Stock symbol")
    period: str = Field(..., description="Time period description")
    data_points: int = Field(..., ge=1, description="Number of data points")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    historical_data: List[HistoricalDataPoint] = Field(
        ..., min_length=1, description="Historical OHLCV data points"
    )
    metadata: HistoricalDataMetadata = Field(..., description="Additional metadata")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate stock symbol format."""
        return v.strip().upper()


class ApiResponse(BaseModel):
    """Generic API response wrapper.

    Provides a consistent response format for all API endpoints with
    success indication and optional error handling.

    Args:
        success: Whether the request was successful
        data: Response data (None if error occurred)
        error: Error information (None if successful)

    Example:
        >>> response = ApiResponse(
        ...     success=True,
        ...     data={"symbol": "AAPL", "price": 150.00}
        ... )
        >>> print(response.success)
        True
    """

    success: bool = Field(..., description="Request success status")
    data: Any | None = Field(None, description="Response data")
    error: Dict[str, Any] | None = Field(None, description="Error information")
