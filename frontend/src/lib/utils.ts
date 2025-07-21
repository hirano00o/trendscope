/**
 * Utility functions for the Trendscope application
 *
 * @description Common utility functions including CSS class management,
 * data formatting, validation, and other helper functions used throughout
 * the application.
 */

import { type ClassValue, clsx } from "clsx"

/**
 * Combines CSS classes with conditional logic and deduplication
 *
 * @description Utility function for merging CSS classes with support for
 * conditional classes, arrays, and automatic deduplication. Built on top
 * of clsx for robust class combination.
 *
 * @param inputs - CSS classes, conditional classes, or arrays of classes
 * @returns Combined and deduplicated CSS class string
 *
 * @example
 * ```typescript
 * cn("base-class", condition && "conditional-class", ["array", "of", "classes"])
 * // Result: "base-class conditional-class array of classes"
 * ```
 */
export function cn(...inputs: ClassValue[]) {
    return clsx(inputs)
}

/**
 * Formats a number as a percentage with specified decimal places
 *
 * @param value - The numeric value to format (0.1234 = 12.34%)
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted percentage string
 *
 * @example
 * ```typescript
 * formatPercentage(0.1234) // "12.34%"
 * formatPercentage(0.1234, 1) // "12.3%"
 * ```
 */
export function formatPercentage(value: number, decimals: number = 2): string {
    return `${(value * 100).toFixed(decimals)}%`
}

/**
 * Formats a price value with proper currency formatting
 *
 * @param price - The price value to format
 * @param currency - Currency code (default: "USD")
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted price string
 *
 * @example
 * ```typescript
 * formatPrice(123.456) // "$123.46"
 * formatPrice(123.456, "EUR", 3) // "€123.456"
 * ```
 */
export function formatPrice(price: number, currency: string = "USD", decimals: number = 2): string {
    const formatter = new Intl.NumberFormat("en-US", {
        style: "currency",
        currency,
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    })
    return formatter.format(price)
}

/**
 * Formats large numbers with appropriate suffixes (K, M, B)
 *
 * @param value - The numeric value to format
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted number string with suffix
 *
 * @example
 * ```typescript
 * formatLargeNumber(1234) // "1.2K"
 * formatLargeNumber(1234567) // "1.2M"
 * formatLargeNumber(1234567890) // "1.2B"
 * ```
 */
export function formatLargeNumber(value: number, decimals: number = 1): string {
    if (value >= 1e9) {
        return `${(value / 1e9).toFixed(decimals)}B`
    }
    if (value >= 1e6) {
        return `${(value / 1e6).toFixed(decimals)}M`
    }
    if (value >= 1e3) {
        return `${(value / 1e3).toFixed(decimals)}K`
    }
    return value.toString()
}

/**
 * Calculates percentage change between two values
 *
 * @param current - Current value
 * @param previous - Previous value
 * @returns Percentage change as decimal (0.1 = 10% increase)
 *
 * @example
 * ```typescript
 * calculatePercentageChange(110, 100) // 0.1 (10% increase)
 * calculatePercentageChange(90, 100) // -0.1 (10% decrease)
 * ```
 */
export function calculatePercentageChange(current: number, previous: number): number {
    if (previous === 0) return 0
    return (current - previous) / previous
}

/**
 * Determines the color class based on a numeric value (positive/negative)
 *
 * @param value - The numeric value to evaluate
 * @param positiveColor - CSS class for positive values (default: "text-success-600")
 * @param negativeColor - CSS class for negative values (default: "text-danger-600")
 * @param neutralColor - CSS class for zero values (default: "text-neutral-600")
 * @returns Appropriate CSS color class
 *
 * @example
 * ```typescript
 * getColorClass(5.2) // "text-success-600"
 * getColorClass(-2.1) // "text-danger-600"
 * getColorClass(0) // "text-neutral-600"
 * ```
 */
export function getColorClass(
    value: number,
    positiveColor: string = "text-success-600",
    negativeColor: string = "text-danger-600",
    neutralColor: string = "text-neutral-600",
): string {
    if (value > 0) return positiveColor
    if (value < 0) return negativeColor
    return neutralColor
}

/**
 * Validates a stock symbol format for both US and Japanese markets
 *
 * @param symbol - Stock symbol to validate (US: AAPL, Japanese: 7203.T)
 * @returns True if symbol format is valid
 *
 * @example
 * ```typescript
 * isValidStockSymbol("AAPL") // true - US stock
 * isValidStockSymbol("GOOGL") // true - US stock
 * isValidStockSymbol("7203.T") // true - Japanese stock (Toyota)
 * isValidStockSymbol("6758.T") // true - Japanese stock (Sony)
 * isValidStockSymbol("invalid@") // false - invalid characters
 * isValidStockSymbol("") // false - empty
 * ```
 */
export function isValidStockSymbol(symbol: string): boolean {
    if (!symbol || symbol.length === 0) return false
    // Enhanced validation: 1-10 characters, supports US stocks (letters) and Japanese stocks (numbers.T)
    const symbolRegex = /^[A-Z0-9.-]{1,10}$/
    return symbolRegex.test(symbol.toUpperCase())
}

/**
 * Normalizes a stock symbol to uppercase and removes whitespace
 *
 * @param symbol - Stock symbol to normalize (US or Japanese format)
 * @returns Normalized stock symbol
 *
 * @example
 * ```typescript
 * normalizeStockSymbol("  aapl  ") // "AAPL"
 * normalizeStockSymbol("googl") // "GOOGL"
 * normalizeStockSymbol(" 7203.t ") // "7203.T"
 * normalizeStockSymbol("6758.T") // "6758.T"
 * ```
 */
export function normalizeStockSymbol(symbol: string): string {
    return symbol.trim().toUpperCase()
}

/**
 * Generates a confidence level description based on numeric confidence
 *
 * @param confidence - Confidence value between 0 and 1
 * @returns Human-readable confidence description
 *
 * @example
 * ```typescript
 * getConfidenceDescription(0.9) // "Very High"
 * getConfidenceDescription(0.6) // "Moderate"
 * getConfidenceDescription(0.3) // "Low"
 * ```
 */
export function getConfidenceDescription(confidence: number): string {
    if (confidence >= 0.8) return "Very High"
    if (confidence >= 0.7) return "High"
    if (confidence >= 0.5) return "Moderate"
    if (confidence >= 0.3) return "Low"
    return "Very Low"
}

/**
 * Converts signal strength to visual indicator
 *
 * @param strength - Signal strength between 0 and 1
 * @param type - Signal type ("bullish" | "bearish" | "neutral")
 * @returns Object with color, text, and icon properties for UI display
 *
 * @example
 * ```typescript
 * getSignalIndicator(0.8, "bullish")
 * // { color: "text-success-600", text: "Strong Bullish", icon: "↑" }
 * ```
 */
export function getSignalIndicator(strength: number, type: "bullish" | "bearish" | "neutral") {
    if (type === "neutral") {
        return {
            color: "text-neutral-600",
            text: "Neutral",
            icon: "→",
        }
    }

    const isStrong = strength >= 0.7
    const isBullish = type === "bullish"

    return {
        color: isBullish ? "text-success-600" : "text-danger-600",
        text: `${isStrong ? "Strong " : ""}${isBullish ? "Bullish" : "Bearish"}`,
        icon: isBullish ? "↑" : "↓",
    }
}

/**
 * Debounce function for limiting API calls
 *
 * @param func - Function to debounce
 * @param wait - Wait time in milliseconds
 * @returns Debounced function
 *
 * @example
 * ```typescript
 * const debouncedSearch = debounce(searchFunction, 300)
 * ```
 */
export function debounce<T extends (...args: any[]) => any>(func: T, wait: number): (...args: Parameters<T>) => void {
    let timeout: NodeJS.Timeout | null = null

    return (...args: Parameters<T>) => {
        if (timeout) clearTimeout(timeout)
        timeout = setTimeout(() => func(...args), wait)
    }
}
