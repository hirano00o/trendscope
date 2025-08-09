/**
 * Type definitions for stock analysis data structures
 *
 * @description Comprehensive type definitions matching the backend API
 * response format for 6-category stock analysis including technical
 * indicators, patterns, volatility, ML predictions, and integrated scoring.
 */

// Base types for analysis results
export interface CategoryScore {
    category: string
    score: number
    confidence: number
    weight: number
    details?: Record<string, any>
}

export interface IntegratedScore {
    overall_score: number
    confidence_level: number
    recommendation: "BUY" | "HOLD" | "SELL"
    category_scores: CategoryScore[]
    risk_assessment: "LOW" | "MODERATE" | "HIGH"
}

// Technical Analysis Types
export interface TechnicalIndicators {
    sma_20?: number
    sma_50?: number
    ema_12?: number
    ema_26?: number
    rsi?: number
    macd?: number
    macd_signal?: number
    bollinger_upper?: number
    bollinger_lower?: number
}

export interface TechnicalAnalysisResult {
    indicators: TechnicalIndicators
    trend_signals: {
        sma_signal: "bullish" | "bearish" | "neutral"
        ema_signal: "bullish" | "bearish" | "neutral"
        macd_signal: "bullish" | "bearish" | "neutral"
        rsi_signal: "overbought" | "oversold" | "neutral"
        bollinger_signal: "above_upper" | "below_lower" | "within_bands"
    }
    overall_signal: "bullish" | "bearish" | "neutral"
    signal_strength: number
}

// Pattern Analysis Types
export type PatternType =
    | "BULLISH_ENGULFING"
    | "BEARISH_ENGULFING"
    | "DOJI"
    | "HAMMER"
    | "SHOOTING_STAR"
    | "SUPPORT_LEVEL"
    | "RESISTANCE_LEVEL"
    | "TREND_LINE"

export type PatternSignal = "STRONG_BULLISH" | "BULLISH" | "NEUTRAL" | "BEARISH" | "STRONG_BEARISH"

export interface PatternDetection {
    pattern_type: PatternType
    signal: PatternSignal
    confidence: number
    start_index: number
    end_index: number
    description: string
    key_levels?: Record<string, number>
}

export interface PatternAnalysisResult {
    patterns: PatternDetection[]
    overall_signal: PatternSignal
    signal_strength: number
    pattern_score: number
}

// Volatility Analysis Types
export interface VolatilityMetrics {
    atr: number
    atr_percentage: number
    std_dev: number
    std_dev_annualized: number
    parkinson_volatility: number
    garman_klass_volatility: number
    volatility_ratio: number
    volatility_percentile: number
}

export interface VolatilityAnalysisResult {
    metrics: VolatilityMetrics
    regime: "LOW" | "MODERATE" | "HIGH" | "EXTREME"
    risk_level: "LOW" | "MODERATE" | "HIGH"
    volatility_score: number
    trend_volatility: "increasing" | "decreasing" | "stable"
    breakout_probability: number
    analysis_summary: string
}

// Machine Learning Types
export type ModelType = "RANDOM_FOREST" | "SVM" | "ARIMA" | "ENSEMBLE"

export type PredictionHorizon = "SHORT_TERM" | "MEDIUM_TERM" | "LONG_TERM"

export interface ModelPrediction {
    model_type: ModelType
    predicted_price: number
    confidence: number
    prediction_horizon: PredictionHorizon
    features_used: string[]
    model_accuracy: number
}

export interface MLAnalysisResult {
    individual_predictions: ModelPrediction[]
    ensemble_prediction: ModelPrediction
    consensus_score: number
    trend_direction: "up" | "down" | "sideways"
    price_target: number
    risk_assessment: "low" | "moderate" | "high"
    model_performance: Record<string, number>
}

// Main Analysis Data Structure
export interface AnalysisData {
    symbol: string
    timestamp: string
    current_price: number

    // 6 Category Analysis Results
    technical_analysis: TechnicalAnalysisResult
    pattern_analysis: PatternAnalysisResult
    volatility_analysis: VolatilityAnalysisResult
    ml_analysis: MLAnalysisResult

    // Fundamental analysis (volume-based for now)
    fundamental_analysis: {
        volume_analysis: {
            current_volume: number
            average_volume: number
            volume_ratio: number
            volume_trend: "increasing" | "decreasing" | "stable"
        }
        score: number
        confidence: number
    }

    // Integrated scoring results
    integrated_score: IntegratedScore

    // Additional metadata
    analysis_metadata: {
        data_points_used: number
        analysis_timestamp: string
        data_quality_score: number
        confidence_factors: string[]
    }
}

// API Response wrapper
export interface AnalysisResponse {
    success: boolean
    data?: AnalysisData
    error?: {
        code: string
        message: string
        details?: any
    }
}

// Historical Data Types
export interface HistoricalDataPoint {
    date: string
    open: number
    high: number
    low: number
    close: number
    volume: number
}

export interface HistoricalDataMetadata {
    current_price: number
    price_change: number
    price_change_percent: number
    average_volume: number
    data_quality: "high" | "medium" | "low"
    retrieved_at: string
}

export interface HistoricalDataResponse {
    symbol: string
    period: string
    data_points: number
    start_date: string
    end_date: string
    historical_data: HistoricalDataPoint[]
    metadata: HistoricalDataMetadata
}

export interface HistoricalApiResponse {
    success: boolean
    data?: HistoricalDataResponse
    error?: {
        code: string
        message: string
        details?: any
    }
}

// Component prop types
export interface AnalysisResultsProps {
    data: AnalysisData
}

export interface StockAnalysisFormProps {
    onAnalyze?: (symbol: string) => Promise<void>
}

// Chart data types for visualizations
export interface ChartDataPoint {
    date: string
    value: number
    label?: string
}

export interface ChartSeries {
    name: string
    data: ChartDataPoint[]
    color: string
    type?: "line" | "area" | "bar"
}

// Signal strength display types
export interface SignalStrengthProps {
    strength: number
    signal: "bullish" | "bearish" | "neutral"
    confidence: number
    label: string
}

// Metric card types for dashboard
export interface MetricCardProps {
    title: string
    value: string | number
    change?: {
        value: number
        type: "increase" | "decrease"
        timeframe: string
    }
    trend?: ChartDataPoint[]
    status?: "positive" | "negative" | "neutral"
    description?: string
}
