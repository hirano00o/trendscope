/**
 * Landing page component for Trendscope application
 *
 * @description Main entry point featuring stock symbol input and analysis dashboard.
 * Provides interface for users to enter stock symbols and view comprehensive
 * 6-category analysis results with probability-based predictions.
 */

"use client"

import { useState } from "react"
import { StockAnalysisForm } from "@/components/stock-analysis-form"
import { AnalysisResults } from "@/components/analysis-results"
import { HeroSection } from "@/components/hero-section"
import { useComprehensiveAnalysis } from "@/hooks/use-analysis"
import { type AnalysisData } from "@/types/analysis"

/**
 * Main landing page component
 *
 * @returns JSX element containing the complete landing page layout
 *
 * @example
 * ```tsx
 * // This component is automatically rendered for the "/" route
 * export default function Page() {
 *   return <LandingPage />
 * }
 * ```
 */
export default function Page() {
    const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null)
    const [isAnalyzing, setIsAnalyzing] = useState(false)
    const [error, setError] = useState<string | null>(null)

    /**
     * Handles stock analysis request
     *
     * @param symbol - Stock symbol to analyze (e.g., "AAPL", "GOOGL")
     * @throws {Error} When analysis fails or symbol is invalid
     */
    const handleAnalysis = async (symbol: string) => {
        console.log(`🚀 Starting analysis for symbol: ${symbol}`)
        setIsAnalyzing(true)
        setAnalysisData(null)
        setError(null)

        try {
            // Call the API directly using fetch
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
            const url = `${apiUrl}/api/v1/comprehensive/${symbol}`

            console.log(`📡 Making API request to: ${url}`)

            const response = await fetch(url, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                },
            })

            console.log(`📊 API response status: ${response.status}`)

            if (!response.ok) {
                const errorText = await response.text()
                console.error(`❌ API error: ${response.status} - ${errorText}`)
                throw new Error(`API request failed: ${response.status}`)
            }

            const response_data = await response.json()
            console.log(`✅ API response received:`, response_data)

            // Check if the response has the expected wrapper structure
            if (response_data && response_data.success && response_data.data) {
                console.log(`🎯 Setting analysis data...`)
                setAnalysisData(response_data.data)
            } else {
                console.error(`❌ Invalid response structure:`, response_data)
                throw new Error("Invalid response data structure")
            }
        } catch (error) {
            console.error("❌ Analysis failed:", error)
            const errorMessage = error instanceof Error ? error.message : "不明なエラーが発生しました"
            setError(errorMessage)
            throw error
        } finally {
            setIsAnalyzing(false)
            console.log(`🏁 Analysis completed for ${symbol}`)
        }
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-neutral-100">
            {/* Navigation Header */}
            <nav className="border-b border-neutral-200 bg-white/80 backdrop-blur-sm">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <div className="flex h-16 items-center justify-between">
                        <div className="flex items-center">
                            <h1 className="text-xl font-bold text-neutral-900">トレンドスコープ</h1>
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
                {!analysisData && !isAnalyzing ? (
                    <div className="space-y-12">
                        {/* Hero Section */}
                        <HeroSection />

                        {/* Stock Analysis Form */}
                        <div className="mx-auto max-w-2xl">
                            {error && (
                                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                                    <h3 className="text-lg font-medium text-red-800 mb-2">エラーが発生しました</h3>
                                    <p className="text-red-700">{error}</p>
                                    <button
                                        onClick={() => setError(null)}
                                        className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
                                    >
                                        エラーを閉じる
                                    </button>
                                </div>
                            )}
                            <StockAnalysisForm onAnalyze={handleAnalysis} isLoading={isAnalyzing} />
                        </div>

                        {/* Features Overview */}
                        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
                            <div className="card">
                                <div className="card-header">
                                    <h3 className="card-title">テクニカル分析</h3>
                                </div>
                                <p className="text-sm text-neutral-600">
                                    SMA/EMAクロスオーバー、RSI、MACD、ボリンジャーバンド分析による
                                    包括的なトレンド識別。
                                </p>
                            </div>

                            <div className="card">
                                <div className="card-header">
                                    <h3 className="card-title">パターン認識</h3>
                                </div>
                                <p className="text-sm text-neutral-600">
                                    ローソク足パターン、サポート/レジスタンスレベル、
                                    トレンドライン分析によるマーケットセンチメント解析。
                                </p>
                            </div>

                            <div className="card">
                                <div className="card-header">
                                    <h3 className="card-title">機械学習予測</h3>
                                </div>
                                <p className="text-sm text-neutral-600">
                                    ランダムフォレスト、SVM、ARIMAを含むアンサンブル機械学習モデルによる 価格予測。
                                </p>
                            </div>
                        </div>
                    </div>
                ) : isAnalyzing ? (
                    <div className="flex items-center justify-center min-h-[60vh]">
                        <div className="text-center">
                            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mb-4"></div>
                            <h2 className="text-xl font-semibold text-neutral-900 mb-2">株式を分析中...</h2>
                            <p className="text-neutral-600">包括的な分析を実行しています。しばらくお待ちください。</p>
                        </div>
                    </div>
                ) : analysisData ? (
                    <div className="space-y-8">
                        {/* Back to Search */}
                        <div className="flex items-center justify-between">
                            <button onClick={() => setAnalysisData(null)} className="btn btn-outline">
                                ← 新しい分析
                            </button>
                            <div className="text-right">
                                <h2 className="text-lg font-semibold text-neutral-900">分析結果</h2>
                                <p className="text-sm text-neutral-600">
                                    {analysisData.symbol} • {new Date().toLocaleDateString("ja-JP")}
                                </p>
                            </div>
                        </div>

                        {/* Analysis Results */}
                        <AnalysisResults data={analysisData} />
                    </div>
                ) : null}
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
