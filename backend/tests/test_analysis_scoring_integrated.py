"""Tests for integrated scoring system.

This module contains comprehensive tests for the integrated scoring engine
that combines multiple analysis categories into unified recommendations.
"""

from decimal import Decimal
import pytest

from trendscope_backend.analysis.scoring.integrated_scoring import (
    CategoryScore,
    IntegratedScore,
    IntegratedScoringEngine,
)
from trendscope_backend.data.models import TechnicalIndicators
from trendscope_backend.analysis.patterns.pattern_recognition import (
    PatternAnalysisResult, PatternDetection, PatternType, PatternSignal
)
from trendscope_backend.analysis.volatility.volatility_analysis import (
    VolatilityAnalysisResult, VolatilityMetrics, VolatilityRegime, RiskLevel
)
from trendscope_backend.analysis.ml.ml_predictions import (
    MLAnalysisResult, ModelPrediction, ModelType, PredictionHorizon
)


class TestCategoryScore:
    """Test cases for CategoryScore dataclass."""
    
    def test_category_score_creation(self) -> None:
        """Test creating a CategoryScore instance."""
        score = CategoryScore(
            category="technical",
            score=Decimal("0.72"),
            confidence=Decimal("0.85"),
            weight=Decimal("0.25")
        )
        
        assert score.category == "technical"
        assert score.score == Decimal("0.72")
        assert score.confidence == Decimal("0.85")
        assert score.weight == Decimal("0.25")
        assert score.details is None
    
    def test_category_score_with_details(self) -> None:
        """Test CategoryScore with additional details."""
        details = {"rsi": 65.5, "macd": 2.45}
        score = CategoryScore(
            category="technical",
            score=Decimal("0.68"),
            confidence=Decimal("0.80"),
            weight=Decimal("0.30"),
            details=details
        )
        
        assert score.details == details
        assert score.details["rsi"] == 65.5


class TestIntegratedScore:
    """Test cases for IntegratedScore dataclass."""
    
    def test_integrated_score_creation(self) -> None:
        """Test creating an IntegratedScore instance."""
        category_scores = [
            CategoryScore("technical", Decimal("0.72"), Decimal("0.85"), Decimal("0.5")),
            CategoryScore("fundamental", Decimal("0.65"), Decimal("0.70"), Decimal("0.5"))
        ]
        
        integrated = IntegratedScore(
            overall_score=Decimal("0.68"),
            confidence_level=Decimal("0.77"),
            recommendation="BUY",
            category_scores=category_scores,
            risk_assessment="MODERATE"
        )
        
        assert integrated.overall_score == Decimal("0.68")
        assert integrated.confidence_level == Decimal("0.77")
        assert integrated.recommendation == "BUY"
        assert len(integrated.category_scores) == 2
        assert integrated.risk_assessment == "MODERATE"


class TestIntegratedScoringEngine:
    """Test cases for IntegratedScoringEngine class."""
    
    @pytest.fixture
    def scoring_engine(self) -> IntegratedScoringEngine:
        """Create a test scoring engine."""
        return IntegratedScoringEngine()
    
    @pytest.fixture
    def custom_weights_engine(self) -> IntegratedScoringEngine:
        """Create a scoring engine with custom weights."""
        weights = {
            "technical": Decimal("0.4"),
            "fundamental": Decimal("0.3"),
            "sentiment": Decimal("0.3")
        }
        return IntegratedScoringEngine(weights)
    
    @pytest.fixture
    def sample_technical_indicators(self) -> TechnicalIndicators:
        """Create sample technical indicators for testing."""
        return TechnicalIndicators(
            sma_20=Decimal("155.0"),
            sma_50=Decimal("150.0"),
            ema_12=Decimal("156.0"),
            ema_26=Decimal("152.0"),
            rsi=Decimal("65.5"),
            macd=Decimal("2.45"),
            macd_signal=Decimal("1.85"),
            bollinger_upper=Decimal("158.0"),
            bollinger_lower=Decimal("145.0")
        )
    
    def test_engine_initialization_default(self, scoring_engine: IntegratedScoringEngine) -> None:
        """Test engine initialization with default weights."""
        assert scoring_engine.default_weights["technical"] == Decimal("0.25")
        assert scoring_engine.default_weights["patterns"] == Decimal("0.20")
        assert scoring_engine.default_weights["volatility"] == Decimal("0.15")
        assert sum(scoring_engine.default_weights.values()) == Decimal("1.0")
    
    def test_engine_initialization_custom(self, custom_weights_engine: IntegratedScoringEngine) -> None:
        """Test engine initialization with custom weights."""
        assert custom_weights_engine.default_weights["technical"] == Decimal("0.4")
        assert custom_weights_engine.default_weights["fundamental"] == Decimal("0.3")
        assert custom_weights_engine.default_weights["sentiment"] == Decimal("0.3")
    
    def test_calculate_technical_category_score(
        self, 
        scoring_engine: IntegratedScoringEngine,
        sample_technical_indicators: TechnicalIndicators
    ) -> None:
        """Test technical category score calculation."""
        score = scoring_engine.calculate_technical_category_score(
            sample_technical_indicators, 
            data_points=30
        )
        
        assert score.category == "technical"
        assert isinstance(score.score, Decimal)
        assert 0 <= score.score <= 1
        assert isinstance(score.confidence, Decimal)
        assert 0 <= score.confidence <= 1
        assert score.weight == Decimal("0.25")  # Default weight
        assert score.details is not None
        assert "trend_signals" in score.details
        assert "momentum_signals" in score.details
    
    def test_technical_score_details_structure(
        self,
        scoring_engine: IntegratedScoringEngine,
        sample_technical_indicators: TechnicalIndicators
    ) -> None:
        """Test the structure of technical score details."""
        score = scoring_engine.calculate_technical_category_score(
            sample_technical_indicators,
            data_points=50
        )
        
        details = score.details
        assert "trend_signals" in details
        assert "momentum_signals" in details
        assert "volatility_signals" in details
        
        # Check trend signals
        trend_signals = details["trend_signals"]
        assert "sma_cross" in trend_signals
        assert "ema_cross" in trend_signals
        
        # Check momentum signals
        momentum_signals = details["momentum_signals"]
        assert "rsi" in momentum_signals
        assert "macd" in momentum_signals
        
        # Verify RSI signal structure
        rsi_signal = momentum_signals["rsi"]
        assert "value" in rsi_signal
        assert "signal" in rsi_signal
        assert "strength" in rsi_signal
    
    def test_calculate_integrated_score_single_category(
        self, 
        scoring_engine: IntegratedScoringEngine
    ) -> None:
        """Test integrated score calculation with single category."""
        category_scores = [
            CategoryScore("technical", Decimal("0.72"), Decimal("0.85"), Decimal("1.0"))
        ]
        
        integrated = scoring_engine.calculate_integrated_score(category_scores)
        
        assert integrated.overall_score == Decimal("0.72")
        assert integrated.confidence_level == Decimal("0.85")
        assert integrated.recommendation in ["BUY", "HOLD", "SELL"]
        assert len(integrated.category_scores) == 1
        assert integrated.risk_assessment in ["LOW", "MODERATE", "HIGH"]
    
    def test_calculate_integrated_score_multiple_categories(
        self, 
        scoring_engine: IntegratedScoringEngine
    ) -> None:
        """Test integrated score calculation with multiple categories."""
        category_scores = [
            CategoryScore("technical", Decimal("0.75"), Decimal("0.85"), Decimal("0.4")),
            CategoryScore("fundamental", Decimal("0.65"), Decimal("0.70"), Decimal("0.3")),
            CategoryScore("sentiment", Decimal("0.55"), Decimal("0.60"), Decimal("0.3"))
        ]
        
        integrated = scoring_engine.calculate_integrated_score(category_scores)
        
        # Weighted average: (0.75*0.4 + 0.65*0.3 + 0.55*0.3) = 0.66
        expected_score = Decimal("0.66")
        assert abs(integrated.overall_score - expected_score) < Decimal("0.01")
        
        # Weighted confidence: (0.85*0.4 + 0.70*0.3 + 0.60*0.3) = 0.73
        expected_confidence = Decimal("0.73")
        assert abs(integrated.confidence_level - expected_confidence) < Decimal("0.05")  # Allow for consensus adjustment
        
        assert integrated.recommendation in ["BUY", "HOLD", "SELL"]
        assert len(integrated.category_scores) == 3
    
    def test_calculate_integrated_score_empty_list(
        self, 
        scoring_engine: IntegratedScoringEngine
    ) -> None:
        """Test integrated score calculation with empty category list."""
        with pytest.raises(ValueError, match="At least one category score is required"):
            scoring_engine.calculate_integrated_score([])
    
    def test_calculate_integrated_score_zero_weights(
        self, 
        scoring_engine: IntegratedScoringEngine
    ) -> None:
        """Test integrated score calculation with zero total weight."""
        category_scores = [
            CategoryScore("technical", Decimal("0.72"), Decimal("0.85"), Decimal("0.0")),
            CategoryScore("fundamental", Decimal("0.65"), Decimal("0.70"), Decimal("0.0"))
        ]
        
        with pytest.raises(ValueError, match="Total weight cannot be zero"):
            scoring_engine.calculate_integrated_score(category_scores)
    
    def test_recommendation_generation_high_confidence(
        self, 
        scoring_engine: IntegratedScoringEngine
    ) -> None:
        """Test recommendation generation with high confidence scores."""
        # High confidence bullish score
        bullish_scores = [
            CategoryScore("technical", Decimal("0.75"), Decimal("0.90"), Decimal("1.0"))
        ]
        bullish_result = scoring_engine.calculate_integrated_score(bullish_scores)
        assert bullish_result.recommendation == "BUY"
        
        # High confidence bearish score
        bearish_scores = [
            CategoryScore("technical", Decimal("0.25"), Decimal("0.90"), Decimal("1.0"))
        ]
        bearish_result = scoring_engine.calculate_integrated_score(bearish_scores)
        assert bearish_result.recommendation == "SELL"
        
        # High confidence neutral score
        neutral_scores = [
            CategoryScore("technical", Decimal("0.50"), Decimal("0.90"), Decimal("1.0"))
        ]
        neutral_result = scoring_engine.calculate_integrated_score(neutral_scores)
        assert neutral_result.recommendation == "HOLD"
    
    def test_recommendation_generation_low_confidence(
        self, 
        scoring_engine: IntegratedScoringEngine
    ) -> None:
        """Test recommendation generation with low confidence scores."""
        # Low confidence requires more extreme scores for BUY/SELL
        low_confidence_scores = [
            CategoryScore("technical", Decimal("0.65"), Decimal("0.40"), Decimal("1.0"))
        ]
        result = scoring_engine.calculate_integrated_score(low_confidence_scores)
        assert result.recommendation == "HOLD"  # Not extreme enough for low confidence
    
    def test_risk_assessment_low_risk(
        self, 
        scoring_engine: IntegratedScoringEngine
    ) -> None:
        """Test risk assessment for low risk scenarios."""
        # High confidence, low volatility
        category_scores = [
            CategoryScore("technical", Decimal("0.70"), Decimal("0.90"), Decimal("0.5")),
            CategoryScore("fundamental", Decimal("0.72"), Decimal("0.85"), Decimal("0.5"))
        ]
        
        integrated = scoring_engine.calculate_integrated_score(category_scores)
        assert integrated.risk_assessment == "LOW"
    
    def test_risk_assessment_high_risk(
        self, 
        scoring_engine: IntegratedScoringEngine
    ) -> None:
        """Test risk assessment for high risk scenarios."""
        # Low confidence, high volatility
        category_scores = [
            CategoryScore("technical", Decimal("0.80"), Decimal("0.40"), Decimal("0.5")),
            CategoryScore("fundamental", Decimal("0.30"), Decimal("0.45"), Decimal("0.5"))
        ]
        
        integrated = scoring_engine.calculate_integrated_score(category_scores)
        assert integrated.risk_assessment == "HIGH"
    
    def test_consensus_factor_calculation(
        self, 
        scoring_engine: IntegratedScoringEngine
    ) -> None:
        """Test consensus factor calculation with different score patterns."""
        # High consensus (similar scores)
        high_consensus_scores = [
            CategoryScore("technical", Decimal("0.70"), Decimal("0.80"), Decimal("0.5")),
            CategoryScore("fundamental", Decimal("0.72"), Decimal("0.75"), Decimal("0.5"))
        ]
        
        high_consensus_result = scoring_engine.calculate_integrated_score(high_consensus_scores)
        
        # Low consensus (divergent scores)
        low_consensus_scores = [
            CategoryScore("technical", Decimal("0.80"), Decimal("0.80"), Decimal("0.5")),
            CategoryScore("fundamental", Decimal("0.30"), Decimal("0.75"), Decimal("0.5"))
        ]
        
        low_consensus_result = scoring_engine.calculate_integrated_score(low_consensus_scores)
        
        # High consensus should have higher confidence adjustment
        assert high_consensus_result.confidence_level >= low_consensus_result.confidence_level
    
    def test_technical_indicators_with_none_values(
        self, 
        scoring_engine: IntegratedScoringEngine
    ) -> None:
        """Test technical score calculation with some None indicator values."""
        partial_indicators = TechnicalIndicators(
            sma_20=Decimal("155.0"),
            sma_50=None,  # Missing
            ema_12=None,  # Missing
            ema_26=None,  # Missing
            rsi=Decimal("65.5"),
            macd=Decimal("2.45"),
            macd_signal=Decimal("1.85")
        )
        
        score = scoring_engine.calculate_technical_category_score(partial_indicators, 25)
        
        assert score.category == "technical"
        assert isinstance(score.score, Decimal)
        assert isinstance(score.confidence, Decimal)
        assert score.details is not None
        
        # Should handle missing indicators gracefully
        details = score.details
        trend_signals = details["trend_signals"]
        
        # SMA cross should not be present (sma_50 is None)
        assert "sma_cross" not in trend_signals
        # EMA cross should not be present (both EMAs are None)
        assert "ema_cross" not in trend_signals
        
        # RSI and MACD should still be present
        momentum_signals = details["momentum_signals"]
        assert "rsi" in momentum_signals
        assert "macd" in momentum_signals
    
    def test_pattern_category_score_calculation(
        self, 
        scoring_engine: IntegratedScoringEngine
    ) -> None:
        """Test pattern analysis category score calculation."""
        # Create mock pattern analysis result
        patterns = [
            PatternDetection(
                pattern_type=PatternType.BULLISH_ENGULFING,
                signal=PatternSignal.BULLISH,
                confidence=Decimal("0.8"),
                start_index=5,
                end_index=6,
                description="Bullish engulfing pattern"
            ),
            PatternDetection(
                pattern_type=PatternType.SUPPORT_LEVEL,
                signal=PatternSignal.BULLISH,
                confidence=Decimal("0.7"),
                start_index=10,
                end_index=10,
                description="Support level"
            )
        ]
        
        pattern_result = PatternAnalysisResult(
            patterns=patterns,
            overall_signal=PatternSignal.BULLISH,
            signal_strength=Decimal("0.75"),
            pattern_score=Decimal("0.68")
        )
        
        score = scoring_engine.calculate_pattern_category_score(pattern_result)
        
        assert score.category == "patterns"
        assert score.score == Decimal("0.68")
        assert score.confidence == Decimal("0.75")
        assert score.weight == scoring_engine.default_weights.get("patterns", Decimal("0.20"))
        assert score.details is not None
        
        details = score.details
        assert details["patterns_detected"] == 2
        assert details["overall_signal"] == "bullish"
        assert details["signal_strength"] == 0.75
        assert len(details["pattern_types"]) == 2
    
    def test_volatility_category_score_calculation(
        self, 
        scoring_engine: IntegratedScoringEngine
    ) -> None:
        """Test volatility analysis category score calculation."""
        # Create mock volatility analysis result
        metrics = VolatilityMetrics(
            atr=Decimal("2.5"),
            atr_percentage=Decimal("1.6"),
            std_dev=Decimal("0.025"),
            std_dev_annualized=Decimal("0.39"),
            parkinson_volatility=Decimal("0.41"),
            garman_klass_volatility=Decimal("0.38"),
            volatility_ratio=Decimal("1.15"),
            volatility_percentile=Decimal("72.5")
        )
        
        volatility_result = VolatilityAnalysisResult(
            metrics=metrics,
            regime=VolatilityRegime.MODERATE,
            risk_level=RiskLevel.MODERATE,
            volatility_score=Decimal("0.6"),
            trend_volatility="increasing",
            breakout_probability=Decimal("0.45"),
            analysis_summary="Moderate volatility regime"
        )
        
        score = scoring_engine.calculate_volatility_category_score(volatility_result)
        
        assert score.category == "volatility"
        assert score.confidence == Decimal("0.45")  # Based on breakout probability
        assert score.weight == scoring_engine.default_weights.get("volatility", Decimal("0.15"))
        assert score.details is not None
        
        details = score.details
        assert details["volatility_regime"] == "moderate"
        assert details["risk_level"] == "moderate"
        assert details["trend_volatility"] == "increasing"
    
    def test_ml_category_score_calculation(
        self, 
        scoring_engine: IntegratedScoringEngine
    ) -> None:
        """Test ML prediction category score calculation."""
        # Create mock ML analysis result
        individual_predictions = [
            ModelPrediction(
                model_type=ModelType.RANDOM_FOREST,
                predicted_price=Decimal("155.0"),
                confidence=Decimal("0.8"),
                prediction_horizon=PredictionHorizon.SHORT_TERM,
                features_used=["price", "volume"],
                model_accuracy=Decimal("0.75")
            )
        ]
        
        ensemble_prediction = ModelPrediction(
            model_type=ModelType.ENSEMBLE,
            predicted_price=Decimal("154.5"),
            confidence=Decimal("0.82"),
            prediction_horizon=PredictionHorizon.SHORT_TERM,
            features_used=["price", "volume", "indicators"],
            model_accuracy=Decimal("0.78")
        )
        
        ml_result = MLAnalysisResult(
            individual_predictions=individual_predictions,
            ensemble_prediction=ensemble_prediction,
            consensus_score=Decimal("0.85"),
            trend_direction="up",
            price_target=Decimal("154.5"),
            risk_assessment="moderate",
            model_performance={"random_forest": 0.75}
        )
        
        score = scoring_engine.calculate_ml_category_score(ml_result)
        
        assert score.category == "ml"
        assert score.confidence == ensemble_prediction.confidence
        assert score.weight == scoring_engine.default_weights.get("ml", Decimal("0.20"))
        assert score.details is not None
        
        details = score.details
        assert details["trend_direction"] == "up"
        assert details["consensus_score"] == 0.85
        assert details["risk_assessment"] == "moderate"
    
    def test_fundamental_category_score_calculation(
        self, 
        scoring_engine: IntegratedScoringEngine
    ) -> None:
        """Test fundamental analysis category score calculation."""
        volume_data = [1000, 1100, 1200, 1300, 1400, 1500]
        
        score = scoring_engine.calculate_fundamental_category_score(volume_data)
        
        assert score.category == "fundamental"
        assert isinstance(score.score, Decimal)
        assert isinstance(score.confidence, Decimal)
        assert score.weight == scoring_engine.default_weights.get("fundamental", Decimal("0.15"))
        assert score.details is not None
        
        details = score.details
        assert "volume_ratio" in details
        assert "recent_volume" in details
        assert "average_volume" in details
        assert "volume_trend" in details
    
    def test_fundamental_category_score_empty_data(
        self, 
        scoring_engine: IntegratedScoringEngine
    ) -> None:
        """Test fundamental analysis with empty volume data."""
        score = scoring_engine.calculate_fundamental_category_score([])
        
        assert score.category == "fundamental"
        assert score.score == Decimal("0.5")
        assert score.confidence == Decimal("0.3")
        assert "error" in score.details
    
    def test_comprehensive_six_category_integration(
        self, 
        scoring_engine: IntegratedScoringEngine
    ) -> None:
        """Test integration of all six analysis categories."""
        # Create scores for all six categories
        category_scores = []
        
        # 1. Technical analysis
        technical_indicators = TechnicalIndicators(
            sma_20=Decimal("150"), rsi=Decimal("65"), macd=Decimal("2.5")
        )
        tech_score = scoring_engine.calculate_technical_category_score(technical_indicators, 30)
        category_scores.append(tech_score)
        
        # 2. Pattern analysis
        patterns = [PatternDetection(
            pattern_type=PatternType.BULLISH_ENGULFING,
            signal=PatternSignal.BULLISH,
            confidence=Decimal("0.8"),
            start_index=5, end_index=6,
            description="Test pattern"
        )]
        pattern_result = PatternAnalysisResult(
            patterns=patterns,
            overall_signal=PatternSignal.BULLISH,
            signal_strength=Decimal("0.7"),
            pattern_score=Decimal("0.65")
        )
        pattern_score = scoring_engine.calculate_pattern_category_score(pattern_result)
        category_scores.append(pattern_score)
        
        # 3. Volatility analysis
        vol_metrics = VolatilityMetrics(
            atr=Decimal("2.5"), atr_percentage=Decimal("1.6"),
            std_dev=Decimal("0.025"), std_dev_annualized=Decimal("0.39"),
            parkinson_volatility=Decimal("0.41"), garman_klass_volatility=Decimal("0.38"),
            volatility_ratio=Decimal("1.15"), volatility_percentile=Decimal("72.5")
        )
        vol_result = VolatilityAnalysisResult(
            metrics=vol_metrics, regime=VolatilityRegime.MODERATE,
            risk_level=RiskLevel.MODERATE, volatility_score=Decimal("0.6"),
            trend_volatility="stable", breakout_probability=Decimal("0.45"),
            analysis_summary="Test volatility"
        )
        vol_score = scoring_engine.calculate_volatility_category_score(vol_result)
        category_scores.append(vol_score)
        
        # 4. ML predictions
        ml_pred = ModelPrediction(
            model_type=ModelType.ENSEMBLE, predicted_price=Decimal("155.0"),
            confidence=Decimal("0.8"), prediction_horizon=PredictionHorizon.SHORT_TERM,
            features_used=["test"], model_accuracy=Decimal("0.75")
        )
        ml_result = MLAnalysisResult(
            individual_predictions=[ml_pred], ensemble_prediction=ml_pred,
            consensus_score=Decimal("0.85"), trend_direction="up",
            price_target=Decimal("155.0"), risk_assessment="moderate",
            model_performance={"test": 0.75}
        )
        ml_score = scoring_engine.calculate_ml_category_score(ml_result)
        category_scores.append(ml_score)
        
        # 5. Fundamental analysis
        fund_score = scoring_engine.calculate_fundamental_category_score([1000, 1100, 1200])
        category_scores.append(fund_score)
        
        # Calculate integrated score
        integrated = scoring_engine.calculate_integrated_score(category_scores)
        
        assert len(integrated.category_scores) == 5
        assert integrated.overall_score > Decimal("0")
        assert integrated.confidence_level > Decimal("0")
        assert integrated.recommendation in ["BUY", "HOLD", "SELL"]
        assert integrated.risk_assessment in ["LOW", "MODERATE", "HIGH"]
        
        # Check that all categories are represented
        categories = {score.category for score in integrated.category_scores}
        expected_categories = {"technical", "patterns", "volatility", "ml", "fundamental"}
        assert categories == expected_categories