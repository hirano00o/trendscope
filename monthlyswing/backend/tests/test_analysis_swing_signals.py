"""test_analysis_swing_signals.py: スイングシグナル分析のテストスイート.

Swing Signals コンポーネントのTDD実装テストスイート。
各機能を単機能レベルで徹底的にテストし、品質を保証する。

テスト対象:
- 基本シグナル生成ロジック
- 価格レベル計算機能
- 信頼度とファクター評価
- 統合シグナルジェネレーター

TDD サイクル:
1. テスト作成 (Red)
2. 最小実装 (Green) 
3. リファクタリング
4. Lint/Format
"""

from datetime import datetime, UTC
from decimal import Decimal
import pytest
import numpy as np
import pandas as pd

from monthlyswing_backend.models.swing_models import (
    MonthlyTrendResult,
    TrendStrengthMetrics, 
    TrendDirection,
    SignalType,
    SwingSignal,
    SupportResistanceLevel,
    MonthlyReturn
)


class TestBasicSignalGeneration:
    """基本シグナル生成ロジックのテストクラス.
    
    Monthly Trend Analysis の結果から基本的な
    BUY/SELL/HOLD/WAIT シグナルを生成する機能をテスト。
    """

    def test_generate_buy_signal_from_strong_uptrend(self):
        """強い上昇トレンドからBUYシグナル生成.
        
        Given:
            - 強い上昇トレンド (strength > 0.7)
            - 高い信頼度 (confidence > 0.8)
            - 継続確率が高い (> 0.7)
            
        Expected:
            - SignalType.BUY が生成される
            - 適切な信頼度が設定される
            - supporting_factors にトレンド情報が含まれる
        """
        from monthlyswing_backend.analysis.swing_signals import generate_basic_signal
        
        # 強い上昇トレンドデータ作成
        trend_strength = TrendStrengthMetrics(
            direction=TrendDirection.UPTREND,
            strength=Decimal("0.85"),
            confidence=Decimal("0.90"),
            momentum=Decimal("0.75"),
            consistency=Decimal("0.80"),
            duration_days=25
        )
        
        monthly_trend_result = MonthlyTrendResult(
            symbol="AAPL",
            data_period={"start_date": datetime(2024, 1, 1), "end_date": datetime(2024, 3, 31)},
            monthly_returns=[
                MonthlyReturn(
                    start_date=datetime(2024, 1, 1),
                    end_date=datetime(2024, 1, 31),
                    return_rate=Decimal("0.08"),
                    start_price=Decimal("150.00"),
                    end_price=Decimal("162.00")
                )
            ],
            trend_strength=trend_strength,
            support_resistance={"support": [], "resistance": []},
            continuation_probability=Decimal("0.78")
        )
        
        # シグナル生成実行
        signal = generate_basic_signal(monthly_trend_result)
        
        # 検証
        assert signal.signal_type == SignalType.BUY
        assert signal.confidence >= Decimal("0.7")
        assert len(signal.supporting_factors) > 0
        assert "強い上昇トレンド" in " ".join(signal.supporting_factors)
        assert signal.generated_at is not None

    def test_generate_sell_signal_from_strong_downtrend(self):
        """強い下降トレンドからSELLシグナル生成.
        
        Given:
            - 強い下降トレンド (strength > 0.7)
            - 高い信頼度 (confidence > 0.8)
            - 継続確率が高い (> 0.7)
            
        Expected:
            - SignalType.SELL が生成される
            - 適切な信頼度が設定される
            - supporting_factors に下降トレンド情報が含まれる
        """
        from monthlyswing_backend.analysis.swing_signals import generate_basic_signal
        
        # 強い下降トレンドデータ作成
        trend_strength = TrendStrengthMetrics(
            direction=TrendDirection.DOWNTREND,
            strength=Decimal("0.82"),
            confidence=Decimal("0.88"),
            momentum=Decimal("-0.68"),
            consistency=Decimal("0.77"),
            duration_days=28
        )
        
        monthly_trend_result = MonthlyTrendResult(
            symbol="TSLA",
            data_period={"start_date": datetime(2024, 1, 1), "end_date": datetime(2024, 3, 31)},
            monthly_returns=[
                MonthlyReturn(
                    start_date=datetime(2024, 1, 1),
                    end_date=datetime(2024, 1, 31),
                    return_rate=Decimal("-0.12"),
                    start_price=Decimal("200.00"),
                    end_price=Decimal("176.00")
                )
            ],
            trend_strength=trend_strength,
            support_resistance={"support": [], "resistance": []},
            continuation_probability=Decimal("0.75")
        )
        
        # シグナル生成実行
        signal = generate_basic_signal(monthly_trend_result)
        
        # 検証
        assert signal.signal_type == SignalType.SELL
        assert signal.confidence >= Decimal("0.7")
        assert len(signal.supporting_factors) > 0
        assert "強い下降トレンド" in " ".join(signal.supporting_factors)

    def test_generate_hold_signal_from_sideways_trend(self):
        """横這いトレンドからHOLDシグナル生成.
        
        Given:
            - 横這いトレンド
            - 中程度の強度 (0.3 < strength < 0.6)
            - 安定した価格推移
            
        Expected:
            - SignalType.HOLD が生成される
            - 信頼度が適切に設定される
            - supporting_factors に横這い情報が含まれる
        """
        from monthlyswing_backend.analysis.swing_signals import generate_basic_signal
        
        # 横這いトレンドデータ作成
        trend_strength = TrendStrengthMetrics(
            direction=TrendDirection.SIDEWAYS,
            strength=Decimal("0.45"),
            confidence=Decimal("0.72"),
            momentum=Decimal("0.05"),
            consistency=Decimal("0.68"),
            duration_days=30
        )
        
        monthly_trend_result = MonthlyTrendResult(
            symbol="SPY",
            data_period={"start_date": datetime(2024, 1, 1), "end_date": datetime(2024, 3, 31)},
            monthly_returns=[
                MonthlyReturn(
                    start_date=datetime(2024, 1, 1),
                    end_date=datetime(2024, 1, 31),
                    return_rate=Decimal("0.02"),
                    start_price=Decimal("480.00"),
                    end_price=Decimal("489.60")
                )
            ],
            trend_strength=trend_strength,
            support_resistance={"support": [], "resistance": []},
            continuation_probability=Decimal("0.65")
        )
        
        # シグナル生成実行
        signal = generate_basic_signal(monthly_trend_result)
        
        # 検証
        assert signal.signal_type == SignalType.HOLD
        assert Decimal("0.5") <= signal.confidence <= Decimal("0.8")
        assert "横這いトレンド" in " ".join(signal.supporting_factors)

    def test_generate_wait_signal_from_unclear_trend(self):
        """不明確なトレンドからWAITシグナル生成.
        
        Given:
            - 不明確なトレンド (UNKNOWN)
            - 低い信頼度 (< 0.6)
            - 不安定な状況
            
        Expected:
            - SignalType.WAIT が生成される
            - 低い信頼度が設定される
            - supporting_factors に不確実性が記載される
        """
        from monthlyswing_backend.analysis.swing_signals import generate_basic_signal
        
        # 不明確なトレンドデータ作成
        trend_strength = TrendStrengthMetrics(
            direction=TrendDirection.UNKNOWN,
            strength=Decimal("0.25"),
            confidence=Decimal("0.45"),
            momentum=Decimal("0.15"),
            consistency=Decimal("0.30"),
            duration_days=15
        )
        
        monthly_trend_result = MonthlyTrendResult(
            symbol="VOLATILE",
            data_period={"start_date": datetime(2024, 1, 1), "end_date": datetime(2024, 3, 31)},
            monthly_returns=[
                MonthlyReturn(
                    start_date=datetime(2024, 1, 1),
                    end_date=datetime(2024, 1, 31),
                    return_rate=Decimal("-0.01"),
                    start_price=Decimal("100.00"),
                    end_price=Decimal("99.00")
                )
            ],
            trend_strength=trend_strength,
            support_resistance={"support": [], "resistance": []},
            continuation_probability=Decimal("0.42")
        )
        
        # シグナル生成実行
        signal = generate_basic_signal(monthly_trend_result)
        
        # 検証
        assert signal.signal_type == SignalType.WAIT
        assert signal.confidence < Decimal("0.6")
        assert any("不明確" in factor or "様子見" in factor for factor in signal.supporting_factors)

    def test_signal_generation_edge_cases(self):
        """エッジケースのテスト.
        
        Given:
            - 境界値のデータ
            - None値を含むデータ
            
        Expected:
            - 適切なエラーハンドリング
            - デフォルト値の使用
        """
        from monthlyswing_backend.analysis.swing_signals import generate_basic_signal
        
        # 境界値データ作成
        trend_strength = TrendStrengthMetrics(
            direction=TrendDirection.UPTREND,
            strength=Decimal("0.70"),  # 境界値
            confidence=Decimal("0.60"),  # 境界値
            momentum=Decimal("0.00"),  # ゼロ
            consistency=Decimal("1.00"),  # 最大値
            duration_days=1  # 最小値
        )
        
        monthly_trend_result = MonthlyTrendResult(
            symbol="EDGE",
            data_period={"start_date": datetime(2024, 1, 1), "end_date": datetime(2024, 1, 31)},
            monthly_returns=[],  # 空のリスト
            trend_strength=trend_strength,
            support_resistance={"support": [], "resistance": []},
            continuation_probability=Decimal("0.50")  # 境界値
        )
        
        # シグナル生成実行（エラーが発生しないことを確認）
        signal = generate_basic_signal(monthly_trend_result)
        
        # 基本的な検証
        assert signal.signal_type in [SignalType.BUY, SignalType.SELL, SignalType.HOLD, SignalType.WAIT]
        assert Decimal("0.0") <= signal.confidence <= Decimal("1.0")
        assert signal.generated_at is not None


class TestPriceLevelCalculation:
    """価格レベル計算機能のテストクラス.
    
    target_price と stop_loss の自動計算機能をテスト。
    サポート・レジスタンスレベルと期待リターンを考慮。
    """

    def test_calculate_target_price_from_resistance_levels(self):
        """レジスタンスレベルからターゲット価格計算.
        
        Given:
            - BUYシグナル
            - 複数のレジスタンスレベル
            - 現在価格
            
        Expected:
            - 適切なターゲット価格が計算される
            - リスクリワード比率が合理的
        """
        from monthlyswing_backend.analysis.swing_signals import calculate_target_price
        from decimal import Decimal
        
        # テストデータ準備
        current_price = Decimal("100.00")
        resistance_levels = [
            SupportResistanceLevel(
                level=Decimal("120.00"),
                confidence=Decimal("0.85"),
                touch_count=3,
                last_touch_date=datetime(2024, 1, 15),
                level_type="レジスタンス",
                strength_score=Decimal("0.8")
            ),
            SupportResistanceLevel(
                level=Decimal("125.00"),
                confidence=Decimal("0.75"),
                touch_count=2,
                last_touch_date=datetime(2024, 1, 10),
                level_type="レジスタンス", 
                strength_score=Decimal("0.7")
            )
        ]
        
        signal_type = SignalType.BUY
        expected_return_rate = Decimal("0.15")  # 15%期待リターン
        
        # ターゲット価格計算実行
        target_price = calculate_target_price(
            current_price=current_price,
            signal_type=signal_type,
            resistance_levels=resistance_levels,
            support_levels=[],
            expected_return_rate=expected_return_rate
        )
        
        # 検証
        assert target_price is not None
        assert target_price > current_price  # BUYなので現在価格より高い
        assert target_price <= Decimal("120.00")  # 最初のレジスタンスレベル以下
        assert target_price >= current_price * (Decimal("1.0") + expected_return_rate * Decimal("0.8"))  # 期待リターンの80%以上

    def test_calculate_stop_loss_from_support_levels(self):
        """サポートレベルからストップロス計算.
        
        Given:
            - BUYシグナル
            - サポートレベル
            - リスク許容度
            
        Expected:
            - 適切なストップロス価格が計算される
            - 損失が許容範囲内
        """
        from monthlyswing_backend.analysis.swing_signals import calculate_stop_loss
        from decimal import Decimal
        
        # テストデータ準備
        current_price = Decimal("100.00")
        support_levels = [
            SupportResistanceLevel(
                level=Decimal("95.00"),
                confidence=Decimal("0.80"),
                touch_count=4,
                last_touch_date=datetime(2024, 1, 20),
                level_type="サポート",
                strength_score=Decimal("0.85")
            ),
            SupportResistanceLevel(
                level=Decimal("90.00"),
                confidence=Decimal("0.70"),
                touch_count=2,
                last_touch_date=datetime(2024, 1, 5),
                level_type="サポート",
                strength_score=Decimal("0.65")
            )
        ]
        
        signal_type = SignalType.BUY
        risk_tolerance = Decimal("0.08")  # 8%リスク許容度
        
        # ストップロス計算実行
        stop_loss = calculate_stop_loss(
            current_price=current_price,
            signal_type=signal_type,
            support_levels=support_levels,
            resistance_levels=[],
            risk_tolerance=risk_tolerance
        )
        
        # 検証
        assert stop_loss is not None
        assert stop_loss < current_price  # BUYなので現在価格より低い
        assert stop_loss >= Decimal("95.00")  # サポートレベル付近
        loss_rate = (current_price - stop_loss) / current_price
        assert loss_rate <= risk_tolerance * Decimal("1.2")  # 許容損失の120%以内

    def test_calculate_risk_reward_ratio(self):
        """リスクリワード比率計算.
        
        Given:
            - 現在価格
            - ターゲット価格
            - ストップロス価格
            
        Expected:
            - 適切なリスクリワード比率が計算される
            - 最低1.5:1以上が推奨
        """
        from monthlyswing_backend.analysis.swing_signals import calculate_risk_reward_ratio
        from decimal import Decimal
        
        current_price = Decimal("100.00")
        target_price = Decimal("115.00")  # 15%利益
        stop_loss = Decimal("92.00")      # 8%損失
        
        # リスクリワード比率計算
        ratio = calculate_risk_reward_ratio(
            current_price=current_price,
            target_price=target_price,
            stop_loss=stop_loss
        )
        
        # 検証
        assert ratio is not None
        assert ratio >= Decimal("1.5")  # 最低1.5:1比率
        expected_ratio = Decimal("15") / Decimal("8")  # 15%÷8% = 1.875
        assert abs(ratio - expected_ratio) < Decimal("0.1")

    def test_sell_signal_price_calculations(self):
        """SELLシグナル用価格計算.
        
        Given:
            - SELLシグナル
            - サポート・レジスタンスレベル
            
        Expected:
            - ターゲット価格 < 現在価格
            - ストップロス > 現在価格
            - 適切なリスクリワード比率
        """
        from monthlyswing_backend.analysis.swing_signals import (
            calculate_target_price, calculate_stop_loss
        )
        from decimal import Decimal
        
        current_price = Decimal("100.00")
        
        # SELLシグナル用サポートレベル
        support_levels = [
            SupportResistanceLevel(
                level=Decimal("85.00"),
                confidence=Decimal("0.80"),
                touch_count=3,
                last_touch_date=datetime(2024, 1, 15),
                level_type="サポート",
                strength_score=Decimal("0.75")
            )
        ]
        
        # SELLシグナル用レジスタンスレベル  
        resistance_levels = [
            SupportResistanceLevel(
                level=Decimal("105.00"),
                confidence=Decimal("0.85"),
                touch_count=4,
                last_touch_date=datetime(2024, 1, 20),
                level_type="レジスタンス",
                strength_score=Decimal("0.80")
            )
        ]
        
        # SELLシグナル価格計算
        target_price = calculate_target_price(
            current_price=current_price,
            signal_type=SignalType.SELL,
            resistance_levels=resistance_levels,
            support_levels=support_levels,
            expected_return_rate=Decimal("0.12")
        )
        
        stop_loss = calculate_stop_loss(
            current_price=current_price,
            signal_type=SignalType.SELL,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            risk_tolerance=Decimal("0.06")
        )
        
        # 検証
        assert target_price < current_price  # SELLなので現在価格より低い
        assert stop_loss > current_price     # SELLなので現在価格より高い
        assert target_price >= Decimal("85.00")  # サポートレベル以上


class TestConfidenceAndFactorEvaluation:
    """信頼度とファクター評価のテストクラス.
    
    複数指標を合成した信頼度計算と
    supporting_factors 自動生成をテスト。
    """

    def test_calculate_composite_confidence_score(self):
        """複合信頼度スコア計算.
        
        Given:
            - 複数の分析指標
            - 各指標の重み
            
        Expected:
            - 重み付け平均による信頼度計算
            - 0-1 範囲での正規化
        """
        from monthlyswing_backend.analysis.swing_signals import calculate_composite_confidence
        from decimal import Decimal
        
        # テストデータ準備
        technical_confidence = Decimal("0.85")  # テクニカル分析信頼度
        pattern_confidence = Decimal("0.70")    # パターン分析信頼度
        volume_confidence = Decimal("0.90")     # 出来高分析信頼度
        trend_strength = Decimal("0.80")        # トレンド強度
        
        # 重みの設定（合計1.0）
        weights = {
            "technical": Decimal("0.30"),
            "pattern": Decimal("0.25"), 
            "volume": Decimal("0.20"),
            "trend": Decimal("0.25")
        }
        
        # 複合信頼度計算実行
        composite_confidence = calculate_composite_confidence(
            technical_confidence=technical_confidence,
            pattern_confidence=pattern_confidence,
            volume_confidence=volume_confidence,
            trend_strength=trend_strength,
            weights=weights
        )
        
        # 検証
        assert composite_confidence is not None
        assert Decimal("0.0") <= composite_confidence <= Decimal("1.0")  # 0-1範囲内
        
        # 手動計算による検証
        expected = (
            technical_confidence * weights["technical"] +
            pattern_confidence * weights["pattern"] +
            volume_confidence * weights["volume"] +
            trend_strength * weights["trend"]
        )
        assert abs(composite_confidence - expected) < Decimal("0.001")  # 計算精度確認

    def test_generate_supporting_factors_automatically(self):
        """シグナル根拠の自動生成.
        
        Given:
            - 分析結果データ
            - シグナルタイプ
            
        Expected:
            - 判定根拠の自動生成
            - 日本語での説明文
        """
        from monthlyswing_backend.analysis.swing_signals import generate_enhanced_factors
        from decimal import Decimal
        
        # テストデータ準備
        analysis_data = {
            "technical_confidence": Decimal("0.85"),
            "pattern_confidence": Decimal("0.70"),
            "volume_confidence": Decimal("0.90"),
            "trend_strength": Decimal("0.80"),
            "price_momentum": Decimal("0.75"),
            "risk_reward_ratio": Decimal("2.5"),
            "target_price": Decimal("110.00"),
            "stop_loss": Decimal("95.00"),
            "current_price": Decimal("100.00")
        }
        
        signal_type = SignalType.BUY
        composite_confidence = Decimal("0.81")  # 複合信頼度
        
        # 拡張根拠生成実行
        factors = generate_enhanced_factors(
            signal_type=signal_type,
            analysis_data=analysis_data,
            composite_confidence=composite_confidence
        )
        
        # 検証
        assert isinstance(factors, list)
        assert len(factors) >= 5  # 最低5つの根拠
        
        # 信頼度に関する説明が含まれているか
        confidence_explained = any("信頼度" in factor for factor in factors)
        assert confidence_explained
        
        # リスクリワード比率の説明が含まれているか
        risk_reward_explained = any("リスク" in factor for factor in factors)
        assert risk_reward_explained
        
        # 価格目標の説明が含まれているか
        price_target_explained = any("ターゲット" in factor or "目標" in factor for factor in factors)
        assert price_target_explained
        
        # 全ての根拠が文字列で日本語で記述されているか
        for factor in factors:
            assert isinstance(factor, str)
            assert len(factor) > 0
            
    def test_confidence_score_edge_cases(self):
        """信頼度計算のエッジケーステスト.
        
        Given:
            - 極端な値（0.0, 1.0）
            - 不均等な重み
            
        Expected:
            - 適切な範囲制限
            - エラーハンドリング
        """
        from monthlyswing_backend.analysis.swing_signals import calculate_composite_confidence
        from decimal import Decimal
        
        # エッジケース1: 全て最小値
        weights_balanced = {
            "technical": Decimal("0.25"),
            "pattern": Decimal("0.25"),
            "volume": Decimal("0.25"),
            "trend": Decimal("0.25")
        }
        
        min_confidence = calculate_composite_confidence(
            technical_confidence=Decimal("0.0"),
            pattern_confidence=Decimal("0.0"),
            volume_confidence=Decimal("0.0"),
            trend_strength=Decimal("0.0"),
            weights=weights_balanced
        )
        assert min_confidence == Decimal("0.0")
        
        # エッジケース2: 全て最大値
        max_confidence = calculate_composite_confidence(
            technical_confidence=Decimal("1.0"),
            pattern_confidence=Decimal("1.0"),
            volume_confidence=Decimal("1.0"),
            trend_strength=Decimal("1.0"),
            weights=weights_balanced
        )
        assert max_confidence == Decimal("1.0")
        
        # エッジケース3: 不均等な重み
        unbalanced_weights = {
            "technical": Decimal("0.70"),
            "pattern": Decimal("0.10"),
            "volume": Decimal("0.10"),
            "trend": Decimal("0.10")
        }
        
        unbalanced_confidence = calculate_composite_confidence(
            technical_confidence=Decimal("0.9"),  # 高い値
            pattern_confidence=Decimal("0.3"),    # 低い値
            volume_confidence=Decimal("0.3"),     # 低い値
            trend_strength=Decimal("0.3"),        # 低い値
            weights=unbalanced_weights
        )
        
        # テクニカル分析の重みが高いため、結果もそれに近くなるはず
        assert unbalanced_confidence > Decimal("0.7")  # テクニカル分析寄り


class TestIntegratedSignalGenerator:
    """統合シグナルジェネレーターのテストクラス.
    
    全機能を統合した完全なシグナル生成システムをテスト。
    MonthlyTrendAnalyzer との連携も含む。
    """

    def test_complete_signal_generation_workflow(self):
        """完全なシグナル生成ワークフロー.
        
        Given:
            - 株価データ
            - 分析設定
            
        Expected:
            - 月次分析からシグナル生成まで一貫して実行
            - 全フィールドが適切に設定
        """
        # この機能は次のTDDサイクルで実装
        pass

    def test_signal_generator_error_handling(self):
        """シグナルジェネレーターのエラーハンドリング.
        
        Given:
            - 不正なデータ
            - 分析失敗ケース
            
        Expected:
            - 適切なエラーハンドリング
            - ログ出力
            - フォールバック動作
        """
        # この機能は次のTDDサイクルで実装
        pass