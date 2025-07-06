"""Tests for data models and schemas."""

from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from trendscope_backend.data.models import (
    AnalysisRequest,
    AnalysisResult,
    StockData,
    StockInfo,
    TechnicalIndicators,
    TimeSeriesData,
)


class TestStockData:
    """Test cases for StockData model."""

    def test_stock_data_creation_valid(self) -> None:
        """Test creating StockData with valid data."""
        stock_data = StockData(
            symbol="AAPL",
            date=datetime(2024, 1, 1),
            open=Decimal("150.00"),
            high=Decimal("155.00"),
            low=Decimal("148.00"),
            close=Decimal("153.00"),
            volume=1000000,
        )

        assert stock_data.symbol == "AAPL"
        assert stock_data.date == datetime(2024, 1, 1)
        assert stock_data.open == Decimal("150.00")
        assert stock_data.high == Decimal("155.00")
        assert stock_data.low == Decimal("148.00")
        assert stock_data.close == Decimal("153.00")
        assert stock_data.volume == 1000000

    def test_stock_data_symbol_validation(self) -> None:
        """Test symbol validation in StockData."""
        # Valid symbols
        stock_data = StockData(
            symbol="AAPL",
            date=datetime(2024, 1, 1),
            open=Decimal("150.00"),
            high=Decimal("155.00"),
            low=Decimal("148.00"),
            close=Decimal("153.00"),
            volume=1000000,
        )
        assert stock_data.symbol == "AAPL"

        # Invalid empty symbol
        with pytest.raises(ValidationError):
            StockData(
                symbol="",
                date=datetime(2024, 1, 1),
                open=Decimal("150.00"),
                high=Decimal("155.00"),
                low=Decimal("148.00"),
                close=Decimal("153.00"),
                volume=1000000,
            )

    def test_stock_data_price_validation(self) -> None:
        """Test price validation in StockData."""
        # Valid prices
        stock_data = StockData(
            symbol="AAPL",
            date=datetime(2024, 1, 1),
            open=Decimal("150.00"),
            high=Decimal("155.00"),
            low=Decimal("148.00"),
            close=Decimal("153.00"),
            volume=1000000,
        )
        assert stock_data.open > 0

        # Invalid negative price
        with pytest.raises(ValidationError):
            StockData(
                symbol="AAPL",
                date=datetime(2024, 1, 1),
                open=Decimal("-150.00"),
                high=Decimal("155.00"),
                low=Decimal("148.00"),
                close=Decimal("153.00"),
                volume=1000000,
            )

    def test_stock_data_volume_validation(self) -> None:
        """Test volume validation in StockData."""
        # Valid volume
        stock_data = StockData(
            symbol="AAPL",
            date=datetime(2024, 1, 1),
            open=Decimal("150.00"),
            high=Decimal("155.00"),
            low=Decimal("148.00"),
            close=Decimal("153.00"),
            volume=1000000,
        )
        assert stock_data.volume >= 0

        # Invalid negative volume
        with pytest.raises(ValidationError):
            StockData(
                symbol="AAPL",
                date=datetime(2024, 1, 1),
                open=Decimal("150.00"),
                high=Decimal("155.00"),
                low=Decimal("148.00"),
                close=Decimal("153.00"),
                volume=-1000,
            )

    def test_stock_data_price_relationship_validation(self) -> None:
        """Test price relationship validation in StockData."""
        # Valid price relationships (high >= max(open, close), low <= min(open, close))
        StockData(
            symbol="AAPL",
            date=datetime(2024, 1, 1),
            open=Decimal("150.00"),
            high=Decimal("155.00"),
            low=Decimal("148.00"),
            close=Decimal("153.00"),
            volume=1000000,
        )

        # Invalid: high < close
        with pytest.raises(ValidationError):
            StockData(
                symbol="AAPL",
                date=datetime(2024, 1, 1),
                open=Decimal("150.00"),
                high=Decimal("145.00"),  # high < open and close
                low=Decimal("148.00"),
                close=Decimal("153.00"),
                volume=1000000,
            )

    def test_stock_data_serialization(self) -> None:
        """Test StockData model serialization."""
        stock_data = StockData(
            symbol="AAPL",
            date=datetime(2024, 1, 1),
            open=Decimal("150.00"),
            high=Decimal("155.00"),
            low=Decimal("148.00"),
            close=Decimal("153.00"),
            volume=1000000,
        )

        # Test model dump
        data_dict = stock_data.model_dump()
        assert data_dict["symbol"] == "AAPL"
        assert data_dict["open"] == Decimal("150.00")

        # Test JSON serialization
        json_data = stock_data.model_dump_json()
        assert "AAPL" in json_data
        assert "150.00" in json_data


class TestStockInfo:
    """Test cases for StockInfo model."""

    def test_stock_info_creation_valid(self) -> None:
        """Test creating StockInfo with valid data."""
        stock_info = StockInfo(
            symbol="AAPL",
            name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=2500000000000,
            currency="USD",
        )

        assert stock_info.symbol == "AAPL"
        assert stock_info.name == "Apple Inc."
        assert stock_info.sector == "Technology"
        assert stock_info.industry == "Consumer Electronics"
        assert stock_info.market_cap == 2500000000000
        assert stock_info.currency == "USD"

    def test_stock_info_optional_fields(self) -> None:
        """Test StockInfo with optional fields."""
        # Minimum required fields
        stock_info = StockInfo(
            symbol="AAPL",
            name="Apple Inc.",
        )

        assert stock_info.symbol == "AAPL"
        assert stock_info.name == "Apple Inc."
        assert stock_info.sector is None
        assert stock_info.industry is None
        assert stock_info.market_cap is None
        assert stock_info.currency is None

    def test_stock_info_validation(self) -> None:
        """Test StockInfo validation rules."""
        # Valid market cap
        StockInfo(
            symbol="AAPL",
            name="Apple Inc.",
            market_cap=1000000,
        )

        # Invalid negative market cap
        with pytest.raises(ValidationError):
            StockInfo(
                symbol="AAPL",
                name="Apple Inc.",
                market_cap=-1000000,
            )


class TestTimeSeriesData:
    """Test cases for TimeSeriesData model."""

    def test_time_series_data_creation(self) -> None:
        """Test creating TimeSeriesData with valid data."""
        stock_data_list = [
            StockData(
                symbol="AAPL",
                date=datetime(2024, 1, 1),
                open=Decimal("150.00"),
                high=Decimal("155.00"),
                low=Decimal("148.00"),
                close=Decimal("153.00"),
                volume=1000000,
            ),
            StockData(
                symbol="AAPL",
                date=datetime(2024, 1, 2),
                open=Decimal("153.00"),
                high=Decimal("158.00"),
                low=Decimal("151.00"),
                close=Decimal("156.00"),
                volume=1100000,
            ),
        ]

        time_series = TimeSeriesData(
            symbol="AAPL",
            data=stock_data_list,
            period="1mo",
        )

        assert time_series.symbol == "AAPL"
        assert len(time_series.data) == 2
        assert time_series.period == "1mo"

    def test_time_series_data_validation(self) -> None:
        """Test TimeSeriesData validation rules."""
        # Empty data list should fail
        with pytest.raises(ValidationError):
            TimeSeriesData(
                symbol="AAPL",
                data=[],
                period="1mo",
            )

    def test_time_series_data_computed_fields(self) -> None:
        """Test computed fields in TimeSeriesData."""
        stock_data_list = [
            StockData(
                symbol="AAPL",
                date=datetime(2024, 1, 1),
                open=Decimal("150.00"),
                high=Decimal("155.00"),
                low=Decimal("148.00"),
                close=Decimal("153.00"),
                volume=1000000,
            ),
            StockData(
                symbol="AAPL",
                date=datetime(2024, 1, 2),
                open=Decimal("153.00"),
                high=Decimal("158.00"),
                low=Decimal("151.00"),
                close=Decimal("156.00"),
                volume=1100000,
            ),
        ]

        time_series = TimeSeriesData(
            symbol="AAPL",
            data=stock_data_list,
            period="1mo",
        )

        assert time_series.start_date == datetime(2024, 1, 1)
        assert time_series.end_date == datetime(2024, 1, 2)
        assert time_series.data_points == 2


class TestTechnicalIndicators:
    """Test cases for TechnicalIndicators model."""

    def test_technical_indicators_creation(self) -> None:
        """Test creating TechnicalIndicators with valid data."""
        indicators = TechnicalIndicators(
            sma_20=Decimal("152.50"),
            sma_50=Decimal("148.75"),
            ema_12=Decimal("153.25"),
            ema_26=Decimal("150.80"),
            rsi=Decimal("65.5"),
            macd=Decimal("2.45"),
            macd_signal=Decimal("1.85"),
            bollinger_upper=Decimal("158.00"),
            bollinger_lower=Decimal("145.00"),
        )

        assert indicators.sma_20 == Decimal("152.50")
        assert indicators.sma_50 == Decimal("148.75")
        assert indicators.rsi == Decimal("65.5")

    def test_technical_indicators_validation(self) -> None:
        """Test TechnicalIndicators validation rules."""
        # Valid RSI (0-100 range)
        TechnicalIndicators(rsi=Decimal("50.0"))
        TechnicalIndicators(rsi=Decimal("0.0"))
        TechnicalIndicators(rsi=Decimal("100.0"))

        # Invalid RSI values
        with pytest.raises(ValidationError):
            TechnicalIndicators(rsi=Decimal("-10.0"))

        with pytest.raises(ValidationError):
            TechnicalIndicators(rsi=Decimal("110.0"))

    def test_technical_indicators_optional_fields(self) -> None:
        """Test TechnicalIndicators with optional fields."""
        # All fields are optional
        indicators = TechnicalIndicators()

        assert indicators.sma_20 is None
        assert indicators.sma_50 is None
        assert indicators.rsi is None


class TestAnalysisRequest:
    """Test cases for AnalysisRequest model."""

    def test_analysis_request_creation_with_period(self) -> None:
        """Test creating AnalysisRequest with period."""
        request = AnalysisRequest(
            symbol="AAPL",
            period="1mo",
            indicators=["sma", "rsi", "macd"],
        )

        assert request.symbol == "AAPL"
        assert request.period == "1mo"
        assert request.start_date is None
        assert request.end_date is None
        assert request.indicators == ["sma", "rsi", "macd"]

    def test_analysis_request_creation_with_dates(self) -> None:
        """Test creating AnalysisRequest with date range."""
        request = AnalysisRequest(
            symbol="AAPL",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            indicators=["sma", "rsi"],
        )

        assert request.symbol == "AAPL"
        assert request.period is None
        assert request.start_date == datetime(2024, 1, 1)
        assert request.end_date == datetime(2024, 1, 31)

    def test_analysis_request_validation(self) -> None:
        """Test AnalysisRequest validation rules."""
        # Must have either period or date range
        with pytest.raises(ValidationError):
            AnalysisRequest(
                symbol="AAPL",
                indicators=["sma"],
            )

        # Cannot have both period and date range
        with pytest.raises(ValidationError):
            AnalysisRequest(
                symbol="AAPL",
                period="1mo",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
                indicators=["sma"],
            )

        # Start date must be before end date
        with pytest.raises(ValidationError):
            AnalysisRequest(
                symbol="AAPL",
                start_date=datetime(2024, 1, 31),
                end_date=datetime(2024, 1, 1),
                indicators=["sma"],
            )

    def test_analysis_request_valid_indicators(self) -> None:
        """Test valid indicator values in AnalysisRequest."""
        valid_indicators = ["sma", "ema", "rsi", "macd", "bollinger"]

        for indicator in valid_indicators:
            request = AnalysisRequest(
                symbol="AAPL",
                period="1mo",
                indicators=[indicator],
            )
            assert indicator in request.indicators

        # Invalid indicator
        with pytest.raises(ValidationError):
            AnalysisRequest(
                symbol="AAPL",
                period="1mo",
                indicators=["invalid_indicator"],
            )


class TestAnalysisResult:
    """Test cases for AnalysisResult model."""

    def test_analysis_result_creation(self) -> None:
        """Test creating AnalysisResult with valid data."""
        time_series = TimeSeriesData(
            symbol="AAPL",
            data=[
                StockData(
                    symbol="AAPL",
                    date=datetime(2024, 1, 1),
                    open=Decimal("150.00"),
                    high=Decimal("155.00"),
                    low=Decimal("148.00"),
                    close=Decimal("153.00"),
                    volume=1000000,
                )
            ],
            period="1mo",
        )

        indicators = TechnicalIndicators(
            sma_20=Decimal("152.50"),
            rsi=Decimal("65.5"),
        )

        result = AnalysisResult(
            symbol="AAPL",
            time_series=time_series,
            indicators=indicators,
            analysis_date=datetime(2024, 1, 15),
            probability_up=Decimal("0.72"),
            confidence_level=Decimal("0.85"),
        )

        assert result.symbol == "AAPL"
        assert result.time_series.symbol == "AAPL"
        assert result.indicators.sma_20 == Decimal("152.50")
        assert result.probability_up == Decimal("0.72")
        assert result.confidence_level == Decimal("0.85")

    def test_analysis_result_probability_validation(self) -> None:
        """Test probability validation in AnalysisResult."""
        time_series = TimeSeriesData(
            symbol="AAPL",
            data=[
                StockData(
                    symbol="AAPL",
                    date=datetime(2024, 1, 1),
                    open=Decimal("150.00"),
                    high=Decimal("155.00"),
                    low=Decimal("148.00"),
                    close=Decimal("153.00"),
                    volume=1000000,
                )
            ],
            period="1mo",
        )

        indicators = TechnicalIndicators()

        # Valid probability (0.0 to 1.0)
        AnalysisResult(
            symbol="AAPL",
            time_series=time_series,
            indicators=indicators,
            analysis_date=datetime(2024, 1, 15),
            probability_up=Decimal("0.5"),
            confidence_level=Decimal("0.8"),
        )

        # Invalid probability > 1.0
        with pytest.raises(ValidationError):
            AnalysisResult(
                symbol="AAPL",
                time_series=time_series,
                indicators=indicators,
                analysis_date=datetime(2024, 1, 15),
                probability_up=Decimal("1.5"),
                confidence_level=Decimal("0.8"),
            )

        # Invalid probability < 0.0
        with pytest.raises(ValidationError):
            AnalysisResult(
                symbol="AAPL",
                time_series=time_series,
                indicators=indicators,
                analysis_date=datetime(2024, 1, 15),
                probability_up=Decimal("-0.1"),
                confidence_level=Decimal("0.8"),
            )

    def test_analysis_result_recommendation_computed(self) -> None:
        """Test computed recommendation field in AnalysisResult."""
        time_series = TimeSeriesData(
            symbol="AAPL",
            data=[
                StockData(
                    symbol="AAPL",
                    date=datetime(2024, 1, 1),
                    open=Decimal("150.00"),
                    high=Decimal("155.00"),
                    low=Decimal("148.00"),
                    close=Decimal("153.00"),
                    volume=1000000,
                )
            ],
            period="1mo",
        )

        indicators = TechnicalIndicators()

        # High probability -> BUY
        result_buy = AnalysisResult(
            symbol="AAPL",
            time_series=time_series,
            indicators=indicators,
            analysis_date=datetime(2024, 1, 15),
            probability_up=Decimal("0.75"),
            confidence_level=Decimal("0.85"),
        )
        assert result_buy.recommendation == "BUY"

        # Low probability -> SELL
        result_sell = AnalysisResult(
            symbol="AAPL",
            time_series=time_series,
            indicators=indicators,
            analysis_date=datetime(2024, 1, 15),
            probability_up=Decimal("0.25"),
            confidence_level=Decimal("0.85"),
        )
        assert result_sell.recommendation == "SELL"

        # Medium probability -> HOLD
        result_hold = AnalysisResult(
            symbol="AAPL",
            time_series=time_series,
            indicators=indicators,
            analysis_date=datetime(2024, 1, 15),
            probability_up=Decimal("0.55"),
            confidence_level=Decimal("0.85"),
        )
        assert result_hold.recommendation == "HOLD"
