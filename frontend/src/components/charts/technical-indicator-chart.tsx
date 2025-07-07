/**
 * Technical Indicator Chart Component
 * 
 * @description Specialized chart component for displaying technical indicators
 * such as RSI, MACD, and momentum oscillators. Features separate panels for
 * different indicator types with appropriate scaling and reference lines.
 */

"use client"

import * as React from "react"
import {
    ComposedChart,
    LineChart,
    Line,
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
import { TechnicalIndicatorChartProps, defaultChartTheme } from "./types"
import { adaptTechnicalIndicators, createMockHistoricalData } from "./data-adapters"
import { cn } from "@/lib/utils"

/**
 * Custom Tooltip for Technical Indicators
 * 
 * @description Displays technical indicator values with proper formatting
 * and contextual information about indicator levels.
 */
interface TechnicalTooltipProps {
    active?: boolean
    payload?: any[]
    label?: string
    indicatorType?: "rsi" | "macd" | "momentum"
}

const TechnicalTooltip: React.FC<TechnicalTooltipProps> = ({ 
    active, 
    payload, 
    label, 
    indicatorType 
}) => {
    if (!active || !payload || !payload.length) return null
    
    const getIndicatorContext = (type: string, value: number) => {
        switch (type) {
            case "rsi":
                if (value > 70) return { status: "Overbought", color: "text-danger-600" }
                if (value < 30) return { status: "Oversold", color: "text-success-600" }
                return { status: "Neutral", color: "text-neutral-600" }
            case "macd":
                return { 
                    status: value > 0 ? "Bullish" : "Bearish", 
                    color: value > 0 ? "text-success-600" : "text-danger-600" 
                }
            default:
                return { status: "", color: "text-neutral-600" }
        }
    }
    
    return (
        <div className="bg-white p-3 border border-neutral-200 rounded-lg shadow-lg">
            <p className="font-medium text-neutral-800 mb-2">{label}</p>
            <div className="space-y-1 text-sm">
                {payload.map((entry, index) => {
                    const context = getIndicatorContext(indicatorType || "", entry.value)
                    return (
                        <div key={index} className="flex justify-between items-center space-x-4">
                            <span className="text-neutral-600">{entry.name}:</span>
                            <div className="text-right">
                                <span className="font-medium">
                                    {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
                                </span>
                                {context.status && (
                                    <span className={cn("block text-xs", context.color)}>
                                        {context.status}
                                    </span>
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
 * RSI Chart Component
 * 
 * @description Displays RSI indicator with overbought/oversold levels
 */
interface RSIChartProps {
    data: any[]
    theme: any
    height?: number
}

const RSIChart: React.FC<RSIChartProps> = ({ data, theme, height = 150 }) => (
    <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.grid} opacity={0.3} />
                <XAxis 
                    dataKey="date" 
                    tick={{ fontSize: 11, fill: theme.text }}
                    stroke={theme.text}
                />
                <YAxis 
                    domain={[0, 100]}
                    tick={{ fontSize: 11, fill: theme.text }}
                    stroke={theme.text}
                />
                <Tooltip content={<TechnicalTooltip indicatorType="rsi" />} />
                
                {/* RSI Zones */}
                <ReferenceArea y1={70} y2={100} fill={theme.danger} fillOpacity={0.1} />
                <ReferenceArea y1={0} y2={30} fill={theme.success} fillOpacity={0.1} />
                
                {/* RSI Lines */}
                <ReferenceLine y={70} stroke={theme.danger} strokeDasharray="2 2" />
                <ReferenceLine y={50} stroke={theme.neutral} strokeDasharray="1 1" />
                <ReferenceLine y={30} stroke={theme.success} strokeDasharray="2 2" />
                
                <Line 
                    type="monotone" 
                    dataKey="rsi" 
                    stroke={theme.primary}
                    strokeWidth={2}
                    dot={false}
                    name="RSI"
                />
            </LineChart>
        </ResponsiveContainer>
    </div>
)

/**
 * MACD Chart Component
 * 
 * @description Displays MACD line, signal line, and histogram
 */
interface MACDChartProps {
    data: any[]
    theme: any
    height?: number
}

const MACDChart: React.FC<MACDChartProps> = ({ data, theme, height = 150 }) => (
    <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.grid} opacity={0.3} />
                <XAxis 
                    dataKey="date" 
                    tick={{ fontSize: 11, fill: theme.text }}
                    stroke={theme.text}
                />
                <YAxis 
                    tick={{ fontSize: 11, fill: theme.text }}
                    stroke={theme.text}
                />
                <Tooltip content={<TechnicalTooltip indicatorType="macd" />} />
                
                {/* Zero Line */}
                <ReferenceLine y={0} stroke={theme.neutral} strokeDasharray="1 1" />
                
                {/* MACD Histogram */}
                <Bar 
                    dataKey="macdHistogram" 
                    fill={theme.neutral}
                    opacity={0.3}
                    name="MACD Histogram"
                />
                
                {/* MACD Lines */}
                <Line 
                    type="monotone" 
                    dataKey="macd" 
                    stroke={theme.primary}
                    strokeWidth={2}
                    dot={false}
                    name="MACD"
                />
                <Line 
                    type="monotone" 
                    dataKey="macdSignal" 
                    stroke={theme.warning}
                    strokeWidth={2}
                    dot={false}
                    name="Signal"
                />
            </ComposedChart>
        </ResponsiveContainer>
    </div>
)

/**
 * Technical Indicator Chart Component
 * 
 * @param props - Technical indicator chart props
 * @returns JSX element with technical indicator visualization
 * 
 * @example
 * ```tsx
 * <TechnicalIndicatorChart 
 *   indicators={technicalData.indicators}
 *   height={300}
 *   activeIndicators={["rsi", "macd"]}
 * />
 * ```
 */
export const TechnicalIndicatorChart: React.FC<TechnicalIndicatorChartProps> = ({
    indicators,
    historicalData,
    height = 300,
    width = "auto",
    activeIndicators = ["rsi", "macd"],
    theme,
}) => {
    const mergedTheme = React.useMemo(() => ({
        ...defaultChartTheme,
        ...theme,
    }), [theme])
    
    // Prepare chart data
    const chartData = React.useMemo(() => {
        // Create mock historical data for demonstration
        const mockData = createMockHistoricalData(30, 150)
        
        // Add technical indicators to historical data
        return mockData.map((point, index) => ({
            date: point.date,
            // RSI (mock calculation)
            rsi: indicators.rsi || (45 + Math.sin(index * 0.1) * 20 + Math.random() * 10),
            // MACD (mock calculation)
            macd: indicators.macd || (Math.sin(index * 0.05) * 2 + Math.random() * 0.5),
            macdSignal: indicators.macd_signal || (Math.sin(index * 0.05 - 0.1) * 1.8 + Math.random() * 0.3),
            macdHistogram: indicators.macd && indicators.macd_signal ? 
                indicators.macd - indicators.macd_signal : 
                (Math.sin(index * 0.05) * 0.5 + Math.random() * 0.2),
            // Momentum (mock calculation)
            momentum: Math.sin(index * 0.03) * 5 + Math.random() * 2,
        }))
    }, [indicators, historicalData])
    
    // Calculate panel heights based on active indicators
    const panelCount = activeIndicators.length
    const panelHeight = height / panelCount
    
    return (
        <ChartContainer
            title="Technical Indicators"
            height={height}
            width={width}
            theme={mergedTheme}
            badges={[
                { label: `${activeIndicators.length} Indicators`, variant: "secondary" },
                { label: "Real-time", variant: "success" },
            ]}
        >
            <div className="space-y-4">
                {activeIndicators.includes("rsi") && (
                    <div>
                        <h4 className="text-sm font-medium text-neutral-700 mb-2">
                            RSI (14) - Relative Strength Index
                        </h4>
                        <RSIChart 
                            data={chartData}
                            theme={mergedTheme}
                            height={panelHeight}
                        />
                    </div>
                )}
                
                {activeIndicators.includes("macd") && (
                    <div>
                        <h4 className="text-sm font-medium text-neutral-700 mb-2">
                            MACD (12,26,9) - Moving Average Convergence Divergence
                        </h4>
                        <MACDChart 
                            data={chartData}
                            theme={mergedTheme}
                            height={panelHeight}
                        />
                    </div>
                )}
                
                {activeIndicators.includes("momentum") && (
                    <div>
                        <h4 className="text-sm font-medium text-neutral-700 mb-2">
                            Momentum - Price Rate of Change
                        </h4>
                        <div style={{ height: panelHeight }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke={mergedTheme.grid} opacity={0.3} />
                                    <XAxis 
                                        dataKey="date" 
                                        tick={{ fontSize: 11, fill: mergedTheme.text }}
                                        stroke={mergedTheme.text}
                                    />
                                    <YAxis 
                                        tick={{ fontSize: 11, fill: mergedTheme.text }}
                                        stroke={mergedTheme.text}
                                    />
                                    <Tooltip content={<TechnicalTooltip indicatorType="momentum" />} />
                                    
                                    <ReferenceLine y={0} stroke={mergedTheme.neutral} strokeDasharray="1 1" />
                                    
                                    <Line 
                                        type="monotone" 
                                        dataKey="momentum" 
                                        stroke={mergedTheme.success}
                                        strokeWidth={2}
                                        dot={false}
                                        name="Momentum"
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                )}
            </div>
        </ChartContainer>
    )
}

export default TechnicalIndicatorChart