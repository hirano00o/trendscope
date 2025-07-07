/**
 * Chart components export module
 * 
 * @description Centralized exports for all chart components used throughout
 * the application for displaying technical analysis and stock data visualizations.
 */

export { PriceChart } from "./price-chart"
export { TechnicalIndicatorChart } from "./technical-indicator-chart"
export { VolatilityChart } from "./volatility-chart"
export { PatternChart } from "./pattern-chart"
export { ChartContainer, ChartLoading, ChartError } from "./chart-container"

// Data adapters and utilities
export {
    adaptTechnicalIndicators,
    adaptVolatilityMetrics,
    adaptPatternDetections,
    adaptPriceDataToLine,
    createMockHistoricalData,
    normalizeDataSeries,
    validateChartData,
    formatNumberForChart,
} from "./data-adapters"

// Type exports
export type {
    PriceChartProps,
    TechnicalIndicatorChartProps,
    VolatilityChartProps,
    PatternChartProps,
    ChartTheme,
    ChartDataPoint,
    CandlestickDataPoint,
    LineChartData,
    ChartConfig,
    ChartTimeframe,
    ChartType,
    IndicatorType,
} from "./types"