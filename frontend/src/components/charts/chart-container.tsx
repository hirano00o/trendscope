/**
 * Chart Container Component
 * 
 * @description Common container component providing consistent layout,
 * theming, and responsive behavior for all chart types. Handles loading
 * states, error boundaries, and accessibility features.
 */

"use client"

import * as React from "react"
import { ResponsiveContainer } from "recharts"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { ChartTheme, defaultChartTheme } from "./types"

export interface ChartContainerProps {
    /**
     * Chart title displayed in header
     */
    title: string
    /**
     * Optional subtitle or description
     */
    subtitle?: string
    /**
     * Chart height in pixels
     */
    height?: number
    /**
     * Chart width, 'auto' for responsive
     */
    width?: number | "auto"
    /**
     * Chart theme colors
     */
    theme?: Partial<ChartTheme>
    /**
     * Whether the chart is loading
     */
    isLoading?: boolean
    /**
     * Error message if chart failed to load
     */
    error?: string
    /**
     * Chart content
     */
    children: React.ReactNode
    /**
     * Additional CSS classes
     */
    className?: string
    /**
     * Optional action buttons in header
     */
    actions?: React.ReactNode
    /**
     * Chart status indicator
     */
    status?: "success" | "warning" | "error" | "neutral"
    /**
     * Additional metadata badges
     */
    badges?: Array<{
        label: string
        variant?: "default" | "success" | "warning" | "destructive" | "secondary"
    }>
}

/**
 * Chart Container with responsive layout and theming
 * 
 * @param props - Container props including title, dimensions, and theme
 * @returns JSX element with chart container layout
 * 
 * @example
 * ```tsx
 * <ChartContainer 
 *   title="Price Chart" 
 *   subtitle="AAPL - Last 30 days"
 *   height={400}
 *   status="success"
 *   badges={[{ label: "Live Data", variant: "success" }]}
 * >
 *   <PriceChart data={priceData} />
 * </ChartContainer>
 * ```
 */
export const ChartContainer: React.FC<ChartContainerProps> = ({
    title,
    subtitle,
    height = 400,
    width = "auto",
    theme,
    isLoading = false,
    error,
    children,
    className,
    actions,
    status = "neutral",
    badges = [],
}) => {
    const mergedTheme = React.useMemo(() => ({
        ...defaultChartTheme,
        ...theme,
    }), [theme])

    const getStatusColor = (status: string) => {
        switch (status) {
            case "success": return "text-success-600"
            case "warning": return "text-warning-600"
            case "error": return "text-danger-600"
            default: return "text-neutral-600"
        }
    }

    if (error) {
        return (
            <Card className={cn("w-full", className)}>
                <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                        <span>{title}</span>
                        <Badge variant="destructive" size="sm">Error</Badge>
                    </CardTitle>
                    {subtitle && (
                        <p className="text-sm text-neutral-600">{subtitle}</p>
                    )}
                </CardHeader>
                <CardContent>
                    <div 
                        className="flex items-center justify-center bg-danger-50 border border-danger-200 rounded-lg p-8"
                        style={{ height: height }}
                    >
                        <div className="text-center">
                            <div className="text-danger-600 text-lg mb-2">⚠️</div>
                            <p className="text-danger-700 font-medium">Chart Error</p>
                            <p className="text-danger-600 text-sm mt-1">{error}</p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        )
    }

    return (
        <Card className={cn("w-full", className)}>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div className="flex-1">
                        <CardTitle className="flex items-center space-x-2">
                            <span className={getStatusColor(status)}>{title}</span>
                            {badges.map((badge, index) => (
                                <Badge
                                    key={index}
                                    variant={badge.variant || "default"}
                                    size="sm"
                                >
                                    {badge.label}
                                </Badge>
                            ))}
                        </CardTitle>
                        {subtitle && (
                            <p className="text-sm text-neutral-600 mt-1">{subtitle}</p>
                        )}
                    </div>
                    {actions && (
                        <div className="flex items-center space-x-2">
                            {actions}
                        </div>
                    )}
                </div>
            </CardHeader>
            <CardContent>
                {isLoading ? (
                    <div 
                        className="flex items-center justify-center bg-neutral-50 border border-neutral-200 rounded-lg"
                        style={{ height: height }}
                    >
                        <div className="text-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-3"></div>
                            <p className="text-neutral-600">Loading chart...</p>
                        </div>
                    </div>
                ) : (
                    <div
                        className="chart-container"
                        style={{
                            height: height,
                            width: width === "auto" ? "100%" : width,
                        }}
                    >
                        <ResponsiveContainer width="100%" height="100%">
                            <div
                                style={{
                                    color: mergedTheme.text,
                                    fontFamily: "system-ui, sans-serif",
                                }}
                            >
                                {children}
                            </div>
                        </ResponsiveContainer>
                    </div>
                )}
            </CardContent>
        </Card>
    )
}

/**
 * Chart Loading Component
 * 
 * @description Standalone loading component for charts
 */
export const ChartLoading: React.FC<{ height?: number; message?: string }> = ({
    height = 400,
    message = "Loading chart...",
}) => (
    <div 
        className="flex items-center justify-center bg-neutral-50 border border-neutral-200 rounded-lg"
        style={{ height }}
    >
        <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-3"></div>
            <p className="text-neutral-600">{message}</p>
        </div>
    </div>
)

/**
 * Chart Error Component
 * 
 * @description Standalone error component for charts
 */
export const ChartError: React.FC<{ 
    height?: number; 
    error: string; 
    onRetry?: () => void 
}> = ({
    height = 400,
    error,
    onRetry,
}) => (
    <div 
        className="flex items-center justify-center bg-danger-50 border border-danger-200 rounded-lg"
        style={{ height }}
    >
        <div className="text-center">
            <div className="text-danger-600 text-lg mb-2">⚠️</div>
            <p className="text-danger-700 font-medium">Chart Error</p>
            <p className="text-danger-600 text-sm mt-1 mb-3">{error}</p>
            {onRetry && (
                <button
                    onClick={onRetry}
                    className="px-4 py-2 bg-danger-600 text-white rounded-lg hover:bg-danger-700 transition-colors"
                >
                    Retry
                </button>
            )}
        </div>
    </div>
)