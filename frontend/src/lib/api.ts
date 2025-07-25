/**
 * API client and service functions for Trendscope backend integration
 *
 * @description Centralized API client with error handling, retry logic,
 * and type-safe methods for interacting with the Trendscope backend.
 * Includes comprehensive analysis endpoints and error management.
 */

import { AnalysisData, AnalysisResponse, HistoricalDataResponse, HistoricalApiResponse } from "@/types/analysis"

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
 * API service functions for stock analysis
 */
export const analysisApi = {
    /**
     * Performs comprehensive 6-category analysis for a stock symbol
     *
     * @description Uses the frontend proxy API to bridge browser requests to the backend service.
     * This resolves DNS resolution issues where browsers cannot directly access
     * cluster-internal service names.
     *
     * @param symbol - Stock symbol to analyze (e.g., "AAPL", "GOOGL", "7203.T")
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

        console.log(`[Analysis API] Requesting analysis for symbol: ${normalizedSymbol}`)
        console.log(`[Analysis API] Using proxy endpoint: /api/analysis/${normalizedSymbol}`)

        // Use relative path to proxy API endpoint (no runtime config needed)
        const response = await fetch(`/api/analysis/${normalizedSymbol}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        })

        if (!response.ok) {
            let errorData
            try {
                errorData = await response.json()
            } catch {
                errorData = { message: response.statusText }
            }

            console.error(`[Analysis API] Request failed:`, errorData)
            throw new ApiError(
                response.status,
                errorData.error || errorData.message || `HTTP ${response.status}: ${response.statusText}`,
                errorData,
            )
        }

        const analysisResponse = await response.json() as AnalysisResponse
        
        console.log(`[Analysis API] Received response:`, analysisResponse.success)

        if (!analysisResponse.success || !analysisResponse.data) {
            throw new ApiError(500, analysisResponse.error?.message || "Analysis failed", analysisResponse.error)
        }

        return analysisResponse.data
    },

    /**
     * Gets technical analysis only for a stock symbol
     *
     * @param symbol - Stock symbol to analyze
     * @returns Promise resolving to technical analysis data
     * @throws {ApiError} When analysis fails
     */
    async getTechnicalAnalysis(symbol: string) {
        // TODO: Implement technical analysis proxy endpoint
        throw new ApiError(501, "Technical analysis API not yet implemented with proxy")
    },

    /**
     * Gets pattern analysis only for a stock symbol
     *
     * @param symbol - Stock symbol to analyze
     * @returns Promise resolving to pattern analysis data
     * @throws {ApiError} When analysis fails
     */
    async getPatternAnalysis(symbol: string) {
        // TODO: Implement pattern analysis proxy endpoint
        throw new ApiError(501, "Pattern analysis API not yet implemented with proxy")
    },

    /**
     * Gets volatility analysis only for a stock symbol
     *
     * @param symbol - Stock symbol to analyze
     * @returns Promise resolving to volatility analysis data
     * @throws {ApiError} When analysis fails
     */
    async getVolatilityAnalysis(symbol: string) {
        // TODO: Implement volatility analysis proxy endpoint
        throw new ApiError(501, "Volatility analysis API not yet implemented with proxy")
    },

    /**
     * Gets ML predictions only for a stock symbol
     *
     * @param symbol - Stock symbol to analyze
     * @returns Promise resolving to ML prediction data
     * @throws {ApiError} When analysis fails
     */
    async getMLAnalysis(symbol: string) {
        // TODO: Implement ML analysis proxy endpoint
        throw new ApiError(501, "ML analysis API not yet implemented with proxy")
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
        // TODO: Implement historical data proxy endpoint
        throw new ApiError(501, "Historical data API not yet implemented with proxy")
    },

    /**
     * Checks API health status
     *
     * @returns Promise resolving to health check data
     * @throws {ApiError} When health check fails
     */
    async checkHealth() {
        // TODO: Implement health check proxy endpoint
        throw new ApiError(501, "Health check API not yet implemented with proxy")
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
 * Export only the used API service functions
 */
// analysisApi and apiUtils are exported via their declarations above
