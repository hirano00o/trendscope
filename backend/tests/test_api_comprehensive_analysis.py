"""Tests for comprehensive analysis API endpoints."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, UTC
from decimal import Decimal

from fastapi import HTTPException

from trendscope_backend.api.comprehensive_analysis import (
    get_comprehensive_analysis,
    _perform_comprehensive_analysis,
    _generate_integrated_analysis,
    _format_technical_analysis,
    _format_pattern_analysis,
    _format_volatility_analysis,
    _format_ml_analysis,
    _format_fundamental_analysis,
    _generate_analysis_summary,
)
from trendscope_backend.data.models import StockData, TechnicalIndicators
from trendscope_backend.analysis.patterns.pattern_recognition import (
    PatternAnalysisResult, PatternDetection, PatternType, PatternSignal
)
from trendscope_backend.analysis.volatility.volatility_analysis import (
    VolatilityAnalysisResult, VolatilityMetrics, VolatilityRegime, RiskLevel
)
from trendscope_backend.analysis.ml.ml_predictions import (
    MLAnalysisResult, ModelPrediction, ModelType, PredictionHorizon
)
from trendscope_backend.analysis.scoring.integrated_scoring import (
    IntegratedScore, CategoryScore
)


class TestComprehensiveAnalysis:
    """Test class for comprehensive analysis functionality."""
    
    @pytest.mark.asyncio
    async def test_get_comprehensive_analysis_empty_symbol(self):
        """Test comprehensive analysis with empty symbol."""
        with pytest.raises(HTTPException) as exc_info:
            await get_comprehensive_analysis("")
        
        assert exc_info.value.status_code == 400
        assert "Invalid Parameter" in exc_info.value.detail["error"]
    
    @pytest.mark.asyncio
    async def test_get_comprehensive_analysis_invalid_period(self):
        """Test comprehensive analysis with invalid period."""
        with pytest.raises(HTTPException) as exc_info:
            await get_comprehensive_analysis("AAPL", period="invalid")
        
        assert exc_info.value.status_code == 400
        assert "Invalid Parameter" in exc_info.value.detail["error"]
    
    @pytest.mark.asyncio
    @patch('trendscope_backend.api.comprehensive_analysis.StockDataFetcher')
    async def test_get_comprehensive_analysis_no_data(self, mock_fetcher):
        """Test comprehensive analysis with no stock data."""
        mock_instance = Mock()
        mock_instance.fetch_stock_data.return_value = []
        mock_fetcher.return_value = mock_instance
        
        with pytest.raises(HTTPException) as exc_info:
            await get_comprehensive_analysis("INVALID", period="1mo")
        
        assert exc_info.value.status_code == 404
        assert "Data Not Available" in exc_info.value.detail["error"]
    
    @pytest.mark.asyncio
    @patch('trendscope_backend.api.comprehensive_analysis.StockDataFetcher')
    @patch('trendscope_backend.api.comprehensive_analysis._perform_comprehensive_analysis')
    @patch('trendscope_backend.api.comprehensive_analysis._generate_integrated_analysis')
    async def test_get_comprehensive_analysis_success(self, mock_generate, mock_perform, mock_fetcher):
        """Test successful comprehensive analysis."""
        # Mock stock data fetcher
        mock_instance = Mock()
        stock_data = self._create_sample_stock_data()
        mock_instance.fetch_stock_data.return_value = stock_data
        mock_fetcher.return_value = mock_instance
        
        # Mock analysis results
        mock_results = {"technical": {}, "patterns": {"success": True}}
        mock_perform.return_value = mock_results
        
        # Mock integrated analysis
        mock_integrated = {
            "symbol": "AAPL",
            "analysis_date": "2023-01-01T00:00:00Z",
            "integrated_score": {"overall_score": "0.72"}
        }
        mock_generate.return_value = mock_integrated
        
        result = await get_comprehensive_analysis("AAPL", period="1mo")
        
        assert result["symbol"] == "AAPL"
        assert "integrated_score" in result
        mock_perform.assert_called_once()
        mock_generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_perform_comprehensive_analysis(self):
        """Test comprehensive analysis performance."""
        stock_data = self._create_sample_stock_data()
        
        with patch('trendscope_backend.api.comprehensive_analysis.TechnicalIndicatorCalculator') as mock_tech, \
             patch('trendscope_backend.api.comprehensive_analysis.PatternRecognizer') as mock_pattern, \
             patch('trendscope_backend.api.comprehensive_analysis.VolatilityAnalyzer') as mock_vol, \
             patch('trendscope_backend.api.comprehensive_analysis.MLPredictor') as mock_ml:
            
            # Mock technical analysis
            mock_tech_instance = Mock()
            mock_indicators = TechnicalIndicators(
                sma_20=Decimal("150"), rsi=Decimal("65"), macd=Decimal("2.5")
            )
            mock_tech_instance.calculate_all_indicators.return_value = mock_indicators
            mock_tech.return_value = mock_tech_instance
            
            # Mock pattern analysis
            mock_pattern_instance = Mock()
            mock_pattern_result = self._create_mock_pattern_result()
            mock_pattern_instance.analyze_patterns.return_value = mock_pattern_result
            mock_pattern.return_value = mock_pattern_instance
            
            # Mock volatility analysis
            mock_vol_instance = Mock()
            mock_vol_result = self._create_mock_volatility_result()
            mock_vol_instance.analyze_volatility.return_value = mock_vol_result
            mock_vol.return_value = mock_vol_instance
            
            # Mock ML analysis
            mock_ml_instance = Mock()
            mock_ml_result = self._create_mock_ml_result()
            mock_ml_instance.predict_stock_price.return_value = mock_ml_result
            mock_ml.return_value = mock_ml_instance
            
            results = await _perform_comprehensive_analysis(stock_data, include_ml=True)
            
            assert "technical" in results
            assert "patterns" in results
            assert "volatility" in results
            assert "ml" in results
            assert "fundamental" in results
            
            assert results["technical"]["indicators"] == mock_indicators
            assert results["patterns"]["success"] is True
            assert results["volatility"]["success"] is True
            assert results["ml"]["success"] is True
            assert results["fundamental"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_perform_comprehensive_analysis_without_ml(self):
        """Test comprehensive analysis without ML predictions."""
        stock_data = self._create_sample_stock_data()
        
        with patch('trendscope_backend.api.comprehensive_analysis.TechnicalIndicatorCalculator') as mock_tech:
            mock_tech_instance = Mock()
            mock_indicators = TechnicalIndicators(sma_20=Decimal("150"))
            mock_tech_instance.calculate_all_indicators.return_value = mock_indicators
            mock_tech.return_value = mock_tech_instance
            
            results = await _perform_comprehensive_analysis(stock_data, include_ml=False)
            
            assert "technical" in results
            assert "ml" in results
            assert results["ml"]["success"] is False
            assert "skipped" in results["ml"]
    
    def test_generate_integrated_analysis(self):
        """Test integrated analysis generation."""
        stock_data = self._create_sample_stock_data()
        results = {
            "technical": {
                "indicators": TechnicalIndicators(sma_20=Decimal("150"), rsi=Decimal("65")),
                "data_points": 30
            },
            "patterns": {
                "result": self._create_mock_pattern_result(),
                "success": True
            },
            "volatility": {
                "result": self._create_mock_volatility_result(),
                "success": True
            },
            "ml": {
                "result": self._create_mock_ml_result(),
                "success": True
            },
            "fundamental": {
                "volume_data": [1000, 1100, 1200],
                "success": True
            }
        }
        
        with patch('trendscope_backend.api.comprehensive_analysis.IntegratedScoringEngine') as mock_engine:
            mock_engine_instance = Mock()
            
            # Mock category scores
            mock_tech_score = CategoryScore("technical", Decimal("0.7"), Decimal("0.8"), Decimal("0.25"))
            mock_pattern_score = CategoryScore("patterns", Decimal("0.6"), Decimal("0.7"), Decimal("0.2"))
            mock_vol_score = CategoryScore("volatility", Decimal("0.5"), Decimal("0.6"), Decimal("0.15"))
            mock_ml_score = CategoryScore("ml", Decimal("0.8"), Decimal("0.9"), Decimal("0.2"))
            mock_fund_score = CategoryScore("fundamental", Decimal("0.6"), Decimal("0.5"), Decimal("0.15"))
            
            mock_engine_instance.calculate_technical_category_score.return_value = mock_tech_score
            mock_engine_instance.calculate_pattern_category_score.return_value = mock_pattern_score
            mock_engine_instance.calculate_volatility_category_score.return_value = mock_vol_score
            mock_engine_instance.calculate_ml_category_score.return_value = mock_ml_score
            mock_engine_instance.calculate_fundamental_category_score.return_value = mock_fund_score
            
            # Mock integrated score
            mock_integrated = IntegratedScore(
                overall_score=Decimal("0.68"),
                confidence_level=Decimal("0.75"),
                recommendation="BUY",
                category_scores=[mock_tech_score, mock_pattern_score],
                risk_assessment="MODERATE"
            )
            mock_engine_instance.calculate_integrated_score.return_value = mock_integrated
            mock_engine.return_value = mock_engine_instance
            
            result = _generate_integrated_analysis(results, "AAPL", stock_data)
            
            assert result["symbol"] == "AAPL"
            assert "analysis_date" in result
            assert "technical_analysis" in result
            assert "pattern_analysis" in result
            assert "volatility_analysis" in result
            assert "ml_predictions" in result
            assert "fundamental_analysis" in result
            assert "integrated_score" in result
            assert "summary" in result
            
            # Check integrated score format
            integrated = result["integrated_score"]
            assert integrated["overall_score"] == "0.68"
            assert integrated["confidence_level"] == "0.75"
            assert integrated["recommendation"] == "BUY"
            assert integrated["risk_assessment"] == "MODERATE"
            assert len(integrated["category_scores"]) == 5
    
    def test_format_technical_analysis(self):
        """Test technical analysis formatting."""
        technical_data = {
            "indicators": TechnicalIndicators(
                sma_20=Decimal("150.25"),
                rsi=Decimal("65.5"),
                macd=Decimal("2.45")
            )
        }
        
        result = _format_technical_analysis(technical_data)
        
        assert result["success"] is True
        assert "indicators" in result
        assert result["indicators"]["sma_20"] == "150.25"
        assert result["indicators"]["rsi"] == "65.5"
        assert result["indicators"]["macd"] == "2.45"
    
    def test_format_technical_analysis_none(self):
        """Test technical analysis formatting with None input."""
        result = _format_technical_analysis(None)
        assert "error" in result
    
    def test_format_pattern_analysis(self):
        """Test pattern analysis formatting."""
        pattern_data = {
            "result": self._create_mock_pattern_result(),
            "success": True
        }
        
        result = _format_pattern_analysis(pattern_data)
        
        assert result["success"] is True
        assert "patterns_detected" in result
        assert "overall_signal" in result
        assert "signal_strength" in result
        assert "pattern_score" in result
        assert "patterns" in result
    
    def test_format_pattern_analysis_error(self):
        """Test pattern analysis formatting with error."""
        pattern_data = {
            "error": "Pattern analysis failed",
            "success": False
        }
        
        result = _format_pattern_analysis(pattern_data)
        assert "error" in result
        assert result["error"] == "Pattern analysis failed"
    
    def test_format_volatility_analysis(self):
        """Test volatility analysis formatting."""
        volatility_data = {
            "result": self._create_mock_volatility_result(),
            "success": True
        }
        
        result = _format_volatility_analysis(volatility_data)
        
        assert result["success"] is True
        assert "regime" in result
        assert "risk_level" in result
        assert "volatility_score" in result
        assert "metrics" in result
    
    def test_format_ml_analysis(self):
        """Test ML analysis formatting."""
        ml_data = {
            "result": self._create_mock_ml_result(),
            "success": True
        }
        
        result = _format_ml_analysis(ml_data)
        
        assert result["success"] is True
        assert "trend_direction" in result
        assert "price_target" in result
        assert "consensus_score" in result
        assert "ensemble_prediction" in result
        assert "individual_predictions" in result
    
    def test_format_fundamental_analysis(self):
        """Test fundamental analysis formatting."""
        fundamental_data = {
            "volume_data": [1000, 1100, 1200, 1300, 1400],
            "success": True
        }
        
        result = _format_fundamental_analysis(fundamental_data)
        
        assert result["success"] is True
        assert "volume_analysis" in result
        assert "recent_average" in result["volume_analysis"]
        assert "overall_average" in result["volume_analysis"]
        assert "volume_trend" in result["volume_analysis"]
    
    def test_generate_analysis_summary(self):
        """Test analysis summary generation."""
        integrated_score = IntegratedScore(
            overall_score=Decimal("0.72"),
            confidence_level=Decimal("0.85"),
            recommendation="BUY",
            category_scores=[],
            risk_assessment="MODERATE"
        )
        
        category_scores = [
            CategoryScore("technical", Decimal("0.8"), Decimal("0.9"), Decimal("0.25")),
            CategoryScore("patterns", Decimal("0.6"), Decimal("0.7"), Decimal("0.2"))
        ]
        
        summary = _generate_analysis_summary(integrated_score, category_scores, "AAPL")
        
        assert isinstance(summary, str)
        assert "AAPL" in summary
        assert "bullish" in summary.lower()
        assert "BUY" in summary
        assert "MODERATE" in summary
    
    def _create_sample_stock_data(self) -> list[StockData]:
        """Create sample stock data for testing."""
        return [
            StockData(symbol="TEST", 
                date=datetime(2023, 1, i, tzinfo=UTC),
                open=Decimal(str(100 + i)),
                high=Decimal(str(105 + i)),
                low=Decimal(str(95 + i)),
                close=Decimal(str(102 + i)),
                volume=1000 + i * 10
            )
            for i in range(1, 31)  # 30 data points
        ]
    
    def _create_mock_pattern_result(self) -> PatternAnalysisResult:
        """Create mock pattern analysis result."""
        patterns = [
            PatternDetection(
                pattern_type=PatternType.BULLISH_ENGULFING,
                signal=PatternSignal.BULLISH,
                confidence=Decimal("0.8"),
                start_index=5,
                end_index=6,
                description="Bullish engulfing pattern"
            )
        ]
        
        return PatternAnalysisResult(
            patterns=patterns,
            overall_signal=PatternSignal.BULLISH,
            signal_strength=Decimal("0.7"),
            pattern_score=Decimal("0.65")
        )
    
    def _create_mock_volatility_result(self) -> VolatilityAnalysisResult:
        """Create mock volatility analysis result."""
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
        
        return VolatilityAnalysisResult(
            metrics=metrics,
            regime=VolatilityRegime.MODERATE,
            risk_level=RiskLevel.MODERATE,
            volatility_score=Decimal("0.6"),
            trend_volatility="stable",
            breakout_probability=Decimal("0.45"),
            analysis_summary="Moderate volatility regime"
        )
    
    def _create_mock_ml_result(self) -> MLAnalysisResult:
        """Create mock ML analysis result."""
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
            model_accuracy=Decimal("0.78"),
            prediction_interval=(Decimal("150.0"), Decimal("159.0"))
        )
        
        return MLAnalysisResult(
            individual_predictions=individual_predictions,
            ensemble_prediction=ensemble_prediction,
            consensus_score=Decimal("0.85"),
            trend_direction="up",
            price_target=Decimal("154.5"),
            risk_assessment="moderate",
            model_performance={"random_forest": 0.75}
        )