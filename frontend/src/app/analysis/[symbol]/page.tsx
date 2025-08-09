/**
 * Dynamic analysis page for individual stock symbols
 *
 * @description Displays comprehensive analysis results for a specific stock symbol.
 * Supports both US stocks (AAPL) and Japanese stocks (7203.T) format.
 * Handles URL parameters, loading states, and error scenarios.
 */

"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { AnalysisResults } from "@/components/analysis-results"
import { analysisApi } from "@/lib/api"
import { isValidStockSymbol, normalizeStockSymbol } from "@/lib/utils"
import { useErrorHandler } from "@/lib/error-handling"
import type { AnalysisData } from "@/types/analysis"

/**
 * Analysis page component for individual stock symbols
 *
 * @description Handles URL-based stock analysis display with proper loading,
 * error states, and navigation. Supports browser history and direct URL access.
 *
 * @returns JSX element containing the analysis page layout
 *
 * @example
 * URL: /analysis/AAPL
 * URL: /analysis/7203.T
 */
export default function AnalysisPage() {
    const params = useParams()
    const router = useRouter()
    const { handleError } = useErrorHandler()

    const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Extract and normalize the symbol from URL parameters
    const rawSymbol = params.symbol as string
    const normalizedSymbol = normalizeStockSymbol(rawSymbol)

    /**
     * Validates the stock symbol from URL
     *
     * @param symbol - Symbol to validate
     * @returns Error message if invalid, null if valid
     */
    const validateUrlSymbol = (symbol: string): string | null => {
        if (!symbol) {
            return "株式コードが指定されていません"
        }

        const normalized = normalizeStockSymbol(symbol)
        if (!normalized || !isValidStockSymbol(normalized)) {
            return `無効な株式コードです: ${symbol}`
        }

        return null
    }

    /**
     * Performs comprehensive analysis for the given symbol
     *
     * @param symbol - Stock symbol to analyze
     */
    const performAnalysis = async (symbol: string) => {
        console.log(`🚀 Starting analysis for URL symbol: ${symbol}`)
        setIsLoading(true)
        setAnalysisData(null)
        setError(null)

        try {
            console.log(`📡 Fetching comprehensive analysis for: ${symbol}`)
            const result = await analysisApi.getComprehensiveAnalysis(symbol)
            console.log(`✅ Analysis completed successfully:`, result)
            setAnalysisData(result)
        } catch (error) {
            console.error("❌ Analysis failed:", error)
            const errorInfo = handleError(error, "analysis-page")
            setError(errorInfo.message)
        } finally {
            setIsLoading(false)
            console.log(`🏁 Analysis completed for ${symbol}`)
        }
    }

    // Effect to handle symbol validation and analysis
    useEffect(() => {
        if (!rawSymbol) return

        const validationError = validateUrlSymbol(rawSymbol)
        if (validationError) {
            setError(validationError)
            setIsLoading(false)
            return
        }

        if (normalizedSymbol) {
            performAnalysis(normalizedSymbol)
        }
    }, [rawSymbol, normalizedSymbol])

    /**
     * Handles navigation back to the main page
     */
    const handleBackToHome = () => {
        router.push("/")
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-neutral-100">
            {/* Navigation Header */}
            <nav className="border-b border-neutral-200 bg-white/80 backdrop-blur-sm">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <div className="flex h-16 items-center justify-between">
                        <div className="flex items-center">
                            <Link href="/" className="text-xl font-bold text-neutral-900 hover:text-primary-600">
                                トレンドスコープ
                            </Link>
                            <span className="ml-2 rounded-full bg-primary-100 px-2 py-1 text-xs font-medium text-primary-700">
                                ベータ版
                            </span>
                        </div>
                        <div className="flex items-center space-x-4">
                            <span className="text-sm text-neutral-600">高度な株価分析</span>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                {/* Loading State */}
                {isLoading && (
                    <div className="flex items-center justify-center min-h-[60vh]">
                        <div className="text-center">
                            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mb-4"></div>
                            <h2 className="text-xl font-semibold text-neutral-900 mb-2">
                                {normalizedSymbol ? `${normalizedSymbol} を分析中...` : "株式を分析中..."}
                            </h2>
                            <p className="text-neutral-600">包括的な分析を実行しています。しばらくお待ちください。</p>
                        </div>
                    </div>
                )}

                {/* Error State */}
                {error && !isLoading && (
                    <div className="max-w-2xl mx-auto">
                        <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
                            <h2 className="text-xl font-medium text-red-800 mb-2">エラーが発生しました</h2>
                            <p className="text-red-700 mb-4">{error}</p>
                            <div className="flex gap-3">
                                <button onClick={handleBackToHome} className="btn btn-primary">
                                    ← トップページに戻る
                                </button>
                                <button onClick={() => window.location.reload()} className="btn btn-outline">
                                    再試行
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Success State - Analysis Results */}
                {analysisData && !isLoading && !error && (
                    <div className="space-y-8">
                        {/* Page Header with Navigation */}
                        <div className="flex items-center justify-between">
                            <button onClick={handleBackToHome} className="btn btn-outline">
                                ← 新しい分析
                            </button>
                            <div className="text-right">
                                <h1 className="text-2xl font-bold text-neutral-900">{analysisData.symbol} 分析結果</h1>
                                <p className="text-sm text-neutral-600">{new Date().toLocaleDateString("ja-JP")}</p>
                            </div>
                        </div>

                        {/* Analysis Results Component */}
                        <AnalysisResults data={analysisData} />

                        {/* Additional Actions */}
                        <div className="flex justify-center pt-8">
                            <button onClick={handleBackToHome} className="btn btn-primary">
                                別の株式を分析
                            </button>
                        </div>
                    </div>
                )}
            </main>

            {/* Footer */}
            <footer className="border-t border-neutral-200 bg-white">
                <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                    <div className="text-center text-sm text-neutral-600">
                        <p>トレンドスコープ • 高度な株価分析プラットフォーム</p>
                        <p className="mt-1">免責事項：これは教育目的のみのためです。投資助言ではありません。</p>
                    </div>
                </div>
            </footer>
        </div>
    )
}
