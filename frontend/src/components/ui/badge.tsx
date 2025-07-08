/**
 * Badge component for displaying status indicators and labels
 *
 * @description Flexible badge component with multiple variants for
 * displaying status, signals, and categorical information throughout
 * the application. Supports different sizes and interactive states.
 */

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
    "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
    {
        variants: {
            variant: {
                default: "border-transparent bg-primary-100 text-primary-800 hover:bg-primary-200",
                secondary: "border-transparent bg-neutral-100 text-neutral-800 hover:bg-neutral-200",
                destructive: "border-transparent bg-danger-100 text-danger-800 hover:bg-danger-200",
                success: "border-transparent bg-success-100 text-success-800 hover:bg-success-200",
                warning: "border-transparent bg-warning-100 text-warning-800 hover:bg-warning-200",
                outline: "border-neutral-300 text-neutral-700 hover:bg-neutral-50",

                // Signal-specific variants
                bullish: "border-transparent bg-success-100 text-success-800",
                bearish: "border-transparent bg-danger-100 text-danger-800",
                neutral: "border-transparent bg-neutral-100 text-neutral-800",

                // Signal strength variants
                "strong-bullish": "border-transparent bg-success-600 text-white",
                "strong-bearish": "border-transparent bg-danger-600 text-white",

                // Risk level variants
                "low-risk": "border-transparent bg-success-50 text-success-700 border-success-200",
                "moderate-risk": "border-transparent bg-warning-50 text-warning-700 border-warning-200",
                "high-risk": "border-transparent bg-danger-50 text-danger-700 border-danger-200",
            },
            size: {
                default: "px-2.5 py-0.5 text-xs",
                sm: "px-2 py-0.5 text-xs",
                lg: "px-3 py-1 text-sm",
                xl: "px-4 py-1.5 text-sm",
            },
        },
        defaultVariants: {
            variant: "default",
            size: "default",
        },
    },
)

// Base props shared by both variants
interface BaseBadgeProps extends VariantProps<typeof badgeVariants> {
    /**
     * Icon to display before the badge text
     */
    icon?: React.ReactNode
    /**
     * Whether the badge is interactive/clickable
     */
    interactive?: boolean
}

// Badge as div (non-interactive)
export interface BadgeAsDivProps extends React.HTMLAttributes<HTMLDivElement>, BaseBadgeProps {
    interactive?: false
}

// Badge as button (interactive)
export interface BadgeAsButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, BaseBadgeProps {
    interactive: true
}

// Union type for all badge props
export type BadgeProps = BadgeAsDivProps | BadgeAsButtonProps

/**
 * Badge component for status and label display
 *
 * @param props - Badge props including variant, size, and interactive state
 * @returns JSX element with badge styling (div or button based on interactive prop)
 *
 * @example
 * ```tsx
 * <Badge variant="success">Bullish</Badge>
 * <Badge variant="warning" size="lg">Moderate Risk</Badge>
 * <Badge variant="outline" interactive>Click me</Badge>
 * <Badge variant="strong-bullish" icon={<ArrowUpIcon />}>
 *   Strong Buy Signal
 * </Badge>
 * ```
 */
const Badge = React.forwardRef<HTMLDivElement | HTMLButtonElement, BadgeProps>(
    ({ className, variant, size, icon, interactive = false, children, ...props }, ref) => {
        if (interactive) {
            const buttonProps = props as React.ButtonHTMLAttributes<HTMLButtonElement>
            return (
                <button
                    ref={ref as React.Ref<HTMLButtonElement>}
                    className={cn(
                        badgeVariants({ variant, size }),
                        "cursor-pointer hover:scale-105 active:scale-95 transition-transform",
                        className,
                    )}
                    {...buttonProps}
                >
                    {icon && <span className="mr-1">{icon}</span>}
                    {children}
                </button>
            )
        } else {
            const divProps = props as React.HTMLAttributes<HTMLDivElement>
            return (
                <div
                    ref={ref as React.Ref<HTMLDivElement>}
                    className={cn(badgeVariants({ variant, size }), className)}
                    {...divProps}
                >
                    {icon && <span className="mr-1">{icon}</span>}
                    {children}
                </div>
            )
        }
    },
)
Badge.displayName = "Badge"

/**
 * Signal Badge component for displaying trading signals
 */
export interface SignalBadgeProps extends Omit<BadgeAsDivProps, "variant" | "interactive"> {
    signal: "bullish" | "bearish" | "neutral" | "strong-bullish" | "strong-bearish"
    strength?: number
    showIcon?: boolean
}

/**
 * Specialized badge for displaying trading signals with appropriate styling
 *
 * @param props - Signal badge props including signal type and strength
 * @returns JSX badge element optimized for signal display
 *
 * @example
 * ```tsx
 * <SignalBadge signal="bullish" strength={0.75} showIcon />
 * <SignalBadge signal="strong-bearish" size="lg" />
 * <SignalBadge signal="neutral" />
 * ```
 */
const SignalBadge = React.forwardRef<HTMLDivElement, SignalBadgeProps>(
    ({ signal, strength, showIcon = true, children, ...props }, ref) => {
        const getSignalText = () => {
            if (children) return children

            switch (signal) {
                case "strong-bullish":
                    return "Strong Bullish"
                case "bullish":
                    return "Bullish"
                case "neutral":
                    return "Neutral"
                case "bearish":
                    return "Bearish"
                case "strong-bearish":
                    return "Strong Bearish"
                default:
                    return signal
            }
        }

        const getSignalIcon = () => {
            if (!showIcon) return null

            switch (signal) {
                case "strong-bullish":
                    return <span className="text-xs">⬆⬆</span>
                case "bullish":
                    return <span className="text-xs">↑</span>
                case "neutral":
                    return <span className="text-xs">→</span>
                case "bearish":
                    return <span className="text-xs">↓</span>
                case "strong-bearish":
                    return <span className="text-xs">⬇⬇</span>
                default:
                    return null
            }
        }

        return (
            <Badge ref={ref} variant={signal} icon={getSignalIcon()} interactive={false} {...props}>
                {getSignalText()}
                {strength && <span className="ml-1 opacity-75">({(strength * 100).toFixed(0)}%)</span>}
            </Badge>
        )
    },
)
SignalBadge.displayName = "SignalBadge"

/**
 * Risk Badge component for displaying risk levels
 */
export interface RiskBadgeProps extends Omit<BadgeAsDivProps, "variant" | "interactive"> {
    risk: "low" | "moderate" | "high"
}

/**
 * Specialized badge for displaying risk levels with appropriate color coding
 *
 * @param props - Risk badge props including risk level
 * @returns JSX badge element optimized for risk display
 *
 * @example
 * ```tsx
 * <RiskBadge risk="low" />
 * <RiskBadge risk="moderate" size="lg" />
 * <RiskBadge risk="high" />
 * ```
 */
const RiskBadge = React.forwardRef<HTMLDivElement, RiskBadgeProps>(({ risk, children, ...props }, ref) => {
    const getRiskVariant = () => {
        switch (risk) {
            case "low":
                return "low-risk"
            case "moderate":
                return "moderate-risk"
            case "high":
                return "high-risk"
            default:
                return "secondary"
        }
    }

    const getRiskText = () => {
        if (children) return children

        switch (risk) {
            case "low":
                return "Low Risk"
            case "moderate":
                return "Moderate Risk"
            case "high":
                return "High Risk"
            default:
                return risk
        }
    }

    return (
        <Badge ref={ref} variant={getRiskVariant()} interactive={false} {...props}>
            {getRiskText()}
        </Badge>
    )
})
RiskBadge.displayName = "RiskBadge"

export { Badge, SignalBadge, RiskBadge, badgeVariants }
