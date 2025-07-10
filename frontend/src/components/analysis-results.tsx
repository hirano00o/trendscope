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
import { Tooltip } from "@/components/ui/tooltip"
import {
    PriceChart,
    TechnicalIndicatorChart,
    VolatilityChart,
    PatternChart,
    createMockHistoricalData,
} from "@/components/charts"
import { useHistoricalData } from "@/hooks/use-historical-data"
import { cn, formatPrice, formatPercentage } from "@/lib/utils"
import type { AnalysisResultsProps } from "@/types/analysis"

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
        integrated_score,
        analysis_metadata,
    } = data

    // Fetch historical data for price chart
    const {
        data: historicalData,
        isLoading: isHistoricalLoading,
        error: historicalError,
    } = useHistoricalData(symbol, {
        period: "1mo",
        enabled: !!symbol,
    })

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
                            <Tooltip
                                content={
                                    <div className="max-w-xs text-xs whitespace-pre-line">
                                        {`総合スコア
範囲: 0〜100

6つの分析カテゴリーを統合して算出された、総合的な投資魅力度スコアです。

投資判断:
70以上: 強い買いシグナル
30未満: 強い売りシグナル
30〜70: 中立

注意: 全ての分析手法を総合した最終判断です。ただし、個別要因も必ず確認してください。`}
                                    </div>
                                }
                            >
                                <div className="cursor-help">
                                    <div className="text-3xl font-bold text-primary-600">
                                        {Math.round(integrated_score.overall_score * 100)}
                                    </div>
                                    <div className="text-sm text-neutral-600">総合スコア</div>
                                </div>
                            </Tooltip>
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
                            <Tooltip
                                content={
                                    <div className="max-w-xs text-xs whitespace-pre-line">
                                        {`信頼度
範囲: 0〜100%

分析結果に対する統計的な信頼性の度合いを示します。

投資判断:
80%以上: 高信頼
50%未満: 低信頼
50〜80%: 中信頼

注意: 信頼度が低い場合は、追加情報の収集や慎重な判断が推奨されます。`}
                                    </div>
                                }
                            >
                                <div className="cursor-help">
                                    <ConfidenceProgress
                                        confidence={integrated_score.confidence_level}
                                        showLabel
                                        labelPosition="top"
                                        size="lg"
                                    />
                                </div>
                            </Tooltip>
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
            {isHistoricalLoading ? (
                <Card variant="elevated" size="lg">
                    <CardContent className="flex items-center justify-center h-96">
                        <div className="text-center">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
                            <p className="text-neutral-600">株価チャートを読み込み中...</p>
                        </div>
                    </CardContent>
                </Card>
            ) : historicalError ? (
                <Card variant="elevated" size="lg">
                    <CardContent className="flex items-center justify-center h-96">
                        <div className="text-center">
                            <p className="text-danger-600 mb-2">株価データの取得に失敗しました</p>
                            <p className="text-neutral-600 text-sm">
                                {historicalError.message || "データを取得できませんでした"}
                            </p>
                            <p className="text-neutral-500 text-xs mt-2">
                                モックデータを表示しています
                            </p>
                        </div>
                    </CardContent>
                </Card>
            ) : (
                <PriceChart
                    data={
                        historicalData?.historical_data || 
                        createMockHistoricalData(30, current_price)
                    }
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
            )}

            {/* Category Scores Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {integrated_score.category_scores.map((categoryScore) => (
                    <MetricCard
                        key={categoryScore.category}
                        title={
                            categoryScore.category === "technical"
                                ? "テクニカル分析"
                                : categoryScore.category === "pattern"
                                  ? "パターン分析"
                                  : categoryScore.category === "volatility"
                                    ? "ボラティリティ分析"
                                    : categoryScore.category === "ml"
                                      ? "機械学習分析"
                                      : categoryScore.category === "fundamental"
                                        ? "ファンダメンタル分析"
                                        : categoryScore.category.charAt(0).toUpperCase() +
                                          categoryScore.category.slice(1)
                        }
                        value={`${Math.round(categoryScore.score * 100)}/100`}
                        change={{
                            value: categoryScore.confidence * 100,
                            type: categoryScore.score > 0.5 ? "increase" : "decrease",
                            timeframe: "confidence",
                        }}
                        status={
                            categoryScore.score > 0.6 ? "positive" : categoryScore.score < 0.4 ? "negative" : "neutral"
                        }
                        description={`重み: ${formatPercentage(categoryScore.weight)}`}
                        tooltip={{
                            category: "category",
                            metricKey: categoryScore.category.toLowerCase(),
                        }}
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
                                        <Tooltip
                                            content={
                                                <div className="max-w-xs text-xs whitespace-pre-line">
                                                    {`RSI (相対力指数)
範囲: 0〜100

株価の上昇圧力と下降圧力を比較し、買われ過ぎ・売られ過ぎを判定する指標です。

投資判断:
70以上: 買われ過ぎ（売り検討）
30以下: 売られ過ぎ（買い検討）
30〜70: 正常範囲

注意: 単独では判断せず、他の指標と組み合わせて使用することが重要です。`}
                                                </div>
                                            }
                                        >
                                            <span className="text-sm cursor-help">RSI (14):</span>
                                        </Tooltip>
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
                                        <Tooltip
                                            content={
                                                <div className="max-w-xs text-xs whitespace-pre-line">
                                                    {`MACD (移動平均収束拡散手法)
範囲: 制限なし（正負の値）

2つの移動平均線の差とその移動平均を用いて、トレンドの変化を捉える指標です。

投資判断:
MACDがシグナル線を上抜け: 買いシグナル
MACDがシグナル線を下抜け: 売りシグナル

注意: トレンド相場で威力を発揮しますが、横ばい相場では偽シグナルが多くなります。`}
                                                </div>
                                            }
                                        >
                                            <span className="text-sm cursor-help">MACD:</span>
                                        </Tooltip>
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
                                        <Tooltip
                                            content={
                                                <div className="max-w-xs text-xs whitespace-pre-line">
                                                    {`SMAクロス (単純移動平均クロス)
範囲: 強気/弱気/中立

短期移動平均線と長期移動平均線の位置関係で、トレンドの方向性を判定します。

投資判断:
短期SMA > 長期SMA: 強気（上昇トレンド）
短期SMA < 長期SMA: 弱気（下降トレンド）

注意: トレンド系指標のため、レンジ相場では効果が限定的です。`}
                                                </div>
                                            }
                                        >
                                            <span className="text-sm cursor-help">SMAクロス:</span>
                                        </Tooltip>
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
                                <Tooltip
                                    content={
                                        <div className="max-w-xs text-xs whitespace-pre-line">
                                            {`総合パターンシグナル
範囲: 強気/弱気/中立

検出されたすべてのパターンを総合して算出された売買シグナルです。

投資判断:
強気: 買い優勢
弱気: 売り優勢
中立: 様子見

注意: 短期的な価格変動の予測に適していますが、中長期トレンドも考慮してください。`}
                                        </div>
                                    }
                                >
                                    <span className="font-medium cursor-help">パターンシグナル:</span>
                                </Tooltip>
                                <SignalBadge
                                    signal={pattern_analysis.overall_signal.toLowerCase().replace("_", "-") as any}
                                    strength={pattern_analysis.signal_strength}
                                />
                            </div>

                            {/* Pattern Score */}
                            <div>
                                <div className="flex justify-between items-center mb-2">
                                    <Tooltip
                                        content={
                                            <div className="max-w-xs text-xs whitespace-pre-line">
                                                {`パターンスコア
範囲: 0〜100%

検出されたテクニカルパターンの信頼性と強さを総合的に評価したスコアです。

投資判断:
60%以上: 強いパターンシグナル
40%未満: 弱いパターンシグナル
40〜60%: 中程度

注意: 複数のパターンが同時に検出されると、スコアが高くなる傾向があります。`}
                                            </div>
                                        }
                                    >
                                        <span className="text-sm font-medium cursor-help">パターンスコア</span>
                                    </Tooltip>
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
                                                {pattern.signal.includes("BULLISH")
                                                    ? "強気"
                                                    : pattern.signal.includes("BEARISH")
                                                      ? "弱気"
                                                      : "中立"}{" "}
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
                    priceData={
                        historicalData?.historical_data || 
                        createMockHistoricalData(30, current_price)
                    }
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
                                    {volatility_analysis.regime === "LOW"
                                        ? "低"
                                        : volatility_analysis.regime === "MODERATE"
                                          ? "中程度"
                                          : volatility_analysis.regime === "HIGH"
                                            ? "高"
                                            : volatility_analysis.regime === "EXTREME"
                                              ? "極高"
                                              : volatility_analysis.regime}
                                </Badge>
                            </div>

                            {/* ATR */}
                            <div className="flex items-center justify-between">
                                <Tooltip
                                    content={
                                        <div className="max-w-xs text-xs whitespace-pre-line">
                                            {`ATR% (平均真の値幅率)
範囲: 0%〜（上限なし）

過去一定期間の価格変動幅の平均を現在価格で割ったもので、ボラティリティの大きさを示します。

投資判断:
3%未満: 低ボラティリティ
3〜7%: 中程度
7%以上: 高ボラティリティ

注意: 高ボラティリティ時は利益機会が大きいが、リスクも高くなります。`}
                                        </div>
                                    }
                                >
                                    <span className="text-sm cursor-help">ATR (%):</span>
                                </Tooltip>
                                <span className="text-sm font-medium">
                                    {volatility_analysis.metrics.atr_percentage.toFixed(2)}%
                                </span>
                            </div>

                            {/* Breakout Probability */}
                            <div>
                                <div className="flex justify-between items-center mb-2">
                                    <Tooltip
                                        content={
                                            <div className="max-w-xs text-xs whitespace-pre-line">
                                                {`ブレイクアウト確率
範囲: 0〜100%

現在の価格が重要なサポート・レジスタンスラインを突破する可能性を示します。

投資判断:
70%以上: ブレイクアウト可能性高
30%未満: レンジ継続可能性高
30〜70%: 不確実

注意: ブレイクアウト後は大きな価格変動が予想されるため、ポジション管理に注意が必要です。`}
                                            </div>
                                        }
                                    >
                                        <span className="text-sm font-medium cursor-help">ブレイクアウト確率</span>
                                    </Tooltip>
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
                            <Tooltip
                                content={
                                    <div className="max-w-xs text-xs whitespace-pre-line">
                                        {`目標株価
範囲: 現在価格の±30%程度

機械学習モデルが予測する将来の株価水準です。複数モデルのアンサンブル予測です。

投資判断:
現在価格より高い: 上昇期待
現在価格より低い: 下落リスク

注意: 予測期間は通常1〜3ヶ月程度です。マクロ経済要因は考慮されていません。`}
                                    </div>
                                }
                            >
                                <div className="text-center p-4 bg-primary-50 rounded-lg cursor-help">
                                    <div className="text-2xl font-bold text-primary-700">
                                        {formatPrice(ml_analysis.price_target)}
                                    </div>
                                    <div className="text-sm text-primary-600">目標株価</div>
                                    <div className="text-xs text-neutral-600 mt-1">
                                        現在価格から
                                        {(((ml_analysis.price_target - current_price) / current_price) * 100).toFixed(
                                            1,
                                        )}
                                        %
                                    </div>
                                </div>
                            </Tooltip>

                            {/* Consensus Score */}
                            <div>
                                <div className="flex justify-between items-center mb-2">
                                    <Tooltip
                                        content={
                                            <div className="max-w-xs text-xs whitespace-pre-line">
                                                {`モデル合意度
範囲: 0〜100%

複数の機械学習モデルの予測結果がどの程度一致しているかを示す指標です。

投資判断:
80%以上: 高い信頼性
50%未満: 低い信頼性
50〜80%: 中程度の信頼性

注意: 合意度が高いほど予測の確実性が高いと考えられますが、市場の急変には注意が必要です。`}
                                            </div>
                                        }
                                    >
                                        <span className="text-sm font-medium cursor-help">モデル合意度</span>
                                    </Tooltip>
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
