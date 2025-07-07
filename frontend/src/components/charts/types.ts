/**
 * Chart component type definitions
 * 
 * @description Type definitions for chart components including data structures,
 * props interfaces, and configuration options for technical analysis visualizations.
 */

import { TechnicalIndicators, VolatilityMetrics, PatternDetection } from "@/types/analysis"

// Base chart data types
export interface ChartDataPoint {
    /** Date string in ISO format */
    date: string
    /** Numeric value for the data point */
    value: number
    /** Optional label for the data point */
    label?: string
    /** Optional color override for this data point */
    color?: string
}

export interface CandlestickDataPoint {
    date: string
    open: number
    high: number
    low: number
    close: number
    volume?: number
}

export interface LineChartData {
    name: string
    data: ChartDataPoint[]
    color: string
    strokeWidth?: number
    type?: "line" | "area"
}

// Chart theme configuration
export interface ChartTheme {
    primary: string
    success: string
    warning: string
    danger: string
    neutral: string
    background: string
    grid: string
    text: string
}

// Price Chart Props
export interface PriceChartProps {
    /** Historical price data */
    data: CandlestickDataPoint[]
    /** Chart height in pixels */
    height?: number
    /** Chart width, 'auto' for responsive */
    width?: number | "auto"
    /** Whether to show volume bars */
    showVolume?: boolean
    /** Chart theme colors */
    theme?: Partial<ChartTheme>
    /** Time range for display */
    timeRange?: "1D" | "1W" | "1M" | "3M" | "6M" | "1Y"
    /** Additional technical indicators to overlay */
    indicators?: {
        sma?: { period: number; color: string }[]
        ema?: { period: number; color: string }[]
        bollinger?: { show: boolean; color: string }
    }
}

// Technical Indicator Chart Props
export interface TechnicalIndicatorChartProps {
    /** Technical indicator data */
    indicators: TechnicalIndicators
    /** Historical data for context */
    historicalData?: ChartDataPoint[]
    /** Chart height in pixels */
    height?: number
    /** Chart width, 'auto' for responsive */
    width?: number | "auto"
    /** Which indicators to display */
    activeIndicators?: Array<"rsi" | "macd" | "sma" | "ema" | "bollinger" | "momentum">
    /** Chart theme colors */
    theme?: Partial<ChartTheme>
}

// Volatility Chart Props
export interface VolatilityChartProps {
    /** Volatility metrics */
    metrics: VolatilityMetrics
    /** Historical volatility data */
    historicalData?: ChartDataPoint[]
    /** Chart height in pixels */
    height?: number
    /** Chart width, 'auto' for responsive */
    width?: number | "auto"
    /** Chart theme colors */
    theme?: Partial<ChartTheme>
    /** Volatility display type */
    displayType?: "atr" | "std_dev" | "parkinson" | "garman_klass"
}

// Pattern Chart Props
export interface PatternChartProps {
    /** Detected patterns */
    patterns: PatternDetection[]
    /** Price data for pattern context */
    priceData: CandlestickDataPoint[]
    /** Chart height in pixels */
    height?: number
    /** Chart width, 'auto' for responsive */
    width?: number | "auto"
    /** Chart theme colors */
    theme?: Partial<ChartTheme>
    /** Whether to highlight pattern areas */
    highlightPatterns?: boolean
}

// Chart configuration types
export interface ChartConfig {
    responsive: boolean
    maintainAspectRatio: boolean
    animationDuration: number
    gridLines: boolean
    tooltips: boolean
    legend: boolean
}

// Default chart theme
export const defaultChartTheme: ChartTheme = {
    primary: "#3B82F6",
    success: "#10B981",
    warning: "#F59E0B",
    danger: "#EF4444",
    neutral: "#6B7280",
    background: "#FFFFFF",
    grid: "#F3F4F6",
    text: "#374151",
}

// Chart utility types
export type ChartTimeframe = "1D" | "1W" | "1M" | "3M" | "6M" | "1Y"
export type ChartType = "line" | "area" | "candlestick" | "bar"
export type IndicatorType = "rsi" | "macd" | "sma" | "ema" | "bollinger" | "atr" | "momentum"