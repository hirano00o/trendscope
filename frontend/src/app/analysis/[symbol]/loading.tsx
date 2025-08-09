/**
 * Loading page for stock analysis
 *
 * @description Displays loading state while the analysis page is being rendered.
 * This is automatically shown by Next.js App Router when the page component is loading.
 */

/**
 * Loading component for analysis page
 *
 * @description Shows a loading spinner and message while the analysis is being fetched.
 * Automatically integrated with Next.js App Router loading states.
 *
 * @returns JSX element containing the loading interface
 *
 * @example
 * // This component is automatically used by Next.js when the page is loading
 * // URL: /analysis/AAPL (while loading)
 */
export default function Loading() {
    return (
        <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-neutral-100">
            {/* Navigation Header */}
            <nav className="border-b border-neutral-200 bg-white/80 backdrop-blur-sm">
                <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                    <div className="flex h-16 items-center justify-between">
                        <div className="flex items-center">
                            <div className="text-xl font-bold text-neutral-900">トレンドスコープ</div>
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

            {/* Loading Content */}
            <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                <div className="flex items-center justify-center min-h-[60vh]">
                    <div className="text-center">
                        {/* Loading Spinner */}
                        <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-4 border-primary-600 mb-6"></div>

                        {/* Loading Text */}
                        <h2 className="text-2xl font-semibold text-neutral-900 mb-3">分析を準備中...</h2>

                        <p className="text-neutral-600 mb-6">包括的な株式分析を開始しています</p>

                        {/* Loading Steps */}
                        <div className="max-w-md mx-auto">
                            <div className="space-y-3 text-sm text-neutral-500">
                                <div className="flex items-center justify-center">
                                    <div className="w-2 h-2 bg-primary-400 rounded-full animate-pulse mr-2"></div>
                                    <span>株価データを取得中...</span>
                                </div>
                                <div className="flex items-center justify-center">
                                    <div
                                        className="w-2 h-2 bg-primary-400 rounded-full animate-pulse mr-2"
                                        style={{ animationDelay: "0.2s" }}
                                    ></div>
                                    <span>テクニカル分析を実行中...</span>
                                </div>
                                <div className="flex items-center justify-center">
                                    <div
                                        className="w-2 h-2 bg-primary-400 rounded-full animate-pulse mr-2"
                                        style={{ animationDelay: "0.4s" }}
                                    ></div>
                                    <span>機械学習モデルを適用中...</span>
                                </div>
                            </div>
                        </div>

                        {/* Progress Bar */}
                        <div className="mt-8 max-w-xs mx-auto">
                            <div className="w-full bg-neutral-200 rounded-full h-2">
                                <div
                                    className="bg-primary-600 h-2 rounded-full animate-pulse"
                                    style={{ width: "60%" }}
                                ></div>
                            </div>
                            <p className="text-xs text-neutral-500 mt-2">しばらくお待ちください...</p>
                        </div>
                    </div>
                </div>
            </main>

            {/* Footer */}
            <footer className="border-t border-neutral-200 bg-white">
                <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
                    <div className="text-center text-sm text-neutral-600">
                        <p>トレンドスコープ • 高度な株価分析プラットフォーム</p>
                    </div>
                </div>
            </footer>
        </div>
    )
}
