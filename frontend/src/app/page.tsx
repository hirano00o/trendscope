/**
 * Landing page component for Trendscope application
 *
 * @description Main entry point featuring stock symbol input and analysis dashboard.
 * Provides interface for users to enter stock symbols and view comprehensive
 * 6-category analysis results with probability-based predictions.
 */

"use client"

import { useRouter } from "next/navigation"
import { StockAnalysisForm } from "@/components/stock-analysis-form"
import { HeroSection } from "@/components/hero-section"

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
    const router = useRouter()

    /**
     * Handles stock analysis request by navigating to the analysis page
     *
     * @param symbol - Stock symbol to analyze (e.g., "AAPL", "GOOGL")
     */
    const handleAnalysis = async (symbol: string) => {
        console.log(`🚀 Navigating to analysis page for symbol: ${symbol}`)

        // Navigate to the analysis page with the symbol parameter
        router.push(`/analysis/${symbol}` as any)
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
                <div className="space-y-12">
                    {/* Hero Section */}
                    <HeroSection />

                    {/* Stock Analysis Form */}
                    <div className="mx-auto max-w-2xl">
                        <StockAnalysisForm onAnalyze={handleAnalysis} />
                    </div>

                    {/* Features Overview */}
                    <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
                        <div className="card">
                            <div className="card-header">
                                <h3 className="card-title">テクニカル分析</h3>
                            </div>
                            <p className="text-sm text-neutral-600">
                                SMA/EMAクロスオーバー、RSI、MACD、ボリンジャーバンド分析による 包括的なトレンド識別。
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
