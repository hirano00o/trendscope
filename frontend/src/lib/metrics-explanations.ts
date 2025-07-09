/**
 * Metrics explanations for tooltip display
 *
 * @description Comprehensive Japanese explanations for all analysis metrics
 * including ranges, meanings, and investment implications for users.
 */

export interface MetricExplanation {
    /** 指標名 */
    name: string
    /** 値の範囲 */
    range: string
    /** 指標の意味と解釈 */
    meaning: string
    /** 投資判断の指針 */
    investmentGuidance: string
    /** 注意点や補足情報 */
    notes?: string
}

/**
 * Technical analysis indicators explanations
 */
export const technicalIndicatorsExplanations: Record<string, MetricExplanation> = {
    rsi: {
        name: "RSI (相対力指数)",
        range: "0〜100",
        meaning: "株価の上昇圧力と下降圧力を比較し、買われ過ぎ・売られ過ぎを判定する指標です。",
        investmentGuidance: "70以上: 買われ過ぎ（売り検討）\n30以下: 売られ過ぎ（買い検討）\n30〜70: 正常範囲",
        notes: "単独では判断せず、他の指標と組み合わせて使用することが重要です。",
    },
    macd: {
        name: "MACD (移動平均収束拡散手法)",
        range: "制限なし（正負の値）",
        meaning: "2つの移動平均線の差とその移動平均を用いて、トレンドの変化を捉える指標です。",
        investmentGuidance: "MACDがシグナル線を上抜け: 買いシグナル\nMACDがシグナル線を下抜け: 売りシグナル",
        notes: "トレンド相場で威力を発揮しますが、横ばい相場では偽シグナルが多くなります。",
    },
    sma_cross: {
        name: "SMAクロス (単純移動平均クロス)",
        range: "強気/弱気/中立",
        meaning: "短期移動平均線と長期移動平均線の位置関係で、トレンドの方向性を判定します。",
        investmentGuidance: "短期SMA > 長期SMA: 強気（上昇トレンド）\n短期SMA < 長期SMA: 弱気（下降トレンド）",
        notes: "トレンド系指標のため、レンジ相場では効果が限定的です。",
    },
}

/**
 * Pattern analysis explanations
 */
export const patternAnalysisExplanations: Record<string, MetricExplanation> = {
    pattern_score: {
        name: "パターンスコア",
        range: "0〜100%",
        meaning: "検出されたテクニカルパターンの信頼性と強さを総合的に評価したスコアです。",
        investmentGuidance: "60%以上: 強いパターンシグナル\n40%未満: 弱いパターンシグナル\n40〜60%: 中程度",
        notes: "複数のパターンが同時に検出されると、スコアが高くなる傾向があります。",
    },
    overall_signal: {
        name: "総合パターンシグナル",
        range: "強気/弱気/中立",
        meaning: "検出されたすべてのパターンを総合して算出された売買シグナルです。",
        investmentGuidance: "強気: 買い優勢\n弱気: 売り優勢\n中立: 様子見",
        notes: "短期的な価格変動の予測に適していますが、中長期トレンドも考慮してください。",
    },
}

/**
 * Volatility analysis explanations
 */
export const volatilityAnalysisExplanations: Record<string, MetricExplanation> = {
    atr_percentage: {
        name: "ATR% (平均真の値幅率)",
        range: "0%〜（上限なし）",
        meaning: "過去一定期間の価格変動幅の平均を現在価格で割ったもので、ボラティリティの大きさを示します。",
        investmentGuidance: "3%未満: 低ボラティリティ\n3〜7%: 中程度\n7%以上: 高ボラティリティ",
        notes: "高ボラティリティ時は利益機会が大きいが、リスクも高くなります。",
    },
    breakout_probability: {
        name: "ブレイクアウト確率",
        range: "0〜100%",
        meaning: "現在の価格が重要なサポート・レジスタンスラインを突破する可能性を示します。",
        investmentGuidance: "70%以上: ブレイクアウト可能性高\n30%未満: レンジ継続可能性高\n30〜70%: 不確実",
        notes: "ブレイクアウト後は大きな価格変動が予想されるため、ポジション管理に注意が必要です。",
    },
    volatility_regime: {
        name: "ボラティリティ環境",
        range: "LOW/MODERATE/HIGH/EXTREME",
        meaning: "現在の市場のボラティリティ水準を過去のデータと比較して分類したものです。",
        investmentGuidance: "LOW: 安定期（長期投資向き）\nMODERATE: 通常期\nHIGH/EXTREME: 不安定期（短期取引注意）",
        notes: "ボラティリティ環境により、適切な投資戦略や期間が変わります。",
    },
}

/**
 * Machine learning predictions explanations
 */
export const mlAnalysisExplanations: Record<string, MetricExplanation> = {
    consensus_score: {
        name: "モデル合意度",
        range: "0〜100%",
        meaning: "複数の機械学習モデルの予測結果がどの程度一致しているかを示す指標です。",
        investmentGuidance: "80%以上: 高い信頼性\n50%未満: 低い信頼性\n50〜80%: 中程度の信頼性",
        notes: "合意度が高いほど予測の確実性が高いと考えられますが、市場の急変には注意が必要です。",
    },
    price_target: {
        name: "目標株価",
        range: "現在価格の±30%程度",
        meaning: "機械学習モデルが予測する将来の株価水準です。複数モデルのアンサンブル予測です。",
        investmentGuidance: "現在価格より高い: 上昇期待\n現在価格より低い: 下落リスク",
        notes: "予測期間は通常1〜3ヶ月程度です。マクロ経済要因は考慮されていません。",
    },
    trend_direction: {
        name: "トレンド方向",
        range: "上昇/下降/横ばい",
        meaning: "機械学習モデルが予測する今後の価格トレンドの方向性です。",
        investmentGuidance: "上昇: 買いポジション検討\n下降: 売りポジション検討\n横ばい: 様子見",
        notes: "短期的な方向性予測であり、長期投資判断には別途分析が必要です。",
    },
}

/**
 * Integrated scoring explanations
 */
export const integratedScoringExplanations: Record<string, MetricExplanation> = {
    overall_score: {
        name: "総合スコア",
        range: "0〜100",
        meaning: "6つの分析カテゴリーを統合して算出された、総合的な投資魅力度スコアです。",
        investmentGuidance: "70以上: 強い買いシグナル\n30未満: 強い売りシグナル\n30〜70: 中立",
        notes: "全ての分析手法を総合した最終判断です。ただし、個別要因も必ず確認してください。",
    },
    confidence_level: {
        name: "信頼度",
        range: "0〜100%",
        meaning: "分析結果に対する統計的な信頼性の度合いを示します。",
        investmentGuidance: "80%以上: 高信頼\n50%未満: 低信頼\n50〜80%: 中信頼",
        notes: "信頼度が低い場合は、追加情報の収集や慎重な判断が推奨されます。",
    },
    recommendation: {
        name: "投資推奨",
        range: "買い/保有/売り",
        meaning: "総合的な分析結果に基づく、具体的な投資行動の推奨です。",
        investmentGuidance: "買い: 新規購入推奨\n保有: 現状維持推奨\n売り: 売却推奨",
        notes: "個人の投資目標、リスク許容度、ポートフォリオ状況を考慮して最終判断してください。",
    },
    risk_assessment: {
        name: "リスク評価",
        range: "LOW/MODERATE/HIGH",
        meaning: "現在の投資に伴うリスクレベルの評価です。",
        investmentGuidance: "LOW: 相対的に安全\nMODERATE: 通常レベル\nHIGH: 高リスク（注意必要）",
        notes: "高リスク時は投資金額の調整や、分散投資の検討が重要です。",
    },
}

/**
 * Category scores explanations
 */
export const categoryScoringExplanations: Record<string, MetricExplanation> = {
    technical: {
        name: "テクニカル分析スコア",
        range: "0〜100",
        meaning: "価格と出来高の動きから算出される技術的分析の評価スコアです。",
        investmentGuidance: "70以上: テクニカル的に強気\n30未満: テクニカル的に弱気",
        notes: "短期〜中期の価格動向予測に有効です。",
    },
    pattern: {
        name: "パターン分析スコア",
        range: "0〜100",
        meaning: "チャートパターンや値動きのパターンから算出される評価スコアです。",
        investmentGuidance: "高スコア: パターン的に有利\n低スコア: パターン的に不利",
        notes: "過去のパターンが今後も継続する前提での分析です。",
    },
    volatility: {
        name: "ボラティリティ分析スコア",
        range: "0〜100",
        meaning: "価格変動性の観点から算出される評価スコアです。",
        investmentGuidance: "スコアが示すリスクレベルに応じて投資戦略を調整してください。",
        notes: "ボラティリティ自体は良い悪いではなく、投資スタイルとの適合性が重要です。",
    },
    ml: {
        name: "機械学習スコア",
        range: "0〜100",
        meaning: "複数の機械学習モデルの予測結果から算出される評価スコアです。",
        investmentGuidance: "高スコア: AI予測的に有望\n低スコア: AI予測的に注意",
        notes: "過去データに基づく予測であり、未来の市場環境変化は予測できません。",
    },
    fundamental: {
        name: "ファンダメンタル分析スコア",
        range: "0〜100",
        meaning: "出来高分析など、基本的な市場要因から算出される評価スコアです。",
        investmentGuidance: "高スコア: 基本的要因が良好\n低スコア: 基本的要因に注意",
        notes: "現在は出来高分析が中心です。今後、財務指標等も追加予定です。",
    },
}

/**
 * Get explanation for a specific metric
 *
 * @description Retrieves the explanation object for a given metric key
 * from the appropriate category.
 *
 * @param category - The analysis category
 * @param metricKey - The specific metric key
 * @returns MetricExplanation object or undefined if not found
 *
 * @example
 * ```typescript
 * const rsiExplanation = getMetricExplanation('technical', 'rsi')
 * console.log(rsiExplanation?.meaning)
 * ```
 */
export function getMetricExplanation(
    category: "technical" | "pattern" | "volatility" | "ml" | "integrated" | "category",
    metricKey: string,
): MetricExplanation | undefined {
    switch (category) {
        case "technical":
            return technicalIndicatorsExplanations[metricKey]
        case "pattern":
            return patternAnalysisExplanations[metricKey]
        case "volatility":
            return volatilityAnalysisExplanations[metricKey]
        case "ml":
            return mlAnalysisExplanations[metricKey]
        case "integrated":
            return integratedScoringExplanations[metricKey]
        case "category":
            return categoryScoringExplanations[metricKey]
        default:
            return undefined
    }
}

/**
 * Format explanation content for tooltip display
 *
 * @description Formats the metric explanation into a readable tooltip content.
 *
 * @param explanation - The metric explanation object
 * @returns Formatted string for tooltip display
 *
 * @example
 * ```typescript
 * const explanation = getMetricExplanation('technical', 'rsi')
 * const tooltipContent = formatExplanationForTooltip(explanation)
 * ```
 */
export function formatExplanationForTooltip(explanation: MetricExplanation): string {
    let content = `${explanation.name}\n`
    content += `範囲: ${explanation.range}\n\n`
    content += `${explanation.meaning}\n\n`
    content += `投資判断:\n${explanation.investmentGuidance}`

    if (explanation.notes) {
        content += `\n\n注意: ${explanation.notes}`
    }

    return content
}
