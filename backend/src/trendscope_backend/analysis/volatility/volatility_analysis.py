"""Volatility analysis module for stock price analysis.

This module provides comprehensive volatility analysis tools including
Average True Range (ATR), standard deviation, volatility ratios, and
risk assessment metrics for stock price analysis.
"""

import pandas as pd
import numpy as np
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from trendscope_backend.data.models import StockData
from trendscope_backend.utils.logging import get_logger

logger = get_logger(__name__)


class VolatilityRegime(Enum):
    """Volatility regime classification."""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class RiskLevel(Enum):
    """Risk level classification."""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class VolatilityMetrics:
    """Comprehensive volatility metrics for stock analysis.
    
    Args:
        atr: Average True Range value
        atr_percentage: ATR as percentage of current price
        std_dev: Standard deviation of returns
        std_dev_annualized: Annualized standard deviation
        parkinson_volatility: Parkinson volatility estimator
        garman_klass_volatility: Garman-Klass volatility estimator
        volatility_ratio: Current volatility vs historical average
        volatility_percentile: Percentile rank of current volatility
        
    Example:
        >>> metrics = VolatilityMetrics(
        ...     atr=Decimal("2.45"),
        ...     atr_percentage=Decimal("1.6"),
        ...     std_dev=Decimal("0.025"),
        ...     std_dev_annualized=Decimal("0.39"),
        ...     parkinson_volatility=Decimal("0.41"),
        ...     garman_klass_volatility=Decimal("0.38"),
        ...     volatility_ratio=Decimal("1.15"),
        ...     volatility_percentile=Decimal("72.5")
        ... )
    """
    atr: Decimal
    atr_percentage: Decimal
    std_dev: Decimal
    std_dev_annualized: Decimal
    parkinson_volatility: Decimal
    garman_klass_volatility: Decimal
    volatility_ratio: Decimal
    volatility_percentile: Decimal


@dataclass
class VolatilityAnalysisResult:
    """Result of comprehensive volatility analysis.
    
    Args:
        metrics: Calculated volatility metrics
        regime: Current volatility regime classification
        risk_level: Risk level assessment
        volatility_score: Numerical score for volatility (0.0 to 1.0)
        trend_volatility: Trend in volatility (increasing/decreasing)
        breakout_probability: Probability of price breakout based on volatility
        analysis_summary: Summary of volatility analysis
        
    Example:
        >>> result = VolatilityAnalysisResult(
        ...     metrics=metrics,
        ...     regime=VolatilityRegime.MODERATE,
        ...     risk_level=RiskLevel.MODERATE,
        ...     volatility_score=Decimal("0.65"),
        ...     trend_volatility="increasing",
        ...     breakout_probability=Decimal("0.72"),
        ...     analysis_summary="Moderate volatility with increasing trend"
        ... )
    """
    metrics: VolatilityMetrics
    regime: VolatilityRegime
    risk_level: RiskLevel
    volatility_score: Decimal
    trend_volatility: str
    breakout_probability: Decimal
    analysis_summary: str


class VolatilityAnalyzer:
    """Advanced volatility analysis engine for stock price analysis.
    
    This class provides comprehensive volatility analysis including multiple
    volatility estimators, regime detection, and risk assessment metrics.
    Supports both realized and implied volatility calculations.
    
    Example:
        >>> analyzer = VolatilityAnalyzer()
        >>> result = analyzer.analyze_volatility(stock_data)
        >>> print(f"Volatility regime: {result.regime}")
        Volatility regime: VolatilityRegime.MODERATE
        >>> print(f"Risk level: {result.risk_level}")
        Risk level: RiskLevel.MODERATE
    """
    
    def __init__(self, atr_period: int = 14, lookback_period: int = 20):
        """Initialize the volatility analyzer.
        
        Args:
            atr_period: Period for ATR calculation
            lookback_period: Lookback period for volatility comparisons
            
        Example:
            >>> analyzer = VolatilityAnalyzer(atr_period=21, lookback_period=40)
        """
        self.atr_period = atr_period
        self.lookback_period = lookback_period
        self.volatility_cache: Dict[str, VolatilityAnalysisResult] = {}
    
    def analyze_volatility(self, stock_data: List[StockData]) -> VolatilityAnalysisResult:
        """Perform comprehensive volatility analysis.
        
        Calculates multiple volatility metrics, determines volatility regime,
        assesses risk levels, and provides breakout probability analysis.
        
        Args:
            stock_data: List of stock data points for analysis
            
        Returns:
            VolatilityAnalysisResult containing comprehensive volatility analysis
            
        Raises:
            ValueError: If stock_data is empty or insufficient for analysis
            
        Example:
            >>> result = analyzer.analyze_volatility(stock_data)
            >>> print(f"ATR: {result.metrics.atr}")
            ATR: 2.45
            >>> print(f"Volatility regime: {result.regime}")
            Volatility regime: VolatilityRegime.MODERATE
        """
        if not stock_data:
            raise ValueError("Stock data cannot be empty")
        
        if len(stock_data) < max(self.atr_period, self.lookback_period):
            raise ValueError(f"Insufficient data for volatility analysis "
                           f"(minimum {max(self.atr_period, self.lookback_period)} data points)")
        
        logger.info(f"Starting volatility analysis for {len(stock_data)} data points")
        
        # Convert to DataFrame for easier manipulation
        df = self._convert_to_dataframe(stock_data)
        
        # Calculate comprehensive volatility metrics
        metrics = self._calculate_volatility_metrics(df)
        
        # Determine volatility regime
        regime = self._determine_volatility_regime(metrics)
        
        # Assess risk level
        risk_level = self._assess_risk_level(metrics, regime)
        
        # Calculate volatility score
        volatility_score = self._calculate_volatility_score(metrics, regime)
        
        # Analyze volatility trend
        trend_volatility = self._analyze_volatility_trend(df)
        
        # Calculate breakout probability
        breakout_probability = self._calculate_breakout_probability(metrics, regime)
        
        # Generate analysis summary
        analysis_summary = self._generate_analysis_summary(metrics, regime, risk_level, trend_volatility)
        
        result = VolatilityAnalysisResult(
            metrics=metrics,
            regime=regime,
            risk_level=risk_level,
            volatility_score=volatility_score,
            trend_volatility=trend_volatility,
            breakout_probability=breakout_probability,
            analysis_summary=analysis_summary
        )
        
        logger.info(f"Volatility analysis completed: regime={regime}, "
                   f"risk_level={risk_level}, score={volatility_score}")
        
        return result
    
    def _convert_to_dataframe(self, stock_data: List[StockData]) -> pd.DataFrame:
        """Convert stock data to pandas DataFrame for analysis.
        
        Args:
            stock_data: List of stock data points
            
        Returns:
            DataFrame with OHLCV data and calculated fields
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
        df.sort_index(inplace=True)
        
        # Calculate returns
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Calculate true range
        df['prev_close'] = df['close'].shift(1)
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['prev_close']),
                abs(df['low'] - df['prev_close'])
            )
        )
        
        return df
    
    def _calculate_volatility_metrics(self, df: pd.DataFrame) -> VolatilityMetrics:
        """Calculate comprehensive volatility metrics.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            VolatilityMetrics object with all calculated metrics
        """
        # Average True Range (ATR)
        atr = df['tr'].rolling(window=self.atr_period).mean().iloc[-1]
        current_price = df['close'].iloc[-1]
        atr_percentage = (atr / current_price) * 100
        
        # Standard deviation of returns
        std_dev = df['returns'].std()
        std_dev_annualized = std_dev * np.sqrt(252)  # Annualized (252 trading days)
        
        # Parkinson volatility estimator
        df['parkinson_component'] = np.log(df['high'] / df['low']) ** 2
        parkinson_volatility = np.sqrt(
            df['parkinson_component'].rolling(window=self.lookback_period).mean().iloc[-1] * 252
        )
        
        # Garman-Klass volatility estimator
        df['gk_component'] = (
            0.5 * (np.log(df['high'] / df['low']) ** 2) -
            (2 * np.log(2) - 1) * (np.log(df['close'] / df['open']) ** 2)
        )
        garman_klass_volatility = np.sqrt(
            df['gk_component'].rolling(window=self.lookback_period).mean().iloc[-1] * 252
        )
        
        # Volatility ratio (current vs historical)
        recent_volatility = df['returns'].tail(self.atr_period).std()
        historical_volatility = df['returns'].head(-self.atr_period).std()
        volatility_ratio = recent_volatility / historical_volatility if historical_volatility > 0 else 1.0
        
        # Volatility percentile
        rolling_volatility = df['returns'].rolling(window=self.atr_period).std()
        current_vol = rolling_volatility.iloc[-1]
        volatility_percentile = (rolling_volatility < current_vol).sum() / len(rolling_volatility) * 100
        
        return VolatilityMetrics(
            atr=Decimal(str(round(atr, 4))),
            atr_percentage=Decimal(str(round(atr_percentage, 2))),
            std_dev=Decimal(str(round(std_dev, 4))),
            std_dev_annualized=Decimal(str(round(std_dev_annualized, 4))),
            parkinson_volatility=Decimal(str(round(parkinson_volatility, 4))),
            garman_klass_volatility=Decimal(str(round(garman_klass_volatility, 4))),
            volatility_ratio=Decimal(str(round(volatility_ratio, 4))),
            volatility_percentile=Decimal(str(round(volatility_percentile, 2)))
        )
    
    def _determine_volatility_regime(self, metrics: VolatilityMetrics) -> VolatilityRegime:
        """Determine current volatility regime based on metrics.
        
        Args:
            metrics: Calculated volatility metrics
            
        Returns:
            VolatilityRegime classification
        """
        # Use ATR percentage as primary indicator
        atr_pct = float(metrics.atr_percentage)
        vol_percentile = float(metrics.volatility_percentile)
        
        # Combine ATR percentage and volatility percentile for regime classification
        if atr_pct < 1.0 and vol_percentile < 20:
            return VolatilityRegime.VERY_LOW
        elif atr_pct < 2.0 and vol_percentile < 40:
            return VolatilityRegime.LOW
        elif atr_pct < 3.5 and vol_percentile < 70:
            return VolatilityRegime.MODERATE
        elif atr_pct < 5.0 and vol_percentile < 90:
            return VolatilityRegime.HIGH
        else:
            return VolatilityRegime.VERY_HIGH
    
    def _assess_risk_level(self, metrics: VolatilityMetrics, regime: VolatilityRegime) -> RiskLevel:
        """Assess risk level based on volatility metrics and regime.
        
        Args:
            metrics: Calculated volatility metrics
            regime: Current volatility regime
            
        Returns:
            RiskLevel classification
        """
        # Base risk assessment on volatility regime
        regime_risk_map = {
            VolatilityRegime.VERY_LOW: RiskLevel.VERY_LOW,
            VolatilityRegime.LOW: RiskLevel.LOW,
            VolatilityRegime.MODERATE: RiskLevel.MODERATE,
            VolatilityRegime.HIGH: RiskLevel.HIGH,
            VolatilityRegime.VERY_HIGH: RiskLevel.VERY_HIGH
        }
        
        base_risk = regime_risk_map[regime]
        
        # Adjust based on volatility trend
        vol_ratio = float(metrics.volatility_ratio)
        if vol_ratio > 1.5:  # Increasing volatility
            # Increase risk level
            risk_levels = list(RiskLevel)
            current_index = risk_levels.index(base_risk)
            if current_index < len(risk_levels) - 1:
                return risk_levels[current_index + 1]
        elif vol_ratio < 0.7:  # Decreasing volatility
            # Decrease risk level
            risk_levels = list(RiskLevel)
            current_index = risk_levels.index(base_risk)
            if current_index > 0:
                return risk_levels[current_index - 1]
        
        return base_risk
    
    def _calculate_volatility_score(self, metrics: VolatilityMetrics, regime: VolatilityRegime) -> Decimal:
        """Calculate numerical volatility score.
        
        Args:
            metrics: Calculated volatility metrics
            regime: Current volatility regime
            
        Returns:
            Volatility score between 0.0 and 1.0
        """
        # Base score from regime
        regime_scores = {
            VolatilityRegime.VERY_LOW: Decimal("0.1"),
            VolatilityRegime.LOW: Decimal("0.3"),
            VolatilityRegime.MODERATE: Decimal("0.5"),
            VolatilityRegime.HIGH: Decimal("0.7"),
            VolatilityRegime.VERY_HIGH: Decimal("0.9")
        }
        
        base_score = regime_scores[regime]
        
        # Adjust based on volatility percentile
        percentile_adjustment = (metrics.volatility_percentile - Decimal("50")) / Decimal("100")
        
        # Adjust based on volatility ratio
        ratio_adjustment = (metrics.volatility_ratio - Decimal("1")) * Decimal("0.1")
        
        final_score = base_score + percentile_adjustment * Decimal("0.2") + ratio_adjustment
        
        return max(Decimal("0.0"), min(Decimal("1.0"), final_score))
    
    def _analyze_volatility_trend(self, df: pd.DataFrame) -> str:
        """Analyze trend in volatility over time.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Volatility trend description
        """
        # Calculate rolling volatility
        rolling_vol = df['returns'].rolling(window=self.atr_period).std()
        
        # Compare recent vs earlier volatility
        recent_vol = rolling_vol.tail(self.atr_period // 2).mean()
        earlier_vol = rolling_vol.head(-self.atr_period // 2).tail(self.atr_period // 2).mean()
        
        if recent_vol > earlier_vol * 1.1:
            return "increasing"
        elif recent_vol < earlier_vol * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_breakout_probability(self, metrics: VolatilityMetrics, regime: VolatilityRegime) -> Decimal:
        """Calculate probability of price breakout based on volatility.
        
        Args:
            metrics: Calculated volatility metrics
            regime: Current volatility regime
            
        Returns:
            Breakout probability between 0.0 and 1.0
        """
        # Base probability from volatility regime
        regime_breakout_prob = {
            VolatilityRegime.VERY_LOW: Decimal("0.15"),
            VolatilityRegime.LOW: Decimal("0.25"),
            VolatilityRegime.MODERATE: Decimal("0.45"),
            VolatilityRegime.HIGH: Decimal("0.70"),
            VolatilityRegime.VERY_HIGH: Decimal("0.85")
        }
        
        base_prob = regime_breakout_prob[regime]
        
        # Adjust based on volatility ratio (increasing volatility increases breakout probability)
        vol_ratio = metrics.volatility_ratio
        if vol_ratio > Decimal("1.2"):
            adjustment = (vol_ratio - Decimal("1")) * Decimal("0.15")
            base_prob += adjustment
        elif vol_ratio < Decimal("0.8"):
            adjustment = (Decimal("1") - vol_ratio) * Decimal("0.1")
            base_prob -= adjustment
        
        return max(Decimal("0.0"), min(Decimal("1.0"), base_prob))
    
    def _generate_analysis_summary(
        self, 
        metrics: VolatilityMetrics, 
        regime: VolatilityRegime, 
        risk_level: RiskLevel,
        trend: str
    ) -> str:
        """Generate human-readable analysis summary.
        
        Args:
            metrics: Calculated volatility metrics
            regime: Current volatility regime
            risk_level: Risk level assessment
            trend: Volatility trend
            
        Returns:
            Analysis summary string
        """
        regime_desc = {
            VolatilityRegime.VERY_LOW: "very low",
            VolatilityRegime.LOW: "low",
            VolatilityRegime.MODERATE: "moderate",
            VolatilityRegime.HIGH: "high",
            VolatilityRegime.VERY_HIGH: "very high"
        }
        
        risk_desc = {
            RiskLevel.VERY_LOW: "very low",
            RiskLevel.LOW: "low",
            RiskLevel.MODERATE: "moderate",
            RiskLevel.HIGH: "high",
            RiskLevel.VERY_HIGH: "very high"
        }
        
        summary = (
            f"Current volatility regime is {regime_desc[regime]} "
            f"with {risk_desc[risk_level]} risk level. "
            f"ATR is {metrics.atr_percentage}% of current price. "
            f"Volatility trend is {trend}. "
            f"Annualized volatility: {metrics.std_dev_annualized}."
        )
        
        return summary
    
    def calculate_volatility_bands(self, df: pd.DataFrame, multiplier: float = 2.0) -> Tuple[pd.Series, pd.Series]:
        """Calculate volatility-based price bands.
        
        Args:
            df: DataFrame with OHLCV data
            multiplier: Multiplier for volatility bands
            
        Returns:
            Tuple of upper and lower volatility bands
        """
        # Calculate ATR-based bands
        atr = df['tr'].rolling(window=self.atr_period).mean()
        middle = df['close']
        
        upper_band = middle + (atr * multiplier)
        lower_band = middle - (atr * multiplier)
        
        return upper_band, lower_band
    
    def detect_volatility_squeeze(self, df: pd.DataFrame, threshold: float = 0.5) -> bool:
        """Detect volatility squeeze conditions.
        
        Args:
            df: DataFrame with OHLCV data
            threshold: Threshold for volatility squeeze detection
            
        Returns:
            True if volatility squeeze is detected
        """
        # Calculate current volatility vs historical
        current_vol = df['returns'].tail(self.atr_period).std()
        historical_vol = df['returns'].std()
        
        vol_ratio = current_vol / historical_vol if historical_vol > 0 else 1.0
        
        return vol_ratio < threshold