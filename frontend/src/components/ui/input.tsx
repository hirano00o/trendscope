/**
 * Input component with validation states and styling
 *
 * @description Customizable input component with support for different
 * variants, sizes, validation states, and icons. Built with consistent
 * styling to match the application's design system.
 */

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const inputVariants = cva(
    "flex w-full rounded-md border bg-white px-3 py-2 text-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-neutral-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
    {
        variants: {
            variant: {
                default: "border-neutral-300 focus-visible:border-primary-500 focus-visible:ring-primary-500",
                error: "border-danger-500 focus-visible:border-danger-500 focus-visible:ring-danger-500",
                success: "border-success-500 focus-visible:border-success-500 focus-visible:ring-success-500",
                warning: "border-warning-500 focus-visible:border-warning-500 focus-visible:ring-warning-500",
            },
            size: {
                default: "h-10",
                sm: "h-9",
                lg: "h-11 px-4 py-3",
                xl: "h-12 px-4 py-3 text-base",
            },
        },
        defaultVariants: {
            variant: "default",
            size: "default",
        },
    },
)

export interface InputProps
    extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "size">,
        VariantProps<typeof inputVariants> {
    /**
     * Icon to display at the start of the input
     */
    startIcon?: React.ReactNode
    /**
     * Icon to display at the end of the input
     */
    endIcon?: React.ReactNode
    /**
     * Error message to display below the input
     */
    error?: string
    /**
     * Helper text to display below the input
     */
    helperText?: string
    /**
     * Label for the input
     */
    label?: string
    /**
     * Whether the label should be visually hidden (still accessible to screen readers)
     */
    hiddenLabel?: boolean
}

/**
 * Input component with validation and icons
 *
 * @param props - Input props including variant, size, validation, and icons
 * @returns JSX input element with proper styling and validation display
 *
 * @example
 * ```tsx
 * <Input
 *   label="Stock Symbol"
 *   placeholder="Enter symbol (e.g., AAPL)"
 *   variant="default"
 * />
 *
 * <Input
 *   variant="error"
 *   error="Invalid stock symbol"
 *   startIcon={<SearchIcon />}
 * />
 *
 * <Input
 *   size="lg"
 *   helperText="Enter a valid stock symbol"
 * />
 * ```
 */
const Input = React.forwardRef<HTMLInputElement, InputProps>(
    (
        {
            className,
            variant,
            size,
            startIcon,
            endIcon,
            error,
            helperText,
            label,
            hiddenLabel = false,
            type = "text",
            id,
            ...props
        },
        ref,
    ) => {
        const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`
        const hasError = error && error.length > 0
        const finalVariant = hasError ? "error" : variant

        return (
            <div className="w-full">
                {label && (
                    <label
                        htmlFor={inputId}
                        className={cn("block text-sm font-medium text-neutral-700 mb-1", hiddenLabel && "sr-only")}
                    >
                        {label}
                    </label>
                )}

                <div className="relative">
                    {startIcon && (
                        <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-400">
                            {startIcon}
                        </div>
                    )}

                    <input
                        type={type}
                        id={inputId}
                        className={cn(
                            inputVariants({ variant: finalVariant, size }),
                            startIcon && "pl-10",
                            endIcon && "pr-10",
                            className,
                        )}
                        ref={ref}
                        {...props}
                    />

                    {endIcon && (
                        <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-neutral-400">
                            {endIcon}
                        </div>
                    )}
                </div>

                {(error || helperText) && (
                    <div className="mt-1">
                        {error && <p className="text-sm text-danger-600">{error}</p>}
                        {!error && helperText && <p className="text-sm text-neutral-600">{helperText}</p>}
                    </div>
                )}
            </div>
        )
    },
)

Input.displayName = "Input"

export { Input, inputVariants }
