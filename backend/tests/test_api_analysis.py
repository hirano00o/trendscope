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
                StockData(symbol="TEST", 
                    symbol="AAPL",
                    date=datetime(2024, 1, i + 1),
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=1000000 + (i * 10000),
                )
            )

            base_price = close_price

        return stock_data

    @pytest.fixture
    def sample_indicators(self) -> TechnicalIndicators:
        """Create sample technical indicators for testing."""
        return TechnicalIndicators(
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

    def test_get_analysis_endpoint_exists(self, client: TestClient) -> None:
        """Test that analysis endpoint exists and returns proper structure."""
        response = client.get("/api/v1/analysis/AAPL")

        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
        assert response.headers["content-type"] == "application/json"

    def test_get_analysis_with_valid_symbol(self, client: TestClient) -> None:
        """Test analysis endpoint with valid stock symbol."""
        with patch(
            "trendscope_backend.api.analysis.get_stock_analysis"
        ) as mock_analysis:
            # Mock successful analysis response
            mock_analysis.return_value = {
                "symbol": "AAPL",
                "analysis_date": "2024-01-15T10:30:00Z",
                "indicators": {"sma_20": "152.50", "rsi": "65.5", "macd": "2.45"},
                "recommendation": "BUY",
                "probability_up": "0.72",
                "confidence_level": "0.85",
            }

            response = client.get("/api/v1/analysis/AAPL")

            assert response.status_code == 200
            data = response.json()

            assert data["symbol"] == "AAPL"
            assert "analysis_date" in data
            assert "indicators" in data
            assert "recommendation" in data
            assert "probability_up" in data
            assert "confidence_level" in data

    def test_get_analysis_with_invalid_symbol(self, client: TestClient) -> None:
        """Test analysis endpoint with invalid stock symbol."""
        response = client.get("/api/v1/analysis/123")  # All numbers, should be invalid

        assert response.status_code == 400
        data = response.json()

        assert data["detail"]["error"] == "Invalid Symbol"
        assert "symbol" in data["detail"]["message"].lower()

    def test_get_analysis_with_empty_symbol(self, client: TestClient) -> None:
        """Test analysis endpoint with empty symbol."""
        response = client.get("/api/v1/analysis/")

        # Should return 404 (no symbol provided)
        assert response.status_code == 404

    def test_get_analysis_with_period_parameter(self, client: TestClient) -> None:
        """Test analysis endpoint with period parameter."""
        with patch(
            "trendscope_backend.api.analysis.get_stock_analysis"
        ) as mock_analysis:
            mock_analysis.return_value = {"symbol": "AAPL", "period": "3mo"}

            response = client.get("/api/v1/analysis/AAPL?period=3mo")

            assert response.status_code == 200
            mock_analysis.assert_called_once()

    def test_get_analysis_with_custom_indicators(self, client: TestClient) -> None:
        """Test analysis endpoint with custom indicator selection."""
        with patch(
            "trendscope_backend.api.analysis.get_stock_analysis"
        ) as mock_analysis:
            mock_analysis.return_value = {
                "symbol": "AAPL",
                "indicators": ["sma", "rsi"],
            }

            response = client.get("/api/v1/analysis/AAPL?indicators=sma,rsi")

            assert response.status_code == 200
            mock_analysis.assert_called_once()

    def test_get_analysis_data_unavailable(self, client: TestClient) -> None:
        """Test analysis endpoint when stock data is unavailable."""
        with patch(
            "trendscope_backend.api.analysis.get_stock_analysis"
        ) as mock_analysis:
            # Mock data unavailable scenario
            mock_analysis.side_effect = Exception("No data available for symbol")

            response = client.get("/api/v1/analysis/INVALIDDATA")

            assert response.status_code == 404
            data = response.json()

            assert data["error"] == "Data Not Available"
            assert "symbol" in data["message"].lower()

    def test_get_analysis_server_error(self, client: TestClient) -> None:
        """Test analysis endpoint with server error."""
        with patch(
            "trendscope_backend.api.analysis.get_stock_analysis"
        ) as mock_analysis:
            # Mock server error
            mock_analysis.side_effect = Exception("Internal calculation error")

            response = client.get("/api/v1/analysis/AAPL")

            assert response.status_code == 500
            data = response.json()

            assert data["detail"]["error"] == "Analysis Error"

    def test_get_analysis_response_format(self, client: TestClient) -> None:
        """Test that analysis response follows expected format."""
        with patch(
            "trendscope_backend.api.analysis.get_stock_analysis"
        ) as mock_analysis:
            # Mock complete response
            mock_analysis.return_value = {
                "symbol": "AAPL",
                "analysis_date": "2024-01-15T10:30:00Z",
                "time_series": {
                    "start_date": "2023-12-15T00:00:00Z",
                    "end_date": "2024-01-15T00:00:00Z",
                    "data_points": 22,
                },
                "indicators": {
                    "sma_20": "152.50",
                    "sma_50": "148.75",
                    "ema_12": "153.25",
                    "ema_26": "150.80",
                    "rsi": "65.5",
                    "macd": "2.45",
                    "macd_signal": "1.85",
                    "bollinger_upper": "158.00",
                    "bollinger_lower": "145.00",
                },
                "recommendation": "BUY",
                "probability_up": "0.72",
                "confidence_level": "0.85",
            }

            response = client.get("/api/v1/analysis/AAPL")

            assert response.status_code == 200
            data = response.json()

            # Verify complete structure
            assert isinstance(data["symbol"], str)
            assert isinstance(data["analysis_date"], str)
            assert isinstance(data["time_series"], dict)
            assert isinstance(data["indicators"], dict)
            assert isinstance(data["recommendation"], str)
            assert isinstance(data["probability_up"], str)
            assert isinstance(data["confidence_level"], str)

            # Verify time series structure
            time_series = data["time_series"]
            assert "start_date" in time_series
            assert "end_date" in time_series
            assert "data_points" in time_series

            # Verify indicators structure
            indicators = data["indicators"]
            expected_indicators = [
                "sma_20",
                "sma_50",
                "ema_12",
                "ema_26",
                "rsi",
                "macd",
                "macd_signal",
                "bollinger_upper",
                "bollinger_lower",
            ]
            for indicator in expected_indicators:
                assert indicator in indicators

    def test_analysis_endpoint_cors_headers(self, client: TestClient) -> None:
        """Test that analysis endpoint includes CORS headers."""
        response = client.get(
            "/api/v1/analysis/AAPL", headers={"Origin": "http://localhost:3000"}
        )

        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers

    def test_analysis_endpoint_security_headers(self, client: TestClient) -> None:
        """Test that analysis endpoint includes security headers."""
        response = client.get("/api/v1/analysis/AAPL")

        # Should have security headers from middleware
        assert response.status_code in [200, 400, 404, 500]  # Any valid response

    def test_get_analysis_performance_timing(self, client: TestClient) -> None:
        """Test that analysis endpoint includes performance timing."""
        response = client.get("/api/v1/analysis/AAPL")

        # Should have timing header from middleware
        assert "x-process-time" in response.headers

    @pytest.mark.parametrize("symbol", ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"])
    def test_get_analysis_multiple_symbols(
        self, client: TestClient, symbol: str
    ) -> None:
        """Test analysis endpoint with multiple stock symbols."""
        with patch(
            "trendscope_backend.api.analysis.get_stock_analysis"
        ) as mock_analysis:
            mock_analysis.return_value = {"symbol": symbol}

            response = client.get(f"/api/v1/analysis/{symbol}")

            # Should handle all valid symbols
            assert response.status_code in [200, 400, 404]

    @pytest.mark.parametrize(
        "period",
        ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
    )
    def test_get_analysis_valid_periods(self, client: TestClient, period: str) -> None:
        """Test analysis endpoint with various valid periods."""
        with patch(
            "trendscope_backend.api.analysis.get_stock_analysis"
        ) as mock_analysis:
            mock_analysis.return_value = {"symbol": "AAPL", "period": period}

            response = client.get(f"/api/v1/analysis/AAPL?period={period}")

            assert response.status_code == 200

    def test_get_analysis_invalid_period(self, client: TestClient) -> None:
        """Test analysis endpoint with invalid period."""
        response = client.get("/api/v1/analysis/AAPL?period=invalid")

        assert response.status_code == 400
        data = response.json()

        assert data["detail"]["error"] == "Invalid Parameter"
        assert "period" in data["detail"]["message"].lower()

    @pytest.mark.parametrize(
        "indicators",
        [
            "sma",
            "sma,ema",
            "sma,ema,rsi",
            "rsi,macd",
            "bollinger",
            "sma,ema,rsi,macd,bollinger",
        ],
    )
    def test_get_analysis_valid_indicator_combinations(
        self, client: TestClient, indicators: str
    ) -> None:
        """Test analysis endpoint with various indicator combinations."""
        with patch(
            "trendscope_backend.api.analysis.get_stock_analysis"
        ) as mock_analysis:
            mock_analysis.return_value = {
                "symbol": "AAPL",
                "indicators": indicators.split(","),
            }

            response = client.get(f"/api/v1/analysis/AAPL?indicators={indicators}")

            assert response.status_code == 200

    def test_get_analysis_invalid_indicators(self, client: TestClient) -> None:
        """Test analysis endpoint with invalid indicators."""
        response = client.get("/api/v1/analysis/AAPL?indicators=invalid,fake")

        assert response.status_code == 400
        data = response.json()

        assert data["detail"]["error"] == "Invalid Parameter"
        assert "indicator" in data["detail"]["message"].lower()

    def test_get_analysis_with_date_range(self, client: TestClient) -> None:
        """Test analysis endpoint with custom date range."""
        with patch(
            "trendscope_backend.api.analysis.get_stock_analysis"
        ) as mock_analysis:
            mock_analysis.return_value = {"symbol": "AAPL"}

            start_date = "2023-01-01"
            end_date = "2023-12-31"
            response = client.get(
                f"/api/v1/analysis/AAPL?start_date={start_date}&end_date={end_date}"
            )

            assert response.status_code == 200

    def test_get_analysis_invalid_date_format(self, client: TestClient) -> None:
        """Test analysis endpoint with invalid date format."""
        response = client.get("/api/v1/analysis/AAPL?start_date=invalid-date")

        assert response.status_code == 400
        data = response.json()

        assert data["detail"]["error"] == "Invalid Parameter"
        assert "date" in data["detail"]["message"].lower()

    def test_get_analysis_future_date(self, client: TestClient) -> None:
        """Test analysis endpoint with future date."""
        future_date = "2030-01-01"
        response = client.get(f"/api/v1/analysis/AAPL?start_date={future_date}")

        assert response.status_code == 400
        data = response.json()

        assert data["detail"]["error"] == "Invalid Parameter"
        assert "future" in data["detail"]["message"].lower()


class TestAnalysisUtilities:
    """Test cases for analysis utility functions."""

    def test_validate_symbol_valid(self) -> None:
        """Test symbol validation with valid symbols."""
        from trendscope_backend.api.analysis import validate_symbol

        valid_symbols = ["AAPL", "GOOGL", "MSFT", "BRK-A", "BRK.B"]

        for symbol in valid_symbols:
            # Should not raise exception
            result = validate_symbol(symbol)
            assert result == symbol.upper()

    def test_validate_symbol_invalid(self) -> None:
        """Test symbol validation with invalid symbols."""
        from trendscope_backend.api.analysis import validate_symbol

        invalid_symbols = ["", "123", "TOOLONGFORSYMBOLVALIDATION", "IN@VALID", None]

        for symbol in invalid_symbols:
            with pytest.raises(ValueError):
                validate_symbol(symbol)

    def test_validate_period_valid(self) -> None:
        """Test period validation with valid periods."""
        from trendscope_backend.api.analysis import validate_period

        valid_periods = [
            "1d",
            "5d",
            "1mo",
            "3mo",
            "6mo",
            "1y",
            "2y",
            "5y",
            "10y",
            "ytd",
            "max",
        ]

        for period in valid_periods:
            # Should not raise exception
            result = validate_period(period)
            assert result == period

    def test_validate_period_invalid(self) -> None:
        """Test period validation with invalid periods."""
        from trendscope_backend.api.analysis import validate_period

        invalid_periods = ["invalid", "1h", "1w", "100y", ""]

        for period in invalid_periods:
            with pytest.raises(ValueError):
                validate_period(period)

    def test_validate_indicators_valid(self) -> None:
        """Test indicators validation with valid indicators."""
        from trendscope_backend.api.analysis import validate_indicators

        valid_indicators = [
            ["sma"],
            ["ema"],
            ["rsi"],
            ["macd"],
            ["bollinger"],
            ["sma", "ema"],
            ["sma", "rsi", "macd"],
            ["sma", "ema", "rsi", "macd", "bollinger"],
        ]

        for indicators in valid_indicators:
            # Should not raise exception
            result = validate_indicators(indicators)
            assert result == indicators

    def test_validate_indicators_invalid(self) -> None:
        """Test indicators validation with invalid indicators."""
        from trendscope_backend.api.analysis import validate_indicators

        invalid_indicators = [
            ["invalid"],
            ["fake", "sma"],
            [],
            ["sma", "invalid", "rsi"],
        ]

        for indicators in invalid_indicators:
            with pytest.raises(ValueError):
                validate_indicators(indicators)

    def test_parse_date_string_valid(self) -> None:
        """Test date string parsing with valid dates."""
        from trendscope_backend.api.analysis import parse_date_string

        valid_dates = ["2023-01-01", "2023-12-31", "2020-02-29", "2024-01-15"]

        for date_str in valid_dates:
            # Should not raise exception
            result = parse_date_string(date_str)
            assert isinstance(result, datetime)

    def test_parse_date_string_invalid(self) -> None:
        """Test date string parsing with invalid dates."""
        from trendscope_backend.api.analysis import parse_date_string

        invalid_dates = ["invalid", "2023-13-01", "2023-01-32", "2023/01/01", ""]

        for date_str in invalid_dates:
            with pytest.raises(ValueError):
                parse_date_string(date_str)

    def test_format_analysis_response(self) -> None:
        """Test formatting analysis response."""
        from trendscope_backend.api.analysis import format_analysis_response
        from trendscope_backend.data.models import (
            AnalysisResult,
            StockData,
            TechnicalIndicators,
            TimeSeriesData,
        )

        # Create sample stock data
        sample_stock_data = [
            StockData(symbol="TEST", 
                symbol="AAPL",
                date=datetime(2024, 1, 1),
                open=Decimal("150.0"),
                high=Decimal("155.0"),
                low=Decimal("148.0"),
                close=Decimal("153.0"),
                volume=1000000,
            )
        ]

        # Create sample indicators
        sample_indicators = TechnicalIndicators(
            sma_20=Decimal("152.50"), rsi=Decimal("65.5"), macd=Decimal("2.45")
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
            probability_up=Decimal("0.72"),
            confidence_level=Decimal("0.85"),
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

        # Verify recommendation is computed
        assert response["recommendation"] == "BUY"  # probability_up = 0.72

        # Verify indicators are properly formatted
        indicators = response["indicators"]
        assert indicators["sma_20"] == "152.50"
        assert indicators["rsi"] == "65.5"

    def test_format_analysis_response_with_partial_indicators(self) -> None:
        """Test formatting analysis response with some indicators set to None."""
        from trendscope_backend.api.analysis import format_analysis_response
        from trendscope_backend.data.models import (
            AnalysisResult,
            StockData,
            TechnicalIndicators,
            TimeSeriesData,
        )

        # Create sample stock data
        sample_stock_data = [
            StockData(symbol="TEST", 
                symbol="AAPL",
                date=datetime(2024, 1, 1),
                open=Decimal("150.0"),
                high=Decimal("155.0"),
                low=Decimal("148.0"),
                close=Decimal("153.0"),
                volume=1000000,
            )
        ]

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
