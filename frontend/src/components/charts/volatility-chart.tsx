/**
 * Volatility Chart Component
 *
 * @description Specialized chart for volatility analysis displaying ATR trends,
 * volatility regimes, percentile rankings, and multiple volatility estimators.
 * Provides insights into market risk and potential breakout scenarios.
 */

"use client"

import * as React from "react"
import {
    ComposedChart,
    LineChart,
    AreaChart,
    BarChart,
    Line,
    Area,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    ReferenceLine,
    ReferenceArea,
} from "recharts"
import { ChartContainer } from "./chart-container"
import { VolatilityChartProps, defaultChartTheme } from "./types"
import { adaptVolatilityMetrics, createMockHistoricalData, formatNumberForChart } from "./data-adapters"
import { cn } from "@/lib/utils"

/**
 * Custom Tooltip for Volatility Charts
 *
 * @description Displays volatility metrics with contextual information
 * about market conditions and risk levels.
 */
interface VolatilityTooltipProps {
    active?: boolean
    payload?: any[]
    label?: string
}

const VolatilityTooltip: React.FC<VolatilityTooltipProps> = ({ active, payload, label }) => {
    if (!active || !payload || !payload.length) return null

    const getVolatilityContext = (value: number, type: string) => {
        switch (type) {
            case "atr_percentage":
                if (value > 3) return { status: "High Volatility", color: "text-danger-600" }
                if (value > 1.5) return { status: "Moderate Volatility", color: "text-warning-600" }
                return { status: "Low Volatility", color: "text-success-600" }
            case "volatility_percentile":
                if (value > 80) return { status: "Extreme", color: "text-danger-600" }
                if (value > 60) return { status: "High", color: "text-warning-600" }
                if (value > 40) return { status: "Moderate", color: "text-neutral-600" }
                return { status: "Low", color: "text-success-600" }
            default:
                return { status: "", color: "text-neutral-600" }
        }
    }

    return (
        <div className="bg-white p-3 border border-neutral-200 rounded-lg shadow-lg">
            <p className="font-medium text-neutral-800 mb-2">{label}</p>
            <div className="space-y-1 text-sm">
                {payload.map((entry, index) => {
                    const context = getVolatilityContext(entry.value, entry.dataKey)
                    return (
                        <div key={index} className="flex justify-between items-center space-x-4">
                            <span className="text-neutral-600">{entry.name}:</span>
                            <div className="text-right">
                                <span className="font-medium">
                                    {typeof entry.value === "number" ? entry.value.toFixed(3) : entry.value}
                                    {entry.dataKey?.includes("percentage") && "%"}
                                </span>
                                {context.status && (
                                    <span className={cn("block text-xs", context.color)}>{context.status}</span>
                                )}
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

/**
 * ATR Trend Chart
 *
 * @description Displays Average True Range over time with trend analysis
 */
interface ATRTrendChartProps {
    data: any[]
    theme: any
    height?: number
}

const ATRTrendChart: React.FC<ATRTrendChartProps> = ({ data, theme, height = 200 }) => (
    <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data} margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.grid} opacity={0.3} />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: theme.text }} stroke={theme.text} />
                <YAxis
                    yAxisId="atr"
                    orientation="left"
                    tick={{ fontSize: 11, fill: theme.text }}
                    stroke={theme.text}
                    tickFormatter={(value) => value.toFixed(3)}
                />
                <YAxis
                    yAxisId="percentage"
                    orientation="right"
                    tick={{ fontSize: 11, fill: theme.text }}
                    stroke={theme.text}
                    tickFormatter={(value) => `${value.toFixed(1)}%`}
                />
                <Tooltip content={<VolatilityTooltip />} />
                <Legend />

                {/* ATR Area */}
                <Area
                    yAxisId="atr"
                    type="monotone"
                    dataKey="atr"
                    stroke={theme.primary}
                    fill={theme.primary}
                    fillOpacity={0.2}
                    strokeWidth={2}
                    name="ATR"
                />

                {/* ATR Percentage Line */}
                <Line
                    yAxisId="percentage"
                    type="monotone"
                    dataKey="atr_percentage"
                    stroke={theme.warning}
                    strokeWidth={2}
                    dot={false}
                    name="ATR %"
                />
            </ComposedChart>
        </ResponsiveContainer>
    </div>
)

/**
 * Volatility Regime Chart
 *
 * @description Displays volatility regimes with color-coded zones
 */
interface VolatilityRegimeChartProps {
    data: any[]
    theme: any
    height?: number
    currentRegime?: string
}

const VolatilityRegimeChart: React.FC<VolatilityRegimeChartProps> = ({
    data,
    theme,
    height = 150,
    currentRegime = "MODERATE",
}) => {
    const getRegimeColor = (regime: string) => {
        switch (regime) {
            case "LOW":
                return theme.success
            case "MODERATE":
                return theme.warning
            case "HIGH":
                return theme.danger
            case "EXTREME":
                return "#991B1B"
            default:
                return theme.neutral
        }
    }

    return (
        <div style={{ height }}>
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data} margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={theme.grid} opacity={0.3} />
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: theme.text }} stroke={theme.text} />
                    <YAxis
                        tick={{ fontSize: 11, fill: theme.text }}
                        stroke={theme.text}
                        domain={[0, 100]}
                        tickFormatter={(value) => `${value}%`}
                    />
                    <Tooltip content={<VolatilityTooltip />} />

                    {/* Volatility Percentile Bars */}
                    <Bar
                        dataKey="volatility_percentile"
                        fill={getRegimeColor(currentRegime)}
                        opacity={0.7}
                        name="Vol Percentile"
                    />

                    {/* Reference lines for regime boundaries */}
                    <ReferenceLine y={20} stroke={theme.success} strokeDasharray="2 2" label="Low" />
                    <ReferenceLine y={50} stroke={theme.warning} strokeDasharray="2 2" label="Moderate" />
                    <ReferenceLine y={80} stroke={theme.danger} strokeDasharray="2 2" label="High" />
                </BarChart>
            </ResponsiveContainer>
        </div>
    )
}

/**
 * Multiple Volatility Estimators Chart
 *
 * @description Compares different volatility estimation methods
 */
interface MultiVolEstimatorsChartProps {
    data: any[]
    theme: any
    height?: number
}

const MultiVolEstimatorsChart: React.FC<MultiVolEstimatorsChartProps> = ({ data, theme, height = 200 }) => (
    <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.grid} opacity={0.3} />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: theme.text }} stroke={theme.text} />
                <YAxis
                    tick={{ fontSize: 11, fill: theme.text }}
                    stroke={theme.text}
                    tickFormatter={(value) => value.toFixed(3)}
                />
                <Tooltip content={<VolatilityTooltip />} />
                <Legend />

                {/* Standard Deviation */}
                <Line
                    type="monotone"
                    dataKey="std_dev"
                    stroke={theme.primary}
                    strokeWidth={2}
                    dot={false}
                    name="Std Dev"
                />

                {/* Parkinson Volatility */}
                <Line
                    type="monotone"
                    dataKey="parkinson_volatility"
                    stroke={theme.success}
                    strokeWidth={2}
                    dot={false}
                    name="Parkinson"
                />

                {/* Garman-Klass Volatility */}
                <Line
                    type="monotone"
                    dataKey="garman_klass_volatility"
                    stroke={theme.warning}
                    strokeWidth={2}
                    dot={false}
                    name="Garman-Klass"
                />
            </LineChart>
        </ResponsiveContainer>
    </div>
)

/**
 * Volatility Chart Component
 *
 * @param props - Volatility chart props including metrics and display options
 * @returns JSX element with volatility analysis visualization
 *
 * @example
 * ```tsx
 * <VolatilityChart
 *   metrics={volatilityMetrics}
 *   height={400}
 *   displayType="atr"
 * />
 * ```
 */
export const VolatilityChart: React.FC<VolatilityChartProps> = ({
    metrics,
    historicalData,
    height = 400,
    width = "auto",
    theme,
    displayType = "atr",
}) => {
    const mergedTheme = React.useMemo(
        () => ({
            ...defaultChartTheme,
            ...theme,
        }),
        [theme],
    )

    // Prepare chart data with volatility metrics
    const chartData = React.useMemo(() => {
        // Create mock historical volatility data
        const mockData = createMockHistoricalData(30, 150)

        return mockData.map((point, index) => ({
            date: point.date,
            // ATR metrics
            atr: metrics.atr || 0.5 + Math.sin(index * 0.1) * 0.2 + Math.random() * 0.1,
            atr_percentage: metrics.atr_percentage || 1.5 + Math.sin(index * 0.1) * 0.5 + Math.random() * 0.3,
            // Standard volatility measures
            std_dev: metrics.std_dev || 0.02 + Math.sin(index * 0.08) * 0.01 + Math.random() * 0.005,
            std_dev_annualized: metrics.std_dev_annualized || (0.02 + Math.sin(index * 0.08) * 0.01) * Math.sqrt(252),
            // Advanced volatility estimators
            parkinson_volatility:
                metrics.parkinson_volatility || 0.025 + Math.sin(index * 0.06) * 0.008 + Math.random() * 0.003,
            garman_klass_volatility:
                metrics.garman_klass_volatility || 0.022 + Math.sin(index * 0.07) * 0.007 + Math.random() * 0.004,
            // Volatility percentile and regime
            volatility_percentile:
                metrics.volatility_percentile || 50 + Math.sin(index * 0.05) * 20 + Math.random() * 10,
            volatility_ratio: metrics.volatility_ratio || 1.0 + Math.sin(index * 0.04) * 0.3 + Math.random() * 0.1,
        }))
    }, [metrics, historicalData])

    // Calculate panel configuration based on display type
    const getPanelConfiguration = () => {
        switch (displayType) {
            case "atr":
                return [
                    { type: "atr_trend", height: height * 0.6 },
                    { type: "regime", height: height * 0.4 },
                ]
            case "std_dev":
                return [
                    { type: "multi_estimators", height: height * 0.7 },
                    { type: "regime", height: height * 0.3 },
                ]
            default:
                return [
                    { type: "atr_trend", height: height * 0.4 },
                    { type: "multi_estimators", height: height * 0.4 },
                    { type: "regime", height: height * 0.2 },
                ]
        }
    }

    const panelConfig = getPanelConfiguration()

    // Get current volatility regime
    const currentRegime = React.useMemo(() => {
        const percentile = metrics.volatility_percentile || 50
        if (percentile > 80) return "EXTREME"
        if (percentile > 60) return "HIGH"
        if (percentile > 40) return "MODERATE"
        return "LOW"
    }, [metrics.volatility_percentile])

    return (
        <ChartContainer
            title="Volatility Analysis"
            height={height}
            width={width}
            theme={mergedTheme}
            badges={[
                {
                    label: currentRegime,
                    variant:
                        currentRegime === "LOW" ? "success" : currentRegime === "MODERATE" ? "warning" : "destructive",
                },
                { label: `${displayType.toUpperCase()}`, variant: "secondary" },
            ]}
        >
            <div className="space-y-4">
                {panelConfig.map((panel, index) => (
                    <div key={index}>
                        {panel.type === "atr_trend" && (
                            <>
                                <h4 className="text-sm font-medium text-neutral-700 mb-2">
                                    Average True Range (ATR) Trend
                                </h4>
                                <ATRTrendChart data={chartData} theme={mergedTheme} height={panel.height} />
                            </>
                        )}

                        {panel.type === "regime" && (
                            <>
                                <h4 className="text-sm font-medium text-neutral-700 mb-2">
                                    Volatility Regime & Percentile Ranking
                                </h4>
                                <VolatilityRegimeChart
                                    data={chartData}
                                    theme={mergedTheme}
                                    height={panel.height}
                                    currentRegime={currentRegime}
                                />
                            </>
                        )}

                        {panel.type === "multi_estimators" && (
                            <>
                                <h4 className="text-sm font-medium text-neutral-700 mb-2">
                                    Multiple Volatility Estimators
                                </h4>
                                <MultiVolEstimatorsChart data={chartData} theme={mergedTheme} height={panel.height} />
                            </>
                        )}
                    </div>
                ))}
            </div>
        </ChartContainer>
    )
}

export default VolatilityChart
