/**
 * Card component for displaying content in containers
 *
 * @description Flexible card component with header, content, and footer
 * sections. Provides consistent styling and structure for displaying
 * analysis results, metrics, and other content throughout the application.
 */

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import { Tooltip } from "./tooltip"
import { getMetricExplanation, formatExplanationForTooltip } from "@/lib/metrics-explanations"

const cardVariants = cva("rounded-lg border bg-white text-neutral-950 shadow-sm", {
    variants: {
        variant: {
            default: "border-neutral-200",
            outlined: "border-neutral-300",
            elevated: "border-neutral-200 shadow-md",
            accent: "border-l-4 border-l-primary-500 border-t-neutral-200 border-r-neutral-200 border-b-neutral-200",
            success: "border-l-4 border-l-success-500 border-t-neutral-200 border-r-neutral-200 border-b-neutral-200",
            warning: "border-l-4 border-l-warning-500 border-t-neutral-200 border-r-neutral-200 border-b-neutral-200",
            danger: "border-l-4 border-l-danger-500 border-t-neutral-200 border-r-neutral-200 border-b-neutral-200",
        },
        size: {
            default: "p-6",
            sm: "p-4",
            lg: "p-8",
            xl: "p-10",
        },
    },
    defaultVariants: {
        variant: "default",
        size: "default",
    },
})

export interface CardProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof cardVariants> {}

/**
 * Main Card component
 *
 * @param props - Card props including variant and size
 * @returns JSX div element with card styling
 *
 * @example
 * ```tsx
 * <Card variant="elevated" size="lg">
 *   <CardHeader>
 *     <CardTitle>Analysis Results</CardTitle>
 *     <CardDescription>Technical indicators for AAPL</CardDescription>
 *   </CardHeader>
 *   <CardContent>
 *     Content goes here
 *   </CardContent>
 * </Card>
 * ```
 */
const Card = React.forwardRef<HTMLDivElement, CardProps>(({ className, variant, size, ...props }, ref) => (
    <div ref={ref} className={cn(cardVariants({ variant, size, className }))} {...props} />
))
Card.displayName = "Card"

/**
 * Card Header component for titles and descriptions
 */
const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
    ({ className, ...props }, ref) => (
        <div
            ref={ref}
            className={cn("flex flex-col space-y-1.5 pb-4 border-b border-neutral-100 mb-4", className)}
            {...props}
        />
    ),
)
CardHeader.displayName = "CardHeader"

/**
 * Card Title component
 */
const CardTitle = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLHeadingElement>>(
    ({ className, ...props }, ref) => (
        <h3
            ref={ref}
            className={cn("text-lg font-semibold leading-none tracking-tight text-neutral-900", className)}
            {...props}
        />
    ),
)
CardTitle.displayName = "CardTitle"

/**
 * Card Description component
 */
const CardDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
    ({ className, ...props }, ref) => <p ref={ref} className={cn("text-sm text-neutral-600", className)} {...props} />,
)
CardDescription.displayName = "CardDescription"

/**
 * Card Content component for main content area
 */
const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
    ({ className, ...props }, ref) => <div ref={ref} className={cn("", className)} {...props} />,
)
CardContent.displayName = "CardContent"

/**
 * Card Footer component for actions and additional content
 */
const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
    ({ className, ...props }, ref) => (
        <div
            ref={ref}
            className={cn("flex items-center pt-4 border-t border-neutral-100 mt-4", className)}
            {...props}
        />
    ),
)
CardFooter.displayName = "CardFooter"

/**
 * Metric Card component for displaying key metrics
 */
export interface MetricCardProps extends CardProps {
    title: string
    value: string | number
    change?: {
        value: number
        type: "increase" | "decrease"
        timeframe?: string
    }
    status?: "positive" | "negative" | "neutral"
    description?: string
    icon?: React.ReactNode
    /** Tooltip configuration for metric explanation */
    tooltip?:
        | {
              category: "technical" | "pattern" | "volatility" | "ml" | "integrated" | "category"
              metricKey: string
          }
        | {
              content: string
          }
}

/**
 * Specialized card for displaying metrics with values and changes
 *
 * @param props - MetricCard props including title, value, and change data
 * @returns JSX card element optimized for metric display
 *
 * @example
 * ```tsx
 * <MetricCard
 *   title="Current Price"
 *   value="$150.25"
 *   change={{ value: 2.5, type: "increase", timeframe: "today" }}
 *   status="positive"
 *   description="Last updated 5 minutes ago"
 * />
 * ```
 */
const MetricCard = React.forwardRef<HTMLDivElement, MetricCardProps>(
    ({ title, value, change, status, description, icon, tooltip, className, ...props }, ref) => {
        const getStatusVariant = () => {
            if (status === "positive") return "success"
            if (status === "negative") return "danger"
            return "default"
        }

        const getChangeColor = () => {
            if (change?.type === "increase") return "text-success-600"
            if (change?.type === "decrease") return "text-danger-600"
            return "text-neutral-600"
        }

        const getTooltipContent = () => {
            if (!tooltip) return null

            if ("content" in tooltip) {
                return tooltip.content
            }

            const explanation = getMetricExplanation(tooltip.category, tooltip.metricKey)
            return explanation ? formatExplanationForTooltip(explanation) : null
        }

        const cardContent = (
            <Card ref={ref} variant={getStatusVariant()} className={cn("", className)} {...props}>
                <div className="flex items-start justify-between">
                    <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                            {icon && <span className="text-neutral-600">{icon}</span>}
                            <p className="text-sm font-medium text-neutral-600">{title}</p>
                        </div>

                        <p className="text-2xl font-bold text-neutral-900 mb-1">{value}</p>

                        {change && (
                            <div className="flex items-center space-x-1">
                                <span className={cn("text-xs font-medium", getChangeColor())}>
                                    {change.type === "increase" ? "↑" : "↓"} {Math.abs(change.value)}%
                                </span>
                                {change.timeframe && (
                                    <span className="text-xs text-neutral-500">{change.timeframe}</span>
                                )}
                            </div>
                        )}

                        {description && <p className="text-xs text-neutral-500 mt-2">{description}</p>}
                    </div>
                </div>
            </Card>
        )

        const tooltipContent = getTooltipContent()

        if (!tooltipContent) {
            return cardContent
        }

        return (
            <Tooltip content={<div className="max-w-xs text-xs whitespace-pre-line">{tooltipContent}</div>}>
                {cardContent}
            </Tooltip>
        )
    },
)
MetricCard.displayName = "MetricCard"

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent, MetricCard, cardVariants }
