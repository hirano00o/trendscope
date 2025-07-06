"""Integrated scoring system for comprehensive stock analysis.

This module provides the core functionality for combining multiple analysis
categories into a unified scoring system with confidence intervals.

The 6-category analysis framework:
1. Technical Analysis: Moving averages, RSI, MACD, Bollinger Bands
2. Price Pattern Analysis: Trend lines, candlestick patterns 
3. Volatility Analysis: Standard deviation, ATR, volatility ratios
4. Machine Learning: ARIMA/SARIMA, LSTM, Random Forest, SVM
5. Fundamental Elements: Volume analysis, sector/market correlations
6. Integrated Scoring: Weighted combination with confidence intervals
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from trendscope_backend.data.models import TechnicalIndicators


@dataclass
class CategoryScore:
    """Represents a score from one analysis category.
    
    Args:
        category: Name of the analysis category
        score: Numerical score (0.0 to 1.0, where >0.5 is bullish)
        confidence: Confidence level in this score (0.0 to 1.0)
        weight: Weight of this category in final scoring (0.0 to 1.0)
        details: Additional details about how this score was calculated
        
    Example:
        >>> technical_score = CategoryScore(
        ...     category="technical",
        ...     score=Decimal("0.72"),
        ...     confidence=Decimal("0.85"),
        ...     weight=Decimal("0.25")
        ... )
    """
    category: str
    score: Decimal
    confidence: Decimal
    weight: Decimal
    details: Optional[Dict[str, Any]] = None


@dataclass
class IntegratedScore:
    """Final integrated analysis score combining all categories.
    
    Args:
        overall_score: Final weighted score (0.0 to 1.0)
        confidence_level: Overall confidence in the analysis
        recommendation: Investment recommendation (BUY/HOLD/SELL)
        category_scores: Individual scores from each category
        risk_assessment: Risk level assessment
        
    Example:
        >>> integrated = IntegratedScore(
        ...     overall_score=Decimal("0.68"),
        ...     confidence_level=Decimal("0.82"),
        ...     recommendation="BUY",
        ...     category_scores=[technical_score, fundamental_score],
        ...     risk_assessment="MODERATE"
        ... )
    """
    overall_score: Decimal
    confidence_level: Decimal
    recommendation: str
    category_scores: List[CategoryScore]
    risk_assessment: str


class IntegratedScoringEngine:
    """Engine for combining multiple analysis categories into unified scores.
    
    This class implements the core logic for the 6-category analysis framework,
    combining technical indicators, patterns, volatility, ML predictions,
    fundamental factors, and generating weighted scores with confidence intervals.
    
    Example:
        >>> engine = IntegratedScoringEngine()
        >>> score = engine.calculate_integrated_score([
        ...     CategoryScore("technical", Decimal("0.72"), Decimal("0.85"), Decimal("0.25")),
        ...     CategoryScore("fundamental", Decimal("0.65"), Decimal("0.70"), Decimal("0.20"))
        ... ])
        >>> print(f"Overall score: {score.overall_score}")
        Overall score: 0.69
    """
    
    def __init__(self, default_weights: Optional[Dict[str, Decimal]] = None):
        """Initialize the scoring engine with category weights.
        
        Args:
            default_weights: Default weights for each category. If not provided,
                equal weights are used for available categories.
                
        Example:
            >>> weights = {
            ...     "technical": Decimal("0.25"),
            ...     "patterns": Decimal("0.20"),
            ...     "volatility": Decimal("0.15"),
            ...     "ml": Decimal("0.20"),
            ...     "fundamental": Decimal("0.15"),
            ...     "sentiment": Decimal("0.05")
            ... }
            >>> engine = IntegratedScoringEngine(weights)
        """
        self.default_weights = default_weights or {
            "technical": Decimal("0.25"),
            "patterns": Decimal("0.20"),
            "volatility": Decimal("0.15"),
            "ml": Decimal("0.20"),
            "fundamental": Decimal("0.15"),
            "sentiment": Decimal("0.05")
        }
    
    def calculate_technical_category_score(
        self, 
        indicators: TechnicalIndicators,
        data_points: int
    ) -> CategoryScore:
        """Calculate score for technical analysis category.
        
        Combines multiple technical indicators into a single category score
        using weighted averages and trend analysis.
        
        Args:
            indicators: Technical indicators calculated from price data
            data_points: Number of data points used in calculation
            
        Returns:
            CategoryScore representing technical analysis results
            
        Example:
            >>> indicators = TechnicalIndicators(
            ...     sma_20=Decimal("152.50"),
            ...     rsi=Decimal("65.5"),
            ...     macd=Decimal("2.45")
            ... )
            >>> score = engine.calculate_technical_category_score(indicators, 30)
            >>> print(f"Technical score: {score.score}")
            Technical score: 0.68
        """
        from trendscope_backend.api.analysis import calculate_probability, calculate_confidence
        
        # Use existing probability and confidence calculations
        probability = calculate_probability(indicators)
        confidence = calculate_confidence(indicators, data_points)
        
        # Calculate detailed breakdown for transparency
        details = self._calculate_technical_details(indicators)
        
        return CategoryScore(
            category="technical",
            score=probability,
            confidence=confidence,
            weight=self.default_weights.get("technical", Decimal("0.25")),
            details=details
        )
    
    def calculate_integrated_score(self, category_scores: List[CategoryScore]) -> IntegratedScore:
        """Calculate final integrated score from all category scores.
        
        Combines multiple category scores using weighted averages, with confidence
        adjustments and risk assessment based on score distribution and volatility.
        
        Args:
            category_scores: List of scores from different analysis categories
            
        Returns:
            IntegratedScore containing final recommendation and analysis
            
        Raises:
            ValueError: If category_scores is empty or contains invalid scores
            
        Example:
            >>> scores = [
            ...     CategoryScore("technical", Decimal("0.72"), Decimal("0.85"), Decimal("0.4")),
            ...     CategoryScore("fundamental", Decimal("0.65"), Decimal("0.70"), Decimal("0.6"))
            ... ]
            >>> integrated = engine.calculate_integrated_score(scores)
            >>> print(f"Recommendation: {integrated.recommendation}")
            Recommendation: BUY
        """
        if not category_scores:
            raise ValueError("At least one category score is required")
        
        # Normalize weights to sum to 1.0
        total_weight = sum(score.weight for score in category_scores)
        if total_weight == 0:
            raise ValueError("Total weight cannot be zero")
        
        # Calculate weighted average score
        weighted_sum = Decimal("0")
        confidence_weighted_sum = Decimal("0")
        
        for score in category_scores:
            normalized_weight = score.weight / total_weight
            weighted_sum += score.score * normalized_weight
            confidence_weighted_sum += score.confidence * normalized_weight
        
        overall_score = weighted_sum
        overall_confidence = confidence_weighted_sum
        
        # Adjust confidence based on score consensus
        consensus_factor = self._calculate_consensus_factor(category_scores)
        adjusted_confidence = overall_confidence * consensus_factor
        
        # Generate recommendation
        recommendation = self._generate_recommendation(overall_score, adjusted_confidence)
        
        # Assess risk level
        risk_assessment = self._assess_risk_level(category_scores, overall_score)
        
        return IntegratedScore(
            overall_score=overall_score,
            confidence_level=adjusted_confidence,
            recommendation=recommendation,
            category_scores=category_scores,
            risk_assessment=risk_assessment
        )
    
    def _calculate_technical_details(self, indicators: TechnicalIndicators) -> Dict[str, Any]:
        """Calculate detailed breakdown of technical indicators.
        
        Args:
            indicators: Technical indicators to analyze
            
        Returns:
            Dictionary containing detailed technical analysis breakdown
        """
        details = {
            "trend_signals": {},
            "momentum_signals": {},
            "volatility_signals": {}
        }
        
        # Trend analysis
        if indicators.sma_20 is not None and indicators.sma_50 is not None:
            details["trend_signals"]["sma_cross"] = {
                "signal": "bullish" if indicators.sma_20 > indicators.sma_50 else "bearish",
                "strength": abs(float(indicators.sma_20 - indicators.sma_50)) / float(indicators.sma_50)
            }
        
        if indicators.ema_12 is not None and indicators.ema_26 is not None:
            details["trend_signals"]["ema_cross"] = {
                "signal": "bullish" if indicators.ema_12 > indicators.ema_26 else "bearish",
                "strength": abs(float(indicators.ema_12 - indicators.ema_26)) / float(indicators.ema_26)
            }
        
        # Momentum analysis
        if indicators.rsi is not None:
            rsi_value = float(indicators.rsi)
            if rsi_value < 30:
                signal = "oversold_bullish"
            elif rsi_value > 70:
                signal = "overbought_bearish"
            else:
                signal = "neutral"
            
            details["momentum_signals"]["rsi"] = {
                "value": rsi_value,
                "signal": signal,
                "strength": min(abs(rsi_value - 50) / 50, 1.0)
            }
        
        if indicators.macd is not None and indicators.macd_signal is not None:
            details["momentum_signals"]["macd"] = {
                "signal": "bullish" if indicators.macd > indicators.macd_signal else "bearish",
                "divergence": float(indicators.macd - indicators.macd_signal)
            }
        
        return details
    
    def _calculate_consensus_factor(self, category_scores: List[CategoryScore]) -> Decimal:
        """Calculate consensus factor based on agreement between categories.
        
        Args:
            category_scores: List of category scores to analyze
            
        Returns:
            Consensus factor (0.5 to 1.0) where 1.0 means perfect agreement
        """
        if len(category_scores) < 2:
            return Decimal("1.0")
        
        # Calculate variance in scores
        scores = [score.score for score in category_scores]
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        
        # Convert variance to consensus factor (lower variance = higher consensus)
        # Variance of 0 = consensus 1.0, variance of 0.25 = consensus 0.5
        max_variance = Decimal("0.25")
        consensus = max(Decimal("0.5"), Decimal("1.0") - (variance / max_variance))
        
        return min(consensus, Decimal("1.0"))
    
    def _generate_recommendation(self, score: Decimal, confidence: Decimal) -> str:
        """Generate investment recommendation based on score and confidence.
        
        Args:
            score: Overall score (0.0 to 1.0)
            confidence: Confidence level (0.0 to 1.0)
            
        Returns:
            Recommendation string: "BUY", "HOLD", or "SELL"
        """
        # Adjust thresholds based on confidence
        if confidence >= Decimal("0.8"):
            buy_threshold = Decimal("0.6")
            sell_threshold = Decimal("0.4")
        elif confidence >= Decimal("0.6"):
            buy_threshold = Decimal("0.65")
            sell_threshold = Decimal("0.35")
        else:
            buy_threshold = Decimal("0.7")
            sell_threshold = Decimal("0.3")
        
        if score >= buy_threshold:
            return "BUY"
        elif score <= sell_threshold:
            return "SELL"
        else:
            return "HOLD"
    
    def _assess_risk_level(self, category_scores: List[CategoryScore], overall_score: Decimal) -> str:
        """Assess risk level based on score distribution and confidence levels.
        
        Args:
            category_scores: List of category scores
            overall_score: Overall integrated score
            
        Returns:
            Risk assessment string: "LOW", "MODERATE", or "HIGH"
        """
        # Calculate average confidence
        avg_confidence = sum(score.confidence for score in category_scores) / len(category_scores)
        
        # Calculate score volatility
        scores = [score.score for score in category_scores]
        if len(scores) > 1:
            mean_score = sum(scores) / len(scores)
            score_volatility = (sum((score - mean_score) ** 2 for score in scores) / len(scores)) ** Decimal("0.5")
        else:
            score_volatility = Decimal("0")
        
        # Assess risk based on confidence and volatility
        if avg_confidence >= Decimal("0.8") and score_volatility <= Decimal("0.1"):
            return "LOW"
        elif avg_confidence >= Decimal("0.6") and score_volatility <= Decimal("0.2"):
            return "MODERATE"
        else:
            return "HIGH"