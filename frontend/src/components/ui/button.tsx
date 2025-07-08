/**
 * Button component with multiple variants and sizes
 *
 * @description Customizable button component built with class-variance-authority
 * for consistent styling across the application. Supports multiple variants,
 * sizes, and states including loading and disabled states.
 */

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
    "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
    {
        variants: {
            variant: {
                default: "bg-primary-600 text-white hover:bg-primary-700 focus-visible:ring-primary-500",
                destructive: "bg-danger-600 text-white hover:bg-danger-700 focus-visible:ring-danger-500",
                outline:
                    "border border-neutral-300 bg-transparent text-neutral-900 hover:bg-neutral-50 focus-visible:ring-neutral-500",
                secondary: "bg-neutral-200 text-neutral-900 hover:bg-neutral-300 focus-visible:ring-neutral-500",
                ghost: "text-neutral-900 hover:bg-neutral-100 focus-visible:ring-neutral-500",
                link: "text-primary-600 underline-offset-4 hover:underline focus-visible:ring-primary-500",
                success: "bg-success-600 text-white hover:bg-success-700 focus-visible:ring-success-500",
                warning: "bg-warning-600 text-white hover:bg-warning-700 focus-visible:ring-warning-500",
            },
            size: {
                default: "h-10 px-4 py-2",
                sm: "h-9 rounded-md px-3",
                lg: "h-11 rounded-md px-8",
                xl: "h-12 rounded-md px-10 text-base",
                icon: "h-10 w-10",
            },
        },
        defaultVariants: {
            variant: "default",
            size: "default",
        },
    },
)

export interface ButtonProps
    extends React.ButtonHTMLAttributes<HTMLButtonElement>,
        VariantProps<typeof buttonVariants> {
    /**
     * Whether the button is in a loading state
     */
    isLoading?: boolean
    /**
     * Loading text to display when isLoading is true
     */
    loadingText?: string
    /**
     * Icon to display at the start of the button
     */
    startIcon?: React.ReactNode
    /**
     * Icon to display at the end of the button
     */
    endIcon?: React.ReactNode
}

/**
 * Button component with variants and loading states
 *
 * @param props - Button props including variant, size, loading state, and icons
 * @returns JSX button element with proper styling and behavior
 *
 * @example
 * ```tsx
 * <Button variant="default" size="lg">
 *   Click me
 * </Button>
 *
 * <Button variant="outline" isLoading loadingText="Analyzing...">
 *   Analyze Stock
 * </Button>
 *
 * <Button variant="ghost" startIcon={<SearchIcon />}>
 *   Search
 * </Button>
 * ```
 */
const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    (
        { className, variant, size, isLoading = false, loadingText, startIcon, endIcon, children, disabled, ...props },
        ref,
    ) => {
        const isDisabled = disabled || isLoading

        return (
            <button
                className={cn(buttonVariants({ variant, size, className }))}
                ref={ref}
                disabled={isDisabled}
                {...props}
            >
                {isLoading && (
                    <svg
                        className="mr-2 h-4 w-4 animate-spin"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                    >
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                    </svg>
                )}

                {!isLoading && startIcon && <span className="mr-2">{startIcon}</span>}

                <span>{isLoading && loadingText ? loadingText : children}</span>

                {!isLoading && endIcon && <span className="ml-2">{endIcon}</span>}
            </button>
        )
    },
)

Button.displayName = "Button"

export { Button, buttonVariants }
