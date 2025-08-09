/**
 * Error page for stock analysis
 *
 * @description Displays error state when the analysis page encounters an error.
 * This is automatically shown by Next.js App Router when an error occurs in the page component.
 */

"use client" // Error components must be Client Components

import { useEffect } from "react"
import Link from "next/link"

interface ErrorProps {
    error: Error & { digest?: string }
    reset: () => void
}

/**
 * Error component for analysis page
 *
 * @description Shows error information and recovery options when the analysis fails.
 * Automatically integrated with Next.js App Router error boundaries.
 *
 * @param props - Error properties including error object and reset function
 * @returns JSX element containing the error interface
 *
 * @example
 * // This component is automatically used by Next.js when an error occurs
 * // in the page component or its children
 */
export default function Error({ error, reset }: ErrorProps) {
    useEffect(() => {
        // Log the error to an error reporting service
        console.error("❌ Analysis page error:", error)
    }, [error])

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

            {/* Error Content */}
            <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                <div className="max-w-2xl mx-auto text-center">
                    {/* Error Icon */}
                    <div className="mb-8">
                        <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
                            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                                />
                            </svg>
                        </div>

                        <h1 className="text-3xl font-bold text-neutral-900 mb-2">分析エラー</h1>

                        <p className="text-lg text-neutral-600 mb-8">株式分析中にエラーが発生しました</p>
                    </div>

                    {/* Error Details */}
                    <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-8 text-left">
                        <h3 className="text-lg font-medium text-red-800 mb-3">エラー詳細</h3>
                        <p className="text-red-700 mb-4 font-mono text-sm bg-red-100 p-3 rounded">
                            {error.message || "不明なエラーが発生しました"}
                        </p>

                        {error.digest && <p className="text-red-600 text-xs">エラーID: {error.digest}</p>}
                    </div>

                    {/* Recovery Options */}
                    <div className="space-y-6">
                        <h3 className="text-lg font-medium text-neutral-900">この問題を解決するには</h3>

                        <div className="grid gap-4 sm:grid-cols-2">
                            {/* Try Again Button */}
                            <button onClick={reset} className="btn btn-primary p-4 h-auto">
                                <div>
                                    <div className="font-medium">再試行</div>
                                    <div className="text-sm opacity-90">分析をもう一度実行する</div>
                                </div>
                            </button>

                            {/* Go Home Button */}
                            <Link href="/" className="btn btn-outline p-4 h-auto inline-block">
                                <div>
                                    <div className="font-medium">トップページに戻る</div>
                                    <div className="text-sm opacity-70">新しい分析を始める</div>
                                </div>
                            </Link>
                        </div>

                        {/* Additional Help */}
                        <div className="pt-6 border-t border-neutral-200">
                            <h4 className="text-sm font-medium text-neutral-700 mb-3">よくある原因</h4>
                            <ul className="text-sm text-neutral-600 space-y-2 text-left max-w-md mx-auto">
                                <li className="flex items-start">
                                    <span className="w-2 h-2 bg-neutral-400 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                                    無効な株式コードが指定された
                                </li>
                                <li className="flex items-start">
                                    <span className="w-2 h-2 bg-neutral-400 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                                    ネットワーク接続の問題
                                </li>
                                <li className="flex items-start">
                                    <span className="w-2 h-2 bg-neutral-400 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                                    サーバーの一時的な問題
                                </li>
                                <li className="flex items-start">
                                    <span className="w-2 h-2 bg-neutral-400 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                                    市場閉場時関のデータ取得制限
                                </li>
                            </ul>
                        </div>

                        {/* Refresh Page Alternative */}
                        <div className="pt-4">
                            <button
                                onClick={() => window.location.reload()}
                                className="text-sm text-primary-600 hover:text-primary-800 underline"
                            >
                                ページをリロードして再試行
                            </button>
                        </div>
                    </div>
                </div>
            </main>

            {/* Footer */}
            <footer className="border-t border-neutral-200 bg-white">
                <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                    <div className="text-center text-sm text-neutral-600">
                        <p>トレンドスコープ • 高度な株価分析プラットフォーム</p>
                        <p className="mt-1">問題が続く場合は、サポートにお問い合わせください。</p>
                    </div>
                </div>
            </footer>
        </div>
    )
}
