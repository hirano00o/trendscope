"""Technical pattern recognition module for stock analysis.

This module provides functionality to detect and analyze various technical patterns
in stock price data, including trend lines, candlestick patterns, and support/resistance levels.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from trendscope_backend.data.models import StockData
from trendscope_backend.utils.logging import get_logger

logger = get_logger(__name__)


class PatternType(Enum):
    """Enumeration of supported pattern types."""
    BULLISH_ENGULFING = "bullish_engulfing"
    BEARISH_ENGULFING = "bearish_engulfing"
    DOJI = "doji"
    HAMMER = "hammer"
    SHOOTING_STAR = "shooting_star"
    SUPPORT_LEVEL = "support_level"
    RESISTANCE_LEVEL = "resistance_level"
    TREND_LINE = "trend_line"
    TRIANGLE = "triangle"
    DOUBLE_TOP = "double_top"
    DOUBLE_BOTTOM = "double_bottom"


class PatternSignal(Enum):
    """Signal strength enumeration."""
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"


@dataclass
class PatternDetection:
    """Represents a detected pattern in stock data.
    
    Args:
        pattern_type: Type of pattern detected
        signal: Signal strength and direction
        confidence: Confidence level in pattern detection (0.0 to 1.0)
        start_index: Starting index of the pattern in the data
        end_index: Ending index of the pattern in the data
        description: Human-readable description of the pattern
        key_levels: Important price levels associated with the pattern
        
    Example:
        >>> pattern = PatternDetection(
        ...     pattern_type=PatternType.BULLISH_ENGULFING,
        ...     signal=PatternSignal.BULLISH,
        ...     confidence=Decimal("0.85"),
        ...     start_index=45,
        ...     end_index=46,
        ...     description="Strong bullish engulfing pattern detected",
        ...     key_levels={"support": Decimal("150.25"), "resistance": Decimal("155.80")}
        ... )
    """
    pattern_type: PatternType
    signal: PatternSignal
    confidence: float
    start_index: int
    end_index: int
    description: str
    key_levels: Optional[Dict[str, float]] = None


@dataclass
class PatternAnalysisResult:
    """Result of pattern analysis containing all detected patterns.
    
    Args:
        patterns: List of detected patterns
        overall_signal: Overall signal based on all patterns
        signal_strength: Strength of the overall signal (0.0 to 1.0)
        pattern_score: Numerical score for pattern analysis (0.0 to 1.0)
        
    Example:
        >>> result = PatternAnalysisResult(
        ...     patterns=[pattern1, pattern2],
        ...     overall_signal=PatternSignal.BULLISH,
        ...     signal_strength=Decimal("0.72"),
        ...     pattern_score=Decimal("0.68")
        ... )
    """
    patterns: List[PatternDetection]
    overall_signal: PatternSignal
    signal_strength: float
    pattern_score: float


class PatternRecognizer:
    """Advanced pattern recognition engine for technical analysis.
    
    This class implements various pattern recognition algorithms to detect
    common technical patterns in stock price data, including candlestick patterns,
    support/resistance levels, and trend formations.
    
    Example:
        >>> recognizer = PatternRecognizer()
        >>> result = recognizer.analyze_patterns(stock_data)
        >>> print(f"Found {len(result.patterns)} patterns")
        Found 3 patterns
        >>> print(f"Overall signal: {result.overall_signal}")
        Overall signal: PatternSignal.BULLISH
    """
    
    def __init__(self, min_confidence: float = 0.6):
        """Initialize the pattern recognizer.
        
        Args:
            min_confidence: Minimum confidence threshold for pattern detection
            
        Example:
            >>> recognizer = PatternRecognizer(min_confidence=0.7)
        """
        self.min_confidence = min_confidence
        self.patterns_cache: Dict[str, PatternAnalysisResult] = {}
    
    def analyze_patterns(self, stock_data: List[StockData]) -> PatternAnalysisResult:
        """Analyze stock data for technical patterns.
        
        Performs comprehensive pattern analysis including candlestick patterns,
        support/resistance levels, and trend formations.
        
        Args:
            stock_data: List of stock data points to analyze
            
        Returns:
            PatternAnalysisResult containing all detected patterns and overall signal
            
        Raises:
            ValueError: If stock_data is empty or invalid
            
        Example:
            >>> result = recognizer.analyze_patterns(stock_data)
            >>> for pattern in result.patterns:
            ...     print(f"{pattern.pattern_type}: {pattern.signal}")
            PatternType.BULLISH_ENGULFING: PatternSignal.BULLISH
            PatternType.SUPPORT_LEVEL: PatternSignal.BULLISH
        """
        if not stock_data:
            raise ValueError("Stock data cannot be empty")
        
        if len(stock_data) < 5:
            raise ValueError("Insufficient data for pattern analysis (minimum 5 data points)")
        
        logger.info(f"Starting pattern analysis for {len(stock_data)} data points")
        
        # Convert to DataFrame for easier manipulation
        df = self._convert_to_dataframe(stock_data)
        
        # Detect various pattern types
        patterns = []
        
        # Candlestick patterns
        patterns.extend(self._detect_candlestick_patterns(df))
        
        # Support and resistance levels
        patterns.extend(self._detect_support_resistance_levels(df))
        
        # Trend patterns
        patterns.extend(self._detect_trend_patterns(df))
        
        # Filter patterns by confidence threshold
        filtered_patterns = [p for p in patterns if p.confidence >= self.min_confidence]
        
        # Calculate overall signal and score
        overall_signal, signal_strength = self._calculate_overall_signal(filtered_patterns)
        pattern_score = self._calculate_pattern_score(filtered_patterns, overall_signal)
        
        result = PatternAnalysisResult(
            patterns=filtered_patterns,
            overall_signal=overall_signal,
            signal_strength=signal_strength,
            pattern_score=pattern_score
        )
        
        logger.info(f"Pattern analysis completed: {len(filtered_patterns)} patterns detected, "
                   f"overall signal: {overall_signal}, score: {pattern_score}")
        
        return result
    
    def _convert_to_dataframe(self, stock_data: List[StockData]) -> pd.DataFrame:
        """Convert stock data to pandas DataFrame for analysis.
        
        Args:
            stock_data: List of stock data points
            
        Returns:
            DataFrame with OHLCV data
        """
        data = []
        for stock in stock_data:
            data.append({
                'date': stock.date,
                'open': float(stock.open),
                'high': float(stock.high),
                'low': float(stock.low),
                'close': float(stock.close),
                'volume': int(stock.volume)
            })
        
        df = pd.DataFrame(data)
        df.set_index('date', inplace=True)
        return df
    
    def _detect_candlestick_patterns(self, df: pd.DataFrame) -> List[PatternDetection]:
        """Detect candlestick patterns in the data.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            List of detected candlestick patterns
        """
        patterns = []
        
        # Calculate body and shadow metrics
        df['body'] = abs(df['close'] - df['open'])
        df['upper_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
        df['body_ratio'] = df['body'] / (df['high'] - df['low'])
        
        # Detect patterns
        for i in range(1, len(df)):
            # Bullish Engulfing
            if (df.iloc[i]['close'] > df.iloc[i]['open'] and  # Current candle is bullish
                df.iloc[i-1]['close'] < df.iloc[i-1]['open'] and  # Previous candle is bearish
                df.iloc[i]['open'] < df.iloc[i-1]['close'] and  # Current open < previous close
                df.iloc[i]['close'] > df.iloc[i-1]['open']):  # Current close > previous open
                
                confidence = min(0.9, 
                               0.7 + (df.iloc[i]['body'] / df.iloc[i-1]['body'] - 1) * 0.1)
                
                patterns.append(PatternDetection(
                    pattern_type=PatternType.BULLISH_ENGULFING,
                    signal=PatternSignal.BULLISH,
                    confidence=max(confidence, 0.6),
                    start_index=i-1,
                    end_index=i,
                    description=f"Bullish engulfing pattern with {confidence:.2f} confidence"
                ))
            
            # Bearish Engulfing
            elif (df.iloc[i]['close'] < df.iloc[i]['open'] and  # Current candle is bearish
                  df.iloc[i-1]['close'] > df.iloc[i-1]['open'] and  # Previous candle is bullish
                  df.iloc[i]['open'] > df.iloc[i-1]['close'] and  # Current open > previous close
                  df.iloc[i]['close'] < df.iloc[i-1]['open']):  # Current close < previous open
                
                confidence = min(0.9, 
                               0.7 + (df.iloc[i]['body'] / df.iloc[i-1]['body'] - 1) * 0.1)
                
                patterns.append(PatternDetection(
                    pattern_type=PatternType.BEARISH_ENGULFING,
                    signal=PatternSignal.BEARISH,
                    confidence=max(confidence, 0.6),
                    start_index=i-1,
                    end_index=i,
                    description=f"Bearish engulfing pattern with {confidence:.2f} confidence"
                ))
            
            # Doji pattern
            elif df.iloc[i]['body_ratio'] < 0.1:  # Very small body
                confidence = 0.7 + (1 - df.iloc[i]['body_ratio']) * 0.2
                
                patterns.append(PatternDetection(
                    pattern_type=PatternType.DOJI,
                    signal=PatternSignal.NEUTRAL,
                    confidence=min(confidence, 0.9),
                    start_index=i,
                    end_index=i,
                    description=f"Doji pattern indicating indecision with {confidence:.2f} confidence"
                ))
            
            # Hammer pattern
            elif (df.iloc[i]['lower_shadow'] > 2 * df.iloc[i]['body'] and  # Long lower shadow
                  df.iloc[i]['upper_shadow'] < 0.5 * df.iloc[i]['body'] and  # Short upper shadow
                  df.iloc[i]['close'] > df.iloc[i]['open']):  # Bullish candle
                
                confidence = 0.75 + min(df.iloc[i]['lower_shadow'] / df.iloc[i]['body'], 3) * 0.05
                
                patterns.append(PatternDetection(
                    pattern_type=PatternType.HAMMER,
                    signal=PatternSignal.BULLISH,
                    confidence=min(confidence, 0.9),
                    start_index=i,
                    end_index=i,
                    description=f"Hammer pattern indicating potential reversal with {confidence:.2f} confidence"
                ))
            
            # Shooting Star pattern
            elif (df.iloc[i]['upper_shadow'] > 2 * df.iloc[i]['body'] and  # Long upper shadow
                  df.iloc[i]['lower_shadow'] < 0.5 * df.iloc[i]['body'] and  # Short lower shadow
                  df.iloc[i]['close'] < df.iloc[i]['open']):  # Bearish candle
                
                confidence = 0.75 + min(df.iloc[i]['upper_shadow'] / df.iloc[i]['body'], 3) * 0.05
                
                patterns.append(PatternDetection(
                    pattern_type=PatternType.SHOOTING_STAR,
                    signal=PatternSignal.BEARISH,
                    confidence=min(confidence, 0.9),
                    start_index=i,
                    end_index=i,
                    description=f"Shooting star pattern indicating potential reversal with {confidence:.2f} confidence"
                ))
        
        return patterns
    
    def _detect_support_resistance_levels(self, df: pd.DataFrame) -> List[PatternDetection]:
        """Detect support and resistance levels in the data.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            List of detected support and resistance levels
        """
        patterns = []
        
        # Calculate local minima and maxima
        window = max(3, len(df) // 10)  # Adaptive window size
        
        # Rolling minima for support levels
        df['local_min'] = df['low'].rolling(window=window, center=True).min()
        df['is_support'] = (df['low'] == df['local_min']) & (df['low'].shift(1) > df['low']) & (df['low'].shift(-1) > df['low'])
        
        # Rolling maxima for resistance levels
        df['local_max'] = df['high'].rolling(window=window, center=True).max()
        df['is_resistance'] = (df['high'] == df['local_max']) & (df['high'].shift(1) < df['high']) & (df['high'].shift(-1) < df['high'])
        
        # Identify significant support levels
        support_levels = df[df['is_support'] == True].copy()
        for idx, row in support_levels.iterrows():
            # Calculate confidence based on how many times the level was tested
            level_price = row['low']
            tests = len(df[(df['low'] <= level_price * 1.02) & (df['low'] >= level_price * 0.98)])
            confidence = min(0.9, 0.6 + (tests - 1) * 0.05)
            
            patterns.append(PatternDetection(
                pattern_type=PatternType.SUPPORT_LEVEL,
                signal=PatternSignal.BULLISH,
                confidence=confidence,
                start_index=df.index.get_loc(idx),
                end_index=df.index.get_loc(idx),
                description=f"Support level at {level_price:.2f} tested {tests} times",
                key_levels={"support": float(level_price)}
            ))
        
        # Identify significant resistance levels
        resistance_levels = df[df['is_resistance'] == True].copy()
        for idx, row in resistance_levels.iterrows():
            # Calculate confidence based on how many times the level was tested
            level_price = row['high']
            tests = len(df[(df['high'] <= level_price * 1.02) & (df['high'] >= level_price * 0.98)])
            confidence = min(0.9, 0.6 + (tests - 1) * 0.05)
            
            patterns.append(PatternDetection(
                pattern_type=PatternType.RESISTANCE_LEVEL,
                signal=PatternSignal.BEARISH,
                confidence=confidence,
                start_index=df.index.get_loc(idx),
                end_index=df.index.get_loc(idx),
                description=f"Resistance level at {level_price:.2f} tested {tests} times",
                key_levels={"resistance": float(level_price)}
            ))
        
        return patterns
    
    def _detect_trend_patterns(self, df: pd.DataFrame) -> List[PatternDetection]:
        """Detect trend patterns in the data.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            List of detected trend patterns
        """
        patterns = []
        
        if len(df) < 10:
            return patterns
        
        # Calculate trend using linear regression on closing prices
        x = np.arange(len(df))
        y = df['close'].values
        
        # Fit linear trend
        coeffs = np.polyfit(x, y, 1)
        trend_slope = coeffs[0]
        trend_line = np.poly1d(coeffs)
        
        # Calculate R-squared to measure trend strength
        y_pred = trend_line(x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Determine trend signal based on slope and R-squared
        if r_squared > 0.7:  # Strong trend
            if trend_slope > 0:
                signal = PatternSignal.STRONG_BULLISH
                description = f"Strong uptrend with slope {trend_slope:.4f}"
            else:
                signal = PatternSignal.STRONG_BEARISH
                description = f"Strong downtrend with slope {trend_slope:.4f}"
        elif r_squared > 0.4:  # Moderate trend
            if trend_slope > 0:
                signal = PatternSignal.BULLISH
                description = f"Moderate uptrend with slope {trend_slope:.4f}"
            else:
                signal = PatternSignal.BEARISH
                description = f"Moderate downtrend with slope {trend_slope:.4f}"
        else:
            signal = PatternSignal.NEUTRAL
            description = "No clear trend identified"
        
        confidence = min(0.95, r_squared + 0.2)
        
        patterns.append(PatternDetection(
            pattern_type=PatternType.TREND_LINE,
            signal=signal,
            confidence=confidence,
            start_index=0,
            end_index=len(df) - 1,
            description=description,
            key_levels={"trend_slope": float(trend_slope), "r_squared": float(r_squared)}
        ))
        
        return patterns
    
    def _calculate_overall_signal(self, patterns: List[PatternDetection]) -> Tuple[PatternSignal, float]:
        """Calculate overall signal from detected patterns.
        
        Args:
            patterns: List of detected patterns
            
        Returns:
            Tuple of overall signal and signal strength
        """
        if not patterns:
            return PatternSignal.NEUTRAL, 0.5
        
        # Weight patterns by confidence and recency
        bullish_score = 0.0
        bearish_score = 0.0
        total_weight = 0.0
        
        for pattern in patterns:
            weight = pattern.confidence
            
            if pattern.signal == PatternSignal.STRONG_BULLISH:
                bullish_score += weight * 2.0
            elif pattern.signal == PatternSignal.BULLISH:
                bullish_score += weight
            elif pattern.signal == PatternSignal.STRONG_BEARISH:
                bearish_score += weight * 2.0
            elif pattern.signal == PatternSignal.BEARISH:
                bearish_score += weight
            # Neutral patterns don't contribute to either score
            
            total_weight += weight
        
        if total_weight == 0:
            return PatternSignal.NEUTRAL, 0.5
        
        # Calculate net signal strength
        net_score = (bullish_score - bearish_score) / total_weight
        signal_strength = min(1.0, abs(net_score))
        
        # Determine overall signal
        if net_score > 0.5:
            overall_signal = PatternSignal.STRONG_BULLISH
        elif net_score > 0.1:
            overall_signal = PatternSignal.BULLISH
        elif net_score < -0.5:
            overall_signal = PatternSignal.STRONG_BEARISH
        elif net_score < -0.1:
            overall_signal = PatternSignal.BEARISH
        else:
            overall_signal = PatternSignal.NEUTRAL
        
        return overall_signal, signal_strength
    
    def _calculate_pattern_score(self, patterns: List[PatternDetection], overall_signal: PatternSignal) -> float:
        """Calculate numerical score for pattern analysis.
        
        Args:
            patterns: List of detected patterns
            overall_signal: Overall signal from pattern analysis
            
        Returns:
            Pattern score between 0.0 and 1.0
        """
        if not patterns:
            return 0.5
        
        # Base score from signal strength
        signal_score_map = {
            PatternSignal.STRONG_BULLISH: 0.8,
            PatternSignal.BULLISH: 0.65,
            PatternSignal.NEUTRAL: 0.5,
            PatternSignal.BEARISH: 0.35,
            PatternSignal.STRONG_BEARISH: 0.2
        }
        
        base_score = signal_score_map.get(overall_signal, 0.5)
        
        # Adjust for pattern confidence
        avg_confidence = sum(p.confidence for p in patterns) / len(patterns)
        confidence_adjustment = (avg_confidence - 0.5) * 0.1
        
        # Adjust for pattern diversity
        pattern_types = set(p.pattern_type for p in patterns)
        diversity_bonus = min(len(pattern_types) * 0.02, 0.1)
        
        final_score = base_score + confidence_adjustment + diversity_bonus
        
        return max(0.0, min(1.0, final_score))