"""monthly_swing_service.py: 月次スイングトレード統合サービス

月次トレンド分析とスイングシグナル生成を統合する高レベルサービス。
ビジネスロジックの中核を担い、APIエンドポイントとの橋渡しを行う。

主要機能:
- 株価データ取得と前処理
- 月次トレンド分析実行
- スイングシグナル生成
- 統合分析結果の構築
- エラーハンドリングと復旧処理

設計原則:
- 単一責任の原則
- 依存性注入対応
- 包括的エラーハンドリング
- ログ記録とモニタリング
- テスタビリティ重視
"""

import logging
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pandas as pd
import yfinance as yf

from monthlyswing_backend.analysis.monthly_trend import (
    MonthlyTrendAnalyzer,
    TrendAnalysisConfig,
)
from monthlyswing_backend.analysis.swing_signals import (
    generate_complete_signal,
)
from monthlyswing_backend.exceptions import (
    DataNotFoundError,
    DataValidationError,
    InsufficientDataError,
    MonthlySwingError,
    YFinanceError,
)
from monthlyswing_backend.models.swing_models import (
    MonthlyTrendResult,
    SignalType,
    SwingSignal,
)
from monthlyswing_backend.utils.error_handling import (
    handle_errors,
    log_performance_metrics,
    retry_on_error,
    validate_dataframe,
)

# ロガー設定
logger = logging.getLogger(__name__)


class MonthlySwingService:
    """月次スイングトレード統合サービス.

    月次トレンド分析からシグナル生成まで一気通貫で実行する
    高レベルサービスクラス。APIエンドポイントとの主要なインターフェース。

    Attributes:
        trend_analyzer: 月次トレンド分析器
        analysis_config: 分析設定

    Example:
        >>> service = MonthlySwingService()
        >>> result = await service.analyze_monthly_swing("AAPL")
        >>> print(f"シグナル: {result['swing_signal']['signal_type']}")
    """

    def __init__(self, analysis_config: TrendAnalysisConfig | None = None):
        """サービス初期化.

        Args:
            analysis_config: 分析設定（省略時はデフォルト使用）
        """
        self.analysis_config = analysis_config or TrendAnalysisConfig()
        self.trend_analyzer = MonthlyTrendAnalyzer(config=self.analysis_config)
        logger.info(
            "MonthlySwingService initialized with config: %s", self.analysis_config
        )

    async def analyze_monthly_swing(self, symbol: str) -> dict[str, Any]:
        """月次スイングトレード統合分析.

        株式シンボルを受け取り、月次トレンド分析からシグナル生成まで
        一気通貫で実行し、統合された分析結果を返す。

        Args:
            symbol: 株式シンボル (例: "AAPL", "7203.T")

        Returns:
            Dict[str, Any]: 統合分析結果
                - symbol: 分析対象シンボル
                - analysis_timestamp: 分析実行時刻
                - monthly_trend_analysis: 月次トレンド分析結果
                - swing_signal: スイングトレードシグナル
                - integrated_analysis: 統合分析スコア
                - risk_assessment: リスク評価
                - metadata: 分析メタデータ

        Raises:
            ValueError: 無効なシンボルまたはデータ不足
            Exception: 分析処理エラー

        Example:
            >>> service = MonthlySwingService()
            >>> result = await service.analyze_monthly_swing("AAPL")
            >>> assert result["symbol"] == "AAPL"
            >>> assert "swing_signal" in result
        """
        analysis_start_time = datetime.now(UTC)

        try:
            logger.info(f"月次スイング分析開始: {symbol}")

            # Step 1: 株価データ取得
            logger.info("Step 1: 株価データ取得")
            stock_data = await self._fetch_stock_data(symbol)

            # Step 2: 月次トレンド分析実行
            logger.info("Step 2: 月次トレンド分析実行")
            monthly_trend_result = await self._analyze_monthly_trend(symbol, stock_data)

            # Step 3: テクニカル信頼度計算
            logger.info("Step 3: テクニカル信頼度計算")
            technical_confidences = await self._calculate_technical_confidences(
                stock_data
            )

            # Step 4: スイングシグナル生成
            logger.info("Step 4: スイングシグナル生成")
            swing_signal = await self._generate_swing_signal(
                monthly_trend_result, technical_confidences
            )

            # Step 5: 統合分析結果構築
            logger.info("Step 5: 統合分析結果構築")
            integrated_result = await self._build_integrated_analysis(
                symbol=symbol,
                analysis_start_time=analysis_start_time,
                monthly_trend_result=monthly_trend_result,
                swing_signal=swing_signal,
                stock_data=stock_data,
                technical_confidences=technical_confidences,
            )

            analysis_end_time = datetime.now(UTC)
            processing_time = (analysis_end_time - analysis_start_time).total_seconds()

            logger.info(
                f"月次スイング分析完了: {symbol} - "
                f"シグナル: {swing_signal.signal_type.value}, "
                f"信頼度: {swing_signal.confidence:.3f}, "
                f"処理時間: {processing_time:.2f}秒"
            )

            return integrated_result

        except Exception as e:
            logger.error(f"月次スイング分析エラー: {symbol} - {e!s}")
            raise ValueError(f"月次スイング分析に失敗しました: {symbol}") from e

    @retry_on_error(max_retries=3, delay=1.0, backoff_factor=2.0)
    @handle_errors("株価データ取得")
    async def _fetch_stock_data(self, symbol: str) -> pd.DataFrame:
        """株価データ取得.

        yfinanceを使用して指定期間の株価データを取得し、
        分析に必要な前処理を実行する。
        
        自動リトライ機能付きで、ネットワークエラーやyfinanceエラーを
        適切にハンドリングする。

        Args:
            symbol: 株式シンボル

        Returns:
            pd.DataFrame: 前処理済み株価データ

        Raises:
            DataNotFoundError: 指定されたシンボルのデータが見つからない
            InsufficientDataError: 分析に必要なデータ量が不足
            DataValidationError: データの形式が不正
            YFinanceError: yfinanceライブラリエラー
        """
        start_time = time.time()
        
        # 3ヶ月分のデータを取得（月次分析に十分な期間）
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=120)  # 約4ヶ月

        try:
            # yfinanceでデータ取得
            ticker = yf.Ticker(symbol)
            stock_data = ticker.history(start=start_date, end=end_date, interval="1d")

            # データが空の場合
            if stock_data.empty:
                raise DataNotFoundError(
                    f"シンボル {symbol} のデータが見つかりません",
                    symbol=symbol,
                    source="yfinance",
                    context={
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    }
                )

            # データ前処理
            stock_data = stock_data.reset_index()
            stock_data.columns = [col.lower() for col in stock_data.columns]

            # データ検証
            required_columns = ["date", "open", "high", "low", "close", "volume"]
            validate_dataframe(
                stock_data,
                required_columns,
                min_rows=self.analysis_config.min_data_points,
                operation_name="株価データ取得"
            )

            # パフォーマンス指標をログ出力
            log_performance_metrics(
                "株価データ取得",
                start_time,
                data_points=len(stock_data),
                symbol=symbol,
                columns_count=len(stock_data.columns)
            )

            return stock_data

        except (DataNotFoundError, InsufficientDataError, DataValidationError):
            # 既にカスタム例外の場合はそのまま再発生
            raise
        except Exception as exc:
            # yfinance特有のエラーを分類
            if "ticker" in str(exc).lower() or "yahoo" in str(exc).lower():
                raise YFinanceError(
                    f"yfinanceからのデータ取得に失敗しました: {exc}",
                    symbol=symbol,
                    context={
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "original_error": str(exc)
                    }
                ) from exc
            else:
                # その他のエラーは一般的なデータ取得エラーとして処理
                raise DataNotFoundError(
                    f"データ取得中に予期しないエラーが発生しました: {exc}",
                    symbol=symbol,
                    source="yfinance",
                    context={"original_error": str(exc)}
                ) from exc

    async def _analyze_monthly_trend(
        self, symbol: str, stock_data: pd.DataFrame
    ) -> MonthlyTrendResult:
        """月次トレンド分析実行.

        Args:
            symbol: 株式シンボル
            stock_data: 株価データ

        Returns:
            MonthlyTrendResult: 月次トレンド分析結果
        """
        try:
            # MonthlyTrendAnalyzerを使用して分析実行
            trend_result = await self.trend_analyzer.analyze_trend(symbol, stock_data)

            logger.info(
                f"月次トレンド分析完了: {symbol} - "
                f"方向: {trend_result.trend_strength.direction.value}, "
                f"強度: {trend_result.trend_strength.strength:.3f}"
            )

            return trend_result

        except Exception as e:
            logger.error(f"月次トレンド分析エラー: {symbol} - {e!s}")
            raise ValueError(f"月次トレンド分析に失敗しました: {symbol}") from e

    async def _calculate_technical_confidences(
        self, stock_data: pd.DataFrame
    ) -> dict[str, Decimal]:
        """テクニカル分析信頼度計算.

        各種テクニカル指標から信頼度スコアを算出する。

        Args:
            stock_data: 株価データ

        Returns:
            Dict[str, Decimal]: 各分析手法の信頼度
                - technical: テクニカル指標信頼度
                - pattern: パターン分析信頼度
                - volume: 出来高分析信頼度
        """
        try:
            # 簡易的な信頼度計算（実際の実装では詳細な計算を行う）
            recent_data = stock_data.tail(20)  # 直近20日のデータ

            # テクニカル信頼度: ボラティリティベース
            price_changes = recent_data["close"].pct_change().dropna()
            volatility = price_changes.std()
            technical_confidence = max(
                Decimal("0.3"), min(Decimal("0.9"), Decimal(str(1.0 - volatility)))
            )

            # パターン信頼度: トレンド一貫性ベース
            trend_consistency = abs(recent_data["close"].corr(range(len(recent_data))))
            pattern_confidence = Decimal(str(max(0.4, min(0.95, trend_consistency))))

            # 出来高信頼度: 出来高変動ベース
            volume_changes = recent_data["volume"].pct_change().dropna()
            volume_stability = 1.0 - volume_changes.std()
            volume_confidence = Decimal(str(max(0.5, min(0.9, volume_stability))))

            confidences = {
                "technical": technical_confidence,
                "pattern": pattern_confidence,
                "volume": volume_confidence,
            }

            logger.info(f"テクニカル信頼度計算完了: {confidences}")
            return confidences

        except Exception as e:
            logger.error(f"テクニカル信頼度計算エラー: {e!s}")
            # フォールバック値を返す
            return {
                "technical": Decimal("0.6"),
                "pattern": Decimal("0.6"),
                "volume": Decimal("0.6"),
            }

    async def _generate_swing_signal(
        self,
        monthly_trend_result: MonthlyTrendResult,
        technical_confidences: dict[str, Decimal],
    ) -> SwingSignal:
        """スイングシグナル生成.

        Args:
            monthly_trend_result: 月次トレンド分析結果
            technical_confidences: テクニカル信頼度

        Returns:
            SwingSignal: 生成されたスイングシグナル
        """
        try:
            # 統合シグナル生成関数を呼び出し
            swing_signal = generate_complete_signal(
                monthly_trend_result=monthly_trend_result,
                technical_confidence=technical_confidences["technical"],
                pattern_confidence=technical_confidences["pattern"],
                volume_confidence=technical_confidences["volume"],
            )

            logger.info(f"スイングシグナル生成完了: {swing_signal.signal_type.value}")
            return swing_signal

        except Exception as e:
            logger.error(f"スイングシグナル生成エラー: {e!s}")
            raise ValueError("スイングシグナル生成に失敗しました") from e

    async def _build_integrated_analysis(
        self,
        symbol: str,
        analysis_start_time: datetime,
        monthly_trend_result: MonthlyTrendResult,
        swing_signal: SwingSignal,
        stock_data: pd.DataFrame,
        technical_confidences: dict[str, Decimal],
    ) -> dict[str, Any]:
        """統合分析結果構築.

        各分析結果を統合して最終的なレスポンス形式を構築する。

        Args:
            symbol: 株式シンボル
            analysis_start_time: 分析開始時刻
            monthly_trend_result: 月次トレンド分析結果
            swing_signal: スイングシグナル
            stock_data: 株価データ
            technical_confidences: テクニカル信頼度

        Returns:
            Dict[str, Any]: 統合分析結果
        """
        try:
            # 現在価格取得
            current_price = float(stock_data["close"].iloc[-1])

            # 統合分析スコア計算
            composite_score = float(swing_signal.confidence)

            # キーインサイト生成
            key_insights = [
                f"トレンド方向: {monthly_trend_result.trend_strength.direction.value}",
                f"トレンド強度: {monthly_trend_result.trend_strength.strength:.3f}",
                f"推奨アクション: {swing_signal.signal_type.value}",
                f"分析信頼度: {swing_signal.confidence:.3f}",
            ]

            # 根拠がある場合は追加
            if swing_signal.supporting_factors:
                key_insights.extend(
                    swing_signal.supporting_factors[:3]
                )  # 上位3つの根拠

            # リスク評価
            risk_level = (
                "低"
                if swing_signal.confidence > Decimal("0.8")
                else "中"
                if swing_signal.confidence > Decimal("0.6")
                else "高"
            )

            # 市場タイプ判定（日本株かUSか）
            market_type = "japanese" if ".T" in symbol else "us"

            # 統合結果構築
            integrated_result = {
                "symbol": symbol,
                "analysis_timestamp": analysis_start_time.isoformat(),
                "monthly_trend_analysis": {
                    "trend_direction": monthly_trend_result.trend_strength.direction.value,
                    "trend_strength": float(
                        monthly_trend_result.trend_strength.strength
                    ),
                    "continuation_probability": float(
                        monthly_trend_result.continuation_probability
                    ),
                    "support_resistance_levels": {
                        "support": [
                            {
                                "level": float(level.level),
                                "confidence": float(level.confidence),
                                "touch_count": level.touch_count,
                            }
                            for level in monthly_trend_result.support_resistance.get(
                                "support", []
                            )
                        ],
                        "resistance": [
                            {
                                "level": float(level.level),
                                "confidence": float(level.confidence),
                                "touch_count": level.touch_count,
                            }
                            for level in monthly_trend_result.support_resistance.get(
                                "resistance", []
                            )
                        ],
                    },
                },
                "swing_signal": {
                    "signal_type": swing_signal.signal_type.value,
                    "confidence": float(swing_signal.confidence),
                    "target_price": float(swing_signal.target_price)
                    if swing_signal.target_price
                    else None,
                    "stop_loss": float(swing_signal.stop_loss)
                    if swing_signal.stop_loss
                    else None,
                    "risk_reward_ratio": float(swing_signal.risk_reward_ratio)
                    if swing_signal.risk_reward_ratio
                    else None,
                    "supporting_factors": swing_signal.supporting_factors,
                    "generated_at": swing_signal.generated_at.isoformat(),
                },
                "integrated_analysis": {
                    "composite_score": composite_score,
                    "key_insights": key_insights,
                    "technical_breakdown": {
                        "technical_confidence": float(
                            technical_confidences["technical"]
                        ),
                        "pattern_confidence": float(technical_confidences["pattern"]),
                        "volume_confidence": float(technical_confidences["volume"]),
                    },
                },
                "risk_assessment": {
                    "risk_level": risk_level,
                    "volatility_assessment": "標準" if composite_score > 0.6 else "高",
                    "position_sizing_recommendation": "通常"
                    if risk_level == "低"
                    else "縮小",
                    "holding_period_estimate": "1-2ヶ月"
                    if swing_signal.signal_type in [SignalType.BUY, SignalType.SELL]
                    else "未定",
                },
                "metadata": {
                    "analysis_version": "1.0",
                    "market_type": market_type,
                    "data_points_used": len(stock_data),
                    "analysis_period": f"{stock_data['date'].iloc[0].strftime('%Y-%m-%d')} - {stock_data['date'].iloc[-1].strftime('%Y-%m-%d')}",
                    "current_price": current_price,
                    "data_quality": {
                        "sufficient_data": len(stock_data)
                        >= self.analysis_config.min_data_points,
                        "data_completeness": 1.0,  # 完全性スコア
                    },
                    "processing_info": {
                        "analysis_duration_seconds": (
                            datetime.now(UTC) - analysis_start_time
                        ).total_seconds(),
                        "analysis_timestamp": datetime.now(UTC).isoformat(),
                    },
                },
            }

            return integrated_result

        except Exception as e:
            logger.error(f"統合分析結果構築エラー: {e!s}")
            raise ValueError("統合分析結果の構築に失敗しました") from e


# 便利関数
async def fetch_stock_data(symbol: str) -> pd.DataFrame:
    """株価データ取得の便利関数.

    Args:
        symbol: 株式シンボル

    Returns:
        pd.DataFrame: 株価データ

    Note:
        テスト用やモック用に使用する簡易版関数
    """
    service = MonthlySwingService()
    return await service._fetch_stock_data(symbol)


async def analyze_monthly_swing_simple(symbol: str) -> dict[str, Any]:
    """月次スイング分析の便利関数.

    Args:
        symbol: 株式シンボル

    Returns:
        Dict[str, Any]: 分析結果

    Note:
        APIエンドポイントから直接呼び出す場合に使用
    """
    service = MonthlySwingService()
    return await service.analyze_monthly_swing(symbol)
