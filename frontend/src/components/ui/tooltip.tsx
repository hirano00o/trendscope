/**
 * Tooltip component for displaying informative text on hover
 *
 * @description A wrapper around Radix UI Tooltip optimized for displaying
 * metric explanations and Japanese language content. Provides consistent
 * styling and accessibility features for all tooltip usage throughout the application.
 */

"use client"

import * as React from "react"
import * as TooltipPrimitive from "@radix-ui/react-tooltip"
import { cn } from "@/lib/utils"

const TooltipProvider = TooltipPrimitive.Provider

const TooltipRoot = TooltipPrimitive.Root

const TooltipTrigger = TooltipPrimitive.Trigger

const TooltipContent = React.forwardRef<
    React.ElementRef<typeof TooltipPrimitive.Content>,
    React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Content>
>(({ className, sideOffset = 4, ...props }, ref) => (
    <TooltipPrimitive.Content
        ref={ref}
        sideOffset={sideOffset}
        className={cn(
            "z-50 overflow-hidden rounded-md border bg-white px-3 py-1.5 text-sm text-neutral-950 shadow-md animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
            className,
        )}
        {...props}
    />
))
TooltipContent.displayName = TooltipPrimitive.Content.displayName

/**
 * Tooltip props interface
 */
export interface TooltipProps {
    /** The content to display in the tooltip */
    content: React.ReactNode
    /** The trigger element that shows the tooltip on hover */
    children: React.ReactNode
    /** Whether the tooltip is disabled */
    disabled?: boolean
    /** Delay before showing the tooltip (ms) */
    delayDuration?: number
    /** Side to display the tooltip */
    side?: "top" | "right" | "bottom" | "left"
    /** Alignment of the tooltip */
    align?: "start" | "center" | "end"
}

/**
 * Main Tooltip component
 *
 * @description Wrapper component that provides a simple API for showing tooltips
 * with consistent styling and behavior. Optimized for metric explanations.
 *
 * @param props - Tooltip configuration props
 * @returns JSX element with tooltip functionality
 *
 * @example
 * ```tsx
 * <Tooltip content="RSI (0-100): 70以上は買われ過ぎ、30以下は売られ過ぎを示します">
 *   <span>RSI: 75.2</span>
 * </Tooltip>
 * ```
 */
export function Tooltip({
    content,
    children,
    disabled = false,
    delayDuration = 400,
    side = "top",
    align = "center",
}: TooltipProps) {
    if (disabled) {
        return <>{children}</>
    }

    return (
        <TooltipRoot delayDuration={delayDuration}>
            <TooltipTrigger asChild>{children}</TooltipTrigger>
            <TooltipContent side={side} align={align}>
                {content}
            </TooltipContent>
        </TooltipRoot>
    )
}

export { TooltipProvider, TooltipRoot, TooltipTrigger, TooltipContent }
