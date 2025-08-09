/**
 * React hook for fetching historical stock price data
 *
 * @description Custom hook that uses TanStack Query to fetch and cache
 * historical stock price data from the backend API. Provides loading states,
 * error handling, and automatic retries.
 */

import { useQuery, useQueryClient, UseQueryResult } from "@tanstack/react-query"
import { analysisApi, apiUtils } from "@/lib/api"
import { HistoricalDataResponse } from "@/types/analysis"

/**
 * Hook options for historical data fetching
 */
export interface UseHistoricalDataOptions {
    period?: string
    startDate?: string
    endDate?: string
    enabled?: boolean
    staleTime?: number
    gcTime?: number
}

/**
 * Hook for fetching historical stock price data
 *
 * @param symbol - Stock symbol to fetch data for
 * @param options - Additional options for the query
 * @returns TanStack Query result with historical data
 *
 * @example
 * ```typescript
 * const { data, isLoading, error } = useHistoricalData("AAPL", {
 *   period: "1mo",
 *   enabled: !!symbol
 * })
 *
 * if (isLoading) return <div>Loading chart...</div>
 * if (error) return <div>Error: {error.message}</div>
 * if (data) return <PriceChart data={data.historical_data} />
 * ```
 */
export function useHistoricalData(
    symbol: string | undefined,
    options: UseHistoricalDataOptions = {},
): UseQueryResult<HistoricalDataResponse, Error> {
    const {
        period = "1mo",
        startDate,
        endDate,
        enabled = true,
        staleTime = 5 * 60 * 1000, // 5 minutes
        gcTime = 10 * 60 * 1000, // 10 minutes
    } = options

    return useQuery({
        queryKey: apiUtils.createQueryKey("historical", {
            symbol: symbol?.toUpperCase(),
            period,
            startDate,
            endDate,
        }),
        queryFn: async () => {
            if (!symbol) {
                throw new Error("Symbol is required")
            }
            return analysisApi.getHistoricalData(symbol, period, startDate, endDate)
        },
        enabled: enabled && !!symbol,
        staleTime,
        gcTime,
        retry: (failureCount, error) => {
            // Don't retry on client errors (4xx)
            if (apiUtils.isApiError(error) && error.status >= 400 && error.status < 500) {
                return false
            }
            // Retry up to 3 times for server errors and network issues
            return failureCount < 3
        },
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    })
}

/**
 * Hook for fetching multiple timeframes of historical data
 *
 * @param symbol - Stock symbol to fetch data for
 * @param periods - Array of time periods to fetch
 * @returns Object with query results for each period
 *
 * @example
 * ```typescript
 * const { data: { "1mo": monthData, "3mo": threeMonthData }, isLoading } =
 *   useMultipleHistoricalData("AAPL", ["1mo", "3mo"])
 * ```
 */
export function useMultipleHistoricalData(
    symbol: string | undefined,
    periods: string[],
): {
    data: Record<string, HistoricalDataResponse | undefined>
    isLoading: boolean
    errors: Record<string, Error | null>
} {
    const queries = periods.map((period) => useHistoricalData(symbol, { period, enabled: !!symbol }))

    const data = periods.reduce(
        (acc, period, index) => {
            acc[period] = queries[index].data
            return acc
        },
        {} as Record<string, HistoricalDataResponse | undefined>,
    )

    const errors = periods.reduce(
        (acc, period, index) => {
            acc[period] = queries[index].error
            return acc
        },
        {} as Record<string, Error | null>,
    )

    const isLoading = queries.some((query) => query.isLoading)

    return { data, isLoading, errors }
}

/**
 * Hook for prefetching historical data
 *
 * @param symbol - Stock symbol to prefetch data for
 * @param options - Prefetch options
 *
 * @example
 * ```typescript
 * const prefetchHistoricalData = usePrefetchHistoricalData()
 *
 * // Prefetch data when user hovers over a stock symbol
 * onMouseEnter={() => prefetchHistoricalData("AAPL", { period: "1mo" })}
 * ```
 */
export function usePrefetchHistoricalData() {
    const queryClient = useQueryClient()

    return (symbol: string, options: UseHistoricalDataOptions = {}) => {
        const { period = "1mo", startDate, endDate } = options

        queryClient.prefetchQuery({
            queryKey: apiUtils.createQueryKey("historical", {
                symbol: symbol.toUpperCase(),
                period,
                startDate,
                endDate,
            }),
            queryFn: () => analysisApi.getHistoricalData(symbol, period, startDate, endDate),
            staleTime: 5 * 60 * 1000, // 5 minutes
        })
    }
}
