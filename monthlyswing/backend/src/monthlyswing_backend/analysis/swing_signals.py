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
    SupportResistanceLevel,
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


def calculate_target_price(
    current_price: Decimal,
    signal_type: SignalType,
    resistance_levels: list[SupportResistanceLevel],
    support_levels: list[SupportResistanceLevel],
    expected_return_rate: Decimal,
) -> Decimal:
    """ターゲット価格計算.

    現在価格とレジスタンスレベルからターゲット価格を算出する。

    Args:
        current_price: 現在の株価
        signal_type: シグナルタイプ（BUY/SELL）
        resistance_levels: レジスタンス・サポートレベルのリスト
        support_levels: サポートレベルのリスト
        expected_return_rate: 期待リターン率（0-1の範囲）

    Returns:
        Decimal: 計算されたターゲット価格

    Raises:
        ValueError: 無効な入力値の場合

    Example:
        >>> target = calculate_target_price(
        ...     Decimal("100.00"), SignalType.BUY, resistance_levels
        ... )
        >>> assert target > Decimal("100.00")
    """
    logger.info(
        f"ターゲット価格計算開始: 現在価格={current_price}, シグナル={signal_type}"
    )

    if current_price <= 0:
        raise ValueError("現在価格は正の値である必要があります")

    if not resistance_levels:
        # レジスタンスレベルがない場合のデフォルト計算
        if signal_type == SignalType.BUY:
            return current_price * Decimal("1.10")  # 10%上昇を目標
        else:  # SELL
            return current_price * Decimal("0.90")  # 10%下降を目標

    try:
        if signal_type == SignalType.BUY:
            # 買いシグナル：現在価格より上のレジスタンスレベルを目標
            upper_resistances = [
                level
                for level in resistance_levels
                if level.level_type == "レジスタンス" and level.level > current_price
            ]
            if upper_resistances:
                # 最も近いレジスタンスレベルを目標とする
                nearest_resistance = min(
                    upper_resistances, key=lambda x: x.level - current_price
                )
                return nearest_resistance.level
            else:
                # レジスタンスがない場合は15%上昇を目標
                return current_price * Decimal("1.15")

        else:  # SELL
            # 売りシグナル：現在価格より下のサポートレベルを目標
            lower_supports = [
                level
                for level in support_levels
                if level.level_type == "サポート" and level.level < current_price
            ]
            if lower_supports:
                # 最も近いサポートレベルを目標とする
                nearest_support = max(lower_supports, key=lambda x: x.level)
                return nearest_support.level
            else:
                # サポートがない場合は15%下降を目標
                return current_price * Decimal("0.85")

    except Exception as e:
        logger.error(f"ターゲット価格計算エラー: {e!s}")
        raise ValueError(f"ターゲット価格の計算に失敗しました: {e!s}") from e


def calculate_stop_loss(
    current_price: Decimal,
    signal_type: SignalType,
    support_levels: list[SupportResistanceLevel],
    resistance_levels: list[SupportResistanceLevel],
    risk_tolerance: Decimal,
) -> Decimal:
    """ストップロス価格計算.

    現在価格とサポートレベルからストップロス価格を算出する。

    Args:
        current_price: 現在の株価
        signal_type: シグナルタイプ（BUY/SELL）
        support_levels: サポート・レジスタンスレベルのリスト
        resistance_levels: レジスタンスレベルのリスト
        risk_tolerance: リスク許容度（0-1の範囲）

    Returns:
        Decimal: 計算されたストップロス価格

    Raises:
        ValueError: 無効な入力値の場合

    Example:
        >>> stop_loss = calculate_stop_loss(
        ...     Decimal("100.00"), SignalType.BUY, support_levels
        ... )
        >>> assert stop_loss < Decimal("100.00")
    """
    logger.info(
        f"ストップロス計算開始: 現在価格={current_price}, シグナル={signal_type}"
    )

    if current_price <= 0:
        raise ValueError("現在価格は正の値である必要があります")

    if not support_levels:
        # サポートレベルがない場合のデフォルト計算
        if signal_type == SignalType.BUY:
            return current_price * Decimal("0.95")  # 5%下落でストップ
        else:  # SELL
            return current_price * Decimal("1.05")  # 5%上昇でストップ

    try:
        if signal_type == SignalType.BUY:
            # 買いシグナル：現在価格より下のサポートレベルをストップロスとする
            lower_supports = [
                level
                for level in support_levels
                if level.level_type == "サポート" and level.level < current_price
            ]
            if lower_supports:
                # 最も近いサポートレベルをストップロスとする
                nearest_support = max(lower_supports, key=lambda x: x.level)
                # サポートレベル付近に設定（わずかに上）
                return nearest_support.level
            else:
                # サポートがない場合は8%下落でストップ
                return current_price * Decimal("0.92")

        else:  # SELL
            # 売りシグナル：現在価格より上のレジスタンスレベルをストップロスとする
            upper_resistances = [
                level
                for level in resistance_levels
                if level.level_type == "レジスタンス" and level.level > current_price
            ]
            if upper_resistances:
                # 最も近いレジスタンスレベルをストップロスとする
                nearest_resistance = min(
                    upper_resistances, key=lambda x: x.level - current_price
                )
                # レジスタンスレベルより少し上にマージンを設ける
                return nearest_resistance.level * Decimal("1.02")
            else:
                # レジスタンスがない場合は8%上昇でストップ
                return current_price * Decimal("1.08")

    except Exception as e:
        logger.error(f"ストップロス計算エラー: {e!s}")
        raise ValueError(f"ストップロス価格の計算に失敗しました: {e!s}") from e


def calculate_risk_reward_ratio(
    current_price: Decimal, target_price: Decimal, stop_loss: Decimal
) -> Decimal:
    """リスクリワード比率計算.

    現在価格、ターゲット価格、ストップロス価格からリスクリワード比率を計算する。

    Args:
        current_price: 現在の株価
        target_price: ターゲット価格
        stop_loss: ストップロス価格

    Returns:
        Decimal: リスクリワード比率（リワード/リスク）

    Raises:
        ValueError: 無効な入力値の場合

    Example:
        >>> ratio = calculate_risk_reward_ratio(
        ...     Decimal("100.00"), Decimal("110.00"), Decimal("95.00")
        ... )
        >>> assert ratio == Decimal("2.0")  # 10%リワード / 5%リスク = 2.0
    """
    logger.info(
        f"リスクリワード比率計算: 現在={current_price}, 目標={target_price}, ストップ={stop_loss}"
    )

    if current_price <= 0 or target_price <= 0 or stop_loss <= 0:
        raise ValueError("全ての価格は正の値である必要があります")

    try:
        # 利益の絶対値を計算
        reward = abs(target_price - current_price)

        # 損失の絶対値を計算
        risk = abs(current_price - stop_loss)

        if risk == 0:
            raise ValueError("リスクが0では比率を計算できません")

        # リスクリワード比率 = リワード / リスク
        ratio = reward / risk

        logger.info(
            f"リスクリワード比率: {ratio:.2f} (リワード: {reward}, リスク: {risk})"
        )
        return ratio

    except Exception as e:
        logger.error(f"リスクリワード比率計算エラー: {e!s}")
        raise ValueError(f"リスクリワード比率の計算に失敗しました: {e!s}") from e


def calculate_composite_confidence(
    technical_confidence: Decimal,
    pattern_confidence: Decimal,
    volume_confidence: Decimal,
    trend_strength: Decimal,
    weights: dict[str, Decimal],
) -> Decimal:
    """複合信頼度スコア計算.

    複数の分析指標を重み付け平均して総合信頼度を算出する。

    Args:
        technical_confidence: テクニカル分析信頼度
        pattern_confidence: パターン分析信頼度
        volume_confidence: 出来高分析信頼度
        trend_strength: トレンド強度
        weights: 各指標の重み辞書

    Returns:
        Decimal: 複合信頼度スコア（0-1の範囲）

    Raises:
        ValueError: 無効な入力値の場合

    Example:
        >>> weights = {
        ...     "technical": Decimal("0.3"),
        ...     "pattern": Decimal("0.3"),
        ...     "volume": Decimal("0.2"),
        ...     "trend": Decimal("0.2"),
        ... }
        >>> confidence = calculate_composite_confidence(
        ...     Decimal("0.8"), Decimal("0.7"), Decimal("0.9"), Decimal("0.75"), weights
        ... )
        >>> assert Decimal("0.0") <= confidence <= Decimal("1.0")
    """
    logger.info("複合信頼度スコア計算開始")

    try:
        # 重みの合計確認
        weight_sum = sum(weights.values())
        if abs(weight_sum - Decimal("1.0")) > Decimal("0.001"):
            raise ValueError(f"重みの合計が1.0ではありません: {weight_sum}")

        # 入力値の範囲確認
        confidence_values = [
            technical_confidence,
            pattern_confidence,
            volume_confidence,
            trend_strength,
        ]
        for i, value in enumerate(confidence_values):
            if not (Decimal("0.0") <= value <= Decimal("1.0")):
                raise ValueError(
                    f"信頼度値が範囲外です（0-1）: index={i}, value={value}"
                )

        # 重み付け平均計算
        composite_score = (
            technical_confidence * weights["technical"]
            + pattern_confidence * weights["pattern"]
            + volume_confidence * weights["volume"]
            + trend_strength * weights["trend"]
        )

        # 0-1範囲に正規化（念のため）
        result = max(Decimal("0.0"), min(Decimal("1.0"), composite_score))

        logger.info(f"複合信頼度スコア計算完了: {result:.3f}")
        return result

    except Exception as e:
        logger.error(f"複合信頼度計算エラー: {e!s}")
        raise ValueError(f"複合信頼度の計算に失敗しました: {e!s}") from e


def generate_enhanced_factors(
    signal_type: SignalType,
    analysis_data: dict[str, Decimal],
    composite_confidence: Decimal,
) -> list[str]:
    """拡張シグナル根拠生成.

    分析結果データから詳細なシグナル判定根拠を自動生成する。

    Args:
        signal_type: シグナルタイプ
        analysis_data: 分析結果データ辞書
        composite_confidence: 複合信頼度スコア

    Returns:
        List[str]: 生成された判定根拠のリスト

    Raises:
        ValueError: 無効な入力値の場合

    Example:
        >>> data = {
        ...     "technical_confidence": Decimal("0.8"),
        ...     "risk_reward_ratio": Decimal("2.0"),
        ... }
        >>> factors = generate_enhanced_factors(SignalType.BUY, data, Decimal("0.8"))
        >>> assert len(factors) >= 5
    """
    logger.info(
        f"拡張根拠生成開始: シグナル={signal_type}, 複合信頼度={composite_confidence}"
    )

    factors = []

    try:
        # 複合信頼度に基づく説明
        if composite_confidence >= Decimal("0.9"):
            factors.append(
                f"非常に高い複合信頼度（{composite_confidence:.1%}）で{signal_type.value}シグナルを確認"
            )
        elif composite_confidence >= Decimal("0.8"):
            factors.append(
                f"高い複合信頼度（{composite_confidence:.1%}）で{signal_type.value}シグナルを確認"
            )
        elif composite_confidence >= Decimal("0.7"):
            factors.append(
                f"中程度の複合信頼度（{composite_confidence:.1%}）で{signal_type.value}シグナルを確認"
            )
        else:
            factors.append(
                f"低めの複合信頼度（{composite_confidence:.1%}）で{signal_type.value}シグナルを検出"
            )

        # 各指標の個別評価
        if "technical_confidence" in analysis_data:
            tech_conf = analysis_data["technical_confidence"]
            if tech_conf >= Decimal("0.8"):
                factors.append(
                    f"テクニカル分析指標が強い買いサポート（信頼度{tech_conf:.1%}）"
                )
            elif tech_conf >= Decimal("0.6"):
                factors.append(
                    f"テクニカル分析指標が中程度のサポート（信頼度{tech_conf:.1%}）"
                )

        if "pattern_confidence" in analysis_data:
            pattern_conf = analysis_data["pattern_confidence"]
            if pattern_conf >= Decimal("0.7"):
                factors.append(
                    f"価格パターンが明確なシグナルを示唆（信頼度{pattern_conf:.1%}）"
                )

        if "volume_confidence" in analysis_data:
            vol_conf = analysis_data["volume_confidence"]
            if vol_conf >= Decimal("0.8"):
                factors.append(
                    f"出来高分析が強いトレンド継続を示唆（信頼度{vol_conf:.1%}）"
                )

        # リスクリワード比率の評価
        if "risk_reward_ratio" in analysis_data:
            ratio = analysis_data["risk_reward_ratio"]
            if ratio >= Decimal("3.0"):
                factors.append(f"非常に有利なリスクリワード比率（{ratio:.1f}:1）")
            elif ratio >= Decimal("2.0"):
                factors.append(f"良好なリスクリワード比率（{ratio:.1f}:1）")
            elif ratio >= Decimal("1.5"):
                factors.append(f"許容範囲のリスクリワード比率（{ratio:.1f}:1）")
            else:
                factors.append(f"リスクリワード比率に注意が必要（{ratio:.1f}:1）")

        # 価格目標の説明
        if all(
            key in analysis_data
            for key in ["current_price", "target_price", "stop_loss"]
        ):
            current = analysis_data["current_price"]
            target = analysis_data["target_price"]
            stop = analysis_data["stop_loss"]

            if signal_type == SignalType.BUY:
                gain_pct = (target - current) / current * 100
                loss_pct = (current - stop) / current * 100
                factors.append(
                    f"ターゲット価格{target}（+{gain_pct:.1f}%）、ストップロス{stop}（-{loss_pct:.1f}%）"
                )
            else:
                gain_pct = (current - target) / current * 100
                loss_pct = (stop - current) / current * 100
                factors.append(
                    f"ターゲット価格{target}（+{gain_pct:.1f}%）、ストップロス{stop}（-{loss_pct:.1f}%）"
                )

        # モメンタム評価
        if "price_momentum" in analysis_data:
            momentum = analysis_data["price_momentum"]
            if momentum >= Decimal("0.8"):
                factors.append("価格モメンタムが非常に強い状態")
            elif momentum >= Decimal("0.6"):
                factors.append("価格モメンタムが良好な状態")

        # 最低限の根拠数を確保
        if len(factors) < 5:
            factors.append(f"{signal_type.value}シグナルの総合的な分析結果に基づく推奨")

        logger.info(f"拡張根拠生成完了: {len(factors)}個の根拠を生成")
        return factors

    except Exception as e:
        logger.error(f"拡張根拠生成エラー: {e!s}")
        raise ValueError(f"拡張根拠の生成に失敗しました: {e!s}") from e


def generate_complete_signal(
    monthly_trend_result: MonthlyTrendResult,
    technical_confidence: Decimal,
    pattern_confidence: Decimal,
    volume_confidence: Decimal,
) -> SwingSignal:
    """統合シグナルジェネレーター.

    全ての機能を統合して最終的なスイングトレードシグナルを生成する。
    基本シグナル、価格レベル計算、信頼度評価、拡張根拠生成を組み合わせる。

    Args:
        monthly_trend_result: 月次トレンド分析結果
        technical_confidence: テクニカル分析信頼度
        pattern_confidence: パターン分析信頼度
        volume_confidence: 出来高分析信頼度

    Returns:
        SwingSignal: 統合された完全なシグナル

    Raises:
        ValueError: 無効な入力値の場合

    Example:
        >>> result = MonthlyTrendResult(...)
        >>> signal = generate_complete_signal(
        ...     result, Decimal("0.8"), Decimal("0.7"), Decimal("0.9")
        ... )
        >>> assert signal.signal_type in [
        ...     SignalType.BUY,
        ...     SignalType.SELL,
        ...     SignalType.HOLD,
        ...     SignalType.WAIT,
        ... ]
    """
    try:
        # 入力値検証
        if monthly_trend_result is None:
            raise ValueError("monthly_trend_result は必須です")

        logger.info(f"統合シグナル生成開始: {monthly_trend_result.symbol}")

        confidence_values = [
            technical_confidence,
            pattern_confidence,
            volume_confidence,
        ]
        for i, value in enumerate(confidence_values):
            if not (Decimal("0.0") <= value <= Decimal("1.0")):
                raise ValueError(
                    f"信頼度値が範囲外です（0-1）: index={i}, value={value}"
                )

        # Step 1: 基本シグナル生成
        logger.info("Step 1: 基本シグナル生成")
        basic_signal = generate_basic_signal(monthly_trend_result)

        # Step 2: 複合信頼度計算
        logger.info("Step 2: 複合信頼度計算")
        trend_strength = monthly_trend_result.trend_strength.strength
        weights = {
            "technical": Decimal("0.30"),
            "pattern": Decimal("0.25"),
            "volume": Decimal("0.20"),
            "trend": Decimal("0.25"),
        }

        composite_confidence = calculate_composite_confidence(
            technical_confidence=technical_confidence,
            pattern_confidence=pattern_confidence,
            volume_confidence=volume_confidence,
            trend_strength=trend_strength,
            weights=weights,
        )

        # Step 3: 価格レベル計算
        logger.info("Step 3: 価格レベル計算")

        # MonthlyTrendResultから現在価格を取得（最新の月次リターンの終値）
        if monthly_trend_result.monthly_returns:
            current_price = monthly_trend_result.monthly_returns[-1].end_price
        else:
            raise ValueError(
                "月次リターンデータが不足しているため、現在価格を取得できません"
            )

        # support_resistanceは辞書形式
        support_levels = monthly_trend_result.support_resistance.get("support", [])
        resistance_levels = monthly_trend_result.support_resistance.get(
            "resistance", []
        )

        target_price = None
        stop_loss = None
        risk_reward_ratio = None

        # BUYまたはSELLシグナルの場合のみ価格計算
        if basic_signal.signal_type in [SignalType.BUY, SignalType.SELL]:
            try:
                target_price = calculate_target_price(
                    current_price=current_price,
                    signal_type=basic_signal.signal_type,
                    resistance_levels=resistance_levels,
                    support_levels=support_levels,
                    expected_return_rate=Decimal("0.12"),  # 12%期待リターン
                )

                stop_loss = calculate_stop_loss(
                    current_price=current_price,
                    signal_type=basic_signal.signal_type,
                    support_levels=support_levels,
                    resistance_levels=resistance_levels,
                    risk_tolerance=Decimal("0.08"),  # 8%リスク許容度
                )

                risk_reward_ratio = calculate_risk_reward_ratio(
                    current_price=current_price,
                    target_price=target_price,
                    stop_loss=stop_loss,
                )

            except Exception as e:
                logger.warning(f"価格レベル計算でエラー: {e!s}. デフォルト値を使用")
                # フォールバック価格設定
                if basic_signal.signal_type == SignalType.BUY:
                    target_price = current_price * Decimal("1.12")
                    stop_loss = current_price * Decimal("0.92")
                else:  # SELL
                    target_price = current_price * Decimal("0.88")
                    stop_loss = current_price * Decimal("1.08")

                risk_reward_ratio = calculate_risk_reward_ratio(
                    current_price=current_price,
                    target_price=target_price,
                    stop_loss=stop_loss,
                )

        # Step 4: 拡張根拠生成
        logger.info("Step 4: 拡張根拠生成")
        analysis_data = {
            "technical_confidence": technical_confidence,
            "pattern_confidence": pattern_confidence,
            "volume_confidence": volume_confidence,
            "trend_strength": trend_strength,
            "price_momentum": monthly_trend_result.trend_strength.momentum,
            "current_price": current_price,
        }

        # 価格データが計算できた場合は追加
        if target_price is not None:
            analysis_data["target_price"] = target_price
        if stop_loss is not None:
            analysis_data["stop_loss"] = stop_loss
        if risk_reward_ratio is not None:
            analysis_data["risk_reward_ratio"] = risk_reward_ratio

        enhanced_factors = generate_enhanced_factors(
            signal_type=basic_signal.signal_type,
            analysis_data=analysis_data,
            composite_confidence=composite_confidence,
        )

        # Step 5: 統合シグナル構築
        logger.info("Step 5: 統合シグナル構築")
        final_signal = SwingSignal(
            signal_type=basic_signal.signal_type,
            confidence=composite_confidence,  # 複合信頼度を使用
            supporting_factors=enhanced_factors,  # 拡張根拠を使用
            generated_at=datetime.now(UTC),
        )

        logger.info(
            f"統合シグナル生成完了: {final_signal.signal_type.value}, "
            f"信頼度: {final_signal.confidence:.3f}, "
            f"根拠数: {len(final_signal.supporting_factors)}"
        )

        return final_signal

    except Exception as e:
        logger.error(f"統合シグナル生成エラー: {e!s}")
        raise ValueError(f"統合シグナルの生成に失敗しました: {e!s}") from e
