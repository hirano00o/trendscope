"""Tests for machine learning predictions module."""

import pytest
import numpy as np
from datetime import datetime, UTC, timedelta
from decimal import Decimal

from trendscope_backend.analysis.ml.ml_predictions import (
    MLPredictor,
    ModelType,
    PredictionHorizon,
    ModelPrediction,
    MLAnalysisResult,
)
from trendscope_backend.data.models import StockData


class TestMLPredictor:
    """Test class for MLPredictor."""
    
    def test_init_default_parameters(self):
        """Test MLPredictor initialization with default parameters."""
        predictor = MLPredictor()
        assert predictor.prediction_horizon == PredictionHorizon.SHORT_TERM
        assert predictor.models_cache == {}
        assert predictor.feature_importance == {}
    
    def test_init_custom_parameters(self):
        """Test MLPredictor initialization with custom parameters."""
        predictor = MLPredictor(PredictionHorizon.MEDIUM_TERM)
        assert predictor.prediction_horizon == PredictionHorizon.MEDIUM_TERM
    
    def test_predict_stock_price_empty_data(self):
        """Test predict_stock_price with empty data."""
        predictor = MLPredictor()
        with pytest.raises(ValueError, match="Stock data cannot be empty"):
            predictor.predict_stock_price([])
    
    def test_predict_stock_price_insufficient_data(self):
        """Test predict_stock_price with insufficient data."""
        predictor = MLPredictor()
        stock_data = self._create_sample_stock_data(20)  # Less than required 30
        
        with pytest.raises(ValueError, match="Insufficient data for ML prediction"):
            predictor.predict_stock_price(stock_data)
    
    def test_predict_stock_price_basic_functionality(self):
        """Test basic ML prediction functionality."""
        predictor = MLPredictor()
        stock_data = self._create_sample_stock_data(50)
        
        result = predictor.predict_stock_price(stock_data)
        
        assert isinstance(result, MLAnalysisResult)
        assert isinstance(result.individual_predictions, list)
        assert isinstance(result.ensemble_prediction, ModelPrediction)
        assert isinstance(result.consensus_score, Decimal)
        assert isinstance(result.trend_direction, str)
        assert isinstance(result.price_target, Decimal)
        assert isinstance(result.risk_assessment, str)
        assert isinstance(result.model_performance, dict)
        
        # Check value ranges and types
        assert len(result.individual_predictions) > 0
        assert Decimal("0") <= result.consensus_score <= Decimal("1")
        assert result.trend_direction in ["up", "down", "sideways"]
        assert result.price_target > Decimal("0")
        assert result.risk_assessment in ["low", "moderate", "high"]
    
    def test_predict_with_specific_models(self):
        """Test prediction with specific model selection."""
        predictor = MLPredictor()
        stock_data = self._create_sample_stock_data(50)
        
        # Test with specific models
        models = [ModelType.RANDOM_FOREST, ModelType.ARIMA]
        result = predictor.predict_stock_price(stock_data, models=models)
        
        # Should have predictions from specified models
        model_types = [pred.model_type for pred in result.individual_predictions]
        assert ModelType.RANDOM_FOREST in model_types or ModelType.ARIMA in model_types
        assert len(result.individual_predictions) <= len(models)
    
    def test_random_forest_prediction(self):
        """Test Random Forest model prediction."""
        predictor = MLPredictor()
        stock_data = self._create_trending_stock_data(50)
        
        # Convert to DataFrame and prepare features
        df = predictor._convert_to_dataframe(stock_data)
        features_df = predictor._prepare_features(df)
        
        prediction = predictor._predict_random_forest(features_df)
        
        assert isinstance(prediction, ModelPrediction)
        assert prediction.model_type == ModelType.RANDOM_FOREST
        assert prediction.predicted_price > Decimal("0")
        assert Decimal("0") <= prediction.confidence <= Decimal("1")
        assert prediction.prediction_horizon == predictor.prediction_horizon
        assert isinstance(prediction.features_used, list)
        assert len(prediction.features_used) > 0
        assert prediction.model_accuracy >= Decimal("0")
    
    def test_svm_prediction(self):
        """Test SVM model prediction."""
        predictor = MLPredictor()
        stock_data = self._create_trending_stock_data(50)
        
        # Convert to DataFrame and prepare features
        df = predictor._convert_to_dataframe(stock_data)
        features_df = predictor._prepare_features(df)
        
        prediction = predictor._predict_svm(features_df)
        
        assert isinstance(prediction, ModelPrediction)
        assert prediction.model_type == ModelType.SVM
        assert prediction.predicted_price > Decimal("0")
        assert Decimal("0") <= prediction.confidence <= Decimal("1")
        assert isinstance(prediction.features_used, list)
        assert len(prediction.features_used) > 0
    
    def test_arima_prediction(self):
        """Test ARIMA model prediction."""
        predictor = MLPredictor()
        stock_data = self._create_trending_stock_data(50)
        
        # Convert to DataFrame and prepare features
        df = predictor._convert_to_dataframe(stock_data)
        features_df = predictor._prepare_features(df)
        
        prediction = predictor._predict_arima(features_df)
        
        assert isinstance(prediction, ModelPrediction)
        assert prediction.model_type == ModelType.ARIMA
        assert prediction.predicted_price > Decimal("0")
        assert Decimal("0") <= prediction.confidence <= Decimal("1")
        assert "close_prices" in prediction.features_used
    
    def test_linear_trend_fallback(self):
        """Test linear trend fallback prediction."""
        predictor = MLPredictor()
        stock_data = self._create_trending_stock_data(50)
        
        # Convert to DataFrame and prepare features
        df = predictor._convert_to_dataframe(stock_data)
        features_df = predictor._prepare_features(df)
        
        prediction = predictor._predict_linear_trend(features_df, ModelType.RANDOM_FOREST)
        
        assert isinstance(prediction, ModelPrediction)
        assert prediction.model_type == ModelType.RANDOM_FOREST
        assert prediction.predicted_price > Decimal("0")
        assert Decimal("0") <= prediction.confidence <= Decimal("1")
        assert "close_prices" in prediction.features_used
    
    def test_ensemble_prediction_creation(self):
        """Test ensemble prediction creation from individual predictions."""
        predictor = MLPredictor()
        
        # Create mock individual predictions
        individual_predictions = [
            ModelPrediction(
                model_type=ModelType.RANDOM_FOREST,
                predicted_price=Decimal("152.00"),
                confidence=Decimal("0.8"),
                prediction_horizon=PredictionHorizon.SHORT_TERM,
                features_used=["feature1", "feature2"],
                model_accuracy=Decimal("0.75")
            ),
            ModelPrediction(
                model_type=ModelType.SVM,
                predicted_price=Decimal("148.00"),
                confidence=Decimal("0.7"),
                prediction_horizon=PredictionHorizon.SHORT_TERM,
                features_used=["feature2", "feature3"],
                model_accuracy=Decimal("0.68")
            )
        ]
        
        ensemble = predictor._create_ensemble_prediction(individual_predictions)
        
        assert isinstance(ensemble, ModelPrediction)
        assert ensemble.model_type == ModelType.ENSEMBLE
        assert ensemble.predicted_price > Decimal("0")
        assert Decimal("0") <= ensemble.confidence <= Decimal("1")
        assert len(ensemble.features_used) >= 1  # Should combine unique features
    
    def test_consensus_score_calculation(self):
        """Test consensus score calculation."""
        predictor = MLPredictor()
        
        # Test with similar predictions (high consensus)
        similar_predictions = [
            ModelPrediction(
                model_type=ModelType.RANDOM_FOREST,
                predicted_price=Decimal("150.00"),
                confidence=Decimal("0.8"),
                prediction_horizon=PredictionHorizon.SHORT_TERM,
                features_used=["feature1"],
                model_accuracy=Decimal("0.75")
            ),
            ModelPrediction(
                model_type=ModelType.SVM,
                predicted_price=Decimal("151.00"),
                confidence=Decimal("0.7"),
                prediction_horizon=PredictionHorizon.SHORT_TERM,
                features_used=["feature2"],
                model_accuracy=Decimal("0.68")
            )
        ]
        
        consensus_high = predictor._calculate_consensus_score(similar_predictions)
        
        # Test with divergent predictions (low consensus)
        divergent_predictions = [
            ModelPrediction(
                model_type=ModelType.RANDOM_FOREST,
                predicted_price=Decimal("150.00"),
                confidence=Decimal("0.8"),
                prediction_horizon=PredictionHorizon.SHORT_TERM,
                features_used=["feature1"],
                model_accuracy=Decimal("0.75")
            ),
            ModelPrediction(
                model_type=ModelType.SVM,
                predicted_price=Decimal("130.00"),
                confidence=Decimal("0.7"),
                prediction_horizon=PredictionHorizon.SHORT_TERM,
                features_used=["feature2"],
                model_accuracy=Decimal("0.68")
            )
        ]
        
        consensus_low = predictor._calculate_consensus_score(divergent_predictions)
        
        assert Decimal("0") <= consensus_high <= Decimal("1")
        assert Decimal("0") <= consensus_low <= Decimal("1")
        assert consensus_high > consensus_low  # Similar predictions should have higher consensus
    
    def test_trend_direction_determination(self):
        """Test trend direction determination."""
        predictor = MLPredictor()
        
        current_price = Decimal("100.00")
        
        # Test upward trend
        up_price = Decimal("105.00")
        trend_up = predictor._determine_trend_direction(up_price, current_price)
        assert trend_up == "up"
        
        # Test downward trend
        down_price = Decimal("95.00")
        trend_down = predictor._determine_trend_direction(down_price, current_price)
        assert trend_down == "down"
        
        # Test sideways trend
        sideways_price = Decimal("101.00")
        trend_sideways = predictor._determine_trend_direction(sideways_price, current_price)
        assert trend_sideways == "sideways"
    
    def test_risk_assessment(self):
        """Test prediction risk assessment."""
        predictor = MLPredictor()
        
        # High confidence, high consensus = low risk
        high_conf_predictions = [
            ModelPrediction(
                model_type=ModelType.RANDOM_FOREST,
                predicted_price=Decimal("150.00"),
                confidence=Decimal("0.9"),
                prediction_horizon=PredictionHorizon.SHORT_TERM,
                features_used=["feature1"],
                model_accuracy=Decimal("0.85")
            )
        ]
        
        risk_low = predictor._assess_prediction_risk(high_conf_predictions, Decimal("0.9"))
        assert risk_low == "low"
        
        # Low confidence, low consensus = high risk
        low_conf_predictions = [
            ModelPrediction(
                model_type=ModelType.RANDOM_FOREST,
                predicted_price=Decimal("150.00"),
                confidence=Decimal("0.3"),
                prediction_horizon=PredictionHorizon.SHORT_TERM,
                features_used=["feature1"],
                model_accuracy=Decimal("0.4")
            )
        ]
        
        risk_high = predictor._assess_prediction_risk(low_conf_predictions, Decimal("0.3"))
        assert risk_high == "high"
    
    def test_feature_preparation(self):
        """Test feature preparation from stock data."""
        predictor = MLPredictor()
        stock_data = self._create_sample_stock_data(50)
        
        df = predictor._convert_to_dataframe(stock_data)
        features_df = predictor._prepare_features(df)
        
        # Check that features are created
        expected_features = ['returns', 'sma_5', 'sma_10', 'ema_5', 'volatility', 'volume_ratio']
        for feature in expected_features:
            assert feature in features_df.columns
        
        # Check that NaN values are handled
        assert not features_df.isnull().any().any()
        
        # Check that we have data after feature engineering
        assert len(features_df) > 0
    
    def test_different_prediction_horizons(self):
        """Test predictions with different time horizons."""
        stock_data = self._create_sample_stock_data(50)
        
        for horizon in [PredictionHorizon.SHORT_TERM, PredictionHorizon.MEDIUM_TERM, PredictionHorizon.LONG_TERM]:
            predictor = MLPredictor(horizon)
            result = predictor.predict_stock_price(stock_data)
            
            assert isinstance(result, MLAnalysisResult)
            assert result.ensemble_prediction.prediction_horizon == horizon
    
    def _create_sample_stock_data(self, count: int) -> list[StockData]:
        """Create sample stock data for testing."""
        np.random.seed(42)  # For reproducible results
        
        data = []
        base_price = 100.0
        
        for i in range(count):
            # Add some random movement
            daily_return = np.random.normal(0, 0.02)
            base_price *= (1 + daily_return)
            
            open_price = base_price * (1 + np.random.normal(0, 0.005))
            # Ensure high >= max(open, close) and low <= min(open, close)
            high = max(base_price, open_price) * (1 + abs(np.random.normal(0, 0.01)))
            low = min(base_price, open_price) * (1 - abs(np.random.normal(0, 0.01)))
            
            data.append(StockData(
                symbol="TEST",
                date=datetime(2023, 1, 1, tzinfo=UTC) + timedelta(days=i),
                open=Decimal(str(round(open_price, 2))),
                high=Decimal(str(round(high, 2))),
                low=Decimal(str(round(low, 2))),
                close=Decimal(str(round(base_price, 2))),
                volume=1000 + i * 10
            ))
        
        return data
    
    def _create_trending_stock_data(self, count: int) -> list[StockData]:
        """Create trending stock data for testing."""
        data = []
        base_price = 100.0
        
        for i in range(count):
            # Add upward trend
            trend = i * 0.5  # Linear upward trend
            noise = np.random.normal(0, 1.0)
            base_price = 100.0 + trend + noise
            
            open_price = base_price * (1 + np.random.normal(0, 0.005))
            # Ensure high >= max(open, close) and low <= min(open, close)
            high = max(base_price, open_price) * 1.02
            low = min(base_price, open_price) * 0.98
            
            data.append(StockData(
                symbol="TEST",
                date=datetime(2023, 1, 1, tzinfo=UTC) + timedelta(days=i),
                open=Decimal(str(round(open_price, 2))),
                high=Decimal(str(round(high, 2))),
                low=Decimal(str(round(low, 2))),
                close=Decimal(str(round(base_price, 2))),
                volume=1000 + i * 10
            ))
        
        return data


class TestModelPrediction:
    """Test class for ModelPrediction dataclass."""
    
    def test_model_prediction_creation(self):
        """Test ModelPrediction creation."""
        prediction = ModelPrediction(
            model_type=ModelType.RANDOM_FOREST,
            predicted_price=Decimal("152.75"),
            confidence=Decimal("0.82"),
            prediction_horizon=PredictionHorizon.SHORT_TERM,
            features_used=["price", "volume", "technical_indicators"],
            model_accuracy=Decimal("0.78")
        )
        
        assert prediction.model_type == ModelType.RANDOM_FOREST
        assert prediction.predicted_price == Decimal("152.75")
        assert prediction.confidence == Decimal("0.82")
        assert prediction.prediction_horizon == PredictionHorizon.SHORT_TERM
        assert prediction.features_used == ["price", "volume", "technical_indicators"]
        assert prediction.model_accuracy == Decimal("0.78")
        assert prediction.prediction_interval is None
    
    def test_model_prediction_with_interval(self):
        """Test ModelPrediction with prediction interval."""
        interval = (Decimal("148.50"), Decimal("157.00"))
        prediction = ModelPrediction(
            model_type=ModelType.SVM,
            predicted_price=Decimal("152.75"),
            confidence=Decimal("0.75"),
            prediction_horizon=PredictionHorizon.MEDIUM_TERM,
            features_used=["returns", "volatility"],
            model_accuracy=Decimal("0.70"),
            prediction_interval=interval
        )
        
        assert prediction.prediction_interval == interval
        assert prediction.prediction_interval[0] == Decimal("148.50")
        assert prediction.prediction_interval[1] == Decimal("157.00")


class TestMLAnalysisResult:
    """Test class for MLAnalysisResult dataclass."""
    
    def test_ml_analysis_result_creation(self):
        """Test MLAnalysisResult creation."""
        individual_predictions = [
            ModelPrediction(
                model_type=ModelType.RANDOM_FOREST,
                predicted_price=Decimal("152.00"),
                confidence=Decimal("0.8"),
                prediction_horizon=PredictionHorizon.SHORT_TERM,
                features_used=["feature1"],
                model_accuracy=Decimal("0.75")
            )
        ]
        
        ensemble_prediction = ModelPrediction(
            model_type=ModelType.ENSEMBLE,
            predicted_price=Decimal("151.50"),
            confidence=Decimal("0.85"),
            prediction_horizon=PredictionHorizon.SHORT_TERM,
            features_used=["feature1", "feature2"],
            model_accuracy=Decimal("0.80")
        )
        
        result = MLAnalysisResult(
            individual_predictions=individual_predictions,
            ensemble_prediction=ensemble_prediction,
            consensus_score=Decimal("0.85"),
            trend_direction="up",
            price_target=Decimal("155.20"),
            risk_assessment="moderate",
            model_performance={"rf": 0.78, "svm": 0.72}
        )
        
        assert result.individual_predictions == individual_predictions
        assert result.ensemble_prediction == ensemble_prediction
        assert result.consensus_score == Decimal("0.85")
        assert result.trend_direction == "up"
        assert result.price_target == Decimal("155.20")
        assert result.risk_assessment == "moderate"
        assert result.model_performance == {"rf": 0.78, "svm": 0.72}