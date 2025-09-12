"""swing_signals.py: スイングトレードシグナル生成.

月次トレンド分析結果からスイングトレードシグナル（エントリー/エグジット）を生成。
TDD(Test-Driven Development)による段階的実装で信頼性を確保。

主要機能:
- 基本シグナル生成ロジック
- 価格レベル計算(target_price, stop_loss)
- 信頼度とファクター評価
- 統合シグナルジェネレーター

技術特徴:
- Monthly Trend Analysisとの連携
- リスクリワード比率の自動計算
- 根拠の自動生成
- Decimal型精度保持
"""

import logging
from datetime import UTC, datetime
from decimal import Decimal

from monthlyswing_backend.models.swing_models import (
    MonthlyTrendResult,
    SignalType,
    SwingSignal,
    TrendDirection,
)

logger = logging.getLogger(__name__)


def generate_basic_signal(monthly_trend_result: MonthlyTrendResult) -> SwingSignal:
    """基本シグナル生成.

    Monthly Trend Analysis の結果から基本的な
    BUY/SELL/HOLD/WAIT シグナルを生成する。

    Args:
        monthly_trend_result: 月次トレンド分析結果

    Returns:
        SwingSignal: 生成されたシグナル

    Raises:
        ValueError: 分析結果が無効な場合

    Example:
        >>> trend_result = MonthlyTrendResult(...)
        >>> signal = generate_basic_signal(trend_result)
        >>> assert signal.signal_type in [SignalType.BUY, SignalType.SELL]
    """
    logger.info(f"基本シグナル生成開始: {monthly_trend_result.symbol}")

    try:
        # トレンド方向と強度からシグナル判定
        trend_strength = monthly_trend_result.trend_strength
        continuation_prob = monthly_trend_result.continuation_probability

        # シグナルタイプ決定
        signal_type = _determine_signal_type(
            trend_strength.direction,
            trend_strength.strength,
            trend_strength.confidence,
            continuation_prob,
        )

        # 信頼度計算
        confidence = _calculate_basic_confidence(
            trend_strength.strength, trend_strength.confidence, continuation_prob
        )

        # 根拠生成
        supporting_factors = _generate_basic_factors(
            signal_type,
            trend_strength.direction,
            trend_strength.strength,
            continuation_prob,
        )

        signal = SwingSignal(
            signal_type=signal_type,
            confidence=confidence,
            supporting_factors=supporting_factors,
            generated_at=datetime.now(UTC),
        )

        logger.info(f"シグナル生成完了: {signal_type.value}, 信頼度: {confidence}")
        return signal

    except Exception as e:
        logger.error(f"シグナル生成エラー: {e!s}")
        raise ValueError(f"シグナル生成に失敗しました: {e!s}") from e


def _determine_signal_type(
    direction: TrendDirection,
    strength: Decimal,
    confidence: Decimal,
    continuation_prob: Decimal,
) -> SignalType:
    """シグナルタイプ決定.

    トレンド方向と各種指標からシグナルタイプを決定する。

    Args:
        direction: トレンド方向
        strength: トレンド強度
        confidence: 分析信頼度
        continuation_prob: 継続確率

    Returns:
        SignalType: 決定されたシグナルタイプ
    """
    # 強いトレンドの閾値
    strong_trend_threshold = Decimal("0.7")
    high_confidence_threshold = Decimal("0.7")
    high_continuation_threshold = Decimal("0.7")

    # 不明確な場合はWAIT
    if (
        direction == TrendDirection.UNKNOWN
        or confidence < Decimal("0.5")
        or strength < Decimal("0.3")
    ):
        return SignalType.WAIT

    # 強い上昇トレンド → BUY
    if (
        direction == TrendDirection.UPTREND
        and strength >= strong_trend_threshold
        and confidence >= high_confidence_threshold
        and continuation_prob >= high_continuation_threshold
    ):
        return SignalType.BUY

    # 強い下降トレンド → SELL
    if (
        direction == TrendDirection.DOWNTREND
        and strength >= strong_trend_threshold
        and confidence >= high_confidence_threshold
        and continuation_prob >= high_continuation_threshold
    ):
        return SignalType.SELL

    # 横這い、または中程度のトレンド → HOLD
    if direction == TrendDirection.SIDEWAYS or strength < strong_trend_threshold:
        return SignalType.HOLD

    # その他の場合はWAIT
    return SignalType.WAIT


def _calculate_basic_confidence(
    strength: Decimal, confidence: Decimal, continuation_prob: Decimal
) -> Decimal:
    """基本信頼度計算.

    複数指標の重み付け平均で信頼度を計算する。

    Args:
        strength: トレンド強度
        confidence: 分析信頼度
        continuation_prob: 継続確率

    Returns:
        Decimal: 計算された信頼度 (0-1)
    """
    # 重みの設定
    strength_weight = Decimal("0.4")
    confidence_weight = Decimal("0.4")
    continuation_weight = Decimal("0.2")

    # 重み付け平均
    weighted_confidence = (
        strength * strength_weight
        + confidence * confidence_weight
        + continuation_prob * continuation_weight
    )

    # 0-1の範囲に正規化
    return max(Decimal("0.0"), min(Decimal("1.0"), weighted_confidence))


def _generate_basic_factors(
    signal_type: SignalType,
    direction: TrendDirection,
    strength: Decimal,
    continuation_prob: Decimal,
) -> list[str]:
    """基本シグナル根拠生成.

    シグナルタイプとトレンド情報から判定根拠を自動生成する。

    Args:
        signal_type: シグナルタイプ
        direction: トレンド方向
        strength: トレンド強度
        continuation_prob: 継続確率

    Returns:
        List[str]: 判定根拠のリスト
    """
    factors = []

    # トレンド方向の説明
    if direction == TrendDirection.UPTREND:
        if strength >= Decimal("0.7"):
            factors.append("強い上昇トレンドが継続中")
        else:
            factors.append("上昇トレンドが確認")
    elif direction == TrendDirection.DOWNTREND:
        if strength >= Decimal("0.7"):
            factors.append("強い下降トレンドが継続中")
        else:
            factors.append("下降トレンドが確認")
    elif direction == TrendDirection.SIDEWAYS:
        factors.append("横這いトレンド（レンジ相場）")
    else:
        factors.append("トレンド方向が不明確")

    # 強度の説明
    if strength >= Decimal("0.8"):
        factors.append("非常に強いトレンド強度")
    elif strength >= Decimal("0.6"):
        factors.append("強いトレンド強度")
    elif strength >= Decimal("0.4"):
        factors.append("中程度のトレンド強度")
    else:
        factors.append("弱いトレンド強度")

    # 継続確率の説明
    if continuation_prob >= Decimal("0.8"):
        factors.append("トレンド継続の確率が非常に高い")
    elif continuation_prob >= Decimal("0.6"):
        factors.append("トレンド継続の確率が高い")
    elif continuation_prob >= Decimal("0.4"):
        factors.append("トレンド継続の確率は中程度")
    else:
        factors.append("トレンド継続の確率は低い")

    # シグナル特有の説明
    if signal_type == SignalType.BUY:
        factors.append("エントリー推奨（買いポジション）")
    elif signal_type == SignalType.SELL:
        factors.append("エントリー推奨（売りポジション）")
    elif signal_type == SignalType.HOLD:
        factors.append("現在のポジションを保持")
    else:  # WAIT
        factors.append("様子見推奨（不確実性が高い）")

    return factors
