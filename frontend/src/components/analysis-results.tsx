/**
 * Analysis results component for displaying comprehensive stock analysis
 *
 * @description Main component for rendering the complete 6-category analysis
 * results including technical indicators, patterns, volatility, ML predictions,
 * fundamental analysis, and integrated scoring with visual representations.
 */

"use client"

import { Card, CardHeader, CardTitle, CardContent, MetricCard } from "@/components/ui/card"
import { Badge, SignalBadge, RiskBadge } from "@/components/ui/badge"
import { Progress, ConfidenceProgress } from "@/components/ui/progress"
import {
    PriceChart,
    TechnicalIndicatorChart,
    VolatilityChart,
    PatternChart,
    createMockHistoricalData,
} from "@/components/charts"
import { cn, formatPrice, formatPercentage, getColorClass } from "@/lib/utils"
import { AnalysisResultsProps } from "@/types/analysis"

/**
 * Main analysis results component
 *
 * @param props - Component props containing analysis data
 * @returns JSX element with comprehensive analysis display
 *
 * @example
 * ```tsx
 * <AnalysisResults data={analysisData} />
 * ```
 */
export function AnalysisResults({ data }: AnalysisResultsProps) {
    const {
        symbol,
        current_price,
        technical_analysis,
        pattern_analysis,
        volatility_analysis,
        ml_analysis,
        fundamental_analysis,
        integrated_score,
        analysis_metadata,
    } = data

    return (
        <div className="space-y-8">
            {/* Overview Section */}
            <Card variant="elevated" size="lg">
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle className="text-2xl">{symbol} 分析</CardTitle>
                            <p className="text-neutral-600 mt-1">現在価格: {formatPrice(current_price)}</p>
                        </div>
                        <div className="text-right">
                            <div className="text-3xl font-bold text-primary-600">
                                {Math.round(integrated_score.overall_score * 100)}
                            </div>
                            <div className="text-sm text-neutral-600">総合スコア</div>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {/* Recommendation */}
                        <div className="text-center">
                            <SignalBadge
                                signal={
                                    integrated_score.recommendation === "BUY"
                                        ? "bullish"
                                        : integrated_score.recommendation === "SELL"
                                          ? "bearish"
                                          : "neutral"
                                }
                                size="lg"
                            >
                                {integrated_score.recommendation === "BUY"
                                    ? "買い"
                                    : integrated_score.recommendation === "SELL"
                                      ? "売り"
                                      : "保有"}
                            </SignalBadge>
                            <p className="text-sm text-neutral-600 mt-2">推奨</p>
                        </div>

                        {/* Confidence Level */}
                        <div>
                            <ConfidenceProgress
                                confidence={integrated_score.confidence_level}
                                showLabel
                                labelPosition="top"
                                size="lg"
                            />
                        </div>

                        {/* Risk Assessment */}
                        <div className="text-center">
                            <RiskBadge
                                risk={integrated_score.risk_assessment.toLowerCase() as "low" | "moderate" | "high"}
                                size="lg"
                            />
                            <p className="text-sm text-neutral-600 mt-2">リスクレベル</p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Price Chart Section */}
            <PriceChart
                data={createMockHistoricalData(30, current_price)}
                height={400}
                showVolume={true}
                timeRange="1M"
                indicators={{
                    sma: [
                        { period: 20, color: "#10B981" },
                        { period: 50, color: "#F59E0B" },
                    ],
                    bollinger: {
                        show: technical_analysis.indicators.bollinger_upper !== undefined,
                        color: "#8B5CF6",
                    },
                }}
            />

            {/* Category Scores Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {integrated_score.category_scores.map((categoryScore) => (
                    <MetricCard
                        key={categoryScore.category}
                        title={categoryScore.category.charAt(0).toUpperCase() + categoryScore.category.slice(1)}
                        value={`${Math.round(categoryScore.score * 100)}/100`}
                        change={{
                            value: categoryScore.confidence * 100,
                            type: categoryScore.score > 0.5 ? "increase" : "decrease",
                            timeframe: "confidence",
                        }}
                        status={
                            categoryScore.score > 0.6 ? "positive" : categoryScore.score < 0.4 ? "negative" : "neutral"
                        }
                        description={`Weight: ${formatPercentage(categoryScore.weight)}`}
                    />
                ))}
            </div>

            {/* Detailed Analysis Sections */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Technical Analysis */}
                <Card>
                    <CardHeader>
                        <CardTitle>テクニカル分析</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {/* Overall Signal */}
                            <div className="flex items-center justify-between">
                                <span className="font-medium">総合シグナル:</span>
                                <SignalBadge
                                    signal={technical_analysis.overall_signal as any}
                                    strength={technical_analysis.signal_strength}
                                />
                            </div>

                            {/* Technical Indicators */}
                            <div className="space-y-3">
                                <h4 className="font-medium text-neutral-700">主要指標</h4>

                                {technical_analysis.indicators.rsi && (
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm">RSI (14):</span>
                                        <div className="flex items-center space-x-2">
                                            <span className="text-sm font-medium">
                                                {technical_analysis.indicators.rsi.toFixed(1)}
                                            </span>
                                            <Badge
                                                variant={
                                                    technical_analysis.indicators.rsi > 70
                                                        ? "warning"
                                                        : technical_analysis.indicators.rsi < 30
                                                          ? "success"
                                                          : "secondary"
                                                }
                                                size="sm"
                                            >
                                                {technical_analysis.indicators.rsi > 70
                                                    ? "買われ過ぎ"
                                                    : technical_analysis.indicators.rsi < 30
                                                      ? "売られ過ぎ"
                                                      : "中立"}
                                            </Badge>
                                        </div>
                                    </div>
                                )}

                                {technical_analysis.indicators.macd && technical_analysis.indicators.macd_signal && (
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm">MACD:</span>
                                        <div className="flex items-center space-x-2">
                                            <span className="text-sm font-medium">
                                                {technical_analysis.indicators.macd.toFixed(3)}
                                            </span>
                                            <Badge
                                                variant={
                                                    technical_analysis.indicators.macd >
                                                    technical_analysis.indicators.macd_signal
                                                        ? "success"
                                                        : "warning"
                                                }
                                                size="sm"
                                            >
                                                {technical_analysis.indicators.macd >
                                                technical_analysis.indicators.macd_signal
                                                    ? "強気"
                                                    : "弱気"}
                                            </Badge>
                                        </div>
                                    </div>
                                )}

                                {/* Moving Averages */}
                                {technical_analysis.indicators.sma_20 && technical_analysis.indicators.sma_50 && (
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm">SMAクロス:</span>
                                        <Badge
                                            variant={
                                                technical_analysis.indicators.sma_20 >
                                                technical_analysis.indicators.sma_50
                                                    ? "success"
                                                    : "warning"
                                            }
                                            size="sm"
                                        >
                                            {technical_analysis.indicators.sma_20 > technical_analysis.indicators.sma_50
                                                ? "強気"
                                                : "弱気"}
                                        </Badge>
                                    </div>
                                )}
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Technical Indicator Chart */}
                <TechnicalIndicatorChart
                    indicators={technical_analysis.indicators}
                    height={350}
                    activeIndicators={["rsi", "macd"]}
                />

                {/* Pattern Analysis */}
                <Card>
                    <CardHeader>
                        <CardTitle>パターン分析</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {/* Overall Pattern Signal */}
                            <div className="flex items-center justify-between">
                                <span className="font-medium">パターンシグナル:</span>
                                <SignalBadge
                                    signal={pattern_analysis.overall_signal.toLowerCase().replace("_", "-") as any}
                                    strength={pattern_analysis.signal_strength}
                                />
                            </div>

                            {/* Pattern Score */}
                            <div>
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-sm font-medium">パターンスコア</span>
                                    <span className="text-sm">{Math.round(pattern_analysis.pattern_score * 100)}%</span>
                                </div>
                                <Progress
                                    value={pattern_analysis.pattern_score * 100}
                                    variant={
                                        pattern_analysis.pattern_score > 0.6
                                            ? "success"
                                            : pattern_analysis.pattern_score < 0.4
                                              ? "danger"
                                              : "default"
                                    }
                                />
                            </div>

                            {/* Detected Patterns */}
                            <div>
                                <h4 className="font-medium text-neutral-700 mb-2">
                                    検出されたパターン ({pattern_analysis.patterns.length})
                                </h4>
                                <div className="space-y-2 max-h-32 overflow-y-auto">
                                    {pattern_analysis.patterns.slice(0, 3).map((pattern, index) => (
                                        <div key={index} className="flex items-center justify-between text-sm">
                                            <span className="truncate">{pattern.description}</span>
                                            <Badge
                                                variant={
                                                    pattern.signal.includes("BULLISH")
                                                        ? "success"
                                                        : pattern.signal.includes("BEARISH")
                                                          ? "destructive"
                                                          : "secondary"
                                                }
                                                size="sm"
                                            >
                                                {Math.round(pattern.confidence * 100)}%
                                            </Badge>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Pattern Chart */}
                <PatternChart
                    patterns={pattern_analysis.patterns}
                    priceData={createMockHistoricalData(30, current_price)}
                    height={350}
                    highlightPatterns={true}
                />

                {/* Volatility Analysis */}
                <Card>
                    <CardHeader>
                        <CardTitle>ボラティリティ分析</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {/* Volatility Regime */}
                            <div className="flex items-center justify-between">
                                <span className="font-medium">ボラティリティ状況:</span>
                                <Badge
                                    variant={
                                        volatility_analysis.regime === "LOW"
                                            ? "success"
                                            : volatility_analysis.regime === "HIGH" ||
                                                volatility_analysis.regime === "EXTREME"
                                              ? "destructive"
                                              : "warning"
                                    }
                                >
                                    {volatility_analysis.regime}
                                </Badge>
                            </div>

                            {/* ATR */}
                            <div className="flex items-center justify-between">
                                <span className="text-sm">ATR (%):</span>
                                <span className="text-sm font-medium">
                                    {volatility_analysis.metrics.atr_percentage.toFixed(2)}%
                                </span>
                            </div>

                            {/* Breakout Probability */}
                            <div>
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-sm font-medium">ブレイクアウト確率</span>
                                    <span className="text-sm">
                                        {Math.round(volatility_analysis.breakout_probability * 100)}%
                                    </span>
                                </div>
                                <Progress
                                    value={volatility_analysis.breakout_probability * 100}
                                    variant={volatility_analysis.breakout_probability > 0.6 ? "warning" : "default"}
                                />
                            </div>

                            {/* Volatility Summary */}
                            <div className="text-sm text-neutral-600 bg-neutral-50 p-3 rounded">
                                {volatility_analysis.analysis_summary}
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Volatility Chart */}
                <VolatilityChart metrics={volatility_analysis.metrics} height={350} displayType="atr" />

                {/* ML Predictions */}
                <Card>
                    <CardHeader>
                        <CardTitle>機械学習予測</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {/* Price Target */}
                            <div className="text-center p-4 bg-primary-50 rounded-lg">
                                <div className="text-2xl font-bold text-primary-700">
                                    {formatPrice(ml_analysis.price_target)}
                                </div>
                                <div className="text-sm text-primary-600">目標株価</div>
                                <div className="text-xs text-neutral-600 mt-1">
                                    現在価格から
                                    {(((ml_analysis.price_target - current_price) / current_price) * 100).toFixed(1)}%
                                </div>
                            </div>

                            {/* Consensus Score */}
                            <div>
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-sm font-medium">モデル合意度</span>
                                    <span className="text-sm">{Math.round(ml_analysis.consensus_score * 100)}%</span>
                                </div>
                                <Progress value={ml_analysis.consensus_score * 100} variant="default" />
                            </div>

                            {/* Trend Direction */}
                            <div className="flex items-center justify-between">
                                <span className="font-medium">トレンド方向:</span>
                                <Badge
                                    variant={
                                        ml_analysis.trend_direction === "up"
                                            ? "success"
                                            : ml_analysis.trend_direction === "down"
                                              ? "destructive"
                                              : "secondary"
                                    }
                                >
                                    {ml_analysis.trend_direction === "up"
                                        ? "上昇"
                                        : ml_analysis.trend_direction === "down"
                                          ? "下降"
                                          : "横ばい"}
                                </Badge>
                            </div>

                            {/* Model Performance */}
                            <div>
                                <h4 className="font-medium text-neutral-700 mb-2">モデル性能</h4>
                                <div className="space-y-1">
                                    {Object.entries(ml_analysis.model_performance).map(([model, accuracy]) => (
                                        <div key={model} className="flex items-center justify-between text-sm">
                                            <span className="capitalize">{model.replace("_", " ")}</span>
                                            <span className="font-medium">{(accuracy * 100).toFixed(1)}%</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Analysis Metadata */}
            <Card>
                <CardHeader>
                    <CardTitle>分析詳細</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                            <div className="font-medium text-neutral-700">データポイント</div>
                            <div className="text-neutral-600">{analysis_metadata.data_points_used}</div>
                        </div>
                        <div>
                            <div className="font-medium text-neutral-700">データ品質</div>
                            <div className="text-neutral-600">
                                {Math.round(analysis_metadata.data_quality_score * 100)}%
                            </div>
                        </div>
                        <div>
                            <div className="font-medium text-neutral-700">分析時刻</div>
                            <div className="text-neutral-600">
                                {new Date(analysis_metadata.analysis_timestamp).toLocaleTimeString("ja-JP")}
                            </div>
                        </div>
                        <div>
                            <div className="font-medium text-neutral-700">信頼度要因</div>
                            <div className="text-neutral-600">{analysis_metadata.confidence_factors.length} 要因</div>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
