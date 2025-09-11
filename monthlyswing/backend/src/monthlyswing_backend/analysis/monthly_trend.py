"""monthly_trend.py: 月次価格動向分析.

月次スイングトレード戦略における価格動向分析機能を提供。
TDD(テスト駆動開発)に基づく実装で信頼性を確保。

主要機能:
- 月次価格変動率計算
- トレンド強度評価
- サポート・レジスタンスレベル特定
- トレンド継続確率予測
- 統合分析クラス

技術特徴:
- Decimal型による金融計算精度保持
- 非同期処理対応
- 包括的エラーハンドリング
- 設定可能なパラメーター
"""

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import argrelextrema

from monthlyswing_backend.models.swing_models import (
    MonthlyReturn,
    MonthlyTrendResult,
    SupportResistanceLevel,
    TrendAnalysisConfig,
    TrendDirection,
    TrendStrengthMetrics,
)

# ロガー設定
logger = logging.getLogger(__name__)


def calculate_monthly_returns(price_data: pd.DataFrame) -> dict[str, Any]:
    """月次価格変動率計算.

    株価データから月次リターンを計算し、統計情報と共に返す。
    金融計算の精度を保持し、異常値を適切に処理。

    Args:
        price_data: 株価データ(date, close列を含む)

    Returns:
        Dict[str, Any]: 月次リターンと期間情報
        - monthly_returns: 月次リターン一覧(Decimal)
        - periods: 各期間の開始・終了日
        - statistics: 統計情報(平均、標準偏差等)

    Raises:
        ValueError: 入力データが不正な場合

    Example:
        >>> data = pd.DataFrame(
        ...     {
        ...         "date": pd.date_range("2024-01-01", "2024-03-31"),
        ...         "close": [100.0 * (1.01**i) for i in range(90)],
        ...     }
        ... )
        >>> result = calculate_monthly_returns(data)
        >>> len(result["monthly_returns"])
        2
    """
    # 入力検証
    if price_data.empty:
        raise ValueError("株価データが空です")

    if len(price_data) < 30:
        raise ValueError("月次分析には最低30日のデータが必要です")

    required_columns = ["date", "close"]
    missing_columns = [col for col in required_columns if col not in price_data.columns]
    if missing_columns:
        raise ValueError(f"必要な列が不足しています: {missing_columns}")

    try:
        # データの準備
        data = price_data.copy()
        data["date"] = pd.to_datetime(data["date"])
        data = data.sort_values("date").reset_index(drop=True)

        # 終値をDecimal型に変換
        data["close"] = data["close"].apply(lambda x: Decimal(str(x)))

        # 月次データの集約
        data.set_index("date", inplace=True)
        monthly_data = data.resample("ME")["close"].last().dropna()

        if len(monthly_data) < 2:
            raise ValueError("月次リターン計算には最低2ヶ月のデータが必要です")

        # 月次リターン計算
        monthly_returns = []
        periods = []

        for i in range(1, len(monthly_data)):
            start_date = monthly_data.index[i - 1]
            end_date = monthly_data.index[i]
            start_price = monthly_data.iloc[i - 1]
            end_price = monthly_data.iloc[i]

            # リターン計算(Decimal精度保持)
            return_rate = (end_price - start_price) / start_price

            monthly_returns.append(return_rate)
            periods.append(
                {
                    "start_date": start_date.to_pydatetime(),
                    "end_date": end_date.to_pydatetime(),
                    "start_price": start_price,
                    "end_price": end_price,
                }
            )

        # 統計情報計算
        returns_float = [float(r) for r in monthly_returns]
        statistics = {
            "mean_return": Decimal(str(np.mean(returns_float))),
            "std_deviation": Decimal(str(np.std(returns_float))),
            "min_return": min(monthly_returns),
            "max_return": max(monthly_returns),
            "total_return": (monthly_data.iloc[-1] - monthly_data.iloc[0])
            / monthly_data.iloc[0],
        }

        logger.info(f"月次リターン計算完了: {len(monthly_returns)}期間")

        return {
            "monthly_returns": monthly_returns,
            "periods": periods,
            "statistics": statistics,
            "data_quality": {
                "total_days": len(price_data),
                "monthly_periods": len(monthly_returns),
                "data_completeness": 1.0,  # 簡単な実装
            },
        }

    except Exception as e:
        logger.error(f"月次リターン計算エラー: {e!s}")
        raise ValueError(f"月次リターン計算に失敗しました: {e!s}") from e


def identify_support_resistance_levels(
    price_data: pd.DataFrame, sensitivity: float = 0.5, min_touches: int = 2
) -> dict[str, list[dict[str, Any]]]:
    """サポート・レジスタンスレベル特定.

    価格データから重要なサポート・レジスタンスレベルを特定。
    統計的手法と価格動向分析を組み合わせて精度を向上。

    Args:
        price_data: 株価データ（high, low, close列を含む）
        sensitivity: 検出感度（0-1）
        min_touches: レベル認定に必要な最小接触回数

    Returns:
        Dict[str, List[Dict[str, Any]]]: サポート・レジスタンスレベル
        - support_levels: サポートレベル一覧
        - resistance_levels: レジスタンスレベル一覧

    Raises:
        ValueError: 入力データが不正な場合

    Example:
        >>> data = pd.DataFrame(
        ...     {
        ...         "date": pd.date_range("2024-01-01", periods=60),
        ...         "close": [100 + 10 * np.sin(i / 10) for i in range(60)],
        ...         "high": [close + 1 for close in close_prices],
        ...         "low": [close - 1 for close in close_prices],
        ...     }
        ... )
        >>> result = identify_support_resistance_levels(data)
        >>> len(result["support_levels"]) > 0
        True
    """
    # 入力検証
    if price_data.empty:
        raise ValueError("価格データが空です")

    required_columns = ["close", "high", "low"]
    missing_columns = [col for col in required_columns if col not in price_data.columns]
    if missing_columns:
        raise ValueError(f"必要な列が不足しています: {missing_columns}")

    try:
        # データ準備
        data = price_data.copy()
        if "date" in data.columns:
            data["date"] = pd.to_datetime(data["date"])
        else:
            data["date"] = pd.date_range(start="2024-01-01", periods=len(data))

        # 価格配列の準備
        closes = np.array([float(price) for price in data["close"]])
        highs = np.array([float(price) for price in data["high"]])
        lows = np.array([float(price) for price in data["low"]])

        # トレンド検出(線形回帰の傾きで判定)
        x = np.arange(len(closes))
        slope, _ = np.polyfit(x, closes, 1)
        is_trending = abs(slope) > (np.std(closes) / len(closes)) * 0.5

        # トレンド市場に適応した動的パラメータ
        if is_trending:
            # トレンド市場では小さいウィンドウサイズと少ない接触回数を許可
            window_size = max(3, int(len(closes) * 0.05))
            dynamic_min_touches = max(1, min_touches - 1)
            tolerance_factor = 0.03  # 3%許容範囲（より寛容）
        else:
            # レンジ相場では標準的なパラメータ
            window_size = max(5, int(len(closes) * 0.1))
            dynamic_min_touches = min_touches
            tolerance_factor = 0.02  # 2%許容範囲

        # ローカル最大値（レジスタンス候補）
        local_maxima = argrelextrema(highs, np.greater, order=window_size)[0]

        # ローカル最小値（サポート候補）
        local_minima = argrelextrema(lows, np.less, order=window_size)[0]

        # トレンド市場で極値が見つからない場合、より緩い条件で再試行
        if is_trending and (len(local_maxima) == 0 or len(local_minima) == 0):
            # より小さなウィンドウサイズで再試行
            smaller_window = max(1, window_size - 2)
            if len(local_maxima) == 0:
                local_maxima = argrelextrema(highs, np.greater, order=smaller_window)[0]
            if len(local_minima) == 0:
                local_minima = argrelextrema(lows, np.less, order=smaller_window)[0]

        # それでも見つからない場合、単純な高低値検索にフォールバック
        if len(local_minima) == 0:
            # 価格データを複数のセグメントに分割し、各セグメントの最低値を候補とする
            segment_size = max(5, len(lows) // 5)  # 5セグメント程度
            for i in range(0, len(lows), segment_size):
                segment_end = min(i + segment_size, len(lows))
                segment_min_idx = np.argmin(lows[i:segment_end]) + i
                local_minima = np.append(local_minima, segment_min_idx)

        if len(local_maxima) == 0:
            # 価格データを複数のセグメントに分割し、各セグメントの最高値を候補とする
            segment_size = max(5, len(highs) // 5)  # 5セグメント程度
            for i in range(0, len(highs), segment_size):
                segment_end = min(i + segment_size, len(highs))
                segment_max_idx = np.argmax(highs[i:segment_end]) + i
                local_maxima = np.append(local_maxima, segment_max_idx)

        # サポートレベル分析
        support_levels = []
        if len(local_minima) > 0:
            for idx in local_minima:
                level_price = Decimal(str(lows[idx]))

                # レベル周辺の価格接触回数を計算
                tolerance = float(level_price) * tolerance_factor
                touches = sum(
                    1 for low in lows if abs(low - float(level_price)) <= tolerance
                )

                if touches >= dynamic_min_touches:
                    confidence = min(1.0, touches / 8.0)  # より早く信頼度1.0に到達

                    support_levels.append(
                        {
                            "level": level_price,
                            "confidence": confidence,
                            "touch_count": touches,
                            "last_touch_date": data.iloc[idx]["date"],
                            "strength_score": Decimal(str(confidence * sensitivity)),
                        }
                    )

        # レジスタンスレベル分析
        resistance_levels = []
        if len(local_maxima) > 0:
            for idx in local_maxima:
                level_price = Decimal(str(highs[idx]))

                # レベル周辺の価格接触回数を計算（動的パラメータを使用）
                tolerance = float(level_price) * tolerance_factor
                touches = sum(
                    1 for high in highs if abs(high - float(level_price)) <= tolerance
                )

                if touches >= dynamic_min_touches:
                    confidence = min(1.0, touches / 8.0)  # より早く信頼度1.0に到達

                    resistance_levels.append(
                        {
                            "level": level_price,
                            "confidence": confidence,
                            "touch_count": touches,
                            "last_touch_date": data.iloc[idx]["date"],
                            "strength_score": Decimal(str(confidence * sensitivity)),
                        }
                    )

        # 信頼度順でソート
        support_levels.sort(key=lambda x: x["confidence"], reverse=True)
        resistance_levels.sort(key=lambda x: x["confidence"], reverse=True)

        logger.info(
            f"サポート・レジスタンス特定完了: サポート{len(support_levels)}, レジスタンス{len(resistance_levels)}"
        )

        return {
            "support_levels": support_levels,
            "resistance_levels": resistance_levels,
            "analysis_params": {
                "sensitivity": sensitivity,
                "min_touches": min_touches,
                "window_size": window_size,
                "data_points": len(data),
            },
        }

    except Exception as e:
        logger.error(f"サポート・レジスタンス特定エラー: {e!s}")
        raise ValueError(f"サポート・レジスタンス特定に失敗しました: {e!s}")


def evaluate_trend_strength(
    price_data: pd.DataFrame, window: int = 20
) -> dict[str, Any]:
    """トレンド強度評価.

    価格データからトレンドの方向と強度を評価。
    複数の技術指標を組み合わせて総合的なトレンド判定を行う。

    Args:
        price_data: 株価データ（close列を含む）
        window: 移動平均等の計算ウィンドウサイズ

    Returns:
        Dict[str, Any]: トレンド強度評価結果
        - direction: トレンド方向（上昇/下降/横這い）
        - strength: 強度スコア（0-1）
        - confidence: 信頼度（0-1）
        - momentum: モメンタム指標
        - consistency: トレンド一貫性

    Raises:
        ValueError: 入力データが不正な場合

    Example:
        >>> # 上昇トレンドデータ
        >>> data = pd.DataFrame({"close": [100 * (1.01**i) for i in range(50)]})
        >>> result = evaluate_trend_strength(data)
        >>> result["direction"]
        '上昇'
        >>> result["strength"] > 0.7
        True
    """
    # 入力検証
    if price_data.empty:
        raise ValueError("価格データが空です")

    if "close" not in price_data.columns:
        raise ValueError("終値データ（close列）が必要です")

    if len(price_data) < window:
        raise ValueError(f"トレンド分析には最低{window}日のデータが必要です")

    try:
        # データ準備
        data = price_data.copy()
        closes = np.array([float(price) for price in data["close"]])

        # 移動平均計算
        if len(closes) >= window:
            sma_short = np.convolve(
                closes, np.ones(window // 2) / (window // 2), mode="valid"
            )
            sma_long = np.convolve(closes, np.ones(window) / window, mode="valid")
        else:
            sma_short = closes
            sma_long = closes

        # リターン計算
        returns = np.diff(closes) / closes[:-1]

        # トレンド方向の判定
        if len(sma_short) > 0 and len(sma_long) > 0:
            recent_short = np.mean(sma_short[-min(5, len(sma_short)) :])
            recent_long = np.mean(sma_long[-min(5, len(sma_long)) :])
            price_trend = (recent_short - recent_long) / recent_long
        else:
            # 単純な傾きベースの判定
            x = np.arange(len(closes))
            slope, _, _r_value, _, _ = stats.linregress(x, closes)
            price_trend = slope / np.mean(closes)

        # トレンド方向決定
        if price_trend > 0.01:  # 1%以上の上昇傾向
            direction = TrendDirection.UPTREND
        elif price_trend < -0.01:  # 1%以上の下降傾向
            direction = TrendDirection.DOWNTREND
        else:
            direction = TrendDirection.SIDEWAYS

        # モメンタムと一貫性の事前計算
        recent_returns = returns[-min(10, len(returns)) :]
        momentum = (
            Decimal(str(np.mean(recent_returns)))
            if len(recent_returns) > 0
            else Decimal("0")
        )

        # 一貫性スコア（リターンの方向性一貫度）
        if len(recent_returns) > 0:
            positive_count = sum(1 for r in recent_returns if r > 0)
            consistency = abs(
                2 * positive_count / len(recent_returns) - 1
            )  # 0-1スケール
        else:
            consistency = 0.0

        # トレンド強度計算（改善版）
        # 横這い市場では低い強度を示すように調整
        if direction == TrendDirection.SIDEWAYS:
            # 横這い市場：ボラティリティベースの強度計算
            volatility = np.std(returns) if len(returns) > 0 else 0.0
            strength = min(0.3, volatility * 10)  # 横這いは最大0.3
        else:
            # トレンド市場：傾きベースの強度計算
            trend_strength = min(1.0, abs(price_trend) * 50)  # より適度なスケーリング
            consistency_factor = consistency * 0.5 + 0.5  # 一貫性を考慮
            strength = min(1.0, trend_strength * consistency_factor)

        # 信頼度計算（複数要因の組み合わせ）
        confidence = min(1.0, (strength + consistency) / 2)

        # トレンド継続日数推定
        duration_days = len(closes)  # 簡単な実装

        logger.info(f"トレンド強度評価完了: {direction.value}, 強度={strength:.2f}")

        return {
            "direction": direction.value,
            "strength": strength,
            "confidence": confidence,
            "momentum": momentum,
            "consistency": Decimal(str(consistency)),
            "duration_days": duration_days,
            "analysis_params": {
                "window_size": window,
                "data_points": len(closes),
                "trend_threshold": 0.01,
            },
        }

    except Exception as e:
        logger.error(f"トレンド強度評価エラー: {e!s}")
        raise ValueError(f"トレンド強度評価に失敗しました: {e!s}")


def predict_trend_continuation(
    price_data: pd.DataFrame, forecast_days: int = 30
) -> dict[str, Any]:
    """トレンド継続確率予測.

    現在のトレンドが指定期間継続する確率を予測。
    統計的手法と機械学習的アプローチを組み合わせ。

    Args:
        price_data: 株価データ（close列を含む）
        forecast_days: 予測期間（日数）

    Returns:
        Dict[str, Any]: トレンド継続予測結果
        - continuation_probability: 継続確率（0-1）
        - forecast_period_days: 予測期間
        - supporting_factors: 予測根拠
        - confidence_interval: 信頼区間

    Raises:
        ValueError: 入力データが不正な場合

    Example:
        >>> data = pd.DataFrame(
        ...     {
        ...         "close": [100 * (1.005**i) for i in range(45)]  # 安定上昇
        ...     }
        ... )
        >>> result = predict_trend_continuation(data, 30)
        >>> result["continuation_probability"] > 0.5
        True
    """
    # 入力検証
    if price_data.empty:
        raise ValueError("価格データが空です")

    if "close" not in price_data.columns:
        raise ValueError("終値データ（close列）が必要です")

    if len(price_data) < 30:
        raise ValueError("トレンド継続予測には最低30日のデータが必要です")

    if forecast_days < 1 or forecast_days > 90:
        raise ValueError("予測期間は1-90日の範囲で指定してください")

    try:
        # データ準備
        data = price_data.copy()
        closes = np.array([float(price) for price in data["close"]])

        # 基本統計計算
        returns = np.diff(closes) / closes[:-1]
        volatility = np.std(returns)

        # トレンド強度評価
        trend_eval = evaluate_trend_strength(price_data)
        trend_strength = trend_eval["strength"]
        trend_consistency = float(trend_eval["consistency"])

        # 継続確率の基本スコア計算
        base_probability = 0.5  # ベース確率

        # 強度による調整
        strength_factor = trend_strength * 0.3  # 最大30%の調整

        # 一貫性による調整
        consistency_factor = trend_consistency * 0.2  # 最大20%の調整

        # ボラティリティによる調整（低ボラティリティは安定性を示唆）
        volatility_factor = max(0, 0.1 - volatility * 10) * 0.1  # 最大10%の調整

        # 総合継続確率
        continuation_probability = min(
            1.0,
            max(
                0.0,
                base_probability
                + strength_factor
                + consistency_factor
                + volatility_factor,
            ),
        )

        # 予測根拠
        supporting_factors = []

        if trend_strength > 0.6:
            supporting_factors.append(f"強いトレンド強度（{trend_strength:.2f}）")

        if trend_consistency > 0.7:
            supporting_factors.append(f"高いトレンド一貫性（{trend_consistency:.2f}）")

        if volatility < 0.05:
            supporting_factors.append(f"低ボラティリティ（{volatility:.3f}）")

        if len(supporting_factors) == 0:
            supporting_factors.append("統計的基準値による予測")

        # 信頼区間の簡単な計算
        confidence_interval = {
            "lower": max(0.0, continuation_probability - 0.1),
            "upper": min(1.0, continuation_probability + 0.1),
        }

        logger.info(
            f"トレンド継続予測完了: 確率={continuation_probability:.2f}, 期間={forecast_days}日"
        )

        return {
            "continuation_probability": continuation_probability,
            "forecast_period_days": forecast_days,
            "supporting_factors": supporting_factors,
            "confidence_interval": confidence_interval,
            "analysis_components": {
                "trend_strength": trend_strength,
                "consistency": trend_consistency,
                "volatility": volatility,
                "base_probability": base_probability,
            },
        }

    except Exception as e:
        logger.error(f"トレンド継続予測エラー: {e!s}")
        raise ValueError(f"トレンド継続予測に失敗しました: {e!s}")


class MonthlyTrendAnalyzer:
    """月次トレンド分析器.

    月次スイングトレード戦略における包括的なトレンド分析を実行。
    全ての分析コンポーネントを統合し、統一的な結果を提供。

    Attributes:
        config: 分析設定パラメーター

    Example:
        >>> config = TrendAnalysisConfig(
        ...     min_data_points=30, confidence_threshold=Decimal("0.7")
        ... )
        >>> analyzer = MonthlyTrendAnalyzer(config)
        >>> result = analyzer.analyze_monthly_trend("AAPL", price_data)
    """

    def __init__(self, config: TrendAnalysisConfig) -> None:
        """月次トレンド分析器の初期化.

        Args:
            config: トレンド分析設定

        Raises:
            ValueError: 設定が不正な場合
        """
        self.config = config
        logger.info(f"MonthlyTrendAnalyzer初期化完了: {config}")

    def analyze_monthly_trend(
        self, symbol: str, price_data: pd.DataFrame
    ) -> MonthlyTrendResult:
        """月次トレンド完全分析.

        指定された銘柄の包括的な月次トレンド分析を実行。
        全ての分析コンポーネントを統合して統一結果を提供。

        Args:
            symbol: 銘柄シンボル
            price_data: 株価データ

        Returns:
            MonthlyTrendResult: 統合分析結果

        Raises:
            ValueError: 入力データまたは設定が不正な場合

        Example:
            >>> result = analyzer.analyze_monthly_trend("AAPL", data)
            >>> result.symbol
            'AAPL'
            >>> result.trend_strength.direction
            '上昇'
        """
        # 入力検証
        if not symbol or len(symbol.strip()) == 0:
            raise ValueError("シンボルが空または無効です")

        if price_data.empty:
            raise ValueError("分析に必要な価格データがありません")

        if len(price_data) < self.config.min_data_points:
            raise ValueError(
                f"分析に必要な最小データポイント数（{self.config.min_data_points}）未満です"
            )

        try:
            logger.info(f"{symbol}の月次トレンド分析開始")

            # データ期間の特定
            price_data_sorted = (
                price_data.sort_values("date")
                if "date" in price_data.columns
                else price_data
            )
            start_date = (
                price_data_sorted.iloc[0]["date"]
                if "date" in price_data.columns
                else datetime(2024, 1, 1)
            )
            end_date = (
                price_data_sorted.iloc[-1]["date"]
                if "date" in price_data.columns
                else datetime(2024, 3, 31)
            )

            # 各分析コンポーネントの実行

            # 1. 月次リターン計算
            monthly_returns_data = calculate_monthly_returns(price_data)
            monthly_returns = []

            for i, period in enumerate(monthly_returns_data["periods"]):
                monthly_return = MonthlyReturn(
                    start_date=period["start_date"],
                    end_date=period["end_date"],
                    return_rate=monthly_returns_data["monthly_returns"][i],
                    start_price=period["start_price"],
                    end_price=period["end_price"],
                )
                monthly_returns.append(monthly_return)

            # 2. トレンド強度評価
            trend_data = evaluate_trend_strength(
                price_data, self.config.volatility_window
            )
            trend_strength = TrendStrengthMetrics(
                direction=TrendDirection(trend_data["direction"]),
                strength=Decimal(str(trend_data["strength"])),
                confidence=Decimal(str(trend_data["confidence"])),
                momentum=trend_data["momentum"],
                consistency=trend_data["consistency"],
                duration_days=trend_data["duration_days"],
            )

            # 3. サポート・レジスタンス特定
            sr_data = identify_support_resistance_levels(
                price_data, float(self.config.support_resistance_sensitivity)
            )

            support_levels = []
            for level_data in sr_data["support_levels"]:
                level = SupportResistanceLevel(
                    level=level_data["level"],
                    confidence=Decimal(str(level_data["confidence"])),
                    touch_count=level_data["touch_count"],
                    last_touch_date=level_data["last_touch_date"],
                    level_type="サポート",
                    strength_score=level_data["strength_score"],
                )
                support_levels.append(level)

            resistance_levels = []
            for level_data in sr_data["resistance_levels"]:
                level = SupportResistanceLevel(
                    level=level_data["level"],
                    confidence=Decimal(str(level_data["confidence"])),
                    touch_count=level_data["touch_count"],
                    last_touch_date=level_data["last_touch_date"],
                    level_type="レジスタンス",
                    strength_score=level_data["strength_score"],
                )
                resistance_levels.append(level)

            # 4. トレンド継続確率予測
            continuation_data = predict_trend_continuation(
                price_data, self.config.forecast_period_days
            )

            # 5. 統合結果の構築
            result = MonthlyTrendResult(
                symbol=symbol.upper(),
                analysis_date=datetime.now(UTC),
                data_period={
                    "start_date": start_date
                    if isinstance(start_date, datetime)
                    else pd.to_datetime(start_date).to_pydatetime(),
                    "end_date": end_date
                    if isinstance(end_date, datetime)
                    else pd.to_datetime(end_date).to_pydatetime(),
                },
                monthly_returns=monthly_returns,
                trend_strength=trend_strength,
                support_resistance={
                    "support_levels": support_levels,
                    "resistance_levels": resistance_levels,
                },
                continuation_probability=Decimal(
                    str(continuation_data["continuation_probability"])
                ),
                metadata={
                    "analysis_config": self.config.model_dump(),
                    "data_quality": monthly_returns_data.get("data_quality", {}),
                    "analysis_version": "1.0.0",
                },
            )

            logger.info(f"{symbol}の月次トレンド分析完了")
            return result

        except Exception as e:
            logger.error(f"{symbol}の月次トレンド分析エラー: {e!s}")
            raise ValueError(f"月次トレンド分析に失敗しました: {e!s}")
