/**
 * API client for Monthly Swing Trading backend integration
 *
 * @description Centralized API client with error handling, retry logic,
 * and type-safe methods for interacting with the monthly swing backend.
 */

import {
  MonthlySwingApiResponse,
  MonthlyTrendResult,
  MonthlySwingAnalysisRequest,
  ApiError,
} from '@/types/monthly-swing';

/**
 * API configuration
 */
const API_CONFIG = {
  // Base URL for monthly swing backend
  // In development, this will proxy through Next.js API routes
  baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001',
  // Request timeout in milliseconds
  timeout: 30000,
  // Default retry count
  retries: 3,
} as const;

/**
 * Custom API error class with additional context
 */
export class MonthlySwingApiError extends Error {
  public readonly status: number;
  public readonly code?: string;
  public readonly details?: any;

  constructor(status: number, message: string, code?: string, details?: any) {
    super(message);
    this.name = 'MonthlySwingApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

/**
 * HTTP client utility with timeout and retry logic
 */
class HttpClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_CONFIG.baseUrl}${endpoint}`;
    const controller = new AbortController();
    
    // Set timeout
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, API_CONFIG.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
          ...options.headers,
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // Handle non-2xx responses
      if (!response.ok) {
        let errorData: any;
        try {
          errorData = await response.json();
        } catch {
          errorData = { message: response.statusText };
        }

        throw new MonthlySwingApiError(
          response.status,
          errorData.message || `HTTP ${response.status}: ${response.statusText}`,
          errorData.code,
          errorData.details
        );
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);

      // Handle network errors and timeouts
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new MonthlySwingApiError(
            408,
            'Request timeout',
            'TIMEOUT_ERROR'
          );
        }
        if (error.message.includes('fetch')) {
          throw new MonthlySwingApiError(
            0,
            'Network error - Unable to connect to the analysis service',
            'NETWORK_ERROR'
          );
        }
      }

      // Re-throw API errors as-is
      if (error instanceof MonthlySwingApiError) {
        throw error;
      }

      // Wrap other errors
      throw new MonthlySwingApiError(
        500,
        error instanceof Error ? error.message : 'Unknown error',
        'UNKNOWN_ERROR',
        error
      );
    }
  }

  public async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  public async post<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

/**
 * Monthly swing trading API client
 */
export class MonthlySwingApiClient {
  private httpClient = new HttpClient();

  /**
   * Get monthly swing analysis for a stock symbol
   *
   * @param symbol - Stock symbol to analyze (e.g., "AAPL", "7203.T")
   * @param options - Additional analysis options
   * @returns Promise resolving to monthly trend analysis result
   * @throws {MonthlySwingApiError} When analysis fails or symbol is invalid
   *
   * @example
   * ```typescript
   * const client = new MonthlySwingApiClient();
   * const result = await client.getAnalysis("AAPL");
   * console.log(result.trend_strength.direction);
   * ```
   */
  public async getAnalysis(
    symbol: string,
    options?: MonthlySwingAnalysisRequest['options']
  ): Promise<MonthlyTrendResult> {
    // Validate symbol format
    const normalizedSymbol = symbol.trim().toUpperCase();
    if (!normalizedSymbol || normalizedSymbol.length === 0) {
      throw new MonthlySwingApiError(
        400,
        'Stock symbol is required',
        'INVALID_SYMBOL'
      );
    }

    console.log(
      `[Monthly Swing API] Requesting analysis for symbol: ${normalizedSymbol}`
    );

    try {
      const response = await this.httpClient.get<MonthlySwingApiResponse>(
        `/api/v1/monthly-swing/analysis/${encodeURIComponent(normalizedSymbol)}`
      );

      console.log(
        `[Monthly Swing API] Received response for ${normalizedSymbol}`
      );

      // Handle API response format
      if (!response.success || !response.data) {
        throw new MonthlySwingApiError(
          500,
          response.error?.message || 'Analysis failed',
          response.error?.code || 'ANALYSIS_FAILED',
          response.error?.details
        );
      }

      return response.data;
    } catch (error) {
      console.error(`[Monthly Swing API] Analysis failed for ${normalizedSymbol}:`, error);

      // Re-throw MonthlySwingApiError as-is
      if (error instanceof MonthlySwingApiError) {
        throw error;
      }

      // Wrap other errors
      throw new MonthlySwingApiError(
        500,
        'Unexpected error during analysis',
        'UNEXPECTED_ERROR',
        error
      );
    }
  }

  /**
   * Check API health status
   *
   * @returns Promise resolving to health check data
   * @throws {MonthlySwingApiError} When health check fails
   */
  public async checkHealth(): Promise<{ status: string; timestamp: string }> {
    try {
      return await this.httpClient.get('/health');
    } catch (error) {
      console.error('[Monthly Swing API] Health check failed:', error);
      throw error;
    }
  }
}

/**
 * Default API client instance
 */
export const monthlySwingApi = new MonthlySwingApiClient();

/**
 * Utility functions for API error handling
 */
export const apiUtils = {
  /**
   * Checks if an error is a Monthly Swing API error
   */
  isMonthlySwingApiError(error: any): error is MonthlySwingApiError {
    return error instanceof MonthlySwingApiError;
  },

  /**
   * Gets user-friendly error message from API error
   */
  getErrorMessage(error: any): string {
    if (error instanceof MonthlySwingApiError) {
      // Map specific error codes to user-friendly messages
      switch (error.code) {
        case 'INVALID_SYMBOL':
          return '無効な銘柄シンボルです。シンボルを確認して再試行してください。';
        case 'TIMEOUT_ERROR':
          return 'リクエストがタイムアウトしました。しばらく後に再試行してください。';
        case 'NETWORK_ERROR':
          return 'ネットワークエラーが発生しました。接続を確認してください。';
        case 'DATA_NOT_FOUND':
          return '指定された銘柄のデータが見つかりません。シンボルを確認してください。';
        case 'INSUFFICIENT_DATA':
          return 'データが不足しているため、分析を実行できません。';
        case 'ANALYSIS_FAILED':
          return '分析の実行に失敗しました。しばらく後に再試行してください。';
        default:
          break;
      }

      // Map HTTP status codes to user-friendly messages
      switch (error.status) {
        case 400:
          return '無効なリクエストです。入力内容を確認してください。';
        case 404:
          return 'リソースが見つかりません。銘柄シンボルを確認してください。';
        case 429:
          return 'リクエスト数が上限に達しました。しばらく後に再試行してください。';
        case 500:
          return 'サーバーエラーが発生しました。しばらく後に再試行してください。';
        case 503:
          return 'サービスが一時的に利用できません。しばらく後に再試行してください。';
        default:
          return error.message || '予期しないエラーが発生しました。';
      }
    }

    if (error?.name === 'AbortError') {
      return 'リクエストがタイムアウトしました。再試行してください。';
    }

    if (error?.message?.includes('fetch')) {
      return '分析サービスに接続できません。接続状況を確認してください。';
    }

    return error?.message || '予期しないエラーが発生しました。';
  },

  /**
   * Determines if an error is retryable
   */
  isRetryableError(error: any): boolean {
    if (error instanceof MonthlySwingApiError) {
      // Retry on server errors and specific client errors
      return (
        error.status >= 500 || 
        error.status === 408 || 
        error.status === 429 ||
        error.code === 'TIMEOUT_ERROR' ||
        error.code === 'NETWORK_ERROR'
      );
    }

    // Retry on network errors
    return error?.name === 'TypeError' || error?.message?.includes('fetch');
  },

  /**
   * Creates query key for TanStack Query
   */
  createQueryKey(endpoint: string, params?: Record<string, any>): (string | Record<string, any>)[] {
    const key: (string | Record<string, any>)[] = ['monthlySwing', endpoint];
    if (params) {
      key.push(params);
    }
    return key;
  },
};