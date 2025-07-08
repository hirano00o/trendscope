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
            title: "テクニカル分析",
            description: "SMA、EMA、RSI、MACD、ボリンジャーバンドを含む高度な指標",
            icon: "📈",
        },
        {
            title: "パターン認識",
            description: "ローソク足パターンとサポート/レジスタンスレベルの検出",
            icon: "🔍",
        },
        {
            title: "機械学習予測",
            description: "価格予測のためのアンサンブル機械学習モデル",
            icon: "🤖",
        },
        {
            title: "リスク評価",
            description: "包括的なボラティリティ分析とリスク評価",
            icon: "⚖️",
        },
        {
            title: "統合スコアリング",
            description: "信頼度加重による推奨を含む6カテゴリー分析",
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
                        高度な株価
                        <span className="block text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-success-600">
                            トレンド分析
                        </span>
                    </h1>

                    {/* Subtitle */}
                    <p className="mt-6 text-lg leading-8 text-neutral-600 sm:text-xl max-w-2xl mx-auto">
                        6つの分析手法の力を活用し、信頼度加重の確率スコアと包括的なリスク評価で
                        株価の動向を予測します。
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
                                分析カテゴリー
                            </div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-success-600">95%</div>
                            <div className="text-sm font-medium text-neutral-600 mt-1">
                                予測精度
                            </div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-warning-600">リアルタイム</div>
                            <div className="text-sm font-medium text-neutral-600 mt-1">
                                マーケット分析
                            </div>
                        </div>
                    </div>

                    {/* Call to action */}
                    <div className="mt-16 text-center">
                        <p className="text-lg font-medium text-neutral-700 mb-4">
                            次の投資分析を始める準備はできましたか？
                        </p>
                        <div className="text-sm text-neutral-500">
                            下記に株式コードを入力して開始してください
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}