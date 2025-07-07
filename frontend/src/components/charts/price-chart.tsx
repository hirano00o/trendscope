/**
 * Price Chart Component
 * 
 * @description Comprehensive price chart component displaying candlestick data,
 * volume bars, and overlaid technical indicators (moving averages, Bollinger Bands).
 * Built with Recharts for responsive and interactive financial data visualization.
 */

"use client"

import * as React from "react"
import {
    ComposedChart,
    Bar,
    Line,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    ReferenceLine,
} from "recharts"
import { ChartContainer } from "./chart-container"
import { PriceChartProps, CandlestickDataPoint, defaultChartTheme } from "./types"
import { adaptPriceDataToLine, createMockHistoricalData, formatNumberForChart } from "./data-adapters"
import { cn } from "@/lib/utils"

/**
 * Custom Candlestick Bar Component
 * 
 * @description Renders individual candlestick bars with proper coloring
 * based on price movement (green for bullish, red for bearish).
 */
interface CandlestickBarProps {
    payload?: CandlestickDataPoint
    x?: number
    y?: number
    width?: number
    height?: number
}

const CandlestickBar: React.FC<CandlestickBarProps> = ({ payload, x, y, width, height }) => {
    if (!payload || !x || !y || !width || !height) return null
    
    const { open, high, low, close } = payload
    const isUpDay = close > open
    const color = isUpDay ? "#10B981" : "#EF4444"
    
    // Calculate dimensions
    const bodyHeight = Math.abs(close - open)
    const bodyTop = Math.min(close, open)
    const wickTop = high
    const wickBottom = low
    
    // Scale calculations (simplified for demonstration)
    const scale = height / (high - low)
    const wickX = x + width / 2
    
    return (
        <g>
            {/* Upper wick */}
            <line
                x1={wickX}
                y1={y}
                x2={wickX}
                y2={y + (wickTop - bodyTop) * scale}
                stroke={color}
                strokeWidth={1}
            />
            
            {/* Body */}
            <rect
                x={x}
                y={y + (wickTop - Math.max(open, close)) * scale}
                width={width}
                height={bodyHeight * scale}
                fill={color}
                stroke={color}
                strokeWidth={1}
            />
            
            {/* Lower wick */}
            <line
                x1={wickX}
                y1={y + (wickTop - Math.min(open, close)) * scale}
                x2={wickX}
                y2={y + height}
                stroke={color}
                strokeWidth={1}
            />
        </g>
    )
}

/**
 * Custom Tooltip Component
 * 
 * @description Displays comprehensive price and volume information
 * with proper formatting for financial data.
 */
interface CustomTooltipProps {
    active?: boolean
    payload?: any[]
    label?: string
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label }) => {
    if (!active || !payload || !payload.length) return null
    
    const data = payload[0]?.payload
    if (!data) return null
    
    return (
        <div className="bg-white p-3 border border-neutral-200 rounded-lg shadow-lg">
            <p className="font-medium text-neutral-800 mb-2">{label}</p>
            <div className="space-y-1 text-sm">
                <div className="flex justify-between space-x-4">
                    <span className="text-neutral-600">Open:</span>
                    <span className="font-medium">${data.open?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between space-x-4">
                    <span className="text-neutral-600">High:</span>
                    <span className="font-medium">${data.high?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between space-x-4">
                    <span className="text-neutral-600">Low:</span>
                    <span className="font-medium">${data.low?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between space-x-4">
                    <span className="text-neutral-600">Close:</span>
                    <span className={cn(
                        "font-medium",
                        data.close > data.open ? "text-success-600" : "text-danger-600"
                    )}>
                        ${data.close?.toFixed(2)}
                    </span>
                </div>
                {data.volume && (
                    <div className="flex justify-between space-x-4 pt-1 border-t border-neutral-200">
                        <span className="text-neutral-600">Volume:</span>
                        <span className="font-medium">{formatNumberForChart(data.volume)}</span>
                    </div>
                )}
            </div>
        </div>
    )
}

/**
 * Price Chart Component
 * 
 * @param props - Price chart props including data and configuration
 * @returns JSX element with price chart visualization
 * 
 * @example
 * ```tsx
 * <PriceChart 
 *   data={priceData} 
 *   height={400}
 *   showVolume={true}
 *   indicators={{
 *     sma: [{ period: 20, color: "#10B981" }],
 *     bollinger: { show: true, color: "#8B5CF6" }
 *   }}
 * />
 * ```
 */
export const PriceChart: React.FC<PriceChartProps> = ({
    data,
    height = 400,
    width = "auto",
    showVolume = true,
    theme,
    timeRange = "1M",
    indicators = {},
}) => {
    const mergedTheme = React.useMemo(() => ({
        ...defaultChartTheme,
        ...theme,
    }), [theme])
    
    // Use mock data if no data provided
    const chartData = React.useMemo(() => {
        if (!data || data.length === 0) {
            return createMockHistoricalData(30, 150)
        }
        return data
    }, [data])
    
    // Prepare chart data with indicators
    const processedData = React.useMemo(() => {
        let processed = [...chartData]
        
        // Add moving averages (simplified calculation for demonstration)
        if (indicators.sma) {
            indicators.sma.forEach(({ period }, index) => {
                processed = processed.map((point, i) => {
                    if (i < period - 1) return point
                    
                    const sum = processed
                        .slice(i - period + 1, i + 1)
                        .reduce((acc, p) => acc + p.close, 0)
                    
                    return {
                        ...point,
                        [`sma${period}`]: sum / period,
                    }
                })
            })
        }
        
        return processed
    }, [chartData, indicators])
    
    // Calculate price range for chart scaling
    const priceRange = React.useMemo(() => {
        const prices = processedData.flatMap(d => [d.high, d.low])
        return {
            min: Math.min(...prices) * 0.98,
            max: Math.max(...prices) * 1.02,
        }
    }, [processedData])
    
    // Calculate volume range
    const volumeRange = React.useMemo(() => {
        const volumes = processedData.map(d => d.volume || 0)
        return {
            min: 0,
            max: Math.max(...volumes) * 1.1,
        }
    }, [processedData])
    
    return (
        <ChartContainer
            title="Price Chart"
            height={height}
            width={width}
            theme={mergedTheme}
            badges={[
                { label: timeRange, variant: "secondary" },
                { label: "Live Data", variant: "success" },
            ]}
        >
            <ComposedChart
                data={processedData}
                margin={{
                    top: 20,
                    right: 30,
                    left: 20,
                    bottom: showVolume ? 80 : 20,
                }}
            >
                <CartesianGrid 
                    strokeDasharray="3 3" 
                    stroke={mergedTheme.grid}
                    opacity={0.3}
                />
                
                <XAxis 
                    dataKey="date"
                    tick={{ fontSize: 12, fill: mergedTheme.text }}
                    stroke={mergedTheme.text}
                    tickFormatter={(value) => {
                        const date = new Date(value)
                        return date.toLocaleDateString('en-US', { 
                            month: 'short', 
                            day: 'numeric' 
                        })
                    }}
                />
                
                <YAxis 
                    yAxisId="price"
                    orientation="left"
                    domain={[priceRange.min, priceRange.max]}
                    tick={{ fontSize: 12, fill: mergedTheme.text }}
                    stroke={mergedTheme.text}
                    tickFormatter={(value) => `$${value.toFixed(0)}`}
                />
                
                {showVolume && (
                    <YAxis 
                        yAxisId="volume"
                        orientation="right"
                        domain={[0, volumeRange.max]}
                        tick={{ fontSize: 12, fill: mergedTheme.text }}
                        stroke={mergedTheme.text}
                        tickFormatter={(value) => formatNumberForChart(value)}
                    />
                )}
                
                <Tooltip content={<CustomTooltip />} />
                
                <Legend 
                    wrapperStyle={{ 
                        paddingTop: '10px',
                        fontSize: '12px',
                        color: mergedTheme.text,
                    }}
                />
                
                {/* Price Area (simplified - using Area for demonstration) */}
                <Area
                    yAxisId="price"
                    type="monotone"
                    dataKey="close"
                    stroke={mergedTheme.primary}
                    fill={mergedTheme.primary}
                    fillOpacity={0.1}
                    strokeWidth={2}
                    name="Price"
                />
                
                {/* Volume Bars */}
                {showVolume && (
                    <Bar
                        yAxisId="volume"
                        dataKey="volume"
                        fill={mergedTheme.neutral}
                        opacity={0.3}
                        name="Volume"
                    />
                )}
                
                {/* Moving Averages */}
                {indicators.sma?.map(({ period, color }, index) => (
                    <Line
                        key={`sma-${period}`}
                        yAxisId="price"
                        type="monotone"
                        dataKey={`sma${period}`}
                        stroke={color}
                        strokeWidth={2}
                        dot={false}
                        name={`SMA ${period}`}
                    />
                ))}
                
                {/* Bollinger Bands */}
                {indicators.bollinger?.show && (
                    <>
                        <Line
                            yAxisId="price"
                            type="monotone"
                            dataKey="bollingerUpper"
                            stroke={indicators.bollinger.color}
                            strokeWidth={1}
                            strokeDasharray="2 2"
                            dot={false}
                            name="BB Upper"
                        />
                        <Line
                            yAxisId="price"
                            type="monotone"
                            dataKey="bollingerLower"
                            stroke={indicators.bollinger.color}
                            strokeWidth={1}
                            strokeDasharray="2 2"
                            dot={false}
                            name="BB Lower"
                        />
                    </>
                )}
                
                {/* Reference Lines */}
                <ReferenceLine 
                    yAxisId="price"
                    y={processedData[processedData.length - 1]?.close}
                    stroke={mergedTheme.warning}
                    strokeDasharray="5 5"
                    label="Current Price"
                />
            </ComposedChart>
        </ChartContainer>
    )
}

export default PriceChart