/**
 * Error handling utilities for the Trendscope application
 *
 * @description Comprehensive error handling system with user-friendly messages,
 * error boundaries, and integration with TanStack Query error handling.
 * Provides consistent error display and recovery mechanisms.
 */

import React from "react"
import { ApiError, apiUtils } from "./api"

/**
 * Application error types
 */
export enum ErrorType {
    NETWORK = "NETWORK",
    API = "API",
    VALIDATION = "VALIDATION",
    TIMEOUT = "TIMEOUT",
    UNKNOWN = "UNKNOWN",
    RATE_LIMIT = "RATE_LIMIT",
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE",
}

/**
 * Structured error information for UI display
 */
export interface ErrorInfo {
    type: ErrorType
    title: string
    message: string
    suggestion?: string
    action?: {
        label: string
        handler: () => void
    }
    recoverable: boolean
    technical?: string
}

/**
 * Error classification and message generation
 *
 * @param error - Error object to process
 * @param context - Additional context about where the error occurred
 * @returns Structured error information for UI display
 *
 * @example
 * ```typescript
 * try {
 *   await analysisApi.getComprehensiveAnalysis("AAPL")
 * } catch (error) {
 *   const errorInfo = processError(error, "stock-analysis")
 *   showErrorToast(errorInfo.title, errorInfo.message)
 * }
 * ```
 */
export function processError(error: any, context?: string): ErrorInfo {
    // Handle API errors
    if (apiUtils.isApiError(error)) {
        return processApiError(error, context)
    }

    // Handle network errors
    if (error?.name === "TypeError" && error?.message?.includes("fetch")) {
        return {
            type: ErrorType.NETWORK,
            title: "接続エラー",
            message: "分析サービスに接続できません。",
            suggestion: "インターネット接続を確認して、再度お試しください。",
            recoverable: true,
            technical: error.message,
        }
    }

    // Handle timeout errors
    if (error?.name === "AbortError" || error?.message?.includes("timeout")) {
        return {
            type: ErrorType.TIMEOUT,
            title: "リクエストタイムアウト",
            message: "分析に予想より時間がかかっています。",
            suggestion: "サーバーの負荷が高い可能性があります。しばらくしてから再度お試しください。",
            recoverable: true,
            technical: error.message,
        }
    }

    // Handle validation errors
    if (error?.name === "ValidationError" || error?.message?.includes("validation")) {
        return {
            type: ErrorType.VALIDATION,
            title: "入力エラー",
            message: error.message || "入力内容を確認して、再度お試しください。",
            suggestion: "有効な株式コード（例：AAPL、GOOGL）を入力してください。",
            recoverable: true,
            technical: error.message,
        }
    }

    // Default unknown error
    return {
        type: ErrorType.UNKNOWN,
        title: "予期しないエラー",
        message: "何かが間違いました。再度お試しください。",
        suggestion: "問題が持続する場合は、サポートにお問い合わせください。",
        recoverable: true,
        technical: error?.message || String(error),
    }
}

/**
 * Processes API-specific errors with detailed context
 *
 * @param error - ApiError instance
 * @param context - Additional context
 * @returns Structured error information
 */
function processApiError(error: ApiError, context?: string): ErrorInfo {
    const baseInfo = {
        type: ErrorType.API,
        technical: `${error.status}: ${error.message}`,
        recoverable: true,
    }

    switch (error.status) {
        case 400:
            return {
                ...baseInfo,
                type: ErrorType.VALIDATION,
                title: "無効な株式コード",
                message: "入力された株式コードが無効です。",
                suggestion: "有効な株式コード（例：AAPL、GOOGL、MSFT）を入力して、再度お試しください。",
            }

        case 404:
            return {
                ...baseInfo,
                title: "株式が見つかりません",
                message: "指定された株式コードが見つかりませんでした。",
                suggestion: "コードが正しいことを確認してください。一部の株式は分析に利用できない場合があります。",
            }

        case 429:
            return {
                ...baseInfo,
                type: ErrorType.RATE_LIMIT,
                title: "リクエスト数超過",
                message: "分析リクエストが多すぎます。",
                suggestion: "次の分析をリクエストする前に、しばらくお待ちください。",
            }

        case 500:
            return {
                ...baseInfo,
                type: ErrorType.SERVICE_UNAVAILABLE,
                title: "分析サービスエラー",
                message: "分析サービスに一時的な問題が発生しています。",
                suggestion: "チームに通知されました。数分後に再度お試しください。",
            }

        case 503:
            return {
                ...baseInfo,
                type: ErrorType.SERVICE_UNAVAILABLE,
                title: "サービスメンテナンス",
                message: "分析サービスは現在メンテナンス中です。",
                suggestion: "まもなくオンラインに戻ります。後でもう一度お試しください。",
            }

        default:
            return {
                ...baseInfo,
                title: "分析失敗",
                message: error.message || "株式分析を完了できませんでした。",
                suggestion:
                    "再度お試しください。問題が持続する場合、株式データが一時的に利用できない可能性があります。",
            }
    }
}

/**
 * React Error Boundary component for catching and displaying errors
 *
 * @example
 * ```tsx
 * <ErrorBoundary fallback={<ErrorFallback />}>
 *   <AnalysisComponent />
 * </ErrorBoundary>
 * ```
 */

interface ErrorBoundaryState {
    hasError: boolean
    error?: Error
    errorInfo?: ErrorInfo
}

interface ErrorBoundaryProps {
    children: React.ReactNode
    fallback?: React.ComponentType<{ error: ErrorInfo; onRetry: () => void }>
    onError?: (error: Error, errorInfo: ErrorInfo) => void
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
    constructor(props: ErrorBoundaryProps) {
        super(props)
        this.state = { hasError: false }
    }

    static getDerivedStateFromError(error: Error): ErrorBoundaryState {
        const errorInfo = processError(error, "error-boundary")
        return {
            hasError: true,
            error,
            errorInfo,
        }
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        const processedError = processError(error, "error-boundary")

        // Log error for debugging
        console.error("Error Boundary caught an error:", error, errorInfo)

        // Call onError callback if provided
        this.props.onError?.(error, processedError)
    }

    handleRetry = () => {
        this.setState({ hasError: false, error: undefined, errorInfo: undefined })
    }

    render() {
        if (this.state.hasError && this.state.errorInfo) {
            const FallbackComponent = this.props.fallback || DefaultErrorFallback
            return <FallbackComponent error={this.state.errorInfo} onRetry={this.handleRetry} />
        }

        return this.props.children
    }
}

/**
 * Default error fallback component
 */
interface ErrorFallbackProps {
    error: ErrorInfo
    onRetry: () => void
}

function DefaultErrorFallback({ error, onRetry }: ErrorFallbackProps) {
    return (
        <div className="flex flex-col items-center justify-center p-8 text-center">
            <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 max-w-md">
                <h2 className="text-lg font-semibold text-danger-800 mb-2">{error.title}</h2>
                <p className="text-danger-700 mb-4">{error.message}</p>
                {error.suggestion && <p className="text-sm text-danger-600 mb-4">{error.suggestion}</p>}
                {error.recoverable && (
                    <button onClick={onRetry} className="btn btn-primary">
                        再試行
                    </button>
                )}
            </div>
        </div>
    )
}

/**
 * Hook for consistent error handling in components
 *
 * @returns Error handling utilities
 *
 * @example
 * ```tsx
 * function AnalysisComponent() {
 *   const { handleError, showError } = useErrorHandler()
 *
 *   const handleSubmit = async (symbol: string) => {
 *     try {
 *       await analysisApi.getComprehensiveAnalysis(symbol)
 *     } catch (error) {
 *       handleError(error, "analysis-submission")
 *     }
 *   }
 * }
 * ```
 */
export function useErrorHandler() {
    const handleError = React.useCallback((error: any, context?: string) => {
        const errorInfo = processError(error, context)

        // Log for debugging
        console.error(`Error in ${context || "unknown"}:`, error)

        return errorInfo
    }, [])

    const showError = React.useCallback(
        (error: any, context?: string) => {
            const errorInfo = handleError(error, context)

            // You can integrate with your toast/notification system here
            // For now, we'll just log it
            console.warn(`Error to display: ${errorInfo.title} - ${errorInfo.message}`)

            return errorInfo
        },
        [handleError],
    )

    const isRetryableError = React.useCallback((error: any): boolean => {
        const errorInfo = processError(error)
        return errorInfo.recoverable && errorInfo.type !== ErrorType.VALIDATION
    }, [])

    return {
        handleError,
        showError,
        isRetryableError,
        processError,
    }
}

/**
 * Utility for creating error toast notifications
 *
 * @param error - Error to display
 * @param context - Additional context
 * @returns Error information for toast display
 */
export function createErrorToast(error: any, context?: string) {
    const errorInfo = processError(error, context)

    return {
        title: errorInfo.title,
        description: errorInfo.message,
        variant: "destructive" as const,
        duration: errorInfo.type === ErrorType.VALIDATION ? 5000 : 8000,
    }
}

/**
 * Global error handler for unhandled promise rejections
 */
export function setupGlobalErrorHandling() {
    if (typeof window !== "undefined") {
        window.addEventListener("unhandledrejection", (event) => {
            const errorInfo = processError(event.reason, "unhandled-promise")
            console.error("Unhandled promise rejection:", errorInfo)

            // Prevent the default browser error handling
            event.preventDefault()
        })

        window.addEventListener("error", (event) => {
            const errorInfo = processError(event.error, "global-error")
            console.error("Global error:", errorInfo)
        })
    }
}
