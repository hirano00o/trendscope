/**
 * API client and service functions for Trendscope backend integration
 *
 * @description Centralized API client with error handling, retry logic,
 * and type-safe methods for interacting with the Trendscope backend.
 * Includes comprehensive analysis endpoints and error management.
 */

import { AnalysisData, AnalysisResponse, HistoricalDataResponse, HistoricalApiResponse } from "@/types/analysis"

/**
 * Base API configuration
 */
const API_CONFIG = {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    timeout: 30000, // 30 seconds for analysis requests
    retries: 3,
} as const

/**
 * Custom API error class with additional context
 */
export class ApiError extends Error {
    constructor(
        public status: number,
        message: string,
        public data?: any,
    ) {
        super(message)
        this.name = "ApiError"
    }
}

/**
 * HTTP client with error handling and retry logic
 *
 * @param endpoint - API endpoint path
 * @param options - Fetch options
 * @returns Promise resolving to parsed JSON response
 * @throws {ApiError} When request fails or returns error status
 *
 * @example
 * ```typescript
 * const data = await apiClient("/api/v1/health")
 * const result = await apiClient("/api/v1/analyze/AAPL", { method: "POST" })
 * ```
 */
async function apiClient<T = any>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_CONFIG.baseUrl}${endpoint}`

    const config: RequestInit = {
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
        ...options,
    }

    let lastError: Error | null = null

    // Retry logic
    for (let attempt = 1; attempt <= API_CONFIG.retries; attempt++) {
        try {
            const controller = new AbortController()
            const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeout)

            const response = await fetch(url, {
                ...config,
                signal: controller.signal,
            })

            clearTimeout(timeoutId)

            if (!response.ok) {
                let errorData
                try {
                    errorData = await response.json()
                } catch {
                    errorData = { message: response.statusText }
                }

                throw new ApiError(
                    response.status,
                    errorData.message || `HTTP ${response.status}: ${response.statusText}`,
                    errorData,
                )
            }

            const data = await response.json()
            return data
        } catch (error) {
            lastError = error as Error

            // Don't retry on client errors (4xx) except for specific cases
            if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
                if (error.status !== 408 && error.status !== 429) {
                    // Don't retry except for timeout and rate limit
                    throw error
                }
            }

            // Wait before retry (exponential backoff)
            if (attempt < API_CONFIG.retries) {
                const delay = Math.min(1000 * Math.pow(2, attempt - 1), 5000)
                await new Promise((resolve) => setTimeout(resolve, delay))
            }
        }
    }

    throw lastError || new Error("Request failed after all retries")
}

/**
 * API service functions for stock analysis
 */
export const analysisApi = {
    /**
     * Performs comprehensive 6-category analysis for a stock symbol
     *
     * @param symbol - Stock symbol to analyze (e.g., "AAPL", "GOOGL")
     * @returns Promise resolving to comprehensive analysis data
     * @throws {ApiError} When analysis fails or symbol is invalid
     *
     * @example
     * ```typescript
     * const analysis = await analysisApi.getComprehensiveAnalysis("AAPL")
     * console.log(analysis.integrated_score.overall_score)
     * ```
     */
    async getComprehensiveAnalysis(symbol: string): Promise<AnalysisData> {
        const normalizedSymbol = symbol.trim().toUpperCase()

        if (!normalizedSymbol || normalizedSymbol.length === 0) {
            throw new ApiError(400, "Stock symbol is required")
        }

        const response = await apiClient<AnalysisResponse>(`/api/v1/comprehensive/${normalizedSymbol}`)

        if (!response.success || !response.data) {
            throw new ApiError(500, response.error?.message || "Analysis failed", response.error)
        }

        return response.data
    },

    /**
     * Gets technical analysis only for a stock symbol
     *
     * @param symbol - Stock symbol to analyze
     * @returns Promise resolving to technical analysis data
     * @throws {ApiError} When analysis fails
     *
     * @example
     * ```typescript
     * const technical = await analysisApi.getTechnicalAnalysis("AAPL")
     * console.log(technical.indicators.rsi)
     * ```
     */
    async getTechnicalAnalysis(symbol: string) {
        const normalizedSymbol = symbol.trim().toUpperCase()
        return apiClient(`/api/v1/technical/${normalizedSymbol}`)
    },

    /**
     * Gets pattern analysis only for a stock symbol
     *
     * @param symbol - Stock symbol to analyze
     * @returns Promise resolving to pattern analysis data
     * @throws {ApiError} When analysis fails
     */
    async getPatternAnalysis(symbol: string) {
        const normalizedSymbol = symbol.trim().toUpperCase()
        return apiClient(`/api/v1/patterns/${normalizedSymbol}`)
    },

    /**
     * Gets volatility analysis only for a stock symbol
     *
     * @param symbol - Stock symbol to analyze
     * @returns Promise resolving to volatility analysis data
     * @throws {ApiError} When analysis fails
     */
    async getVolatilityAnalysis(symbol: string) {
        const normalizedSymbol = symbol.trim().toUpperCase()
        return apiClient(`/api/v1/volatility/${normalizedSymbol}`)
    },

    /**
     * Gets ML predictions only for a stock symbol
     *
     * @param symbol - Stock symbol to analyze
     * @returns Promise resolving to ML prediction data
     * @throws {ApiError} When analysis fails
     */
    async getMLAnalysis(symbol: string) {
        const normalizedSymbol = symbol.trim().toUpperCase()
        return apiClient(`/api/v1/ml/${normalizedSymbol}`)
    },

    /**
     * Gets historical stock price data (OHLCV) for chart display
     *
     * @param symbol - Stock symbol to get data for (e.g., "AAPL", "7203.T")
     * @param period - Time period (optional, defaults to "1mo")
     * @param startDate - Custom start date (optional)
     * @param endDate - Custom end date (optional)
     * @returns Promise resolving to historical price data
     * @throws {ApiError} When data retrieval fails
     *
     * @example
     * ```typescript
     * const historical = await analysisApi.getHistoricalData("AAPL", "1mo")
     * console.log(historical.historical_data.length) // Number of data points
     * 
     * const customRange = await analysisApi.getHistoricalData("AAPL", undefined, "2024-01-01", "2024-01-31")
     * console.log(customRange.metadata.current_price)
     * ```
     */
    async getHistoricalData(
        symbol: string,
        period?: string,
        startDate?: string,
        endDate?: string
    ): Promise<HistoricalDataResponse> {
        const normalizedSymbol = symbol.trim().toUpperCase()

        if (!normalizedSymbol || normalizedSymbol.length === 0) {
            throw new ApiError(400, "Stock symbol is required")
        }

        // Build query parameters
        const params = new URLSearchParams()
        if (period) {
            params.append("period", period)
        }
        if (startDate) {
            params.append("start_date", startDate)
        }
        if (endDate) {
            params.append("end_date", endDate)
        }

        const queryString = params.toString()
        const endpoint = `/api/v1/historical/${normalizedSymbol}${queryString ? `?${queryString}` : ""}`

        const response = await apiClient<HistoricalApiResponse>(endpoint)

        if (!response.success || !response.data) {
            throw new ApiError(500, response.error?.message || "Historical data retrieval failed", response.error)
        }

        return response.data
    },

    /**
     * Checks API health status
     *
     * @returns Promise resolving to health check data
     * @throws {ApiError} When health check fails
     *
     * @example
     * ```typescript
     * const health = await analysisApi.checkHealth()
     * console.log(health.status) // "ok"
     * ```
     */
    async checkHealth() {
        return apiClient("/health")
    },
}

/**
 * Utility functions for API error handling
 */
export const apiUtils = {
    /**
     * Checks if an error is an API error
     *
     * @param error - Error to check
     * @returns True if error is an ApiError instance
     */
    isApiError(error: any): error is ApiError {
        return error instanceof ApiError
    },

    /**
     * Gets user-friendly error message from API error
     *
     * @param error - Error to process
     * @returns User-friendly error message
     *
     * @example
     * ```typescript
     * try {
     *   await analysisApi.getComprehensiveAnalysis("INVALID")
     * } catch (error) {
     *   const message = apiUtils.getErrorMessage(error)
     *   console.log(message) // "Invalid stock symbol"
     * }
     * ```
     */
    getErrorMessage(error: any): string {
        if (error instanceof ApiError) {
            // Map specific error codes to user-friendly messages
            switch (error.status) {
                case 400:
                    return "Invalid stock symbol. Please check the symbol and try again."
                case 404:
                    return "Stock symbol not found. Please verify the symbol is correct."
                case 429:
                    return "Too many requests. Please wait a moment and try again."
                case 500:
                    return "Analysis service is temporarily unavailable. Please try again later."
                case 503:
                    return "Service is currently under maintenance. Please try again later."
                default:
                    return error.message || "An unexpected error occurred."
            }
        }

        if (error?.name === "AbortError") {
            return "Request timed out. Please try again."
        }

        if (error?.message?.includes("fetch")) {
            return "Unable to connect to the analysis service. Please check your connection."
        }

        return error?.message || "An unexpected error occurred."
    },

    /**
     * Determines if an error is retryable
     *
     * @param error - Error to check
     * @returns True if error should be retried
     */
    isRetryableError(error: any): boolean {
        if (error instanceof ApiError) {
            // Retry on server errors and specific client errors
            return error.status >= 500 || error.status === 408 || error.status === 429
        }

        // Retry on network errors
        return error?.name === "TypeError" || error?.message?.includes("fetch")
    },

    /**
     * Creates query key for TanStack Query
     *
     * @param endpoint - API endpoint
     * @param params - Query parameters
     * @returns Array for use as query key
     *
     * @example
     * ```typescript
     * const queryKey = apiUtils.createQueryKey("comprehensive", { symbol: "AAPL" })
     * // Result: ["analysis", "comprehensive", { symbol: "AAPL" }]
     * ```
     */
    createQueryKey(endpoint: string, params?: Record<string, any>): (string | Record<string, any>)[] {
        const key: (string | Record<string, any>)[] = ["analysis", endpoint]
        if (params) {
            key.push(params)
        }
        return key
    },
}

/**
 * Export the main API client for custom requests
 */
export { apiClient }
