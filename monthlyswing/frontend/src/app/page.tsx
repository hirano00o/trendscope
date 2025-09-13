/**
 * Monthly Swing Trading Analysis - Main Dashboard Page
 *
 * @description Main entry point for the monthly swing trading analysis application.
 * Provides interface for stock symbol input and displays analysis results focused
 * on monthly swing trading strategies with 1-month holding periods.
 */

'use client';

import { useState } from 'react';

import { StockSymbolInput } from '@/components/swing/StockSymbolInput';
import { useMonthlySwingAnalysis } from '@/hooks/use-monthly-swing-analysis';
import { MonthlyTrendResult } from '@/types/monthly-swing';

/**
 * Main dashboard page component
 *
 * @returns JSX element containing the complete dashboard layout
 *
 * @example
 * ```tsx
 * // This component is automatically rendered for the "/" route
 * export default function Page() {
 *   return <MainDashboard />
 * }
 * ```
 */
export default function Page() {
  const [currentSymbol, setCurrentSymbol] = useState('');
  const [analysisData, setAnalysisData] = useState<MonthlyTrendResult | null>(null);

  // Use TanStack Query hook for API calls
  const {
    data,
    isLoading,
    error,
    errorMessage,
    refetch,
    hasData
  } = useMonthlySwingAnalysis(currentSymbol, {
    enabled: !!currentSymbol, // Only run query when symbol is set
    onSuccess: (data) => {
      setAnalysisData(data);
      console.log(`✅ Monthly swing analysis completed for: ${data.symbol}`);
    },
    onError: (error) => {
      console.error('❌ Monthly swing analysis failed:', error);
      setAnalysisData(null);
    },
  });

  /**
   * Handles stock analysis request from the input component
   *
   * @param submittedSymbol - Stock symbol to analyze (e.g., "AAPL", "7203.T")
   */
  const handleAnalysis = async (submittedSymbol: string) => {
    console.log(`🚀 Starting monthly swing analysis for symbol: ${submittedSymbol}`);
    
    // Clear previous data
    setAnalysisData(null);
    
    // Set the symbol to trigger the query
    setCurrentSymbol(submittedSymbol);
    
    // If symbol is the same, manually refetch
    if (submittedSymbol === currentSymbol) {
      refetch();
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="space-y-12">
        {/* Hero Section */}
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-neutral-900 sm:text-4xl">
            月次スイングトレード分析
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-neutral-600">
            1ヶ月程度の保有期間を想定したスイングトレード戦略のための
            <br />
            トレンド分析とシグナル生成システム
          </p>
        </div>

        {/* Stock Symbol Input */}
        <StockSymbolInput
          onAnalyze={handleAnalysis}
          isAnalyzing={isLoading}
        />

        {/* Analysis Results */}
        {error && (
          <div className="mx-auto max-w-4xl">
            <div className="card border-red-200 bg-red-50">
              <div className="text-center">
                <div className="mb-4">
                  <svg
                    className="mx-auto h-12 w-12 text-red-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-red-900 mb-2">
                  分析エラー
                </h3>
                <p className="text-sm text-red-700">
                  {errorMessage || 'エラーが発生しました。しばらく後に再試行してください。'}
                </p>
                {currentSymbol && (
                  <button
                    onClick={() => refetch()}
                    className="mt-4 rounded-md bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                  >
                    再試行
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {hasData && analysisData && (
          <div className="mx-auto max-w-6xl">
            <div className="space-y-8">
              {/* Analysis Header */}
              <div className="text-center">
                <h2 className="text-2xl font-bold text-neutral-900">
                  {analysisData.symbol} - 月次スイング分析結果
                </h2>
                <p className="mt-2 text-sm text-neutral-600">
                  分析実行日: {new Date(analysisData.analysis_date).toLocaleDateString('ja-JP')}
                </p>
              </div>

              {/* Key Metrics Grid */}
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                {/* Trend Direction */}
                <div className="card">
                  <div className="card-header">
                    <h3 className="card-title">トレンド方向</h3>
                  </div>
                  <div className="text-center">
                    <div className={`trend-indicator ${
                      analysisData.trend_strength.direction === '上昇' ? 'trend-up' :
                      analysisData.trend_strength.direction === '下降' ? 'trend-down' :
                      'trend-sideways'
                    }`}>
                      {analysisData.trend_strength.direction}
                    </div>
                    <p className="mt-2 text-xs text-neutral-600">
                      強度: {Math.round(analysisData.trend_strength.strength * 100)}%
                    </p>
                  </div>
                </div>

                {/* Continuation Probability */}
                <div className="card">
                  <div className="card-header">
                    <h3 className="card-title">継続確率</h3>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-primary-600">
                      {Math.round(analysisData.continuation_probability * 100)}%
                    </div>
                    <p className="mt-2 text-xs text-neutral-600">
                      トレンド継続見込み
                    </p>
                  </div>
                </div>

                {/* Analysis Confidence */}
                <div className="card">
                  <div className="card-header">
                    <h3 className="card-title">分析信頼度</h3>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-neutral-900">
                      {Math.round(analysisData.trend_strength.confidence * 100)}%
                    </div>
                    <p className="mt-2 text-xs text-neutral-600">
                      分析精度指標
                    </p>
                  </div>
                </div>

                {/* Duration */}
                <div className="card">
                  <div className="card-header">
                    <h3 className="card-title">トレンド継続期間</h3>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-neutral-900">
                      {analysisData.trend_strength.duration_days}日
                    </div>
                    <p className="mt-2 text-xs text-neutral-600">
                      現在のトレンド継続日数
                    </p>
                  </div>
                </div>
              </div>

              {/* Swing Signals */}
              {analysisData.swing_signals.length > 0 && (
                <div className="card">
                  <div className="card-header">
                    <h3 className="card-title">スイングトレードシグナル</h3>
                  </div>
                  <div className="space-y-4">
                    {analysisData.swing_signals.map((signal, index) => (
                      <div key={index} className="border-l-4 border-primary-500 bg-primary-50 p-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className={`signal-${signal.signal_type === '買い' ? 'buy' : 
                            signal.signal_type === '売り' ? 'sell' : 
                            signal.signal_type === '保持' ? 'hold' : 'wait'}`}>
                            {signal.signal_type}シグナル
                          </span>
                          <span className="text-sm text-neutral-600">
                            信頼度: {Math.round(signal.confidence * 100)}%
                          </span>
                        </div>
                        
                        {(signal.target_price || signal.stop_loss) && (
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            {signal.target_price && (
                              <div>
                                <span className="font-medium">目標価格:</span> ${signal.target_price.toFixed(2)}
                              </div>
                            )}
                            {signal.stop_loss && (
                              <div>
                                <span className="font-medium">ストップロス:</span> ${signal.stop_loss.toFixed(2)}
                              </div>
                            )}
                          </div>
                        )}
                        
                        {signal.supporting_factors.length > 0 && (
                          <div className="mt-3">
                            <div className="text-sm font-medium text-neutral-700 mb-1">根拠:</div>
                            <ul className="text-sm text-neutral-600 space-y-1">
                              {signal.supporting_factors.map((factor, idx) => (
                                <li key={idx} className="flex items-start">
                                  <span className="mr-2">•</span>
                                  <span>{factor}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Monthly Returns Summary */}
              {analysisData.monthly_returns.length > 0 && (
                <div className="card">
                  <div className="card-header">
                    <h3 className="card-title">月次リターン履歴</h3>
                  </div>
                  <div className="text-center text-sm text-neutral-600">
                    過去 {analysisData.monthly_returns.length} ヶ月のパフォーマンス
                  </div>
                  <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                    {analysisData.monthly_returns.slice(0, 4).map((monthReturn, index) => (
                      <div key={index} className="text-center">
                        <div className={`text-lg font-bold ${
                          monthReturn.return_rate >= 0 ? 'metric-positive' : 'metric-negative'
                        }`}>
                          {monthReturn.return_rate >= 0 ? '+' : ''}{(monthReturn.return_rate * 100).toFixed(1)}%
                        </div>
                        <div className="text-xs text-neutral-600">
                          {new Date(monthReturn.start_date).getMonth() + 1}月
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="mx-auto max-w-md">
            <div className="card animate-pulse">
              <div className="text-center">
                <div className="loading-spinner mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-neutral-900">
                  月次スイング分析実行中
                </h3>
                <p className="mt-2 text-sm text-neutral-600">
                  {currentSymbol} の月次トレンドデータを分析しています...
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}