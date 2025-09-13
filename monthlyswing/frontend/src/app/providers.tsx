/**
 * Providers component for Monthly Swing Trading application
 *
 * @description Configures and provides application-wide context providers
 * including TanStack Query for API state management and error boundaries.
 */

'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState } from 'react';

interface ProvidersProps {
  children: React.ReactNode;
}

/**
 * Application providers wrapper
 *
 * @param children - Child components to wrap with providers
 * @returns JSX element containing all necessary providers
 *
 * @example
 * ```tsx
 * // Used in layout.tsx to wrap the entire application
 * <Providers>
 *   <YourApp />
 * </Providers>
 * ```
 */
export function Providers({ children }: ProvidersProps) {
  // Create a new QueryClient instance for each app instance
  // This ensures server-side rendering compatibility
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Stale time for monthly swing data (5 minutes)
            staleTime: 5 * 60 * 1000,
            // Cache time for monthly swing data (30 minutes)
            gcTime: 30 * 60 * 1000,
            // Retry failed requests up to 3 times
            retry: 3,
            // Retry with exponential backoff
            retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
            // Only refetch on window focus if data is older than 5 minutes
            refetchOnWindowFocus: false,
            // Refetch on reconnect for real-time financial data
            refetchOnReconnect: 'always',
          },
          mutations: {
            // Retry mutations once on failure
            retry: 1,
            // Mutation retry delay
            retryDelay: 1000,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {/* Development tools - only in development */}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools 
          initialIsOpen={false}
        />
      )}
    </QueryClientProvider>
  );
}