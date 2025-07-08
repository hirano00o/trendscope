"""Comprehensive analysis API endpoints combining all analysis categories.

This module provides REST API endpoints that integrate all 6 analysis categories:
technical analysis, pattern recognition, volatility analysis, machine learning
predictions, fundamental analysis, and integrated scoring.
"""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import HTTPException

from trendscope_backend.analysis.technical.indicators import TechnicalIndicatorCalculator
from trendscope_backend.analysis.patterns.pattern_recognition import PatternRecognizer
from trendscope_backend.analysis.volatility.volatility_analysis import VolatilityAnalyzer
from trendscope_backend.analysis.ml.ml_predictions import MLPredictor, ModelType
from trendscope_backend.analysis.scoring.integrated_scoring import IntegratedScoringEngine, CategoryScore
from trendscope_backend.data.models import AnalysisRequest, StockData
from trendscope_backend.data.stock_data import StockDataFetcher
from trendscope_backend.utils.logging import get_logger
from trendscope_backend.api.analysis import validate_symbol, validate_period, validate_indicators

logger = get_logger(__name__)


def _convert_dataframe_to_stock_data(df: pd.DataFrame, symbol: str) -> List[StockData]:
    """Convert pandas DataFrame to list of StockData objects.
    
    Args:
        df: DataFrame with OHLCV data (from yfinance)
        symbol: Stock symbol
        
    Returns:
        List of StockData objects
        
    Raises:
        ValueError: If DataFrame structure is invalid
    """
    if df.empty:
        raise ValueError("DataFrame is empty")
    
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    stock_data_list = []
    
    for date_index, row in df.iterrows():
        try:
            # Convert pandas timestamp to datetime
            if hasattr(date_index, 'to_pydatetime'):
                date = date_index.to_pydatetime()
            else:
                date = pd.to_datetime(date_index).to_pydatetime()
            
            stock_data = StockData(
                symbol=symbol,
                date=date,
                open=Decimal(str(row['Open'])),
                high=Decimal(str(row['High'])),
                low=Decimal(str(row['Low'])),
                close=Decimal(str(row['Close'])),
                volume=int(row['Volume'])
            )
            stock_data_list.append(stock_data)
        except Exception as e:
            logger.warning(f"Failed to convert row for {symbol} at {date_index}: {e}")
            continue
    
    if not stock_data_list:
        raise ValueError("No valid stock data could be converted")
    
    logger.info(f"Converted {len(stock_data_list)} data points from DataFrame to StockData objects")
    return stock_data_list


async def get_comprehensive_analysis(
    symbol: str,
    period: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    include_ml: bool = True,
    ml_models: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Perform comprehensive 6-category stock analysis.
    
    Combines technical analysis, pattern recognition, volatility analysis,
    machine learning predictions, fundamental analysis, and integrated scoring
    into a unified analysis report.
    
    Args:
        symbol: Stock symbol to analyze
        period: Time period for analysis (e.g., '1mo', '3mo')
        start_date: Custom start date for analysis
        end_date: Custom end date for analysis
        include_ml: Whether to include ML predictions (can be slow)
        ml_models: List of ML models to use ['random_forest', 'svm', 'arima']
        
    Returns:
        Comprehensive analysis results dictionary
        
    Raises:
        HTTPException: If analysis fails or data unavailable
        
    Example:
        >>> analysis = await get_comprehensive_analysis("AAPL", period="1mo")
        >>> print(analysis["integrated_score"]["overall_score"])
        0.72
    """
    try:
        # Validate symbol
        symbol = validate_symbol(symbol)
        logger.info(f"Starting comprehensive analysis for symbol: {symbol}")
        
        # Create analysis request
        if period:
            period = validate_period(period)
            request = AnalysisRequest(
                symbol=symbol, 
                period=period, 
                indicators=["sma", "ema", "rsi", "macd", "bollinger"]
            )
        elif start_date and end_date:
            request = AnalysisRequest(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                indicators=["sma", "ema", "rsi", "macd", "bollinger"]
            )
        else:
            # Default to 3 months for comprehensive analysis
            request = AnalysisRequest(
                symbol=symbol, 
                period="3mo", 
                indicators=["sma", "ema", "rsi", "macd", "bollinger"]
            )
        
        # Fetch stock data
        data_fetcher = StockDataFetcher()
        
        if request.period:
            stock_data_df = data_fetcher.fetch_stock_data(symbol, period=request.period)
        else:
            stock_data_df = data_fetcher.fetch_stock_data(
                symbol, start_date=request.start_date, end_date=request.end_date
            )
        
        if stock_data_df is None or (hasattr(stock_data_df, 'empty') and stock_data_df.empty):
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Data Not Available",
                    "message": f"No stock data available for symbol {symbol}",
                    "symbol": symbol,
                },
            )
        
        logger.info(f"Retrieved {len(stock_data_df)} data points for analysis")
        
        # Convert DataFrame to list of StockData objects
        stock_data = _convert_dataframe_to_stock_data(stock_data_df, symbol)
        
        # Perform all analysis categories in parallel where possible
        results = await _perform_comprehensive_analysis(
            stock_data, include_ml, ml_models
        )
        
        # Generate integrated score
        integrated_result = _generate_integrated_analysis(
            results, symbol, stock_data
        )
        
        logger.info(f"Comprehensive analysis completed for {symbol}")
        
        return integrated_result
        
    except HTTPException:
        raise
    except ValueError as e:
        error_msg = str(e)
        logger.warning(f"Validation error for {symbol}: {e}")
        
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid Parameter",
                "message": error_msg,
                "symbol": symbol,
            },
        ) from e
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Comprehensive analysis error for {symbol}: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Analysis Error",
                "message": "An error occurred during comprehensive analysis",
                "symbol": symbol,
            },
        ) from e


async def _perform_comprehensive_analysis(
    stock_data: List[StockData],
    include_ml: bool = True,
    ml_models: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Perform all analysis categories.
    
    Args:
        stock_data: Historical stock data
        include_ml: Whether to include ML analysis
        ml_models: List of ML models to use
        
    Returns:
        Dictionary containing results from all analysis categories
    """
    results = {}
    
    # 1. Technical Analysis
    logger.info("Performing technical analysis...")
    technical_calculator = TechnicalIndicatorCalculator()
    technical_indicators = technical_calculator.calculate_all_indicators(stock_data)
    results["technical"] = {
        "indicators": technical_indicators,
        "data_points": len(stock_data)
    }
    
    # 2. Pattern Analysis
    logger.info("Performing pattern analysis...")
    try:
        pattern_recognizer = PatternRecognizer()
        pattern_result = pattern_recognizer.analyze_patterns(stock_data)
        results["patterns"] = {
            "result": pattern_result,
            "success": True
        }
    except Exception as e:
        logger.warning(f"Pattern analysis failed: {e}")
        results["patterns"] = {
            "error": str(e),
            "success": False
        }
    
    # 3. Volatility Analysis
    logger.info("Performing volatility analysis...")
    try:
        volatility_analyzer = VolatilityAnalyzer()
        volatility_result = volatility_analyzer.analyze_volatility(stock_data)
        results["volatility"] = {
            "result": volatility_result,
            "success": True
        }
    except Exception as e:
        logger.warning(f"Volatility analysis failed: {e}")
        results["volatility"] = {
            "error": str(e),
            "success": False
        }
    
    # 4. Machine Learning Predictions (optional, can be slow)
    if include_ml:
        logger.info("Performing ML predictions...")
        try:
            # Convert string model names to ModelType enum
            model_types = []
            if ml_models:
                model_map = {
                    "random_forest": ModelType.RANDOM_FOREST,
                    "svm": ModelType.SVM,
                    "arima": ModelType.ARIMA,
                    "lstm": ModelType.LSTM
                }
                model_types = [model_map[model] for model in ml_models if model in model_map]
            
            ml_predictor = MLPredictor()
            ml_result = ml_predictor.predict_stock_price(
                stock_data, models=model_types if model_types else None
            )
            results["ml"] = {
                "result": ml_result,
                "success": True
            }
        except Exception as e:
            logger.warning(f"ML prediction failed: {e}")
            results["ml"] = {
                "error": str(e),
                "success": False
            }
    else:
        results["ml"] = {
            "skipped": "ML analysis disabled",
            "success": False
        }
    
    # 5. Fundamental Analysis (volume-based)
    logger.info("Performing fundamental analysis...")
    try:
        volume_data = [int(data.volume) for data in stock_data]
        results["fundamental"] = {
            "volume_data": volume_data,
            "success": True
        }
    except Exception as e:
        logger.warning(f"Fundamental analysis failed: {e}")
        results["fundamental"] = {
            "error": str(e),
            "success": False
        }
    
    return results


def _generate_integrated_analysis(
    results: Dict[str, Any],
    symbol: str,
    stock_data: List[StockData]
) -> Dict[str, Any]:
    """Generate integrated analysis combining all categories.
    
    Args:
        results: Results from all analysis categories
        symbol: Stock symbol
        stock_data: Historical stock data
        
    Returns:
        Integrated analysis results
    """
    logger.info("Generating integrated analysis...")
    
    # Initialize scoring engine
    scoring_engine = IntegratedScoringEngine()
    category_scores = []
    
    current_price = stock_data[-1].close
    
    # 1. Technical Analysis Score
    if results["technical"]:
        technical_score = scoring_engine.calculate_technical_category_score(
            results["technical"]["indicators"],
            results["technical"]["data_points"]
        )
        category_scores.append(technical_score)
    
    # 2. Pattern Analysis Score
    if results["patterns"]["success"]:
        pattern_score = scoring_engine.calculate_pattern_category_score(
            results["patterns"]["result"]
        )
        category_scores.append(pattern_score)
    
    # 3. Volatility Analysis Score
    if results["volatility"]["success"]:
        volatility_score = scoring_engine.calculate_volatility_category_score(
            results["volatility"]["result"]
        )
        category_scores.append(volatility_score)
    
    # 4. ML Prediction Score
    if results["ml"]["success"]:
        # Update ML score calculation with current price
        ml_score = scoring_engine.calculate_ml_category_score(
            results["ml"]["result"]
        )
        # Fix the current price issue
        ml_score.details["current_price"] = float(current_price)
        category_scores.append(ml_score)
    
    # 5. Fundamental Analysis Score
    if results["fundamental"]["success"]:
        fundamental_score = scoring_engine.calculate_fundamental_category_score(
            results["fundamental"]["volume_data"]
        )
        category_scores.append(fundamental_score)
    
    # Generate integrated score
    integrated_score = scoring_engine.calculate_integrated_score(category_scores)
    
    # Generate confidence factors for metadata
    confidence_factors = []
    for score in category_scores:
        if score.confidence > 0.7:
            confidence_factors.append(f"High {score.category} confidence")
        elif score.confidence < 0.3:
            confidence_factors.append(f"Low {score.category} confidence")
    
    # Calculate data quality score based on various factors
    data_quality_score = min(1.0, len(stock_data) / 100.0)  # Simple calculation
    
    # Format the comprehensive response
    response = {
        "symbol": symbol,
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "current_price": float(current_price),
        
        # Individual analysis results
        "technical_analysis": _format_technical_analysis(results.get("technical")),
        "pattern_analysis": _format_pattern_analysis(results.get("patterns")),
        "volatility_analysis": _format_volatility_analysis(results.get("volatility")),
        "ml_analysis": _format_ml_analysis(results.get("ml")),
        "fundamental_analysis": _format_fundamental_analysis(results.get("fundamental")),
        
        # Integrated scoring
        "integrated_score": {
            "overall_score": float(integrated_score.overall_score),
            "confidence_level": float(integrated_score.confidence_level),
            "recommendation": integrated_score.recommendation,
            "risk_assessment": integrated_score.risk_assessment,
            "category_scores": [
                {
                    "category": score.category,
                    "score": float(score.score),
                    "confidence": float(score.confidence),
                    "weight": float(score.weight),
                    "details": score.details or {}
                }
                for score in category_scores
            ]
        },
        
        # Analysis metadata
        "analysis_metadata": {
            "data_points_used": len(stock_data),
            "analysis_timestamp": datetime.now(UTC).isoformat() + "Z",
            "data_quality_score": data_quality_score,
            "confidence_factors": confidence_factors or ["Standard analysis"]
        }
    }
    
    # Return wrapped response for frontend API client compatibility
    return {
        "success": True,
        "data": response
    }


def _format_technical_analysis(technical_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Format technical analysis results for API response."""
    if not technical_data:
        return {"error": "Technical analysis not available"}
    
    indicators = technical_data["indicators"]
    
    # Generate trend signals based on indicators
    trend_signals = {
        "sma_signal": "neutral",
        "ema_signal": "neutral", 
        "macd_signal": "neutral",
        "rsi_signal": "neutral",
        "bollinger_signal": "within_bands"
    }
    
    # SMA signal
    if indicators.sma_20 is not None and indicators.sma_50 is not None:
        if indicators.sma_20 > indicators.sma_50:
            trend_signals["sma_signal"] = "bullish"
        elif indicators.sma_20 < indicators.sma_50:
            trend_signals["sma_signal"] = "bearish"
    
    # EMA signal  
    if indicators.ema_12 is not None and indicators.ema_26 is not None:
        if indicators.ema_12 > indicators.ema_26:
            trend_signals["ema_signal"] = "bullish"
        elif indicators.ema_12 < indicators.ema_26:
            trend_signals["ema_signal"] = "bearish"
    
    # MACD signal
    if indicators.macd is not None and indicators.macd_signal is not None:
        if indicators.macd > indicators.macd_signal:
            trend_signals["macd_signal"] = "bullish"
        elif indicators.macd < indicators.macd_signal:
            trend_signals["macd_signal"] = "bearish"
    
    # RSI signal
    if indicators.rsi is not None:
        if indicators.rsi > 70:
            trend_signals["rsi_signal"] = "overbought"
        elif indicators.rsi < 30:
            trend_signals["rsi_signal"] = "oversold"
    
    # Calculate overall signal
    bullish_count = sum(1 for signal in trend_signals.values() if signal == "bullish")
    bearish_count = sum(1 for signal in trend_signals.values() if signal == "bearish")
    
    if bullish_count > bearish_count:
        overall_signal = "bullish"
        signal_strength = bullish_count / len(trend_signals)
    elif bearish_count > bullish_count:
        overall_signal = "bearish"
        signal_strength = bearish_count / len(trend_signals)
    else:
        overall_signal = "neutral"
        signal_strength = 0.5
    
    return {
        "indicators": {
            "sma_20": float(indicators.sma_20) if indicators.sma_20 is not None else None,
            "sma_50": float(indicators.sma_50) if indicators.sma_50 is not None else None,
            "ema_12": float(indicators.ema_12) if indicators.ema_12 is not None else None,
            "ema_26": float(indicators.ema_26) if indicators.ema_26 is not None else None,
            "rsi": float(indicators.rsi) if indicators.rsi is not None else None,
            "macd": float(indicators.macd) if indicators.macd is not None else None,
            "macd_signal": float(indicators.macd_signal) if indicators.macd_signal is not None else None,
            "bollinger_upper": float(indicators.bollinger_upper) if indicators.bollinger_upper is not None else None,
            "bollinger_lower": float(indicators.bollinger_lower) if indicators.bollinger_lower is not None else None,
        },
        "trend_signals": trend_signals,
        "overall_signal": overall_signal,
        "signal_strength": signal_strength
    }


def _format_pattern_analysis(pattern_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Format pattern analysis results for API response."""
    if not pattern_data or not pattern_data.get("success"):
        return {"error": pattern_data.get("error", "Pattern analysis not available")}
    
    result = pattern_data["result"]
    return {
        "patterns": [
            {
                "pattern_type": pattern.pattern_type.value,
                "signal": pattern.signal.value,
                "confidence": float(pattern.confidence),
                "start_index": int(pattern.start_index) if hasattr(pattern, 'start_index') else 0,
                "end_index": int(pattern.end_index) if hasattr(pattern, 'end_index') else 0,
                "description": pattern.description,
                "key_levels": {k: float(v) for k, v in pattern.key_levels.items()} if pattern.key_levels else {}
            }
            for pattern in result.patterns
        ],
        "overall_signal": result.overall_signal.value,
        "signal_strength": float(result.signal_strength),
        "pattern_score": float(result.pattern_score)
    }


def _format_volatility_analysis(volatility_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Format volatility analysis results for API response."""
    if not volatility_data or not volatility_data.get("success"):
        return {"error": volatility_data.get("error", "Volatility analysis not available")}
    
    result = volatility_data["result"]
    return {
        "metrics": {
            "atr": float(result.metrics.atr),
            "atr_percentage": float(result.metrics.atr_percentage),
            "std_dev": float(result.metrics.atr),  # Use ATR as std_dev for now
            "std_dev_annualized": float(result.metrics.std_dev_annualized),
            "parkinson_volatility": float(result.metrics.atr),  # Placeholder
            "garman_klass_volatility": float(result.metrics.atr),  # Placeholder
            "volatility_ratio": float(result.metrics.volatility_ratio),
            "volatility_percentile": float(result.metrics.volatility_percentile)
        },
        "regime": result.regime.value,
        "risk_level": result.risk_level.value,
        "volatility_score": float(result.volatility_score),
        "trend_volatility": result.trend_volatility,
        "breakout_probability": float(result.breakout_probability),
        "analysis_summary": result.analysis_summary
    }


def _format_ml_analysis(ml_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Format ML analysis results for API response."""
    if not ml_data or not ml_data.get("success"):
        return {"error": ml_data.get("error", "ML analysis not available")}
    
    result = ml_data["result"]
    return {
        "individual_predictions": [
            {
                "model_type": pred.model_type.value,
                "predicted_price": float(pred.predicted_price),
                "confidence": float(pred.confidence),
                "prediction_horizon": "SHORT_TERM",  # Default for now
                "features_used": ["price", "volume", "technical_indicators"],  # Default features
                "model_accuracy": float(pred.model_accuracy)
            }
            for pred in result.individual_predictions
        ],
        "ensemble_prediction": {
            "model_type": "ENSEMBLE",
            "predicted_price": float(result.ensemble_prediction.predicted_price),
            "confidence": float(result.ensemble_prediction.confidence),
            "prediction_horizon": "SHORT_TERM",
            "features_used": ["price", "volume", "technical_indicators"],
            "model_accuracy": float(result.ensemble_prediction.model_accuracy)
        },
        "consensus_score": float(result.consensus_score),
        "trend_direction": result.trend_direction,
        "price_target": float(result.price_target),
        "risk_assessment": result.risk_assessment,
        "model_performance": {k: float(v) for k, v in result.model_performance.items()}
    }


def _format_fundamental_analysis(fundamental_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Format fundamental analysis results for API response."""
    if not fundamental_data or not fundamental_data.get("success"):
        return {"error": fundamental_data.get("error", "Fundamental analysis not available")}
    
    volume_data = fundamental_data["volume_data"]
    current_volume = volume_data[-1] if volume_data else 0
    recent_avg = sum(volume_data[-5:]) / 5 if len(volume_data) >= 5 else current_volume
    overall_avg = sum(volume_data) / len(volume_data)
    volume_ratio = recent_avg / overall_avg if overall_avg > 0 else 1.0
    
    # Determine volume trend
    if recent_avg > overall_avg * 1.1:
        volume_trend = "increasing"
    elif recent_avg < overall_avg * 0.9:
        volume_trend = "decreasing"
    else:
        volume_trend = "stable"
    
    # Calculate a simple score and confidence based on volume patterns
    score = min(1.0, volume_ratio) if volume_trend == "increasing" else max(0.0, 1.0 - volume_ratio)
    confidence = min(1.0, len(volume_data) / 30.0)  # More data = higher confidence
    
    return {
        "volume_analysis": {
            "current_volume": int(current_volume),
            "average_volume": int(overall_avg),
            "volume_ratio": round(volume_ratio, 2),
            "volume_trend": volume_trend
        },
        "score": score,
        "confidence": confidence
    }


def _generate_analysis_summary(
    integrated_score,
    category_scores: List[CategoryScore],
    symbol: str
) -> str:
    """Generate human-readable analysis summary."""
    
    score_value = float(integrated_score.overall_score)
    confidence_value = float(integrated_score.confidence_level)
    
    # Determine overall sentiment
    if score_value >= 0.7:
        sentiment = "bullish"
    elif score_value >= 0.6:
        sentiment = "moderately bullish"
    elif score_value >= 0.4:
        sentiment = "neutral"
    elif score_value >= 0.3:
        sentiment = "moderately bearish"
    else:
        sentiment = "bearish"
    
    # Determine confidence level
    if confidence_value >= 0.8:
        conf_level = "high"
    elif confidence_value >= 0.6:
        conf_level = "moderate"
    else:
        conf_level = "low"
    
    # Get strongest category
    strongest_category = max(category_scores, key=lambda x: x.score * x.confidence)
    
    summary = (
        f"Comprehensive analysis of {symbol} shows a {sentiment} outlook "
        f"with {conf_level} confidence (score: {score_value:.2f}, confidence: {confidence_value:.2f}). "
        f"Recommendation: {integrated_score.recommendation}. "
        f"Risk assessment: {integrated_score.risk_assessment}. "
        f"Strongest signal comes from {strongest_category.category} analysis."
    )
    
    return summary