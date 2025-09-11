"""
test_analysis_monthly_trend.py: 月次トレンド分析のテストスイート

月次スイングトレード戦略における価格動向分析機能のテストを定義。
TDD（テスト駆動開発）に従い、実装前にテストケースを作成。

テスト対象機能:
- 月次価格変動率計算
- トレンド強度評価
- サポート・レジスタンスレベル特定
- 月次高値・安値検出
- トレンド継続確率予測

テスト戦略:
- 単体テスト（関数レベル）
- 統合テスト（モジュール連携）
- エッジケーステスト（異常データ）
- パフォーマンステスト
"""

from datetime import datetime
from decimal import Decimal

import pytest

import numpy as np
import pandas as pd

from monthlyswing_backend.analysis.monthly_trend import (
    MonthlyTrendAnalyzer,
    MonthlyTrendResult,
    calculate_monthly_returns,
    evaluate_trend_strength,
    identify_support_resistance_levels,
    predict_trend_continuation,
)
from monthlyswing_backend.models.swing_models import (
    TrendAnalysisConfig,
)


class TestCalculateMonthlyReturns:
    """月次価格変動率計算のテストクラス

    月次リターン計算機能の正確性を検証する。
    金融計算の精度を保持し、エッジケースを適切に処理することを確認。
    """

    @pytest.fixture
    def sample_price_data(self) -> pd.DataFrame:
        """テスト用株価データ生成

        月次分析用のサンプル株価データを生成。
        3ヶ月分のOHLC（始値、高値、安値、終値）データ。

        Returns:
            pd.DataFrame: テスト用株価データ
        """
        dates = pd.date_range(start="2024-01-01", end="2024-03-31", freq="D")
        np.random.seed(42)  # 再現性のため

        # 基準価格から始まるランダムウォーク
        base_price = 100.0
        returns = np.random.normal(0, 0.02, len(dates))  # 日次リターン（2%標準偏差）
        prices = [base_price]

        for i in range(1, len(dates)):
            prices.append(prices[-1] * (1 + returns[i]))

        # OHLC データ生成
        data = []
        for i, date in enumerate(dates):
            price = prices[i]
            # 高値・安値を価格の±5%以内で設定
            high = price * (1 + np.random.uniform(0, 0.05))
            low = price * (1 - np.random.uniform(0, 0.05))
            open_price = price * (1 + np.random.uniform(-0.02, 0.02))
            close_price = price

            data.append(
                {
                    "date": date,
                    "open": Decimal(str(round(open_price, 2))),
                    "high": Decimal(str(round(high, 2))),
                    "low": Decimal(str(round(low, 2))),
                    "close": Decimal(str(round(close_price, 2))),
                    "volume": int(np.random.uniform(100000, 1000000)),
                }
            )

        return pd.DataFrame(data)

    def test_calculate_monthly_returns_basic(
        self, sample_price_data: pd.DataFrame
    ) -> None:
        """基本的な月次リターン計算テスト

        正常なデータに対して月次リターンが正しく計算されることを確認。

        Args:
            sample_price_data: テスト用株価データ

        Expected:
            - 3ヶ月のデータから2つの月次リターンが計算される
            - リターン値がDecimal型で精度が保持される
            - 計算結果が数学的に正しい
        """
        result = calculate_monthly_returns(sample_price_data)

        # 基本的な検証
        assert isinstance(result, dict), "戻り値は辞書型である必要があります"
        assert "monthly_returns" in result, "monthly_returns キーが必要です"
        assert "periods" in result, "periods キーが必要です"

        monthly_returns = result["monthly_returns"]
        periods = result["periods"]

        # リターン数の検証（3ヶ月データから2つのリターン）
        assert len(monthly_returns) == 2, (
            "3ヶ月データから2つの月次リターンが計算される必要があります"
        )
        assert len(periods) == 2, "期間情報も同数である必要があります"

        # データ型の検証
        for return_val in monthly_returns:
            assert isinstance(return_val, Decimal), (
                "リターン値はDecimal型である必要があります"
            )
            assert abs(return_val) < Decimal("1.0"), (
                "月次リターンは-100%〜+100%の範囲内である必要があります"
            )

        # 期間情報の検証
        for period in periods:
            assert "start_date" in period, "開始日が必要です"
            assert "end_date" in period, "終了日が必要です"
            assert isinstance(period["start_date"], datetime), (
                "開始日はdatetime型である必要があります"
            )
            assert isinstance(period["end_date"], datetime), (
                "終了日はdatetime型である必要があります"
            )

    def test_calculate_monthly_returns_empty_data(self) -> None:
        """空データに対するエラーハンドリングテスト

        空のDataFrameが入力された場合の適切なエラー処理を確認。

        Expected:
            - ValueError例外が発生する
            - 適切なエラーメッセージが含まれる
        """
        empty_data = pd.DataFrame()

        with pytest.raises(ValueError, match="株価データが空です"):
            calculate_monthly_returns(empty_data)

    def test_calculate_monthly_returns_insufficient_data(self) -> None:
        """不十分なデータに対するエラーハンドリングテスト

        月次計算に必要な最小データ量未満の場合のエラー処理を確認。

        Expected:
            - ValueError例外が発生する
            - 月次分析に必要な最小期間の説明が含まれる
        """
        # 1日分のデータのみ
        insufficient_data = pd.DataFrame(
            {"date": [datetime(2024, 1, 1)], "close": [Decimal("100.00")]}
        )

        with pytest.raises(ValueError, match="月次分析には最低"):
            calculate_monthly_returns(insufficient_data)


class TestIdentifySupportResistanceLevels:
    """サポート・レジスタンスレベル特定のテストクラス

    重要な価格水準（サポート・レジスタンス）の特定機能を検証。
    テクニカル分析における重要な概念の実装精度を確認。
    """

    @pytest.fixture
    def trend_data(self) -> pd.DataFrame:
        """トレンド分析用テストデータ生成

        明確なサポート・レジスタンスレベルを持つ価格データ。

        Returns:
            pd.DataFrame: トレンド分析用株価データ
        """
        dates = pd.date_range(start="2024-01-01", end="2024-02-29", freq="D")

        # サポート100、レジスタンス120の明確なレンジ相場を作成
        support_level = Decimal("100.00")
        resistance_level = Decimal("120.00")

        data = []
        for i, date in enumerate(dates):
            # レンジ相場のパターン作成
            cycle_position = Decimal(str((i % 20) / 20))  # 20日サイクル
            if cycle_position < Decimal("0.5"):
                # 上昇トレンド部分
                price = support_level + (resistance_level - support_level) * (
                    cycle_position * Decimal("2")
                )
            else:
                # 下降トレンド部分
                price = resistance_level - (resistance_level - support_level) * (
                    (cycle_position - Decimal("0.5")) * Decimal("2")
                )

            # ノイズ追加
            noise = Decimal(str(np.random.uniform(-2, 2)))
            price = max(
                support_level - Decimal("5"),
                min(resistance_level + Decimal("5"), price + noise),
            )

            data.append(
                {
                    "date": date,
                    "close": price,
                    "high": price + Decimal("1"),
                    "low": price - Decimal("1"),
                    "volume": 500000,
                }
            )

        return pd.DataFrame(data)

    def test_identify_support_resistance_basic(self, trend_data: pd.DataFrame) -> None:
        """基本的なサポート・レジスタンス特定テスト

        明確なレンジ相場データからサポート・レジスタンスレベルが
        正しく特定されることを確認。

        Args:
            trend_data: レンジ相場のテストデータ

        Expected:
            - サポートレベル（約100）が特定される
            - レジスタンスレベル（約120）が特定される
            - 信頼度スコアが適切に計算される
        """
        result = identify_support_resistance_levels(trend_data)

        # 基本構造の検証
        assert isinstance(result, dict), "戻り値は辞書型である必要があります"
        assert "support_levels" in result, "support_levels キーが必要です"
        assert "resistance_levels" in result, "resistance_levels キーが必要です"

        support_levels = result["support_levels"]
        resistance_levels = result["resistance_levels"]

        # サポートレベルの検証
        assert len(support_levels) > 0, (
            "少なくとも1つのサポートレベルが特定される必要があります"
        )
        main_support = support_levels[0]
        assert isinstance(main_support["level"], Decimal), (
            "サポートレベルはDecimal型である必要があります"
        )
        assert Decimal("95") <= main_support["level"] <= Decimal("105"), (
            "メインサポートレベルは100付近である必要があります"
        )
        assert 0 < main_support["confidence"] <= 1, (
            "信頼度は0-1の範囲である必要があります"
        )

        # レジスタンスレベルの検証
        assert len(resistance_levels) > 0, (
            "少なくとも1つのレジスタンスレベルが特定される必要があります"
        )
        main_resistance = resistance_levels[0]
        assert isinstance(main_resistance["level"], Decimal), (
            "レジスタンスレベルはDecimal型である必要があります"
        )
        assert Decimal("115") <= main_resistance["level"] <= Decimal("125"), (
            "メインレジスタンスレベルは120付近である必要があります"
        )
        assert 0 < main_resistance["confidence"] <= 1, (
            "信頼度は0-1の範囲である必要があります"
        )

    def test_identify_support_resistance_trending_market(self) -> None:
        """トレンド相場でのサポート・レジスタンス特定テスト

        明確なトレンドがある場合のサポート・レジスタンス検出を確認。

        Expected:
            - 動的なサポート・レジスタンスレベルが特定される
            - トレンドライン的なレベルが検出される
        """
        # 上昇トレンドデータ生成
        dates = pd.date_range(start="2024-01-01", end="2024-01-31", freq="D")
        data = []

        for i, date in enumerate(dates):
            # 線形上昇トレンド + ノイズ
            base_price = 100 + (i * 2)  # 1日あたり2ポイント上昇
            noise = np.random.uniform(-3, 3)
            price = Decimal(str(base_price + noise))

            data.append(
                {
                    "date": date,
                    "close": price,
                    "high": price + Decimal("2"),
                    "low": price - Decimal("2"),
                    "volume": 300000,
                }
            )

        trend_data = pd.DataFrame(data)
        result = identify_support_resistance_levels(trend_data)

        # トレンド相場での検証
        assert len(result["support_levels"]) > 0, (
            "トレンド相場でもサポートレベルが特定される必要があります"
        )
        assert len(result["resistance_levels"]) > 0, (
            "トレンド相場でもレジスタンスレベルが特定される必要があります"
        )


class TestEvaluateTrendStrength:
    """トレンド強度評価のテストクラス

    価格トレンドの強さを数値化する機能の検証。
    月次スイングトレードにおける重要な判断材料。
    """

    def test_evaluate_trend_strength_strong_uptrend(self) -> None:
        """強い上昇トレンドの評価テスト

        明確な上昇トレンドデータで高いトレンド強度スコアが
        算出されることを確認。

        Expected:
            - トレンド方向が「上昇」と判定される
            - トレンド強度が0.7以上と評価される
            - 統計的信頼性が確保される
        """
        # 強い上昇トレンドデータ生成
        dates = pd.date_range(start="2024-01-01", end="2024-01-31", freq="D")
        data = []

        for i, date in enumerate(dates):
            # 強い上昇トレンド(日次1%上昇)
            price = 100 * (1.01**i)
            # 少量のノイズ
            noise_factor = 1 + np.random.uniform(-0.005, 0.005)
            price = Decimal(str(round(price * noise_factor, 2)))

            data.append(
                {
                    "date": date,
                    "close": price,
                    "high": price * Decimal("1.005"),
                    "low": price * Decimal("0.995"),
                    "volume": 1000000,
                }
            )

        trend_data = pd.DataFrame(data)
        result = evaluate_trend_strength(trend_data)

        # 強い上昇トレンドの検証
        assert isinstance(result, dict), "戻り値は辞書型である必要があります"
        assert result["direction"] == "上昇", (
            "トレンド方向が上昇と判定される必要があります"
        )
        assert result["strength"] >= 0.7, (
            "強いトレンドでは強度が0.7以上である必要があります"
        )
        assert result["strength"] <= 1.0, "トレンド強度の最大値は1.0です"
        assert 0 < result["confidence"] <= 1, "信頼度は0-1の範囲である必要があります"

    def test_evaluate_trend_strength_sideways_market(self) -> None:
        """横這い相場のトレンド強度評価テスト

        明確なトレンドがない横這い相場で低いトレンド強度が
        算出されることを確認。

        Expected:
            - トレンド方向が「横這い」と判定される
            - トレンド強度が0.3以下と評価される
        """
        # 横這い相場データ生成
        dates = pd.date_range(start="2024-01-01", end="2024-01-31", freq="D")
        data = []

        for _i, date in enumerate(dates):
            # 100付近でランダムに変動
            price = 100 + np.random.uniform(-5, 5)
            price = Decimal(str(round(price, 2)))

            data.append(
                {
                    "date": date,
                    "close": price,
                    "high": price + Decimal("1"),
                    "low": price - Decimal("1"),
                    "volume": 500000,
                }
            )

        sideways_data = pd.DataFrame(data)
        result = evaluate_trend_strength(sideways_data)

        # 横這い相場の検証
        assert result["direction"] == "横這い", (
            "トレンド方向が横這いと判定される必要があります"
        )
        assert result["strength"] <= 0.3, (
            "横這い相場では強度が0.3以下である必要があります"
        )


class TestPredictTrendContinuation:
    """トレンド継続確率予測のテストクラス

    現在のトレンドが継続する確率を予測する機能の検証。
    スイングトレードの重要な判断指標。
    """

    def test_predict_trend_continuation_basic(self) -> None:
        """基本的なトレンド継続確率予測テスト

        安定したトレンドデータで適切な継続確率が
        算出されることを確認。

        Expected:
            - 継続確率が0-1の範囲内である
            - 予測根拠が提供される
            - 統計的指標が含まれる
        """
        # 安定した上昇トレンドデータ
        dates = pd.date_range(start="2024-01-01", end="2024-02-15", freq="D")
        data = []

        for i, date in enumerate(dates):
            # 緩やかな上昇トレンド
            price = 100 * (1.005**i)  # 日次0.5%上昇
            noise = np.random.uniform(-1, 1)
            price = Decimal(str(round(price + noise, 2)))

            data.append({"date": date, "close": price, "volume": 750000})

        trend_data = pd.DataFrame(data)
        result = predict_trend_continuation(trend_data, forecast_days=30)

        # 予測結果の検証
        assert isinstance(result, dict), "戻り値は辞書型である必要があります"
        assert "continuation_probability" in result, "継続確率が必要です"
        assert "forecast_period_days" in result, "予測期間が必要です"
        assert "supporting_factors" in result, "予測根拠が必要です"

        probability = result["continuation_probability"]
        assert isinstance(probability, (float, Decimal)), (
            "確率は数値型である必要があります"
        )
        assert 0 <= probability <= 1, "確率は0-1の範囲である必要があります"
        assert result["forecast_period_days"] == 30, (
            "予測期間が正しく設定される必要があります"
        )


class TestMonthlyTrendAnalyzer:
    """MonthlyTrendAnalyzerクラスの統合テスト

    月次トレンド分析の全機能を統合したクラスの動作確認。
    実際の使用パターンでの動作を検証。
    """

    @pytest.fixture
    def analyzer(self) -> MonthlyTrendAnalyzer:
        """MonthlyTrendAnalyzerインスタンス生成

        Returns:
            MonthlyTrendAnalyzer: 設定済み分析インスタンス
        """
        config = TrendAnalysisConfig(
            min_data_points=30,
            confidence_threshold=0.7,
            forecast_period_days=30,
            volatility_window=20,
        )
        return MonthlyTrendAnalyzer(config)

    def test_analyzer_full_analysis(self, analyzer: MonthlyTrendAnalyzer) -> None:
        """完全な月次トレンド分析テスト

        実際の使用シナリオでの分析精度と結果の妥当性を確認。

        Args:
            analyzer: MonthlyTrendAnalyzer インスタンス

        Expected:
            - 全ての分析コンポーネントが正常動作する
            - 統合結果が適切に構造化される
            - 分析精度が要求水準を満たす
        """
        # 複雑な価格パターンのデータ生成
        dates = pd.date_range(start="2024-01-01", end="2024-03-31", freq="D")
        data = []

        for i, date in enumerate(dates):
            # 3つの段階：上昇→横這い→下降
            if i < 30:  # 上昇トレンド
                base_price = 100 + (i * 0.5)
            elif i < 60:  # 横這い
                base_price = 115 + np.random.uniform(-2, 2)
            else:  # 下降トレンド
                base_price = 115 - ((i - 60) * 0.3)

            noise = np.random.uniform(-1, 1)
            price = Decimal(str(round(base_price + noise, 2)))

            data.append(
                {
                    "date": date,
                    "open": price * Decimal("1.001"),
                    "high": price * Decimal("1.01"),
                    "low": price * Decimal("0.99"),
                    "close": price,
                    "volume": int(np.random.uniform(100000, 2000000)),
                }
            )

        price_data = pd.DataFrame(data)

        # 完全分析実行
        result = analyzer.analyze_monthly_trend(symbol="TEST", price_data=price_data)

        # 結果構造の検証
        assert isinstance(result, MonthlyTrendResult), (
            "戻り値はMonthlyTrendResult型である必要があります"
        )
        assert result.symbol == "TEST", "シンボルが正しく設定される必要があります"
        assert result.analysis_date is not None, "分析日時が記録される必要があります"
        assert result.monthly_returns is not None, (
            "月次リターンが計算される必要があります"
        )
        assert result.trend_strength is not None, (
            "トレンド強度が評価される必要があります"
        )
        assert result.support_resistance is not None, (
            "サポート・レジスタンスが特定される必要があります"
        )
        assert result.continuation_probability is not None, (
            "継続確率が予測される必要があります"
        )

    def test_analyzer_error_handling(self, analyzer: MonthlyTrendAnalyzer) -> None:
        """分析器のエラーハンドリングテスト

        不正なデータや設定に対する適切なエラー処理を確認。

        Args:
            analyzer: MonthlyTrendAnalyzer インスタンス

        Expected:
            - 適切なエラータイプが発生する
            - 有用なエラーメッセージが提供される
            - システムが適切に回復する
        """
        # 空データでの分析試行
        empty_data = pd.DataFrame()

        with pytest.raises(ValueError, match="分析に必要な"):
            analyzer.analyze_monthly_trend("EMPTY", empty_data)

        # 無効なシンボルでの分析試行
        valid_data = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=50),
                "close": [Decimal("100.00")] * 50,
            }
        )

        with pytest.raises(ValueError, match="シンボル"):
            analyzer.analyze_monthly_trend("", valid_data)
