/**
 * Chart Data Adapters
 *
 * @description Utility functions to transform backend analysis data into
 * formats compatible with Recharts components. Handles data normalization,
 * type conversion, and null/undefined value handling.
 */

import { AnalysisData, TechnicalIndicators, VolatilityMetrics, PatternDetection } from "@/types/analysis"
import { ChartDataPoint, CandlestickDataPoint, LineChartData } from "./types"

/**
 * Transforms technical indicators data for chart display
 *
 * @param indicators - Technical indicators from backend
 * @param historicalData - Optional historical price data for context
 * @returns Formatted data series for technical indicator charts
 *
 * @example
 * ```typescript
 * const chartData = adaptTechnicalIndicators(analysis.technical_analysis.indicators)
 * ```
 */
export function adaptTechnicalIndicators(
    indicators: TechnicalIndicators,
    historicalData?: ChartDataPoint[],
): LineChartData[] {
    const series: LineChartData[] = []

    // RSI Series
    if (indicators.rsi !== undefined) {
        series.push({
            name: "RSI",
            data: [
                {
                    date: new Date().toISOString(),
                    value: indicators.rsi,
                    label: `RSI: ${indicators.rsi.toFixed(2)}`,
                },
            ],
            color: "#8B5CF6",
            type: "line",
        })
    }

    // MACD Series
    if (indicators.macd !== undefined && indicators.macd_signal !== undefined) {
        series.push({
            name: "MACD",
            data: [
                {
                    date: new Date().toISOString(),
                    value: indicators.macd,
                    label: `MACD: ${indicators.macd.toFixed(4)}`,
                },
            ],
            color: "#3B82F6",
            type: "line",
        })

        series.push({
            name: "MACD Signal",
            data: [
                {
                    date: new Date().toISOString(),
                    value: indicators.macd_signal,
                    label: `Signal: ${indicators.macd_signal.toFixed(4)}`,
                },
            ],
            color: "#EF4444",
            type: "line",
        })
    }

    // Moving Averages
    if (indicators.sma_20 !== undefined) {
        series.push({
            name: "SMA 20",
            data: [
                {
                    date: new Date().toISOString(),
                    value: indicators.sma_20,
                    label: `SMA 20: ${indicators.sma_20.toFixed(2)}`,
                },
            ],
            color: "#10B981",
            type: "line",
        })
    }

    if (indicators.sma_50 !== undefined) {
        series.push({
            name: "SMA 50",
            data: [
                {
                    date: new Date().toISOString(),
                    value: indicators.sma_50,
                    label: `SMA 50: ${indicators.sma_50.toFixed(2)}`,
                },
            ],
            color: "#F59E0B",
            type: "line",
        })
    }

    // Bollinger Bands
    if (indicators.bollinger_upper !== undefined && indicators.bollinger_lower !== undefined) {
        series.push({
            name: "Bollinger Upper",
            data: [
                {
                    date: new Date().toISOString(),
                    value: indicators.bollinger_upper,
                    label: `Upper Band: ${indicators.bollinger_upper.toFixed(2)}`,
                },
            ],
            color: "#EC4899",
            type: "line",
        })

        series.push({
            name: "Bollinger Lower",
            data: [
                {
                    date: new Date().toISOString(),
                    value: indicators.bollinger_lower,
                    label: `Lower Band: ${indicators.bollinger_lower.toFixed(2)}`,
                },
            ],
            color: "#EC4899",
            type: "line",
        })
    }

    return series
}

/**
 * Transforms volatility metrics data for chart display
 *
 * @param metrics - Volatility metrics from backend
 * @param historicalData - Optional historical volatility data
 * @returns Formatted data series for volatility charts
 *
 * @example
 * ```typescript
 * const chartData = adaptVolatilityMetrics(analysis.volatility_analysis.metrics)
 * ```
 */
export function adaptVolatilityMetrics(metrics: VolatilityMetrics, historicalData?: ChartDataPoint[]): LineChartData[] {
    const series: LineChartData[] = []

    // ATR Series
    series.push({
        name: "ATR",
        data: [
            {
                date: new Date().toISOString(),
                value: metrics.atr,
                label: `ATR: ${metrics.atr.toFixed(4)}`,
            },
        ],
        color: "#F59E0B",
        type: "line",
    })

    // ATR Percentage
    series.push({
        name: "ATR %",
        data: [
            {
                date: new Date().toISOString(),
                value: metrics.atr_percentage,
                label: `ATR %: ${metrics.atr_percentage.toFixed(2)}%`,
            },
        ],
        color: "#EF4444",
        type: "line",
    })

    // Standard Deviation
    series.push({
        name: "Std Dev",
        data: [
            {
                date: new Date().toISOString(),
                value: metrics.std_dev,
                label: `Std Dev: ${metrics.std_dev.toFixed(4)}`,
            },
        ],
        color: "#8B5CF6",
        type: "line",
    })

    // Volatility Percentile
    series.push({
        name: "Vol Percentile",
        data: [
            {
                date: new Date().toISOString(),
                value: metrics.volatility_percentile,
                label: `Vol Percentile: ${metrics.volatility_percentile.toFixed(1)}%`,
            },
        ],
        color: "#10B981",
        type: "line",
    })

    return series
}

/**
 * Transforms pattern detection data for chart annotations
 *
 * @param patterns - Pattern detection results from backend
 * @param priceData - Price data for pattern context
 * @returns Formatted annotation data for pattern charts
 *
 * @example
 * ```typescript
 * const annotations = adaptPatternDetections(analysis.pattern_analysis.patterns, priceData)
 * ```
 */
export function adaptPatternDetections(
    patterns: PatternDetection[],
    priceData?: CandlestickDataPoint[],
): Array<{
    x: number
    y: number
    label: string
    color: string
    confidence: number
    description: string
}> {
    return patterns.map((pattern, index) => ({
        x: pattern.start_index,
        y: pattern.key_levels?.support || 0,
        label: pattern.pattern_type.replace(/_/g, " "),
        color: getPatternColor(pattern.signal),
        confidence: pattern.confidence,
        description: pattern.description,
    }))
}

/**
 * Creates mock historical data for demonstration purposes
 *
 * @param days - Number of days to generate
 * @param basePrice - Base price for generation
 * @returns Mock historical data points
 *
 * @example
 * ```typescript
 * const mockData = createMockHistoricalData(30, 150.00)
 * ```
 */
export function createMockHistoricalData(days: number = 30, basePrice: number = 100): CandlestickDataPoint[] {
    const data: CandlestickDataPoint[] = []
    let price = basePrice

    for (let i = 0; i < days; i++) {
        const date = new Date()
        date.setDate(date.getDate() - (days - i))

        // Generate realistic price movement
        const change = (Math.random() - 0.5) * 0.1 * price
        const open = price
        const close = price + change
        const high = Math.max(open, close) + Math.random() * 0.02 * price
        const low = Math.min(open, close) - Math.random() * 0.02 * price
        const volume = Math.floor(Math.random() * 1000000) + 100000

        data.push({
            date: date.toISOString().split("T")[0],
            open: Math.round(open * 100) / 100,
            high: Math.round(high * 100) / 100,
            low: Math.round(low * 100) / 100,
            close: Math.round(close * 100) / 100,
            volume,
        })

        price = close
    }

    return data
}

/**
 * Converts price data to line chart format
 *
 * @param priceData - Candlestick price data
 * @param priceType - Which price to extract (open, high, low, close)
 * @returns Line chart data points
 *
 * @example
 * ```typescript
 * const closePrices = adaptPriceDataToLine(priceData, "close")
 * ```
 */
export function adaptPriceDataToLine(
    priceData: CandlestickDataPoint[],
    priceType: "open" | "high" | "low" | "close" = "close",
): ChartDataPoint[] {
    return priceData.map((point) => ({
        date: point.date,
        value: point[priceType],
        label: `${priceType.charAt(0).toUpperCase() + priceType.slice(1)}: ${point[priceType].toFixed(2)}`,
    }))
}

/**
 * Normalizes data series to same scale for comparison
 *
 * @param series - Array of data series
 * @param scale - Target scale range [min, max]
 * @returns Normalized data series
 *
 * @example
 * ```typescript
 * const normalized = normalizeDataSeries(series, [0, 100])
 * ```
 */
export function normalizeDataSeries(series: LineChartData[], scale: [number, number] = [0, 1]): LineChartData[] {
    return series.map((s) => {
        const values = s.data.map((d) => d.value)
        const min = Math.min(...values)
        const max = Math.max(...values)
        const range = max - min

        if (range === 0) return s

        return {
            ...s,
            data: s.data.map((d) => ({
                ...d,
                value: scale[0] + ((d.value - min) / range) * (scale[1] - scale[0]),
            })),
        }
    })
}

/**
 * Helper function to get color based on pattern signal
 *
 * @param signal - Pattern signal type
 * @returns Color hex code
 */
function getPatternColor(signal: string): string {
    switch (signal) {
        case "STRONG_BULLISH":
            return "#10B981"
        case "BULLISH":
            return "#34D399"
        case "NEUTRAL":
            return "#6B7280"
        case "BEARISH":
            return "#F87171"
        case "STRONG_BEARISH":
            return "#EF4444"
        default:
            return "#6B7280"
    }
}

/**
 * Validates chart data for null/undefined values
 *
 * @param data - Chart data to validate
 * @returns Cleaned data with valid values only
 *
 * @example
 * ```typescript
 * const cleanData = validateChartData(rawData)
 * ```
 */
export function validateChartData<T extends { value: number }>(data: T[]): T[] {
    return data.filter(
        (point) => point.value !== null && point.value !== undefined && !isNaN(point.value) && isFinite(point.value),
    )
}

/**
 * Formats large numbers for chart display
 *
 * @param value - Number to format
 * @returns Formatted string with appropriate suffixes
 *
 * @example
 * ```typescript
 * formatNumberForChart(1234567) // "1.23M"
 * ```
 */
export function formatNumberForChart(value: number): string {
    if (value >= 1e9) {
        return (value / 1e9).toFixed(1) + "B"
    } else if (value >= 1e6) {
        return (value / 1e6).toFixed(1) + "M"
    } else if (value >= 1e3) {
        return (value / 1e3).toFixed(1) + "K"
    } else {
        return value.toFixed(2)
    }
}
