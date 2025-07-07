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

    /**
     * Handles stock analysis request
     * 
     * @param symbol - Stock symbol to analyze (e.g., "AAPL", "GOOGL")
     * @throws {Error} When analysis fails or symbol is invalid
     */
    const handleAnalysis = async (symbol: string) => {
        setIsAnalyzing(true)
        setAnalysisData(null)

        try {
            // Call the comprehensive analysis API
            const response = await fetch(`/api/analysis/comprehensive/${symbol}`)
            
            if (!response.ok) {
                throw new Error(`Analysis failed: ${response.statusText}`)
            }

            const data: AnalysisData = await response.json()
            setAnalysisData(data)
        } catch (error) {
            console.error("Analysis failed:", error)
            // In a real app, we'd show proper error handling UI
            throw error
        } finally {
            setIsAnalyzing(false)
        }
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-neutral-100">
            {/* Navigation Header */}
            <nav className="border-b border-neutral-200 bg-white/80 backdrop-blur-sm">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <div className="flex h-16 items-center justify-between">
                        <div className="flex items-center">
                            <h1 className="text-xl font-bold text-neutral-900">
                                Trendscope
                            </h1>
                            <span className="ml-2 rounded-full bg-primary-100 px-2 py-1 text-xs font-medium text-primary-700">
                                Beta
                            </span>
                        </div>
                        <div className="flex items-center space-x-4">
                            <span className="text-sm text-neutral-600">
                                Advanced Stock Analysis
                            </span>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                {!analysisData ? (
                    <div className="space-y-12">
                        {/* Hero Section */}
                        <HeroSection />
                        
                        {/* Stock Analysis Form */}
                        <div className="mx-auto max-w-2xl">
                            <StockAnalysisForm 
                                onAnalyze={handleAnalysis}
                                isLoading={isAnalyzing}
                            />
                        </div>

                        {/* Features Overview */}
                        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
                            <div className="card">
                                <div className="card-header">
                                    <h3 className="card-title">Technical Analysis</h3>
                                </div>
                                <p className="text-sm text-neutral-600">
                                    SMA/EMA crossovers, RSI, MACD, and Bollinger Bands analysis 
                                    for comprehensive trend identification.
                                </p>
                            </div>
                            
                            <div className="card">
                                <div className="card-header">
                                    <h3 className="card-title">Pattern Recognition</h3>
                                </div>
                                <p className="text-sm text-neutral-600">
                                    Candlestick patterns, support/resistance levels, and 
                                    trend line analysis for market sentiment.
                                </p>
                            </div>
                            
                            <div className="card">
                                <div className="card-header">
                                    <h3 className="card-title">ML Predictions</h3>
                                </div>
                                <p className="text-sm text-neutral-600">
                                    Ensemble machine learning models including Random Forest, 
                                    SVM, and ARIMA for price forecasting.
                                </p>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-8">
                        {/* Back to Search */}
                        <div className="flex items-center justify-between">
                            <button
                                onClick={() => setAnalysisData(null)}
                                className="btn btn-outline"
                            >
                                ← New Analysis
                            </button>
                            <div className="text-right">
                                <h2 className="text-lg font-semibold text-neutral-900">
                                    Analysis Results
                                </h2>
                                <p className="text-sm text-neutral-600">
                                    {analysisData.symbol} • {new Date().toLocaleDateString()}
                                </p>
                            </div>
                        </div>

                        {/* Analysis Results */}
                        <AnalysisResults data={analysisData} />
                    </div>
                )}
            </main>

            {/* Footer */}
            <footer className="border-t border-neutral-200 bg-white">
                <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                    <div className="text-center text-sm text-neutral-600">
                        <p>
                            Trendscope • Advanced Stock Analysis Platform
                        </p>
                        <p className="mt-1">
                            Disclaimer: This is for educational purposes only. Not financial advice.
                        </p>
                    </div>
                </div>
            </footer>
        </div>
    )
}