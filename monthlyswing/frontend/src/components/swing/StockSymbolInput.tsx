/**
 * Stock Symbol Input Component for Monthly Swing Trading
 *
 * @description Form component for inputting stock symbols with validation,
 * popular stock suggestions, and analysis trigger functionality.
 */

'use client';

import { useState, useEffect, useId } from 'react';

/**
 * Popular stocks configuration
 */
interface PopularStocks {
  us: string[];
  japan: string[];
}

/**
 * Props for StockSymbolInput component
 */
export interface StockSymbolInputProps {
  /** Callback function triggered when analysis is requested */
  onAnalyze: (symbol: string) => void;
  /** Loading state indicator */
  isAnalyzing?: boolean;
  /** Custom placeholder text */
  placeholder?: string;
  /** Popular stocks configuration */
  popularStocks?: PopularStocks;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Default popular stocks
 */
const DEFAULT_POPULAR_STOCKS: PopularStocks = {
  us: ['AAPL', 'MSFT', 'GOOGL', 'TSLA'],
  japan: ['7203.T', '6758.T', '7267.T', '6861.T'],
};

/**
 * Stock symbol input component with validation and popular stock suggestions
 *
 * @param props - Component props
 * @returns JSX element containing the stock symbol input form
 *
 * @example
 * ```tsx
 * function AnalysisPage() {
 *   const [isAnalyzing, setIsAnalyzing] = useState(false);
 *   
 *   const handleAnalysis = async (symbol: string) => {
 *     setIsAnalyzing(true);
 *     try {
 *       await performAnalysis(symbol);
 *     } finally {
 *       setIsAnalyzing(false);
 *     }
 *   };
 *
 *   return (
 *     <StockSymbolInput
 *       onAnalyze={handleAnalysis}
 *       isAnalyzing={isAnalyzing}
 *     />
 *   );
 * }
 * ```
 */
export function StockSymbolInput({
  onAnalyze,
  isAnalyzing = false,
  placeholder = '例: AAPL, 7203.T',
  popularStocks = DEFAULT_POPULAR_STOCKS,
  className = '',
}: StockSymbolInputProps) {
  const [symbol, setSymbol] = useState('');
  const [validationError, setValidationError] = useState('');
  
  // Generate unique IDs for accessibility
  const inputId = useId();
  const errorId = useId();

  /**
   * Validates stock symbol format
   */
  const validateSymbol = (input: string): string => {
    const trimmed = input.trim();
    
    if (!trimmed) {
      return '';
    }

    // Basic symbol validation - alphanumeric, dots, and hyphens
    const symbolRegex = /^[A-Z0-9.-]+$/;
    if (!symbolRegex.test(trimmed)) {
      return '無効な文字が含まれています。英数字、ドット、ハイフンのみ使用可能です。';
    }

    // Length validation
    if (trimmed.length > 20) {
      return 'シンボルは20文字以内で入力してください。';
    }

    return '';
  };

  /**
   * Handles input value changes
   */
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const inputValue = e.target.value.toUpperCase();
    setSymbol(inputValue);
    
    // Clear validation error when user starts typing
    if (validationError && inputValue !== symbol) {
      setValidationError('');
    }
  };

  /**
   * Handles form submission
   */
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isAnalyzing) return;
    
    const trimmedSymbol = symbol.trim();
    if (!trimmedSymbol) return;

    const error = validateSymbol(trimmedSymbol);
    if (error) {
      setValidationError(error);
      return;
    }

    try {
      onAnalyze(trimmedSymbol);
      setValidationError('');
    } catch (error) {
      console.error('Error during analysis callback:', error);
      setValidationError('分析の開始中にエラーが発生しました。');
    }
  };

  /**
   * Handles popular stock selection
   */
  const handlePopularStockClick = (stockSymbol: string) => {
    if (isAnalyzing) return;
    setSymbol(stockSymbol);
    setValidationError('');
  };

  /**
   * Handles input clearing
   */
  const handleClear = () => {
    if (isAnalyzing) return;
    setSymbol('');
    setValidationError('');
  };

  // Validation check on symbol change
  useEffect(() => {
    if (symbol) {
      const error = validateSymbol(symbol);
      if (error !== validationError) {
        setValidationError(error);
      }
    }
  }, [symbol, validationError]);

  const isSubmitDisabled = !symbol.trim() || !!validationError || isAnalyzing;

  return (
    <div className={`w-full max-w-md mx-auto space-y-6 ${className}`}>
      {/* Input Form */}
      <form onSubmit={handleSubmit} className="card">
        <div className="space-y-4">
          {/* Input Field */}
          <div>
            <label
              htmlFor={inputId}
              className="block text-sm font-medium text-neutral-700 mb-2"
            >
              銘柄シンボル
            </label>
            <div className="relative">
              <input
                type="text"
                id={inputId}
                value={symbol}
                onChange={handleInputChange}
                placeholder={placeholder}
                disabled={isAnalyzing}
                aria-label="銘柄シンボルを入力してください"
                aria-describedby={validationError ? errorId : undefined}
                aria-invalid={!!validationError}
                className={`block w-full rounded-md border px-3 py-2 text-sm placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-neutral-100 disabled:cursor-not-allowed ${
                  validationError
                    ? 'border-red-500 focus:ring-red-500 focus:border-red-500'
                    : 'border-neutral-300'
                }`}
              />
              {/* Clear Button */}
              {symbol && !isAnalyzing && (
                <button
                  type="button"
                  onClick={handleClear}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 text-neutral-400 hover:text-neutral-600 focus:outline-none"
                  aria-label="クリア"
                >
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              )}
            </div>
            
            {/* Help Text */}
            <p className="mt-2 text-xs text-neutral-500">
              米国株（AAPL）または日本株（7203.T）のシンボルを入力してください
            </p>
            
            {/* Validation Error */}
            {validationError && (
              <p id={errorId} role="alert" className="mt-2 text-sm text-red-600">
                {validationError}
              </p>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSubmitDisabled}
            className="w-full rounded-md bg-primary-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-neutral-400 transition-colors"
          >
            {isAnalyzing ? (
              <div className="flex items-center justify-center">
                <div className="loading-spinner mr-2 h-4 w-4" />
                分析中...
              </div>
            ) : (
              '月次スイング分析実行'
            )}
          </button>
        </div>
      </form>

      {/* Popular Stocks */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* US Stocks */}
        <div className="card">
          <h4 className="card-title text-sm mb-3">米国株</h4>
          <div className="space-y-2">
            {popularStocks.us.map((stockSymbol) => (
              <button
                key={stockSymbol}
                onClick={() => handlePopularStockClick(stockSymbol)}
                disabled={isAnalyzing}
                className="block w-full rounded bg-neutral-100 px-3 py-2 text-left text-sm font-mono text-neutral-700 hover:bg-neutral-200 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {stockSymbol}
              </button>
            ))}
          </div>
        </div>

        {/* Japanese Stocks */}
        <div className="card">
          <h4 className="card-title text-sm mb-3">日本株</h4>
          <div className="space-y-2">
            {popularStocks.japan.map((stockSymbol) => (
              <button
                key={stockSymbol}
                onClick={() => handlePopularStockClick(stockSymbol)}
                disabled={isAnalyzing}
                className="block w-full rounded bg-neutral-100 px-3 py-2 text-left text-sm font-mono text-neutral-700 hover:bg-neutral-200 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {stockSymbol}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}