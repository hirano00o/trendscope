/**
 * Pattern Chart Component
 *
 * @description Specialized chart for pattern analysis displaying detected
 * technical patterns, support/resistance levels, and trend lines with
 * annotations and confidence indicators.
 */

"use client"

import * as React from "react"
import {
    ComposedChart,
    LineChart,
    Area,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    ReferenceLine,
    ReferenceArea,
    Cell,
    Scatter,
    ScatterChart,
} from "recharts"
import { ChartContainer } from "./chart-container"
import { PatternChartProps, CandlestickDataPoint, defaultChartTheme } from "./types"
import { adaptPatternDetections, createMockHistoricalData } from "./data-adapters"
import { cn } from "@/lib/utils"
import { PatternDetection } from "@/types/analysis"

/**
 * Custom Pattern Annotation Component
 *
 * @description Renders pattern annotations with icons and confidence indicators
 */
interface PatternAnnotationProps {
    pattern: PatternDetection
    x: number
    y: number
    width: number
    height: number
}

const PatternAnnotation: React.FC<PatternAnnotationProps> = ({ pattern, x, y, width, height }) => {
    const getPatternIcon = (patternType: string) => {
        switch (patternType) {
            case "BULLISH_ENGULFING":
                return "📈"
            case "BEARISH_ENGULFING":
                return "📉"
            case "DOJI":
                return "🤏"
            case "HAMMER":
                return "🔨"
            case "SHOOTING_STAR":
                return "⭐"
            case "SUPPORT_LEVEL":
                return "🟢"
            case "RESISTANCE_LEVEL":
                return "🔴"
            case "TREND_LINE":
                return "📏"
            default:
                return "📊"
        }
    }

    const getPatternColor = (signal: string) => {
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

    return (
        <g>
            {/* Pattern highlight area */}
            <rect
                x={x}
                y={y}
                width={width}
                height={height}
                fill={getPatternColor(pattern.signal)}
                fillOpacity={0.1}
                stroke={getPatternColor(pattern.signal)}
                strokeWidth={1}
                strokeDasharray="3 3"
            />

            {/* Pattern icon and label */}
            <text
                x={x + width / 2}
                y={y - 5}
                textAnchor="middle"
                fontSize="12"
                fill={getPatternColor(pattern.signal)}
                fontWeight="bold"
            >
                {getPatternIcon(pattern.pattern_type)}
            </text>

            {/* Confidence indicator */}
            <circle
                cx={x + width - 10}
                cy={y + 10}
                r={4}
                fill={getPatternColor(pattern.signal)}
                opacity={pattern.confidence}
            />

            <text x={x + width - 10} y={y + 15} textAnchor="middle" fontSize="9" fill="white" fontWeight="bold">
                {Math.round(pattern.confidence * 100)}
            </text>
        </g>
    )
}

/**
 * Custom Tooltip for Pattern Charts
 *
 * @description Displays pattern information with detailed analysis
 */
interface PatternTooltipProps {
    active?: boolean
    payload?: any[]
    label?: string
    patterns?: PatternDetection[]
}

const PatternTooltip: React.FC<PatternTooltipProps> = ({ active, payload, label, patterns }) => {
    if (!active || !payload || !payload.length) return null

    const data = payload[0]?.payload
    const relevantPatterns =
        patterns?.filter((p) => p.start_index <= (data?.index || 0) && p.end_index >= (data?.index || 0)) || []

    return (
        <div className="bg-white p-3 border border-neutral-200 rounded-lg shadow-lg max-w-xs">
            <p className="font-medium text-neutral-800 mb-2">{label}</p>

            {/* Price information */}
            <div className="space-y-1 text-sm mb-3">
                <div className="flex justify-between space-x-4">
                    <span className="text-neutral-600">Price:</span>
                    <span className="font-medium">${data?.close?.toFixed(2)}</span>
                </div>
            </div>

            {/* Pattern information */}
            {relevantPatterns.length > 0 && (
                <div className="border-t border-neutral-200 pt-2">
                    <p className="text-xs font-medium text-neutral-700 mb-1">Detected Patterns:</p>
                    {relevantPatterns.map((pattern, index) => (
                        <div key={index} className="text-xs space-y-1">
                            <div className="flex justify-between">
                                <span className="text-neutral-600">{pattern.pattern_type.replace(/_/g, " ")}:</span>
                                <span
                                    className={cn(
                                        "font-medium",
                                        pattern.signal.includes("BULLISH")
                                            ? "text-success-600"
                                            : pattern.signal.includes("BEARISH")
                                              ? "text-danger-600"
                                              : "text-neutral-600",
                                    )}
                                >
                                    {pattern.signal}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-neutral-500">Confidence:</span>
                                <span className="font-medium">{Math.round(pattern.confidence * 100)}%</span>
                            </div>
                            <p className="text-neutral-600 text-xs italic">{pattern.description}</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

/**
 * Support/Resistance Lines Component
 *
 * @description Renders horizontal lines for support and resistance levels
 */
interface SupportResistanceLinesProps {
    patterns: PatternDetection[]
    theme: any
}

const SupportResistanceLines: React.FC<SupportResistanceLinesProps> = ({ patterns, theme }) => {
    const supportLevels = patterns
        .filter((p) => p.pattern_type === "SUPPORT_LEVEL")
        .map((p) => p.key_levels?.support)
        .filter(Boolean)

    const resistanceLevels = patterns
        .filter((p) => p.pattern_type === "RESISTANCE_LEVEL")
        .map((p) => p.key_levels?.resistance)
        .filter(Boolean)

    return (
        <>
            {supportLevels.map((level, index) => (
                <ReferenceLine
                    key={`support-${index}`}
                    y={level}
                    stroke={theme.success}
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    label={{ value: "Support", position: "top" }}
                />
            ))}
            {resistanceLevels.map((level, index) => (
                <ReferenceLine
                    key={`resistance-${index}`}
                    y={level}
                    stroke={theme.danger}
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    label={{ value: "Resistance", position: "bottom" }}
                />
            ))}
        </>
    )
}

/**
 * Pattern Chart Component
 *
 * @param props - Pattern chart props including patterns and price data
 * @returns JSX element with pattern analysis visualization
 *
 * @example
 * ```tsx
 * <PatternChart
 *   patterns={detectedPatterns}
 *   priceData={historicalPrices}
 *   height={400}
 *   highlightPatterns={true}
 * />
 * ```
 */
export const PatternChart: React.FC<PatternChartProps> = ({
    patterns,
    priceData,
    height = 400,
    width = "auto",
    theme,
    highlightPatterns = true,
}) => {
    const mergedTheme = React.useMemo(
        () => ({
            ...defaultChartTheme,
            ...theme,
        }),
        [theme],
    )

    // Use mock data if no data provided
    const chartData = React.useMemo(() => {
        const mockData = priceData && priceData.length > 0 ? priceData : createMockHistoricalData(30, 150)

        return mockData.map((point, index) => ({
            ...point,
            index,
        }))
    }, [priceData])

    // Create mock patterns if none provided
    const chartPatterns = React.useMemo(() => {
        if (patterns && patterns.length > 0) return patterns

        // Generate mock patterns for demonstration
        return [
            {
                pattern_type: "BULLISH_ENGULFING" as const,
                signal: "BULLISH" as const,
                confidence: 0.85,
                start_index: 5,
                end_index: 7,
                description: "Strong bullish engulfing pattern detected",
                key_levels: { support: 145, resistance: 155 },
            },
            {
                pattern_type: "SUPPORT_LEVEL" as const,
                signal: "NEUTRAL" as const,
                confidence: 0.92,
                start_index: 0,
                end_index: 29,
                description: "Strong support level established",
                key_levels: { support: 145 },
            },
            {
                pattern_type: "RESISTANCE_LEVEL" as const,
                signal: "NEUTRAL" as const,
                confidence: 0.78,
                start_index: 0,
                end_index: 29,
                description: "Resistance level acting as ceiling",
                key_levels: { resistance: 160 },
            },
            {
                pattern_type: "HAMMER" as const,
                signal: "BULLISH" as const,
                confidence: 0.71,
                start_index: 15,
                end_index: 16,
                description: "Hammer candlestick pattern at support",
                key_levels: { support: 147 },
            },
        ]
    }, [patterns])

    // Calculate price range for chart scaling
    const priceRange = React.useMemo(() => {
        const prices = chartData.flatMap((d) => [d.high, d.low])
        return {
            min: Math.min(...prices) * 0.98,
            max: Math.max(...prices) * 1.02,
        }
    }, [chartData])

    // Pattern statistics
    const patternStats = React.useMemo(() => {
        const bullishPatterns = chartPatterns.filter((p) => p.signal.includes("BULLISH")).length
        const bearishPatterns = chartPatterns.filter((p) => p.signal.includes("BEARISH")).length
        const neutralPatterns = chartPatterns.filter((p) => p.signal === "NEUTRAL").length

        return { bullishPatterns, bearishPatterns, neutralPatterns }
    }, [chartPatterns])

    return (
        <ChartContainer
            title="Pattern Analysis"
            height={height}
            width={width}
            theme={mergedTheme}
            badges={[
                { label: `${chartPatterns.length} Patterns`, variant: "secondary" },
                { label: `${patternStats.bullishPatterns} Bullish`, variant: "success" },
                { label: `${patternStats.bearishPatterns} Bearish`, variant: "destructive" },
            ]}
        >
            <ComposedChart
                data={chartData}
                margin={{
                    top: 20,
                    right: 30,
                    left: 20,
                    bottom: 20,
                }}
            >
                <CartesianGrid strokeDasharray="3 3" stroke={mergedTheme.grid} opacity={0.3} />

                <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12, fill: mergedTheme.text }}
                    stroke={mergedTheme.text}
                    tickFormatter={(value) => {
                        const date = new Date(value)
                        return date.toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                        })
                    }}
                />

                <YAxis
                    domain={[priceRange.min, priceRange.max]}
                    tick={{ fontSize: 12, fill: mergedTheme.text }}
                    stroke={mergedTheme.text}
                    tickFormatter={(value) => `$${value.toFixed(0)}`}
                />

                <Tooltip content={<PatternTooltip patterns={chartPatterns} />} />

                <Legend
                    wrapperStyle={{
                        paddingTop: "10px",
                        fontSize: "12px",
                        color: mergedTheme.text,
                    }}
                />

                {/* Price Area Chart */}
                <Area
                    type="monotone"
                    dataKey="close"
                    stroke={mergedTheme.primary}
                    fill={mergedTheme.primary}
                    fillOpacity={0.1}
                    strokeWidth={2}
                    name="Price"
                />

                {/* High/Low Lines */}
                <Line
                    type="monotone"
                    dataKey="high"
                    stroke={mergedTheme.success}
                    strokeWidth={1}
                    dot={false}
                    strokeDasharray="2 2"
                    name="High"
                />

                <Line
                    type="monotone"
                    dataKey="low"
                    stroke={mergedTheme.danger}
                    strokeWidth={1}
                    dot={false}
                    strokeDasharray="2 2"
                    name="Low"
                />

                {/* Support/Resistance Lines */}
                <SupportResistanceLines patterns={chartPatterns} theme={mergedTheme} />
            </ComposedChart>

            {/* Pattern Legend */}
            <div className="mt-4 p-3 bg-neutral-50 rounded-lg">
                <h4 className="text-sm font-medium text-neutral-700 mb-2">Pattern Detection Summary</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                    <div className="text-center">
                        <div className="text-success-600 font-bold text-lg">{patternStats.bullishPatterns}</div>
                        <div className="text-neutral-600">Bullish Patterns</div>
                    </div>
                    <div className="text-center">
                        <div className="text-danger-600 font-bold text-lg">{patternStats.bearishPatterns}</div>
                        <div className="text-neutral-600">Bearish Patterns</div>
                    </div>
                    <div className="text-center">
                        <div className="text-neutral-600 font-bold text-lg">{patternStats.neutralPatterns}</div>
                        <div className="text-neutral-600">Support/Resistance</div>
                    </div>
                    <div className="text-center">
                        <div className="text-primary-600 font-bold text-lg">
                            {Math.round(
                                (chartPatterns.reduce((acc, p) => acc + p.confidence, 0) / chartPatterns.length) * 100,
                            )}
                            %
                        </div>
                        <div className="text-neutral-600">Avg Confidence</div>
                    </div>
                </div>
            </div>
        </ChartContainer>
    )
}

export default PatternChart
