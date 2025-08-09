/**
 * Stock analysis form component for symbol input and analysis initiation
 *
 * @description Interactive form component that handles stock symbol input
 * with validation, suggestions, and integration with the analysis API.
 * Features real-time validation, popular stock suggestions, and loading states.
 */

"use client"

import { useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { cn, isValidStockSymbol, normalizeStockSymbol, debounce } from "@/lib/utils"
import { StockAnalysisFormProps } from "@/types/analysis"

// Popular stock symbols for quick selection (US and Japanese markets)
const POPULAR_STOCKS = [
    { symbol: "AAPL", name: "アップル" },
    { symbol: "GOOGL", name: "アルファベット（グーグル）" },
    { symbol: "MSFT", name: "マイクロソフト" },
    { symbol: "TSLA", name: "テスラ" },
    { symbol: "7203.T", name: "トヨタ自動車" },
    { symbol: "6758.T", name: "ソニーグループ" },
    { symbol: "7267.T", name: "本田技研工業" },
    { symbol: "6861.T", name: "キーエンス" },
] as const

/**
 * Stock analysis form component
 *
 * @param props - Component props including optional onAnalyze callback
 * @returns JSX form element with symbol input and analysis controls
 *
 * @example
 * ```tsx
 * <StockAnalysisForm onAnalyze={handleAnalyzeStock} />
 * ```
 */
export function StockAnalysisForm({ onAnalyze }: StockAnalysisFormProps) {
    const router = useRouter()
    const [symbol, setSymbol] = useState("")
    const [error, setError] = useState("")
    const [suggestions, setSuggestions] = useState<string[]>([])
    const [isNavigating, setIsNavigating] = useState(false)

    /**
     * Validates the entered stock symbol
     *
     * @param value - Symbol to validate
     * @returns Error message if invalid, empty string if valid
     */
    const validateSymbol = useCallback((value: string): string => {
        const normalized = normalizeStockSymbol(value)

        if (!normalized) {
            return "株式コードを入力してください"
        }

        if (normalized.length < 1 || normalized.length > 10) {
            return "株式コードは1〜10文字で入力してください"
        }

        if (!isValidStockSymbol(normalized)) {
            return "有効な株式コードを入力してください（例: AAPL, 7203.T）"
        }

        return ""
    }, [])

    /**
     * Debounced validation function
     */
    const debouncedValidation = useCallback(
        debounce((value: string) => {
            const errorMessage = validateSymbol(value)
            setError(errorMessage)

            // Generate suggestions based on input
            if (value.length >= 1 && !errorMessage) {
                const filtered = POPULAR_STOCKS.filter(
                    (stock) =>
                        stock.symbol.toLowerCase().includes(value.toLowerCase()) ||
                        stock.name.toLowerCase().includes(value.toLowerCase()),
                )
                    .map((stock) => stock.symbol)
                    .slice(0, 5)

                setSuggestions(filtered)
            } else {
                setSuggestions([])
            }
        }, 300),
        [validateSymbol],
    )

    /**
     * Handles symbol input changes
     *
     * @param e - Input change event
     */
    const handleSymbolChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value.toUpperCase()
        setSymbol(value)
        debouncedValidation(value)
    }

    /**
     * Handles form submission with navigation
     *
     * @param e - Form submit event
     */
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        const normalizedSymbol = normalizeStockSymbol(symbol)
        const validationError = validateSymbol(normalizedSymbol)

        if (validationError) {
            setError(validationError)
            return
        }

        try {
            setError("")
            setSuggestions([])
            setIsNavigating(true)

            console.log(`🚀 Form submit: navigating to /analysis/${normalizedSymbol}`)

            // Use onAnalyze callback if provided, otherwise navigate directly
            if (onAnalyze) {
                await onAnalyze(normalizedSymbol)
            } else {
                router.push(`/analysis/${normalizedSymbol}` as any)
            }
        } catch (error) {
            console.error("❌ Form submit error:", error)
            const errorMessage = error instanceof Error ? error.message : "エラーが発生しました"
            setError(errorMessage)
        } finally {
            setIsNavigating(false)
        }
    }

    /**
     * Handles quick selection of popular stocks
     *
     * @param selectedSymbol - Pre-defined symbol to analyze
     */
    const handleQuickSelect = async (selectedSymbol: string) => {
        setSymbol(selectedSymbol)
        setError("")
        setSuggestions([])
        setIsNavigating(true)

        try {
            console.log(`🚀 Quick select: navigating to /analysis/${selectedSymbol}`)

            // Use onAnalyze callback if provided, otherwise navigate directly
            if (onAnalyze) {
                await onAnalyze(selectedSymbol)
            } else {
                router.push(`/analysis/${selectedSymbol}` as any)
            }
        } catch (error) {
            console.error("❌ Quick select error:", error)
            const errorMessage = error instanceof Error ? error.message : "エラーが発生しました"
            setError(errorMessage)
        } finally {
            setIsNavigating(false)
        }
    }

    const canSubmit = symbol.length > 0 && !error && !isNavigating

    return (
        <Card className="p-8">
            <div className="text-center mb-8">
                <h2 className="text-2xl font-bold text-neutral-900 mb-2">任意の株式を分析</h2>
                <p className="text-neutral-600">
                    株式コードを入力して、確率に基づく予測で包括的な分析を取得してください
                </p>
            </div>

            {/* Main form */}
            <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-4">
                    <div className="relative">
                        <Input
                            label="株式コード"
                            placeholder="例: AAPL, GOOGL, 7203.T, 6758.T"
                            value={symbol}
                            onChange={handleSymbolChange}
                            error={error}
                            helperText={
                                !error
                                    ? "米国株（AAPL）または日本株（7203.T）の株式コードを入力してください"
                                    : undefined
                            }
                            size="lg"
                            disabled={isNavigating}
                            startIcon={
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                                    />
                                </svg>
                            }
                        />

                        {/* Suggestions dropdown */}
                        {suggestions.length > 0 && (
                            <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-neutral-200 rounded-md shadow-lg z-10">
                                {suggestions.map((suggestionSymbol) => {
                                    const stock = POPULAR_STOCKS.find((s) => s.symbol === suggestionSymbol)
                                    return (
                                        <button
                                            key={suggestionSymbol}
                                            type="button"
                                            onClick={() => {
                                                setSymbol(suggestionSymbol)
                                                setSuggestions([])
                                                setError("")
                                            }}
                                            className="w-full px-4 py-2 text-left hover:bg-neutral-50 focus:bg-neutral-50 focus:outline-none border-b border-neutral-100 last:border-b-0"
                                        >
                                            <div className="font-medium text-neutral-900">{suggestionSymbol}</div>
                                            {stock && <div className="text-sm text-neutral-600">{stock.name}</div>}
                                        </button>
                                    )
                                })}
                            </div>
                        )}
                    </div>

                    <Button
                        type="submit"
                        size="lg"
                        className="w-full"
                        disabled={!canSubmit}
                        isLoading={isNavigating}
                        loadingText="ページを読み込み中..."
                    >
                        {isNavigating ? "読み込み中..." : "株式を分析"}
                    </Button>
                </div>
            </form>

            {/* Popular stocks section */}
            <div className="mt-8">
                <div className="text-center mb-4">
                    <h3 className="text-sm font-medium text-neutral-700 mb-2">または人気銘柄を試す</h3>
                    <p className="text-xs text-neutral-500">下記のコードをクリックして即座に分析</p>
                </div>

                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                    {POPULAR_STOCKS.map((stock) => (
                        <button
                            key={stock.symbol}
                            onClick={() => handleQuickSelect(stock.symbol)}
                            disabled={isNavigating}
                            className={cn(
                                "p-3 text-left rounded-lg border border-neutral-200 hover:border-primary-300 hover:bg-primary-50 transition-colors group disabled:opacity-50 disabled:cursor-not-allowed",
                                isNavigating && "cursor-not-allowed",
                            )}
                        >
                            <div className="font-semibold text-neutral-900 group-hover:text-primary-700">
                                {stock.symbol}
                            </div>
                            <div className="text-xs text-neutral-600 group-hover:text-primary-600 mt-1 truncate">
                                {stock.name}
                            </div>
                        </button>
                    ))}
                </div>
            </div>

            {/* Analysis features preview */}
            <div className="mt-8 pt-6 border-t border-neutral-200">
                <div className="text-center mb-4">
                    <h4 className="text-sm font-medium text-neutral-700">取得できる分析内容</h4>
                </div>

                <div className="flex flex-wrap justify-center gap-2">
                    <Badge variant="outline" size="sm">
                        テクニカル指標
                    </Badge>
                    <Badge variant="outline" size="sm">
                        パターン分析
                    </Badge>
                    <Badge variant="outline" size="sm">
                        機械学習予測
                    </Badge>
                    <Badge variant="outline" size="sm">
                        リスク評価
                    </Badge>
                    <Badge variant="outline" size="sm">
                        信頼度スコア
                    </Badge>
                    <Badge variant="outline" size="sm">
                        売買シグナル
                    </Badge>
                </div>
            </div>
        </Card>
    )
}
