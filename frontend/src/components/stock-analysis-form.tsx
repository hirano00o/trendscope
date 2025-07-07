/**
 * Stock analysis form component for symbol input and analysis initiation
 * 
 * @description Interactive form component that handles stock symbol input
 * with validation, suggestions, and integration with the analysis API.
 * Features real-time validation, popular stock suggestions, and loading states.
 */

"use client"

import { useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { cn, isValidStockSymbol, normalizeStockSymbol, debounce } from "@/lib/utils"
import { useErrorHandler } from "@/lib/error-handling"
import { StockAnalysisFormProps } from "@/types/analysis"

// Popular stock symbols for quick selection
const POPULAR_STOCKS = [
    { symbol: "AAPL", name: "Apple Inc." },
    { symbol: "GOOGL", name: "Alphabet Inc." },
    { symbol: "MSFT", name: "Microsoft Corp." },
    { symbol: "AMZN", name: "Amazon.com Inc." },
    { symbol: "TSLA", name: "Tesla Inc." },
    { symbol: "NVDA", name: "NVIDIA Corp." },
    { symbol: "META", name: "Meta Platforms Inc." },
    { symbol: "NFLX", name: "Netflix Inc." },
] as const

/**
 * Stock analysis form component
 * 
 * @param props - Component props including onAnalyze callback and loading state
 * @returns JSX form element with symbol input and analysis controls
 * 
 * @example
 * ```tsx
 * <StockAnalysisForm
 *   onAnalyze={handleAnalyzeStock}
 *   isLoading={isAnalyzing}
 * />
 * ```
 */
export function StockAnalysisForm({ onAnalyze, isLoading }: StockAnalysisFormProps) {
    const [symbol, setSymbol] = useState("")
    const [error, setError] = useState("")
    const [suggestions, setSuggestions] = useState<string[]>([])
    const { handleError } = useErrorHandler()

    /**
     * Validates the entered stock symbol
     * 
     * @param value - Symbol to validate
     * @returns Error message if invalid, empty string if valid
     */
    const validateSymbol = useCallback((value: string): string => {
        const normalized = normalizeStockSymbol(value)
        
        if (!normalized) {
            return "Please enter a stock symbol"
        }
        
        if (normalized.length < 1 || normalized.length > 10) {
            return "Symbol must be 1-10 characters long"
        }
        
        if (!isValidStockSymbol(normalized)) {
            return "Symbol can only contain letters"
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
                const filtered = POPULAR_STOCKS
                    .filter(stock => 
                        stock.symbol.toLowerCase().includes(value.toLowerCase()) ||
                        stock.name.toLowerCase().includes(value.toLowerCase())
                    )
                    .map(stock => stock.symbol)
                    .slice(0, 5)
                
                setSuggestions(filtered)
            } else {
                setSuggestions([])
            }
        }, 300),
        [validateSymbol]
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
     * Handles form submission
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
            await onAnalyze(normalizedSymbol)
        } catch (error) {
            const errorInfo = handleError(error, "stock-analysis-form")
            setError(errorInfo.message)
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
        
        try {
            await onAnalyze(selectedSymbol)
        } catch (error) {
            const errorInfo = handleError(error, "quick-select")
            setError(errorInfo.message)
        }
    }

    const canSubmit = symbol.length > 0 && !error && !isLoading

    return (
        <Card className="p-8">
            <div className="text-center mb-8">
                <h2 className="text-2xl font-bold text-neutral-900 mb-2">
                    Analyze Any Stock
                </h2>
                <p className="text-neutral-600">
                    Enter a stock symbol to get comprehensive analysis with probability-based predictions
                </p>
            </div>

            {/* Main form */}
            <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-4">
                    <div className="relative">
                        <Input
                            label="Stock Symbol"
                            placeholder="e.g., AAPL, GOOGL, MSFT"
                            value={symbol}
                            onChange={handleSymbolChange}
                            error={error}
                            helperText={!error ? "Enter any valid stock symbol for analysis" : undefined}
                            size="lg"
                            disabled={isLoading}
                            startIcon={
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                </svg>
                            }
                        />

                        {/* Suggestions dropdown */}
                        {suggestions.length > 0 && (
                            <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-neutral-200 rounded-md shadow-lg z-10">
                                {suggestions.map((suggestionSymbol) => {
                                    const stock = POPULAR_STOCKS.find(s => s.symbol === suggestionSymbol)
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
                                            {stock && (
                                                <div className="text-sm text-neutral-600">{stock.name}</div>
                                            )}
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
                        isLoading={isLoading}
                        loadingText="Analyzing Stock..."
                    >
                        {isLoading ? "Running Analysis..." : "Analyze Stock"}
                    </Button>
                </div>
            </form>

            {/* Popular stocks section */}
            <div className="mt-8">
                <div className="text-center mb-4">
                    <h3 className="text-sm font-medium text-neutral-700 mb-2">
                        Or try a popular stock
                    </h3>
                    <p className="text-xs text-neutral-500">
                        Click any symbol below for instant analysis
                    </p>
                </div>

                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                    {POPULAR_STOCKS.map((stock) => (
                        <button
                            key={stock.symbol}
                            onClick={() => handleQuickSelect(stock.symbol)}
                            disabled={isLoading}
                            className={cn(
                                "p-3 text-left rounded-lg border border-neutral-200 hover:border-primary-300 hover:bg-primary-50 transition-colors group disabled:opacity-50 disabled:cursor-not-allowed",
                                isLoading && "cursor-not-allowed"
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
                    <h4 className="text-sm font-medium text-neutral-700">
                        What you'll get
                    </h4>
                </div>
                
                <div className="flex flex-wrap justify-center gap-2">
                    <Badge variant="outline" size="sm">Technical Indicators</Badge>
                    <Badge variant="outline" size="sm">Pattern Analysis</Badge>
                    <Badge variant="outline" size="sm">ML Predictions</Badge>
                    <Badge variant="outline" size="sm">Risk Assessment</Badge>
                    <Badge variant="outline" size="sm">Confidence Scores</Badge>
                    <Badge variant="outline" size="sm">Buy/Hold/Sell Signals</Badge>
                </div>
            </div>
        </Card>
    )
}