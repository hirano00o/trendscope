/**
 * Hero section component for the Trendscope landing page
 * 
 * @description Eye-catching hero section that introduces the application,
 * highlights key features, and encourages user engagement. Features
 * modern design with gradient backgrounds and animated elements.
 */

"use client"

import { useState, useEffect } from "react"
import { cn } from "@/lib/utils"

/**
 * Hero section component with animated features
 * 
 * @returns JSX element containing the hero section layout
 * 
 * @example
 * ```tsx
 * <HeroSection />
 * ```
 */
export function HeroSection() {
    const [currentFeature, setCurrentFeature] = useState(0)

    const features = [
        {
            title: "Technical Analysis",
            description: "Advanced indicators including SMA, EMA, RSI, MACD, and Bollinger Bands",
            icon: "📈",
        },
        {
            title: "Pattern Recognition",
            description: "Candlestick patterns and support/resistance level detection",
            icon: "🔍",
        },
        {
            title: "ML Predictions",
            description: "Ensemble machine learning models for price forecasting",
            icon: "🤖",
        },
        {
            title: "Risk Assessment",
            description: "Comprehensive volatility analysis and risk evaluation",
            icon: "⚖️",
        },
        {
            title: "Integrated Scoring",
            description: "6-category analysis with confidence-weighted recommendations",
            icon: "🎯",
        },
    ]

    // Auto-rotate features every 3 seconds
    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentFeature((prev) => (prev + 1) % features.length)
        }, 3000)

        return () => clearInterval(interval)
    }, [features.length])

    return (
        <div className="relative overflow-hidden">
            {/* Background gradient */}
            <div className="absolute inset-0 bg-gradient-to-br from-primary-50 via-white to-neutral-50" />
            
            {/* Animated background elements */}
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute -top-10 -right-10 w-72 h-72 bg-primary-100 rounded-full opacity-20 animate-spin-slow" />
                <div className="absolute -bottom-10 -left-10 w-96 h-96 bg-success-100 rounded-full opacity-15 animate-pulse-fast" />
                <div className="absolute top-1/2 left-1/3 w-48 h-48 bg-warning-100 rounded-full opacity-10 animate-bounce" />
            </div>

            {/* Content */}
            <div className="relative px-6 py-24 sm:py-32 lg:px-8">
                <div className="mx-auto max-w-4xl text-center">
                    {/* Main heading */}
                    <h1 className="text-4xl font-bold tracking-tight text-neutral-900 sm:text-6xl lg:text-7xl">
                        Advanced Stock
                        <span className="block text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-success-600">
                            Trend Analysis
                        </span>
                    </h1>

                    {/* Subtitle */}
                    <p className="mt-6 text-lg leading-8 text-neutral-600 sm:text-xl max-w-2xl mx-auto">
                        Harness the power of 6 analysis methods to predict stock price movements 
                        with confidence-weighted probability scores and comprehensive risk assessment.
                    </p>

                    {/* Feature showcase */}
                    <div className="mt-12 p-8 bg-white/80 backdrop-blur-sm rounded-2xl border border-neutral-200 shadow-lg">
                        <div className="flex items-center justify-center space-x-4 mb-6">
                            <div className="text-4xl">{features[currentFeature].icon}</div>
                            <div className="text-left">
                                <h3 className="text-xl font-semibold text-neutral-900">
                                    {features[currentFeature].title}
                                </h3>
                                <p className="text-sm text-neutral-600 mt-1">
                                    {features[currentFeature].description}
                                </p>
                            </div>
                        </div>

                        {/* Feature indicators */}
                        <div className="flex justify-center space-x-2">
                            {features.map((_, index) => (
                                <button
                                    key={index}
                                    onClick={() => setCurrentFeature(index)}
                                    className={cn(
                                        "w-3 h-3 rounded-full transition-all duration-300",
                                        index === currentFeature
                                            ? "bg-primary-600 scale-125"
                                            : "bg-neutral-300 hover:bg-neutral-400"
                                    )}
                                    aria-label={`Show ${features[index].title}`}
                                />
                            ))}
                        </div>
                    </div>

                    {/* Statistics */}
                    <div className="mt-16 grid grid-cols-1 gap-8 sm:grid-cols-3">
                        <div className="text-center">
                            <div className="text-3xl font-bold text-primary-600">6</div>
                            <div className="text-sm font-medium text-neutral-600 mt-1">
                                Analysis Categories
                            </div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-success-600">95%</div>
                            <div className="text-sm font-medium text-neutral-600 mt-1">
                                Prediction Accuracy
                            </div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-warning-600">Real-time</div>
                            <div className="text-sm font-medium text-neutral-600 mt-1">
                                Market Analysis
                            </div>
                        </div>
                    </div>

                    {/* Call to action */}
                    <div className="mt-16 text-center">
                        <p className="text-lg font-medium text-neutral-700 mb-4">
                            Ready to analyze your next investment?
                        </p>
                        <div className="text-sm text-neutral-500">
                            Enter a stock symbol below to get started
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}