/**
 * Progress component for displaying loading and completion states
 *
 * @description Customizable progress component built on Radix UI primitives
 * with support for different variants, sizes, and label display options.
 * Used for showing analysis progress and confidence levels.
 */

import * as React from "react"
import * as ProgressPrimitive from "@radix-ui/react-progress"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const progressVariants = cva("relative h-4 w-full overflow-hidden rounded-full bg-neutral-200", {
    variants: {
        variant: {
            default: "[&>div]:bg-primary-600",
            success: "[&>div]:bg-success-600",
            warning: "[&>div]:bg-warning-600",
            danger: "[&>div]:bg-danger-600",
            neutral: "[&>div]:bg-neutral-600",
        },
        size: {
            default: "h-4",
            sm: "h-2",
            lg: "h-6",
            xl: "h-8",
        },
    },
    defaultVariants: {
        variant: "default",
        size: "default",
    },
})

export interface ProgressProps
    extends React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root>,
        VariantProps<typeof progressVariants> {
    /**
     * Progress value as percentage (0-100)
     */
    value?: number
    /**
     * Maximum value for progress calculation
     */
    max?: number
    /**
     * Whether to show the percentage label
     */
    showLabel?: boolean
    /**
     * Custom label text (overrides percentage)
     */
    label?: string
    /**
     * Label position
     */
    labelPosition?: "top" | "bottom" | "inline"
    /**
     * Whether to animate the progress bar
     */
    animated?: boolean
}

/**
 * Progress component with customizable styling and labeling
 *
 * @param props - Progress props including value, variant, size, and labeling options
 * @returns JSX progress element with proper accessibility and styling
 *
 * @example
 * ```tsx
 * <Progress
 *   value={75}
 *   variant="success"
 *   showLabel
 *   labelPosition="top"
 * />
 *
 * <Progress
 *   value={45}
 *   variant="warning"
 *   label="Confidence Level"
 *   size="lg"
 * />
 *
 * <Progress
 *   value={85}
 *   variant="default"
 *   animated
 *   showLabel
 * />
 * ```
 */
const Progress = React.forwardRef<React.ElementRef<typeof ProgressPrimitive.Root>, ProgressProps>(
    (
        {
            className,
            variant,
            size,
            value = 0,
            max = 100,
            showLabel = false,
            label,
            labelPosition = "top",
            animated = false,
            ...props
        },
        ref,
    ) => {
        const percentage = Math.min(Math.max((value / max) * 100, 0), 100)
        const displayLabel = label || (showLabel ? `${percentage.toFixed(0)}%` : undefined)

        return (
            <div className="w-full">
                {displayLabel && labelPosition === "top" && (
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-neutral-700">{displayLabel}</span>
                        {showLabel && !label && (
                            <span className="text-sm text-neutral-500">{percentage.toFixed(1)}%</span>
                        )}
                    </div>
                )}

                <div className="relative">
                    <ProgressPrimitive.Root
                        ref={ref}
                        className={cn(progressVariants({ variant, size, className }))}
                        value={percentage}
                        max={100}
                        {...props}
                    >
                        <ProgressPrimitive.Indicator
                            className={cn(
                                "h-full w-full flex-1 transition-all duration-300",
                                animated && "animate-pulse-fast",
                            )}
                            style={{ transform: `translateX(-${100 - percentage}%)` }}
                        />
                    </ProgressPrimitive.Root>

                    {displayLabel && labelPosition === "inline" && (
                        <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-xs font-medium text-white mix-blend-difference">{displayLabel}</span>
                        </div>
                    )}
                </div>

                {displayLabel && labelPosition === "bottom" && (
                    <div className="flex justify-between items-center mt-2">
                        <span className="text-sm font-medium text-neutral-700">{displayLabel}</span>
                        {showLabel && !label && (
                            <span className="text-sm text-neutral-500">{percentage.toFixed(1)}%</span>
                        )}
                    </div>
                )}
            </div>
        )
    },
)
Progress.displayName = "Progress"

/**
 * Confidence Level Progress component
 * Specialized progress bar for displaying confidence levels with color coding
 */
export interface ConfidenceProgressProps extends Omit<ProgressProps, "variant"> {
    confidence: number
}

/**
 * Specialized progress component for confidence levels
 * Automatically determines color based on confidence value
 *
 * @param props - Confidence progress props
 * @returns JSX progress element optimized for confidence display
 *
 * @example
 * ```tsx
 * <ConfidenceProgress
 *   confidence={0.85}
 *   showLabel
 *   labelPosition="top"
 * />
 * ```
 */
const ConfidenceProgress = React.forwardRef<React.ElementRef<typeof ProgressPrimitive.Root>, ConfidenceProgressProps>(
    ({ confidence, ...props }, ref) => {
        const getVariant = (conf: number) => {
            if (conf >= 0.8) return "success"
            if (conf >= 0.6) return "default"
            if (conf >= 0.4) return "warning"
            return "danger"
        }

        const getConfidenceLabel = (conf: number) => {
            if (conf >= 0.8) return "High Confidence"
            if (conf >= 0.6) return "Moderate Confidence"
            if (conf >= 0.4) return "Low Confidence"
            return "Very Low Confidence"
        }

        return (
            <Progress
                ref={ref}
                variant={getVariant(confidence)}
                value={confidence * 100}
                label={props.label || getConfidenceLabel(confidence)}
                {...props}
            />
        )
    },
)
ConfidenceProgress.displayName = "ConfidenceProgress"

export { Progress, ConfidenceProgress, progressVariants }
