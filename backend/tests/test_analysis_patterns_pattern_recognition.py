"""Tests for pattern recognition module."""

import pytest
from datetime import datetime, UTC
from decimal import Decimal

from trendscope_backend.analysis.patterns.pattern_recognition import (
    PatternRecognizer,
    PatternType,
    PatternSignal,
    PatternDetection,
    PatternAnalysisResult,
)
from trendscope_backend.data.models import StockData


class TestPatternRecognizer:
    """Test class for PatternRecognizer."""
    
    def test_init_default_confidence(self):
        """Test PatternRecognizer initialization with default confidence."""
        recognizer = PatternRecognizer()
        assert recognizer.min_confidence == Decimal("0.6")
        assert recognizer.patterns_cache == {}
    
    def test_init_custom_confidence(self):
        """Test PatternRecognizer initialization with custom confidence."""
        recognizer = PatternRecognizer(min_confidence=Decimal("0.8"))
        assert recognizer.min_confidence == Decimal("0.8")
    
    def test_analyze_patterns_empty_data(self):
        """Test analyze_patterns with empty data."""
        recognizer = PatternRecognizer()
        with pytest.raises(ValueError, match="Stock data cannot be empty"):
            recognizer.analyze_patterns([])
    
    def test_analyze_patterns_insufficient_data(self):
        """Test analyze_patterns with insufficient data."""
        recognizer = PatternRecognizer()
        stock_data = [
            StockData(
                symbol="TEST",
                date=datetime(2023, 1, 1, tzinfo=UTC),
                open=Decimal("100"),
                high=Decimal("105"),
                low=Decimal("95"),
                close=Decimal("102"),
                volume=1000
            )
        ]
        
        with pytest.raises(ValueError, match="Insufficient data for pattern analysis"):
            recognizer.analyze_patterns(stock_data)
    
    def test_analyze_patterns_basic_functionality(self):
        """Test basic pattern analysis functionality."""
        recognizer = PatternRecognizer()
        stock_data = self._create_sample_stock_data()
        
        result = recognizer.analyze_patterns(stock_data)
        
        assert isinstance(result, PatternAnalysisResult)
        assert isinstance(result.patterns, list)
        assert isinstance(result.overall_signal, PatternSignal)
        assert isinstance(result.signal_strength, Decimal)
        assert isinstance(result.pattern_score, Decimal)
        assert Decimal("0") <= result.signal_strength <= Decimal("1")
        assert Decimal("0") <= result.pattern_score <= Decimal("1")
    
    def test_detect_bullish_engulfing_pattern(self):
        """Test detection of bullish engulfing pattern."""
        recognizer = PatternRecognizer()
        stock_data = self._create_bullish_engulfing_data()
        
        result = recognizer.analyze_patterns(stock_data)
        
        # Should detect bullish engulfing pattern
        engulfing_patterns = [p for p in result.patterns if p.pattern_type == PatternType.BULLISH_ENGULFING]
        assert len(engulfing_patterns) > 0
        
        pattern = engulfing_patterns[0]
        assert pattern.signal == PatternSignal.BULLISH
        assert pattern.confidence >= Decimal("0.6")
        assert "bullish engulfing" in pattern.description.lower()
    
    def test_detect_bearish_engulfing_pattern(self):
        """Test detection of bearish engulfing pattern."""
        recognizer = PatternRecognizer()
        stock_data = self._create_bearish_engulfing_data()
        
        result = recognizer.analyze_patterns(stock_data)
        
        # Should detect bearish engulfing pattern
        engulfing_patterns = [p for p in result.patterns if p.pattern_type == PatternType.BEARISH_ENGULFING]
        assert len(engulfing_patterns) > 0
        
        pattern = engulfing_patterns[0]
        assert pattern.signal == PatternSignal.BEARISH
        assert pattern.confidence >= Decimal("0.6")
        assert "bearish engulfing" in pattern.description.lower()
    
    def test_detect_doji_pattern(self):
        """Test detection of doji pattern."""
        recognizer = PatternRecognizer()
        stock_data = self._create_doji_data()
        
        result = recognizer.analyze_patterns(stock_data)
        
        # Should detect doji pattern
        doji_patterns = [p for p in result.patterns if p.pattern_type == PatternType.DOJI]
        assert len(doji_patterns) > 0
        
        pattern = doji_patterns[0]
        assert pattern.signal == PatternSignal.NEUTRAL
        assert pattern.confidence >= Decimal("0.6")
        assert "doji" in pattern.description.lower()
    
    def test_detect_hammer_pattern(self):
        """Test detection of hammer pattern."""
        recognizer = PatternRecognizer()
        stock_data = self._create_hammer_data()
        
        result = recognizer.analyze_patterns(stock_data)
        
        # Should detect hammer pattern
        hammer_patterns = [p for p in result.patterns if p.pattern_type == PatternType.HAMMER]
        assert len(hammer_patterns) > 0
        
        pattern = hammer_patterns[0]
        assert pattern.signal == PatternSignal.BULLISH
        assert pattern.confidence >= Decimal("0.6")
        assert "hammer" in pattern.description.lower()
    
    def test_detect_support_resistance_levels(self):
        """Test detection of support and resistance levels."""
        recognizer = PatternRecognizer()
        stock_data = self._create_support_resistance_data()
        
        result = recognizer.analyze_patterns(stock_data)
        
        # Should detect support or resistance levels
        support_patterns = [p for p in result.patterns if p.pattern_type == PatternType.SUPPORT_LEVEL]
        resistance_patterns = [p for p in result.patterns if p.pattern_type == PatternType.RESISTANCE_LEVEL]
        
        assert len(support_patterns) > 0 or len(resistance_patterns) > 0
        
        if support_patterns:
            pattern = support_patterns[0]
            assert pattern.signal == PatternSignal.BULLISH
            assert pattern.key_levels is not None
            assert "support" in pattern.key_levels
    
    def test_detect_trend_patterns(self):
        """Test detection of trend patterns."""
        recognizer = PatternRecognizer()
        stock_data = self._create_trending_data()
        
        result = recognizer.analyze_patterns(stock_data)
        
        # Should detect trend pattern
        trend_patterns = [p for p in result.patterns if p.pattern_type == PatternType.TREND_LINE]
        assert len(trend_patterns) > 0
        
        pattern = trend_patterns[0]
        assert pattern.signal in [PatternSignal.BULLISH, PatternSignal.BEARISH, PatternSignal.STRONG_BULLISH, PatternSignal.STRONG_BEARISH]
        assert pattern.key_levels is not None
        assert "trend_slope" in pattern.key_levels
    
    def test_confidence_filtering(self):
        """Test that patterns are filtered by confidence threshold."""
        recognizer_low = PatternRecognizer(min_confidence=Decimal("0.5"))
        recognizer_high = PatternRecognizer(min_confidence=Decimal("0.9"))
        
        stock_data = self._create_sample_stock_data()
        
        result_low = recognizer_low.analyze_patterns(stock_data)
        result_high = recognizer_high.analyze_patterns(stock_data)
        
        # High confidence threshold should result in fewer patterns
        assert len(result_high.patterns) <= len(result_low.patterns)
    
    def test_overall_signal_calculation(self):
        """Test overall signal calculation logic."""
        recognizer = PatternRecognizer()
        stock_data = self._create_mixed_signal_data()
        
        result = recognizer.analyze_patterns(stock_data)
        
        # Should have a valid overall signal
        assert result.overall_signal in [
            PatternSignal.STRONG_BULLISH,
            PatternSignal.BULLISH,
            PatternSignal.NEUTRAL,
            PatternSignal.BEARISH,
            PatternSignal.STRONG_BEARISH
        ]
        
        # Signal strength should be reasonable
        assert Decimal("0") <= result.signal_strength <= Decimal("1")
    
    def test_pattern_score_calculation(self):
        """Test pattern score calculation."""
        recognizer = PatternRecognizer()
        stock_data = self._create_sample_stock_data()
        
        result = recognizer.analyze_patterns(stock_data)
        
        # Pattern score should be between 0 and 1
        assert Decimal("0") <= result.pattern_score <= Decimal("1")
        
        # Should have reasonable relationship with signal
        if result.overall_signal == PatternSignal.STRONG_BULLISH:
            assert result.pattern_score >= Decimal("0.7")
        elif result.overall_signal == PatternSignal.STRONG_BEARISH:
            assert result.pattern_score <= Decimal("0.3")
    
    def _create_sample_stock_data(self) -> list[StockData]:
        """Create sample stock data for testing."""
        return [
            StockData(
                symbol="TEST",
                date=datetime(2023, 1, i, tzinfo=UTC),
                open=Decimal(str(100 + i)),
                high=Decimal(str(105 + i)),
                low=Decimal(str(95 + i)),
                close=Decimal(str(102 + i)),
                volume=1000 + i * 10
            )
            for i in range(1, 11)
        ]
    
    def _create_bullish_engulfing_data(self) -> list[StockData]:
        """Create data with bullish engulfing pattern."""
        data = []
        
        # Create base data
        for i in range(1, 8):
            data.append(StockData(symbol="TEST",
                date=datetime(2023, 1, i, tzinfo=UTC),
                open=Decimal(str(100 + i)),
                high=Decimal(str(105 + i)),
                low=Decimal(str(95 + i)),
                close=Decimal(str(102 + i)),
                volume=1000
            ))
        
        # Add bearish candle
        data.append(StockData(
            symbol="TEST",
            date=datetime(2023, 1, 8, tzinfo=UTC),
            open=Decimal("110"),
            high=Decimal("112"),
            low=Decimal("106"),
            close=Decimal("108"),  # Bearish: close < open
            volume=1000
        ))
        
        # Add bullish engulfing candle
        data.append(StockData(symbol="TEST",
            date=datetime(2023, 1, 9, tzinfo=UTC),
            open=Decimal("107"),  # Below previous close
            high=Decimal("115"),
            low=Decimal("107"),
            close=Decimal("114"),  # Above previous open
            volume=1000
        ))
        
        return data
    
    def _create_bearish_engulfing_data(self) -> list[StockData]:
        """Create data with bearish engulfing pattern."""
        data = []
        
        # Create base data
        for i in range(1, 8):
            data.append(StockData(symbol="TEST",
                date=datetime(2023, 1, i, tzinfo=UTC),
                open=Decimal(str(100 + i)),
                high=Decimal(str(105 + i)),
                low=Decimal(str(95 + i)),
                close=Decimal(str(102 + i)),
                volume=1000
            ))
        
        # Add bullish candle
        data.append(StockData(symbol="TEST", 
            date=datetime(2023, 1, 8, tzinfo=UTC),
            open=Decimal("108"),
            high=Decimal("112"),
            low=Decimal("106"),
            close=Decimal("110"),  # Bullish: close > open
            volume=1000
        ))
        
        # Add bearish engulfing candle
        data.append(StockData(symbol="TEST", 
            date=datetime(2023, 1, 9, tzinfo=UTC),
            open=Decimal("111"),  # Above previous close
            high=Decimal("115"),
            low=Decimal("105"),
            close=Decimal("107"),  # Below previous open
            volume=1000
        ))
        
        return data
    
    def _create_doji_data(self) -> list[StockData]:
        """Create data with doji pattern."""
        data = []
        
        # Create base data
        for i in range(1, 8):
            data.append(StockData(symbol="TEST",
                date=datetime(2023, 1, i, tzinfo=UTC),
                open=Decimal(str(100 + i)),
                high=Decimal(str(105 + i)),
                low=Decimal(str(95 + i)),
                close=Decimal(str(102 + i)),
                volume=1000
            ))
        
        # Add doji candle (open ≈ close)
        data.append(StockData(symbol="TEST", 
            date=datetime(2023, 1, 8, tzinfo=UTC),
            open=Decimal("110.00"),
            high=Decimal("115.00"),
            low=Decimal("105.00"),
            close=Decimal("110.01"),  # Very close to open
            volume=1000
        ))
        
        return data
    
    def _create_hammer_data(self) -> list[StockData]:
        """Create data with hammer pattern."""
        data = []
        
        # Create base data
        for i in range(1, 8):
            data.append(StockData(symbol="TEST",
                date=datetime(2023, 1, i, tzinfo=UTC),
                open=Decimal(str(100 + i)),
                high=Decimal(str(105 + i)),
                low=Decimal(str(95 + i)),
                close=Decimal(str(102 + i)),
                volume=1000
            ))
        
        # Add hammer candle (long lower shadow, short upper shadow)
        data.append(StockData(symbol="TEST", 
            date=datetime(2023, 1, 8, tzinfo=UTC),
            open=Decimal("106.00"),
            high=Decimal("108.00"),  # Short upper shadow  
            low=Decimal("100.00"),   # Long lower shadow
            close=Decimal("107.00"), # Close > open (bullish), larger body
            volume=1000
        ))
        
        return data
    
    def _create_support_resistance_data(self) -> list[StockData]:
        """Create data with support and resistance levels."""
        data = []
        
        # Create data with repeated lows (support) and highs (resistance)
        prices = [100, 102, 105, 103, 100, 101, 105, 104, 100, 102, 105]
        
        for i, price in enumerate(prices):
            data.append(StockData(symbol="TEST", 
                date=datetime(2023, 1, i + 1, tzinfo=UTC),
                open=Decimal(str(price)),
                high=Decimal(str(price + 3)),
                low=Decimal(str(price - 2)),
                close=Decimal(str(price + 1)),
                volume=1000
            ))
        
        return data
    
    def _create_trending_data(self) -> list[StockData]:
        """Create data with clear trend."""
        data = []
        
        # Create uptrending data
        for i in range(1, 15):
            base_price = 100 + i * 2  # Clear uptrend
            data.append(StockData(symbol="TEST", 
                date=datetime(2023, 1, i, tzinfo=UTC),
                open=Decimal(str(base_price)),
                high=Decimal(str(base_price + 3)),
                low=Decimal(str(base_price - 1)),
                close=Decimal(str(base_price + 2)),
                volume=1000
            ))
        
        return data
    
    def _create_mixed_signal_data(self) -> list[StockData]:
        """Create data with mixed bullish and bearish signals."""
        data = []
        
        # Create mixed pattern data
        for i in range(1, 12):
            if i % 3 == 0:
                # Bearish candle
                data.append(StockData(symbol="TEST", 
                    date=datetime(2023, 1, i, tzinfo=UTC),
                    open=Decimal(str(105 + i)),
                    high=Decimal(str(108 + i)),
                    low=Decimal(str(100 + i)),
                    close=Decimal(str(102 + i)),
                    volume=1000
                ))
            else:
                # Bullish candle
                data.append(StockData(symbol="TEST", 
                    date=datetime(2023, 1, i, tzinfo=UTC),
                    open=Decimal(str(100 + i)),
                    high=Decimal(str(108 + i)),
                    low=Decimal(str(98 + i)),
                    close=Decimal(str(106 + i)),
                    volume=1000
                ))
        
        return data


class TestPatternDetection:
    """Test class for PatternDetection dataclass."""
    
    def test_pattern_detection_creation(self):
        """Test PatternDetection creation."""
        pattern = PatternDetection(
            pattern_type=PatternType.BULLISH_ENGULFING,
            signal=PatternSignal.BULLISH,
            confidence=Decimal("0.85"),
            start_index=5,
            end_index=6,
            description="Test pattern"
        )
        
        assert pattern.pattern_type == PatternType.BULLISH_ENGULFING
        assert pattern.signal == PatternSignal.BULLISH
        assert pattern.confidence == Decimal("0.85")
        assert pattern.start_index == 5
        assert pattern.end_index == 6
        assert pattern.description == "Test pattern"
        assert pattern.key_levels is None
    
    def test_pattern_detection_with_key_levels(self):
        """Test PatternDetection with key levels."""
        key_levels = {"support": Decimal("100.50"), "resistance": Decimal("105.75")}
        pattern = PatternDetection(
            pattern_type=PatternType.SUPPORT_LEVEL,
            signal=PatternSignal.BULLISH,
            confidence=Decimal("0.75"),
            start_index=10,
            end_index=10,
            description="Support level",
            key_levels=key_levels
        )
        
        assert pattern.key_levels == key_levels
        assert pattern.key_levels["support"] == Decimal("100.50")
        assert pattern.key_levels["resistance"] == Decimal("105.75")


class TestPatternAnalysisResult:
    """Test class for PatternAnalysisResult dataclass."""
    
    def test_pattern_analysis_result_creation(self):
        """Test PatternAnalysisResult creation."""
        patterns = [
            PatternDetection(
                pattern_type=PatternType.BULLISH_ENGULFING,
                signal=PatternSignal.BULLISH,
                confidence=Decimal("0.85"),
                start_index=5,
                end_index=6,
                description="Test pattern 1"
            ),
            PatternDetection(
                pattern_type=PatternType.SUPPORT_LEVEL,
                signal=PatternSignal.BULLISH,
                confidence=Decimal("0.75"),
                start_index=10,
                end_index=10,
                description="Test pattern 2"
            )
        ]
        
        result = PatternAnalysisResult(
            patterns=patterns,
            overall_signal=PatternSignal.BULLISH,
            signal_strength=Decimal("0.72"),
            pattern_score=Decimal("0.68")
        )
        
        assert result.patterns == patterns
        assert result.overall_signal == PatternSignal.BULLISH
        assert result.signal_strength == Decimal("0.72")
        assert result.pattern_score == Decimal("0.68")
        assert len(result.patterns) == 2