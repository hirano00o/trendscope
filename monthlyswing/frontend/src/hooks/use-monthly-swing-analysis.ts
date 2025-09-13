/**
 * Custom React hooks for Monthly Swing Trading analysis
 *
 * @description TanStack Query-based hooks for managing monthly swing analysis
 * API calls with caching, error handling, and loading states.
 */

import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { useEffect } from 'react';

import { 
  monthlySwingApi, 
  apiUtils, 
  MonthlySwingApiError 
} from '@/lib/api-client';
import { MonthlyTrendResult } from '@/types/monthly-swing';

/**
 * Options for monthly swing analysis query
 */
export interface UseMonthlySwingAnalysisOptions {
  /** Enable/disable automatic query execution */
  enabled?: boolean;
  /** Stale time override (default: 5 minutes) */
  staleTime?: number;
  /** Cache time override (default: 30 minutes) */
  cacheTime?: number;
  /** Retry count override (default: 3) */
  retry?: number;
  /** Custom error handling */
  onError?: (error: MonthlySwingApiError) => void;
  /** Custom success handling */
  onSuccess?: (data: MonthlyTrendResult) => void;
}

/**
 * Hook for fetching monthly swing analysis for a stock symbol
 *
 * @param symbol - Stock symbol to analyze (e.g., "AAPL", "7203.T")
 * @param options - Query configuration options
 * @returns TanStack Query result with monthly swing analysis data
 *
 * @example
 * ```tsx
 * function AnalysisComponent({ symbol }: { symbol: string }) {
 *   const { data, isLoading, error, refetch } = useMonthlySwingAnalysis(symbol, {
 *     enabled: !!symbol,
 *     onError: (error) => console.error('Analysis failed:', error.message),
 *   });
 *
 *   if (isLoading) return <div>Analyzing...</div>;
 *   if (error) return <div>Error: {error.message}</div>;
 *   if (!data) return <div>No data</div>;
 *
 *   return (
 *     <div>
 *       <h2>Analysis for {data.symbol}</h2>
 *       <p>Trend: {data.trend_strength.direction}</p>
 *       <p>Confidence: {data.trend_strength.confidence}</p>
 *     </div>
 *   );
 * }
 * ```
 */
export function useMonthlySwingAnalysis(
  symbol: string,
  options: UseMonthlySwingAnalysisOptions = {}
) {
  const {
    enabled = true,
    staleTime = 5 * 60 * 1000, // 5 minutes
    cacheTime = 30 * 60 * 1000, // 30 minutes
    retry = 3,
    onError,
    onSuccess,
  } = options;

  // Normalize symbol for consistent caching
  const normalizedSymbol = symbol.trim().toUpperCase();

  const queryOptions: UseQueryOptions<
    MonthlyTrendResult,
    MonthlySwingApiError,
    MonthlyTrendResult,
    string[]
  > = {
    queryKey: apiUtils.createQueryKey('analysis', { symbol: normalizedSymbol }) as string[],
    queryFn: () => monthlySwingApi.getAnalysis(normalizedSymbol),
    enabled: enabled && !!normalizedSymbol,
    staleTime,
    gcTime: cacheTime,
    retry: (failureCount, error) => {
      // Don't retry on client errors (4xx), but do retry on server errors (5xx)
      if (apiUtils.isMonthlySwingApiError(error) && !apiUtils.isRetryableError(error)) {
        return false;
      }
      return failureCount < retry;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  };

  const queryResult = useQuery(queryOptions);

  // Handle success and error callbacks via useEffect
  useEffect(() => {
    if (queryResult.isSuccess && queryResult.data && onSuccess) {
      console.log(`Monthly swing analysis completed for ${normalizedSymbol}`);
      onSuccess(queryResult.data);
    }
  }, [queryResult.isSuccess, queryResult.data, normalizedSymbol, onSuccess]);

  useEffect(() => {
    if (queryResult.isError && queryResult.error && onError) {
      console.error(`Monthly swing analysis failed for ${normalizedSymbol}:`, queryResult.error);
      onError(queryResult.error);
    }
  }, [queryResult.isError, queryResult.error, normalizedSymbol, onError]);

  return {
    ...queryResult,
    // Custom error message for UI display
    errorMessage: queryResult.error 
      ? apiUtils.getErrorMessage(queryResult.error)
      : null,
    // Convenience boolean for checking if data exists
    hasData: !!queryResult.data,
    // Symbol being analyzed
    symbol: normalizedSymbol,
  };
}

/**
 * Hook for checking API health status
 *
 * @param options - Query configuration options
 * @returns TanStack Query result with health check data
 *
 * @example
 * ```tsx
 * function HealthIndicator() {
 *   const { data, isLoading, error } = useApiHealth({
 *     refetchInterval: 30000, // Check every 30 seconds
 *   });
 *
 *   if (isLoading) return <div>Checking...</div>;
 *   if (error) return <div className="text-red-500">API Offline</div>;
 *   
 *   return (
 *     <div className="text-green-500">
 *       API Online - {data?.status}
 *     </div>
 *   );
 * }
 * ```
 */
export function useApiHealth(
  options: Omit<UseMonthlySwingAnalysisOptions, 'onSuccess' | 'onError'> & {
    refetchInterval?: number;
  } = {}
) {
  const {
    enabled = true,
    staleTime = 30 * 1000, // 30 seconds
    cacheTime = 60 * 1000, // 1 minute
    retry = 1, // Fewer retries for health checks
    refetchInterval,
  } = options;

  const queryOptions: UseQueryOptions<
    { status: string; timestamp: string },
    MonthlySwingApiError,
    { status: string; timestamp: string },
    string[]
  > = {
    queryKey: apiUtils.createQueryKey('health') as string[],
    queryFn: () => monthlySwingApi.checkHealth(),
    enabled,
    staleTime,
    gcTime: cacheTime,
    retry,
    refetchInterval,
    retryDelay: 1000,
  };

  return useQuery(queryOptions);
}

/**
 * Type guard to check if error is MonthlySwingApiError
 */
export function isMonthlySwingApiError(error: any): error is MonthlySwingApiError {
  return apiUtils.isMonthlySwingApiError(error);
}

/**
 * Utility to get user-friendly error message
 */
export function getErrorMessage(error: any): string {
  return apiUtils.getErrorMessage(error);
}

/**
 * Utility to check if error is retryable
 */
export function isRetryableError(error: any): boolean {
  return apiUtils.isRetryableError(error);
}