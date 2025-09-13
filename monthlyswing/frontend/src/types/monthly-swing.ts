/**
 * TypeScript type definitions for Monthly Swing Trading API
 *
 * @description Type definitions that correspond to the monthly swing backend API
 * responses and ensure type safety throughout the frontend application.
 */

/**
 * Trend direction enumeration
 */
export type TrendDirection = '上昇' | '下降' | '横這い' | '不明';

/**
 * Signal type enumeration for swing trading
 */
export type SignalType = '買い' | '売り' | '保持' | '様子見';

/**
 * Support/Resistance level type
 */
export type SupportResistanceLevelType = 'サポート' | 'レジスタンス';

/**
 * Monthly return data for a specific period
 */
export interface MonthlyReturn {
  /** Period start date */
  start_date: string;
  /** Period end date */
  end_date: string;
  /** Return rate (decimal) */
  return_rate: number;
  /** Period start price */
  start_price: number;
  /** Period end price */
  end_price: number;
  /** Period volatility (optional) */
  volatility?: number;
}

/**
 * Support and resistance level information
 */
export interface SupportResistanceLevel {
  /** Price level */
  level: number;
  /** Confidence score (0-1) */
  confidence: number;
  /** Number of times price touched this level */
  touch_count: number;
  /** Date of last touch */
  last_touch_date: string;
  /** Level type (support or resistance) */
  level_type: SupportResistanceLevelType;
  /** Strength score (0-1) */
  strength_score: number;
}

/**
 * Trend strength metrics
 */
export interface TrendStrengthMetrics {
  /** Trend direction */
  direction: TrendDirection;
  /** Strength score (0-1) */
  strength: number;
  /** Analysis confidence (0-1) */
  confidence: number;
  /** Momentum indicator */
  momentum: number;
  /** Trend consistency score (0-1) */
  consistency: number;
  /** Trend duration in days */
  duration_days: number;
}

/**
 * Swing trading signal
 */
export interface SwingSignal {
  /** Signal type */
  signal_type: SignalType;
  /** Signal confidence (0-1) */
  confidence: number;
  /** Target price (optional) */
  target_price?: number;
  /** Stop loss price (optional) */
  stop_loss?: number;
  /** Expected holding period in days (optional) */
  expected_holding_days?: number;
  /** Risk reward ratio (optional) */
  risk_reward_ratio?: number;
  /** Supporting factors for the signal */
  supporting_factors: string[];
  /** Signal generation timestamp */
  generated_at: string;
}

/**
 * Risk metrics for analysis
 */
export interface RiskMetrics {
  /** Value at Risk */
  var?: number;
  /** Maximum drawdown */
  max_drawdown?: number;
  /** Sharpe ratio */
  sharpe_ratio?: number;
  /** Volatility */
  volatility?: number;
  /** Beta coefficient */
  beta?: number;
  /** Additional risk metrics */
  [key: string]: number | undefined;
}

/**
 * Analysis metadata
 */
export interface AnalysisMetadata {
  /** Data source information */
  data_source?: string;
  /** Number of data points used */
  data_points_count?: number;
  /** Analysis algorithm version */
  algorithm_version?: string;
  /** Processing time in milliseconds */
  processing_time_ms?: number;
  /** Data quality score */
  data_quality_score?: number;
  /** Additional metadata */
  [key: string]: any;
}

/**
 * Main monthly trend analysis result
 */
export interface MonthlyTrendResult {
  /** Stock symbol */
  symbol: string;
  /** Analysis execution timestamp */
  analysis_date: string;
  /** Analysis data period */
  data_period: {
    start_date: string;
    end_date: string;
  };
  /** Monthly returns list */
  monthly_returns: MonthlyReturn[];
  /** Trend strength indicators */
  trend_strength: TrendStrengthMetrics;
  /** Support and resistance levels */
  support_resistance: {
    support: SupportResistanceLevel[];
    resistance: SupportResistanceLevel[];
  };
  /** Swing trading signals */
  swing_signals: SwingSignal[];
  /** Trend continuation probability (0-1) */
  continuation_probability: number;
  /** Risk metrics (optional) */
  risk_metrics?: RiskMetrics;
  /** Analysis metadata */
  metadata: AnalysisMetadata;
}

/**
 * API response wrapper for monthly swing analysis
 */
export interface MonthlySwingApiResponse {
  /** Request success status */
  success: boolean;
  /** Analysis result data */
  data?: MonthlyTrendResult;
  /** Error information (if any) */
  error?: {
    message: string;
    code?: string;
    details?: any;
  };
  /** Response timestamp */
  timestamp: string;
}

/**
 * API error response
 */
export interface ApiError {
  /** Error message */
  message: string;
  /** Error code (optional) */
  code?: string;
  /** HTTP status code */
  status: number;
  /** Additional error details */
  details?: any;
}

/**
 * Request options for monthly swing analysis
 */
export interface MonthlySwingAnalysisRequest {
  /** Stock symbol to analyze */
  symbol: string;
  /** Optional start date for custom analysis period */
  start_date?: string;
  /** Optional end date for custom analysis period */
  end_date?: string;
  /** Additional analysis parameters */
  options?: {
    /** Include detailed risk metrics */
    include_risk_metrics?: boolean;
    /** Include additional metadata */
    include_metadata?: boolean;
    /** Analysis confidence threshold */
    confidence_threshold?: number;
  };
}

/**
 * Chart data point for visualization
 */
export interface ChartDataPoint {
  /** Date for the data point */
  date: string;
  /** Price value */
  price: number;
  /** Volume (optional) */
  volume?: number;
  /** Additional chart data */
  [key: string]: string | number | undefined;
}

/**
 * Chart configuration for monthly swing visualization
 */
export interface ChartConfig {
  /** Chart type */
  type: 'line' | 'bar' | 'candlestick' | 'area';
  /** X-axis data key */
  xDataKey: string;
  /** Y-axis data key */
  yDataKey: string;
  /** Chart color theme */
  color?: string;
  /** Show trend lines */
  showTrendLine?: boolean;
  /** Show support/resistance levels */
  showSupportResistance?: boolean;
}