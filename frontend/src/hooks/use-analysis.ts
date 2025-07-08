/**
 * React hooks for stock analysis API integration
 *
 * @description Custom hooks built on TanStack Query for fetching and managing
 * stock analysis data with proper caching, error handling, and loading states.
 * Provides hooks for comprehensive analysis and individual analysis categories.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { analysisApi, apiUtils } from "@/lib/api"
import { AnalysisData } from "@/types/analysis"

/**
 * Hook for fetching comprehensive 6-category stock analysis
 *
 * @description Fetches complete analysis including technical indicators,
 * patterns, volatility, ML predictions, fundamental data, and integrated scoring.
 * Includes proper caching and error handling.
 *
 * @param symbol - Stock symbol to analyze (e.g., "AAPL")
 * @param options - Query options for customizing behavior
 * @returns Query result with data, loading, and error states
 *
 * @example
 * ```tsx
 * function AnalysisComponent({ symbol }: { symbol: string }) {
 *   const { data, isLoading, error, refetch } = useComprehensiveAnalysis(symbol, {
 *     enabled: !!symbol && symbol.length > 0,
 *     staleTime: 5 * 60 * 1000, // 5 minutes
 *   })
 *
 *   if (isLoading) return <div>Analyzing {symbol}...</div>
 *   if (error) return <div>Error: {error.message}</div>
 *   if (!data) return null
 *
 *   return <AnalysisResults data={data} />
 * }
 * ```
 */
export function useComprehensiveAnalysis(
    symbol: string,
    options: {
        enabled?: boolean
        staleTime?: number
        refetchOnWindowFocus?: boolean
        retry?: boolean | number
    } = {},
) {
    const normalizedSymbol = symbol?.trim().toUpperCase()

    return useQuery({
        queryKey: apiUtils.createQueryKey("comprehensive", { symbol: normalizedSymbol }),
        queryFn: () => analysisApi.getComprehensiveAnalysis(normalizedSymbol),
        enabled: !!normalizedSymbol && normalizedSymbol.length > 0 && (options.enabled ?? true),
        staleTime: options.staleTime ?? 5 * 60 * 1000, // 5 minutes default
        refetchOnWindowFocus: options.refetchOnWindowFocus ?? true,
        retry: (failureCount, error) => {
            // Custom retry logic
            if (options.retry === false) return false
            if (typeof options.retry === "number") return failureCount < options.retry

            // Default retry behavior based on error type
            if (apiUtils.isApiError(error)) {
                return apiUtils.isRetryableError(error) && failureCount < 3
            }
            return failureCount < 3
        },
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
        meta: {
            errorMessage: "Failed to analyze stock. Please try again.",
        },
    })
}

/**
 * Hook for fetching technical analysis only
 *
 * @param symbol - Stock symbol to analyze
 * @param options - Query options
 * @returns Query result with technical analysis data
 *
 * @example
 * ```tsx
 * const { data: technicalData } = useTechnicalAnalysis("AAPL")
 * ```
 */
export function useTechnicalAnalysis(symbol: string, options: { enabled?: boolean } = {}) {
    const normalizedSymbol = symbol?.trim().toUpperCase()

    return useQuery({
        queryKey: apiUtils.createQueryKey("technical", { symbol: normalizedSymbol }),
        queryFn: () => analysisApi.getTechnicalAnalysis(normalizedSymbol),
        enabled: !!normalizedSymbol && normalizedSymbol.length > 0 && (options.enabled ?? true),
        staleTime: 2 * 60 * 1000, // 2 minutes
        meta: {
            errorMessage: "Failed to fetch technical analysis.",
        },
    })
}

/**
 * Hook for fetching pattern analysis only
 *
 * @param symbol - Stock symbol to analyze
 * @param options - Query options
 * @returns Query result with pattern analysis data
 */
export function usePatternAnalysis(symbol: string, options: { enabled?: boolean } = {}) {
    const normalizedSymbol = symbol?.trim().toUpperCase()

    return useQuery({
        queryKey: apiUtils.createQueryKey("patterns", { symbol: normalizedSymbol }),
        queryFn: () => analysisApi.getPatternAnalysis(normalizedSymbol),
        enabled: !!normalizedSymbol && normalizedSymbol.length > 0 && (options.enabled ?? true),
        staleTime: 5 * 60 * 1000, // 5 minutes
        meta: {
            errorMessage: "Failed to fetch pattern analysis.",
        },
    })
}

/**
 * Hook for fetching volatility analysis only
 *
 * @param symbol - Stock symbol to analyze
 * @param options - Query options
 * @returns Query result with volatility analysis data
 */
export function useVolatilityAnalysis(symbol: string, options: { enabled?: boolean } = {}) {
    const normalizedSymbol = symbol?.trim().toUpperCase()

    return useQuery({
        queryKey: apiUtils.createQueryKey("volatility", { symbol: normalizedSymbol }),
        queryFn: () => analysisApi.getVolatilityAnalysis(normalizedSymbol),
        enabled: !!normalizedSymbol && normalizedSymbol.length > 0 && (options.enabled ?? true),
        staleTime: 3 * 60 * 1000, // 3 minutes
        meta: {
            errorMessage: "Failed to fetch volatility analysis.",
        },
    })
}

/**
 * Hook for fetching ML predictions only
 *
 * @param symbol - Stock symbol to analyze
 * @param options - Query options
 * @returns Query result with ML prediction data
 */
export function useMLAnalysis(symbol: string, options: { enabled?: boolean } = {}) {
    const normalizedSymbol = symbol?.trim().toUpperCase()

    return useQuery({
        queryKey: apiUtils.createQueryKey("ml", { symbol: normalizedSymbol }),
        queryFn: () => analysisApi.getMLAnalysis(normalizedSymbol),
        enabled: !!normalizedSymbol && normalizedSymbol.length > 0 && (options.enabled ?? true),
        staleTime: 10 * 60 * 1000, // 10 minutes (ML predictions change less frequently)
        meta: {
            errorMessage: "Failed to fetch ML predictions.",
        },
    })
}

/**
 * Hook for API health check
 *
 * @returns Query result with health status
 *
 * @example
 * ```tsx
 * const { data: health, isError } = useHealthCheck()
 * const isOnline = health?.status === "ok" && !isError
 * ```
 */
export function useHealthCheck() {
    return useQuery({
        queryKey: ["api", "health"],
        queryFn: () => analysisApi.checkHealth(),
        staleTime: 30 * 1000, // 30 seconds
        refetchInterval: 60 * 1000, // Check every minute
        refetchOnWindowFocus: true,
        retry: 1,
        meta: {
            errorMessage: "Unable to connect to analysis service.",
        },
    })
}

/**
 * Mutation hook for triggering analysis on demand
 *
 * @description Useful for manual refresh or when you need to control
 * when analysis is performed. Includes optimistic updates and cache invalidation.
 *
 * @returns Mutation object with mutate function and status
 *
 * @example
 * ```tsx
 * const analysisMutation = useAnalysisMutation()
 *
 * const handleAnalyze = (symbol: string) => {
 *   analysisMutation.mutate(symbol, {
 *     onSuccess: (data) => {
 *       console.log("Analysis complete:", data)
 *     },
 *     onError: (error) => {
 *       console.error("Analysis failed:", error)
 *     }
 *   })
 * }
 *
 * return (
 *   <button
 *     onClick={() => handleAnalyze("AAPL")}
 *     disabled={analysisMutation.isPending}
 *   >
 *     {analysisMutation.isPending ? "Analyzing..." : "Analyze"}
 *   </button>
 * )
 * ```
 */
export function useAnalysisMutation() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (symbol: string) => analysisApi.getComprehensiveAnalysis(symbol),
        onSuccess: (data, symbol) => {
            // Update the cache with new data
            const queryKey = apiUtils.createQueryKey("comprehensive", { symbol: symbol.toUpperCase() })
            queryClient.setQueryData(queryKey, data)

            // Invalidate related queries to trigger refetch if needed
            queryClient.invalidateQueries({
                queryKey: ["analysis"],
                refetchType: "none", // Don't refetch immediately, just mark as stale
            })
        },
        onError: (error, symbol) => {
            console.error(`Analysis failed for ${symbol}:`, error)
        },
        meta: {
            errorMessage: "Analysis failed. Please try again.",
        },
    })
}

/**
 * Hook for prefetching analysis data
 *
 * @description Useful for preloading data when user is likely to request it,
 * such as when hovering over a stock symbol or typing in the search box.
 *
 * @returns Prefetch function
 *
 * @example
 * ```tsx
 * const prefetchAnalysis = useAnalysisPrefetch()
 *
 * return (
 *   <input
 *     onFocus={() => prefetchAnalysis("AAPL")} // Prefetch on focus
 *     onChange={(e) => {
 *       if (e.target.value.length === 4) {
 *         prefetchAnalysis(e.target.value) // Prefetch when 4 chars entered
 *       }
 *     }}
 *   />
 * )
 * ```
 */
export function useAnalysisPrefetch() {
    const queryClient = useQueryClient()

    return (symbol: string) => {
        const normalizedSymbol = symbol?.trim().toUpperCase()
        if (!normalizedSymbol || normalizedSymbol.length === 0) return

        queryClient.prefetchQuery({
            queryKey: apiUtils.createQueryKey("comprehensive", { symbol: normalizedSymbol }),
            queryFn: () => analysisApi.getComprehensiveAnalysis(normalizedSymbol),
            staleTime: 5 * 60 * 1000,
        })
    }
}

/**
 * Hook for getting cached analysis data without triggering a fetch
 *
 * @param symbol - Stock symbol
 * @returns Cached analysis data or undefined
 *
 * @example
 * ```tsx
 * const cachedData = useCachedAnalysis("AAPL")
 * const hasRecentData = !!cachedData
 * ```
 */
export function useCachedAnalysis(symbol: string): AnalysisData | undefined {
    const queryClient = useQueryClient()
    const normalizedSymbol = symbol?.trim().toUpperCase()

    if (!normalizedSymbol) return undefined

    return queryClient.getQueryData(apiUtils.createQueryKey("comprehensive", { symbol: normalizedSymbol }))
}

/**
 * Hook for managing multiple symbol analysis
 *
 * @param symbols - Array of stock symbols to analyze
 * @returns Array of query results for each symbol
 *
 * @example
 * ```tsx
 * const analyses = useMultipleAnalysis(["AAPL", "GOOGL", "MSFT"])
 * const allLoaded = analyses.every(query => !query.isLoading)
 * ```
 */
export function useMultipleAnalysis(symbols: string[]) {
    const validSymbols = symbols.map((s) => s?.trim().toUpperCase()).filter((s) => s && s.length > 0)

    return validSymbols.map((symbol) => useComprehensiveAnalysis(symbol, { enabled: true }))
}
