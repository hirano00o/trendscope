/**
 * Application providers component
 * 
 * @description Wraps the application with necessary providers including
 * TanStack Query for API state management and future providers for theming,
 * authentication, and other global state management.
 */

"use client"

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import { useState, type ReactNode } from "react"

interface ProvidersProps {
    children: ReactNode
}

/**
 * Main providers wrapper component
 * 
 * @param props - Component props
 * @param props.children - Child components to wrap with providers
 * @returns JSX element with all necessary providers
 * 
 * @example
 * ```tsx
 * <Providers>
 *   <App />
 * </Providers>
 * ```
 */
export function Providers({ children }: ProvidersProps) {
    const [queryClient] = useState(
        () => new QueryClient({
            defaultOptions: {
                queries: {
                    // Stale time: 5 minutes for stock data
                    staleTime: 5 * 60 * 1000,
                    // Cache time: 10 minutes
                    gcTime: 10 * 60 * 1000,
                    // Retry failed requests 3 times
                    retry: 3,
                    // Retry delay with exponential backoff
                    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
                    // Refetch on window focus for real-time data
                    refetchOnWindowFocus: true,
                    // Refetch on reconnect
                    refetchOnReconnect: true,
                },
                mutations: {
                    // Retry mutations once
                    retry: 1,
                },
            },
        })
    )

    return (
        <QueryClientProvider client={queryClient}>
            {children}
            {process.env.NODE_ENV === "development" && (
                <ReactQueryDevtools 
                    initialIsOpen={false}
                />
            )}
        </QueryClientProvider>
    )
}