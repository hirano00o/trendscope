"""Tests for technical analysis API endpoints."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from trendscope_backend.api.main import app
from trendscope_backend.data.models import StockData, TechnicalIndicators


class TestTechnicalAnalysisAPI:
    """Test cases for technical analysis API endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client for FastAPI app."""
        return TestClient(app)

    @pytest.fixture
    def sample_stock_data(self) -> list[StockData]:
        """Create sample stock data for testing."""
        stock_data = []
        base_price = Decimal("100.0")

        for i in range(30):
            # Create realistic OHLCV data
            open_price = base_price + Decimal(str(i * 0.5))
            high_price = open_price + Decimal("2.0")
            low_price = open_price - Decimal("1.5")
            close_price = open_price + Decimal("1.0")

            stock_data.append(
                StockData(
                    symbol="AAPL",
                    date=datetime(2024, 1, i + 1),
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=1000000 + (i * 10000),
                )
            )

        # Create sample indicators
        sample_indicators = TechnicalIndicators(
            sma_20=Decimal("152.50"), rsi=Decimal("65.5"), macd=Decimal("2.45")
        )

        # Return the stock data
        return stock_data

        # Create indicators with some None values
        sample_indicators = TechnicalIndicators(
            sma_20=Decimal("152.50"),
            sma_50=None,  # Test None case
            ema_12=Decimal("153.25"),
            ema_26=None,  # Test None case
            rsi=Decimal("65.5"),
            macd=None,  # Test None case
            macd_signal=None,  # Test None case
            bollinger_upper=Decimal("158.00"),
            bollinger_lower=None,  # Test None case
        )

        # Create analysis result
        time_series = TimeSeriesData(
            symbol="AAPL", data=sample_stock_data, period="1mo"
        )

        analysis_result = AnalysisResult(
            symbol="AAPL",
            time_series=time_series,
            indicators=sample_indicators,
            analysis_date=datetime(2024, 1, 15, 10, 30, 0),
            probability_up=Decimal("0.65"),
            confidence_level=Decimal("0.75"),
        )

        # Format response
        response = format_analysis_response(analysis_result)

        # Verify structure
        assert response["symbol"] == "AAPL"
        assert "analysis_date" in response
        assert "time_series" in response
        assert "indicators" in response
        assert "recommendation" in response
        assert "probability_up" in response
        assert "confidence_level" in response

        # Verify only non-None indicators are included
        indicators = response["indicators"]
        assert "sma_20" in indicators
        assert "sma_50" not in indicators  # Should be excluded (None)
        assert "ema_12" in indicators
        assert "ema_26" not in indicators  # Should be excluded (None)
        assert "rsi" in indicators
        assert "macd" not in indicators  # Should be excluded (None)
        assert "macd_signal" not in indicators  # Should be excluded (None)
        assert "bollinger_upper" in indicators
        assert "bollinger_lower" not in indicators  # Should be excluded (None)

        # Verify values
        assert indicators["sma_20"] == "152.50"
        assert indicators["ema_12"] == "153.25"
        assert indicators["rsi"] == "65.5"
        assert indicators["bollinger_upper"] == "158.00"

    def test_calculate_probability_function(self) -> None:
        """Test calculate_probability function with different indicator combinations."""
        from trendscope_backend.api.analysis import calculate_probability
        from trendscope_backend.data.models import TechnicalIndicators

        # Test with bullish indicators
        bullish_indicators = TechnicalIndicators(
            sma_20=Decimal("155.0"),
            sma_50=Decimal("150.0"),  # SMA20 > SMA50 (bullish)
            ema_12=Decimal("156.0"),
            ema_26=Decimal("152.0"),  # EMA12 > EMA26 (bullish)
            rsi=Decimal("25.0"),  # Oversold (bullish)
            macd=Decimal("2.0"),
            macd_signal=Decimal("1.0"),  # MACD > signal (bullish)
        )

        probability = calculate_probability(bullish_indicators)
        assert probability > Decimal("0.5")  # Should be bullish

        # Test with bearish indicators
        bearish_indicators = TechnicalIndicators(
            sma_20=Decimal("145.0"),
            sma_50=Decimal("150.0"),  # SMA20 < SMA50 (bearish)
            ema_12=Decimal("146.0"),
            ema_26=Decimal("150.0"),  # EMA12 < EMA26 (bearish)
            rsi=Decimal("75.0"),  # Overbought (bearish)
            macd=Decimal("1.0"),
            macd_signal=Decimal("2.0"),  # MACD < signal (bearish)
        )

        probability = calculate_probability(bearish_indicators)
        assert probability < Decimal("0.5")  # Should be bearish

    def test_calculate_confidence_function(self) -> None:
        """Test calculate_confidence function with different scenarios."""
        from trendscope_backend.api.analysis import calculate_confidence
        from trendscope_backend.data.models import TechnicalIndicators

        # Test with all indicators available and many data points
        full_indicators = TechnicalIndicators(
            sma_20=Decimal("150.0"),
            sma_50=Decimal("145.0"),
            ema_12=Decimal("151.0"),
            ema_26=Decimal("147.0"),
            rsi=Decimal("60.0"),
            macd=Decimal("1.5"),
            bollinger_upper=Decimal("155.0"),
        )

        confidence_high = calculate_confidence(full_indicators, 60)
        assert confidence_high >= Decimal("0.8")  # Should be high confidence

        # Test with fewer indicators and fewer data points
        partial_indicators = TechnicalIndicators(
            sma_20=Decimal("150.0"),
            rsi=Decimal("60.0"),
        )

        confidence_low = calculate_confidence(partial_indicators, 15)
        assert confidence_low < confidence_high  # Should be lower confidence
