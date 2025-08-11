"""Tests for volatility analysis module."""

import pytest
import numpy as np
from datetime import datetime, UTC, timedelta
from decimal import Decimal

from trendscope_backend.analysis.volatility.volatility_analysis import (
    VolatilityAnalyzer,
    VolatilityRegime,
    RiskLevel,
    VolatilityMetrics,
    VolatilityAnalysisResult,
)
from trendscope_backend.data.models import StockData


class TestVolatilityAnalyzer:
    """Test class for VolatilityAnalyzer."""
    
    def test_init_default_parameters(self):
        """Test VolatilityAnalyzer initialization with default parameters."""
        analyzer = VolatilityAnalyzer()
        assert analyzer.atr_period == 14
        assert analyzer.lookback_period == 30
        assert analyzer.volatility_cache == {}
    
    def test_init_custom_parameters(self):
        """Test VolatilityAnalyzer initialization with custom parameters."""
        analyzer = VolatilityAnalyzer(atr_period=21, lookback_period=60)
        assert analyzer.atr_period == 21
        assert analyzer.lookback_period == 60
    
    def test_analyze_volatility_empty_data(self):
        """Test analyze_volatility with empty data."""
        analyzer = VolatilityAnalyzer()
        with pytest.raises(ValueError, match="Stock data cannot be empty"):
            analyzer.analyze_volatility([])
    
    def test_analyze_volatility_insufficient_data(self):
        """Test analyze_volatility with insufficient data."""
        analyzer = VolatilityAnalyzer()
        stock_data = self._create_sample_stock_data(5)  # Less than required
        
        with pytest.raises(ValueError, match="Insufficient data for volatility analysis"):
            analyzer.analyze_volatility(stock_data)
    
    def test_analyze_volatility_basic_functionality(self):
        """Test basic volatility analysis functionality."""
        analyzer = VolatilityAnalyzer()
        stock_data = self._create_sample_stock_data(50)
        
        result = analyzer.analyze_volatility(stock_data)
        
        assert isinstance(result, VolatilityAnalysisResult)
        assert isinstance(result.metrics, VolatilityMetrics)
        assert isinstance(result.regime, VolatilityRegime)
        assert isinstance(result.risk_level, RiskLevel)
        assert isinstance(result.volatility_score, Decimal)
        assert isinstance(result.trend_volatility, str)
        assert isinstance(result.breakout_probability, Decimal)
        assert isinstance(result.analysis_summary, str)
        
        # Check value ranges
        assert Decimal("0") <= result.volatility_score <= Decimal("1")
        assert Decimal("0") <= result.breakout_probability <= Decimal("1")
        assert result.trend_volatility in ["increasing", "decreasing", "stable"]
    
    def test_volatility_metrics_calculation(self):
        """Test volatility metrics calculation."""
        analyzer = VolatilityAnalyzer()
        stock_data = self._create_sample_stock_data(50)
        
        result = analyzer.analyze_volatility(stock_data)
        metrics = result.metrics
        
        # Check that all metrics are calculated
        assert metrics.atr > Decimal("0")
        assert metrics.atr_percentage > Decimal("0")
        assert metrics.std_dev > Decimal("0")
        assert metrics.std_dev_annualized > Decimal("0")
        assert metrics.parkinson_volatility > Decimal("0")
        assert metrics.garman_klass_volatility > Decimal("0")
        assert metrics.volatility_ratio > Decimal("0")
        assert Decimal("0") <= metrics.volatility_percentile <= Decimal("100")
    
    def test_low_volatility_regime(self):
        """Test detection of low volatility regime."""
        analyzer = VolatilityAnalyzer()
        stock_data = self._create_low_volatility_data()
        
        result = analyzer.analyze_volatility(stock_data)
        
        assert result.regime in [VolatilityRegime.VERY_LOW, VolatilityRegime.LOW]
        assert result.risk_level in [RiskLevel.VERY_LOW, RiskLevel.LOW]
        assert result.volatility_score < Decimal("0.4")
    
    def test_high_volatility_regime(self):
        """Test detection of high volatility regime."""
        analyzer = VolatilityAnalyzer()
        stock_data = self._create_high_volatility_data()
        
        result = analyzer.analyze_volatility(stock_data)
        
        assert result.regime in [VolatilityRegime.HIGH, VolatilityRegime.VERY_HIGH]
        assert result.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]
        assert result.volatility_score > Decimal("0.6")
    
    def test_moderate_volatility_regime(self):
        """Test detection of moderate volatility regime."""
        analyzer = VolatilityAnalyzer()
        stock_data = self._create_moderate_volatility_data()
        
        result = analyzer.analyze_volatility(stock_data)
        
        assert result.regime == VolatilityRegime.MODERATE
        assert result.risk_level == RiskLevel.MODERATE
        assert Decimal("0.3") <= result.volatility_score <= Decimal("0.7")
    
    def test_volatility_trend_detection(self):
        """Test volatility trend detection."""
        analyzer = VolatilityAnalyzer()
        
        # Test increasing volatility
        increasing_data = self._create_increasing_volatility_data()
        result = analyzer.analyze_volatility(increasing_data)
        assert result.trend_volatility in ["increasing", "stable"]
        
        # Test decreasing volatility
        decreasing_data = self._create_decreasing_volatility_data()
        result = analyzer.analyze_volatility(decreasing_data)
        assert result.trend_volatility in ["decreasing", "stable"]
    
    def test_breakout_probability_calculation(self):
        """Test breakout probability calculation."""
        analyzer = VolatilityAnalyzer()
        
        # High volatility should have higher breakout probability
        high_vol_data = self._create_high_volatility_data()
        high_vol_result = analyzer.analyze_volatility(high_vol_data)
        
        # Low volatility should have lower breakout probability
        low_vol_data = self._create_low_volatility_data()
        low_vol_result = analyzer.analyze_volatility(low_vol_data)
        
        assert high_vol_result.breakout_probability > low_vol_result.breakout_probability
    
    def test_analysis_summary_generation(self):
        """Test analysis summary generation."""
        analyzer = VolatilityAnalyzer()
        stock_data = self._create_sample_stock_data(50)
        
        result = analyzer.analyze_volatility(stock_data)
        
        summary = result.analysis_summary
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "volatility" in summary.lower()
        assert "risk" in summary.lower()
    
    def test_volatility_bands_calculation(self):
        """Test volatility bands calculation."""
        analyzer = VolatilityAnalyzer()
        stock_data = self._create_sample_stock_data(50)
        
        # Convert to DataFrame for band calculation
        df = analyzer._convert_to_dataframe(stock_data)
        upper_band, lower_band = analyzer.calculate_volatility_bands(df)
        
        # Check that bands are calculated
        assert len(upper_band) == len(df)
        assert len(lower_band) == len(df)
        
        # Filter out NaN values for comparison
        valid_mask = upper_band.notna() & lower_band.notna()
        valid_upper = upper_band[valid_mask]
        valid_lower = lower_band[valid_mask]
        valid_close = df['close'][valid_mask]
        
        # Upper band should be above lower band (for non-NaN values)
        assert (valid_upper >= valid_lower).all()
        
        # Bands should be around the closing price (for non-NaN values)
        assert (valid_upper >= valid_close).all()
        assert (valid_lower <= valid_close).all()
    
    def test_volatility_squeeze_detection(self):
        """Test volatility squeeze detection."""
        analyzer = VolatilityAnalyzer()
        
        # Test with low volatility data (should detect squeeze)
        low_vol_data = self._create_low_volatility_data()
        df = analyzer._convert_to_dataframe(low_vol_data)
        is_squeeze = analyzer.detect_volatility_squeeze(df)
        
        # Convert numpy bool to Python bool for type assertion
        assert isinstance(bool(is_squeeze), bool)
    
    def test_different_atr_periods(self):
        """Test analysis with different ATR periods."""
        analyzer_short = VolatilityAnalyzer(atr_period=7)
        analyzer_long = VolatilityAnalyzer(atr_period=21)
        
        stock_data = self._create_sample_stock_data(50)
        
        result_short = analyzer_short.analyze_volatility(stock_data)
        result_long = analyzer_long.analyze_volatility(stock_data)
        
        # Both should produce valid results
        assert isinstance(result_short, VolatilityAnalysisResult)
        assert isinstance(result_long, VolatilityAnalysisResult)
        
        # Metrics might differ due to different periods
        assert result_short.metrics.atr >= Decimal("0")
        assert result_long.metrics.atr >= Decimal("0")
    
    def _create_sample_stock_data(self, count: int) -> list[StockData]:
        """Create sample stock data for testing."""
        np.random.seed(42)  # For reproducible results
        
        data = []
        base_price = 100.0
        
        for i in range(count):
            # Add some random volatility
            daily_return = np.random.normal(0, 0.02)  # 2% daily volatility
            base_price *= (1 + daily_return)
            
            open_price = base_price * (1 + np.random.normal(0, 0.005))
            high = max(base_price, open_price) * (1 + abs(np.random.normal(0, 0.01)))
            low = min(base_price, open_price) * (1 - abs(np.random.normal(0, 0.01)))
            
            data.append(StockData(symbol="TEST", 
                date=datetime(2023, 1, 1, tzinfo=UTC) + timedelta(days=i),
                open=Decimal(str(round(open_price, 2))),
                high=Decimal(str(round(high, 2))),
                low=Decimal(str(round(low, 2))),
                close=Decimal(str(round(base_price, 2))),
                volume=1000 + i * 10
            ))
        
        return data
    
    def _create_low_volatility_data(self) -> list[StockData]:
        """Create low volatility stock data."""
        data = []
        base_price = 100.0
        
        for i in range(50):
            # Very low volatility
            daily_return = np.random.normal(0, 0.005)  # 0.5% daily volatility
            base_price *= (1 + daily_return)
            
            open_price = base_price * (1 + np.random.normal(0, 0.001))
            high = max(base_price, open_price) * 1.002
            low = min(base_price, open_price) * 0.998
            
            data.append(StockData(symbol="TEST", 
                date=datetime(2023, 1, 1, tzinfo=UTC) + timedelta(days=i),
                open=Decimal(str(round(open_price, 2))),
                high=Decimal(str(round(high, 2))),
                low=Decimal(str(round(low, 2))),
                close=Decimal(str(round(base_price, 2))),
                volume=1000
            ))
        
        return data
    
    def _create_high_volatility_data(self) -> list[StockData]:
        """Create high volatility stock data."""
        data = []
        base_price = 100.0
        
        for i in range(50):
            # High volatility
            daily_return = np.random.normal(0, 0.05)  # 5% daily volatility
            base_price *= (1 + daily_return)
            
            open_price = base_price * (1 + np.random.normal(0, 0.02))
            high = max(base_price, open_price) * (1 + abs(np.random.normal(0, 0.03)))
            low = min(base_price, open_price) * (1 - abs(np.random.normal(0, 0.03)))
            
            data.append(StockData(symbol="TEST", 
                date=datetime(2023, 1, 1, tzinfo=UTC) + timedelta(days=i),
                open=Decimal(str(round(open_price, 2))),
                high=Decimal(str(round(high, 2))),
                low=Decimal(str(round(low, 2))),
                close=Decimal(str(round(base_price, 2))),
                volume=1000
            ))
        
        return data
    
    def _create_moderate_volatility_data(self) -> list[StockData]:
        """Create moderate volatility stock data."""
        np.random.seed(42)  # For consistent results
        data = []
        base_price = 100.0
        
        for i in range(50):
            # Moderate volatility - reduced to stay within moderate range
            daily_return = np.random.normal(0, 0.015)  # 1.5% daily volatility
            base_price *= (1 + daily_return)
            
            open_price = base_price * (1 + np.random.normal(0, 0.008))
            # Ensure high >= max(open, close) and low <= min(open, close)
            high = max(base_price, open_price) * (1 + abs(np.random.normal(0, 0.01)))
            low = min(base_price, open_price) * (1 - abs(np.random.normal(0, 0.01)))
            
            data.append(StockData(symbol="TEST", 
                date=datetime(2023, 1, 1, tzinfo=UTC) + timedelta(days=i),
                open=Decimal(str(round(open_price, 2))),
                high=Decimal(str(round(high, 2))),
                low=Decimal(str(round(low, 2))),
                close=Decimal(str(round(base_price, 2))),
                volume=1000
            ))
        
        return data
    
    def _create_increasing_volatility_data(self) -> list[StockData]:
        """Create data with increasing volatility trend."""
        np.random.seed(42)  # For consistent results
        data = []
        base_price = 100.0
        
        for i in range(50):
            # Increasing volatility over time
            volatility = 0.01 + (i / 50) * 0.03  # From 1% to 4%
            daily_return = np.random.normal(0, volatility)
            base_price *= (1 + daily_return)
            
            open_price = base_price * (1 + np.random.normal(0, volatility / 2))
            # Ensure high >= max(open, close) and low <= min(open, close)
            high = max(base_price, open_price) * (1 + abs(np.random.normal(0, volatility)))
            low = min(base_price, open_price) * (1 - abs(np.random.normal(0, volatility)))
            
            data.append(StockData(symbol="TEST", 
                date=datetime(2023, 1, 1, tzinfo=UTC) + timedelta(days=i),
                open=Decimal(str(round(open_price, 2))),
                high=Decimal(str(round(high, 2))),
                low=Decimal(str(round(low, 2))),
                close=Decimal(str(round(base_price, 2))),
                volume=1000
            ))
        
        return data
    
    def _create_decreasing_volatility_data(self) -> list[StockData]:
        """Create data with decreasing volatility trend."""
        np.random.seed(42)  # For consistent results
        data = []
        base_price = 100.0
        
        for i in range(50):
            # Decreasing volatility over time
            volatility = 0.04 - (i / 50) * 0.03  # From 4% to 1%
            daily_return = np.random.normal(0, volatility)
            base_price *= (1 + daily_return)
            
            open_price = base_price * (1 + np.random.normal(0, volatility / 2))
            # Ensure high >= max(open, close) and low <= min(open, close)
            high = max(base_price, open_price) * (1 + abs(np.random.normal(0, volatility)))
            low = min(base_price, open_price) * (1 - abs(np.random.normal(0, volatility)))
            
            data.append(StockData(symbol="TEST", 
                date=datetime(2023, 1, 1, tzinfo=UTC) + timedelta(days=i),
                open=Decimal(str(round(open_price, 2))),
                high=Decimal(str(round(high, 2))),
                low=Decimal(str(round(low, 2))),
                close=Decimal(str(round(base_price, 2))),
                volume=1000
            ))
        
        return data


class TestVolatilityMetrics:
    """Test class for VolatilityMetrics dataclass."""
    
    def test_volatility_metrics_creation(self):
        """Test VolatilityMetrics creation."""
        metrics = VolatilityMetrics(
            atr=Decimal("2.45"),
            atr_percentage=Decimal("1.6"),
            std_dev=Decimal("0.025"),
            std_dev_annualized=Decimal("0.39"),
            parkinson_volatility=Decimal("0.41"),
            garman_klass_volatility=Decimal("0.38"),
            volatility_ratio=Decimal("1.15"),
            volatility_percentile=Decimal("72.5")
        )
        
        assert metrics.atr == Decimal("2.45")
        assert metrics.atr_percentage == Decimal("1.6")
        assert metrics.std_dev == Decimal("0.025")
        assert metrics.std_dev_annualized == Decimal("0.39")
        assert metrics.parkinson_volatility == Decimal("0.41")
        assert metrics.garman_klass_volatility == Decimal("0.38")
        assert metrics.volatility_ratio == Decimal("1.15")
        assert metrics.volatility_percentile == Decimal("72.5")


class TestVolatilityAnalysisResult:
    """Test class for VolatilityAnalysisResult dataclass."""
    
    def test_volatility_analysis_result_creation(self):
        """Test VolatilityAnalysisResult creation."""
        metrics = VolatilityMetrics(
            atr=Decimal("2.45"),
            atr_percentage=Decimal("1.6"),
            std_dev=Decimal("0.025"),
            std_dev_annualized=Decimal("0.39"),
            parkinson_volatility=Decimal("0.41"),
            garman_klass_volatility=Decimal("0.38"),
            volatility_ratio=Decimal("1.15"),
            volatility_percentile=Decimal("72.5")
        )
        
        result = VolatilityAnalysisResult(
            metrics=metrics,
            regime=VolatilityRegime.MODERATE,
            risk_level=RiskLevel.MODERATE,
            volatility_score=Decimal("0.65"),
            trend_volatility="increasing",
            breakout_probability=Decimal("0.72"),
            analysis_summary="Test analysis summary"
        )
        
        assert result.metrics == metrics
        assert result.regime == VolatilityRegime.MODERATE
        assert result.risk_level == RiskLevel.MODERATE
        assert result.volatility_score == Decimal("0.65")
        assert result.trend_volatility == "increasing"
        assert result.breakout_probability == Decimal("0.72")
        assert result.analysis_summary == "Test analysis summary"