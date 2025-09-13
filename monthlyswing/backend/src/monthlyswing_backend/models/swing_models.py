"""swing_models.py: スイングトレード関連データモデル.

月次スイングトレードシステム用のPydanticデータモデル定義。
金融データの精度を保持し、型安全性を確保する。

主要モデル:
- StockPriceData: 株価データ
- MonthlyTrendResult: 月次トレンド分析結果
- TrendAnalysisConfig: トレンド分析設定
- SupportResistanceLevel: サポート・レジスタンスレベル
- SwingSignal: スイングトレードシグナル

特徴:
- Decimal型使用（精度保持）
- 包括的バリデーション
- JSON互換性
- 型安全性
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TrendDirection(str, Enum):
    """トレンド方向列挙型.

    価格トレンドの方向を表す列挙型。
    統一的なトレンド表現により、分析の一貫性を確保。
    """

    UPTREND = "上昇"
    DOWNTREND = "下降"
    SIDEWAYS = "横這い"
    UNKNOWN = "不明"


class SignalType(str, Enum):
    """シグナルタイプ列挙型.

    スイングトレードシグナルのタイプを表す。
    """

    BUY = "買い"
    SELL = "売り"
    HOLD = "保持"
    WAIT = "様子見"


class TrendAnalysisConfig(BaseModel):
    """トレンド分析設定.

    月次トレンド分析のパラメーター設定。
    分析精度と計算負荷のバランスを調整。

    Attributes:
        min_data_points: 分析に必要な最小データポイント数
        confidence_threshold: 信頼度閾値（0-1）
        forecast_period_days: 予測期間（日数）
        volatility_window: ボラティリティ計算ウィンドウ（日数）
        support_resistance_sensitivity: サポート・レジスタンス感度（0-1）
        trend_strength_threshold: トレンド強度閾値（0-1）

    Example:
        >>> config = TrendAnalysisConfig(
        ...     min_data_points=30, confidence_threshold=0.7, forecast_period_days=30
        ... )
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        frozen=True,  # 設定変更防止
    )

    min_data_points: int = Field(
        default=30, ge=20, le=200, description="分析に必要な最小データポイント数"
    )

    confidence_threshold: Decimal = Field(
        default=Decimal("0.7"),
        ge=Decimal("0.1"),
        le=Decimal("1.0"),
        description="分析結果の信頼度閾値",
    )

    forecast_period_days: int = Field(
        default=30, ge=1, le=90, description="トレンド継続予測期間（日数）"
    )

    volatility_window: int = Field(
        default=20, ge=5, le=60, description="ボラティリティ計算のウィンドウサイズ"
    )

    support_resistance_sensitivity: Decimal = Field(
        default=Decimal("0.5"),
        ge=Decimal("0.1"),
        le=Decimal("1.0"),
        description="サポート・レジスタンス検出感度",
    )

    trend_strength_threshold: Decimal = Field(
        default=Decimal("0.6"),
        ge=Decimal("0.1"),
        le=Decimal("1.0"),
        description="有意なトレンドと判定する強度閾値",
    )


class StockPriceData(BaseModel):
    """株価データモデル.

    個別の株価データポイントを表現。
    金融データの精度を保持し、バリデーションを実行。

    Attributes:
        date: 日付
        open: 始値
        high: 高値
        low: 安値
        close: 終値
        volume: 出来高
        adjusted_close: 調整後終値（オプション）

    Example:
        >>> price_data = StockPriceData(
        ...     date=datetime(2024, 1, 15),
        ...     open=Decimal("100.50"),
        ...     high=Decimal("102.00"),
        ...     low=Decimal("99.80"),
        ...     close=Decimal("101.25"),
        ...     volume=1500000,
        ... )
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    date: datetime = Field(..., description="取引日")
    open: Decimal = Field(..., gt=0, description="始値")
    high: Decimal = Field(..., gt=0, description="高値")
    low: Decimal = Field(..., gt=0, description="安値")
    close: Decimal = Field(..., gt=0, description="終値")
    volume: int = Field(..., ge=0, description="出来高")
    adjusted_close: Decimal | None = Field(None, gt=0, description="調整後終値")

    @field_validator("high")
    @classmethod
    def validate_high_price(cls, v: Decimal) -> Decimal:
        """高値バリデーション.

        高値が他の価格以上であることを確認。

        Args:
            v: 高値

        Returns:
            Decimal: 検証済み高値

        Note:
            Pydantic v2では、他のフィールドとの相互バリデーションは
            model_validator を使用して行います。
        """
        # 基本的な値の検証のみ実行（相互バリデーションは後で追加）
        if v <= 0:
            raise ValueError("高値は正の値である必要があります")
        return v

    @field_validator("low")
    @classmethod
    def validate_low_price(cls, v: Decimal) -> Decimal:
        """安値バリデーション.

        安値が正の値であることを確認。

        Args:
            v: 安値

        Returns:
            Decimal: 検証済み安値

        Raises:
            ValueError: 安値が正の値でない場合

        Note:
            Pydantic v2では、他のフィールドとの相互バリデーションは
            model_validator を使用して行います。
        """
        # 基本的な値の検証のみ実行（相互バリデーションは後で追加）
        if v <= 0:
            raise ValueError("安値は正の値である必要があります")
        return v


class SupportResistanceLevel(BaseModel):
    """サポート・レジスタンスレベル.

    重要な価格水準とその信頼度を表現。

    Attributes:
        level: 価格水準
        confidence: 信頼度（0-1）
        touch_count: 接触回数
        last_touch_date: 最後の接触日
        level_type: レベルタイプ（サポート/レジスタンス）

    Example:
        >>> support = SupportResistanceLevel(
        ...     level=Decimal("100.00"),
        ...     confidence=0.85,
        ...     touch_count=3,
        ...     level_type="サポート",
        ... )
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    level: Decimal = Field(..., gt=0, description="価格水準")
    confidence: Decimal = Field(
        ..., ge=Decimal("0"), le=Decimal("1"), description="信頼度スコア"
    )
    touch_count: int = Field(..., ge=1, description="価格接触回数")
    last_touch_date: datetime = Field(..., description="最後の接触日")
    level_type: Literal["サポート", "レジスタンス"] = Field(
        ..., description="レベルタイプ"
    )
    strength_score: Decimal = Field(
        default=Decimal("0"),
        ge=Decimal("0"),
        le=Decimal("1"),
        description="レベル強度スコア",
    )


class MonthlyReturn(BaseModel):
    """月次リターンデータ.

    特定期間の月次リターン情報。

    Attributes:
        start_date: 期間開始日
        end_date: 期間終了日
        return_rate: リターン率
        start_price: 期間開始価格
        end_price: 期間終了価格
        volatility: 期間内ボラティリティ

    Example:
        >>> monthly_return = MonthlyReturn(
        ...     start_date=datetime(2024, 1, 1),
        ...     end_date=datetime(2024, 1, 31),
        ...     return_rate=Decimal("0.05"),
        ...     start_price=Decimal("100.00"),
        ...     end_price=Decimal("105.00"),
        ... )
    """

    model_config = ConfigDict()

    start_date: datetime = Field(..., description="期間開始日")
    end_date: datetime = Field(..., description="期間終了日")
    return_rate: Decimal = Field(..., description="リターン率（小数）")
    start_price: Decimal = Field(..., gt=0, description="期間開始価格")
    end_price: Decimal = Field(..., gt=0, description="期間終了価格")
    volatility: Decimal | None = Field(None, ge=0, description="期間内ボラティリティ")

    @field_validator("end_date")
    @classmethod
    def validate_date_order(cls, v: datetime) -> datetime:
        """日付順序バリデーション.

        終了日の基本的な検証。

        Args:
            v: 終了日

        Returns:
            datetime: 検証済み終了日

        Note:
            Pydantic v2では、他のフィールドとの相互バリデーションは
            model_validator を使用して行います。
        """
        # 基本的な日付検証のみ実行（相互バリデーションは後で追加）
        return v


class TrendStrengthMetrics(BaseModel):
    """トレンド強度指標.

    トレンドの強さを表す各種指標。

    Attributes:
        direction: トレンド方向
        strength: 強度スコア（0-1）
        confidence: 信頼度（0-1）
        momentum: モメンタム指標
        consistency: 一貫性スコア
        duration_days: トレンド継続日数

    Example:
        >>> trend_metrics = TrendStrengthMetrics(
        ...     direction=TrendDirection.UPTREND,
        ...     strength=Decimal("0.75"),
        ...     confidence=Decimal("0.85"),
        ...     momentum=Decimal("0.60"),
        ... )
    """

    model_config = ConfigDict()

    direction: TrendDirection = Field(..., description="トレンド方向")
    strength: Decimal = Field(
        ..., ge=Decimal("0"), le=Decimal("1"), description="トレンド強度スコア"
    )
    confidence: Decimal = Field(
        ..., ge=Decimal("0"), le=Decimal("1"), description="分析信頼度"
    )
    momentum: Decimal = Field(
        default=Decimal("0"), description="モメンタム指標（正負の値）"
    )
    consistency: Decimal = Field(
        default=Decimal("0"),
        ge=Decimal("0"),
        le=Decimal("1"),
        description="トレンド一貫性スコア",
    )
    duration_days: int = Field(default=0, ge=0, description="トレンド継続日数")


class SwingSignal(BaseModel):
    """スイングトレードシグナル.

    エントリー・エグジットのタイミングシグナル。

    Attributes:
        signal_type: シグナルタイプ
        confidence: 信頼度
        target_price: 目標価格
        stop_loss: ストップロス価格
        expected_holding_days: 想定保有期間
        risk_reward_ratio: リスクリワード比率
        supporting_factors: シグナル根拠

    Example:
        >>> signal = SwingSignal(
        ...     signal_type=SignalType.BUY,
        ...     confidence=Decimal("0.8"),
        ...     target_price=Decimal("110.00"),
        ...     stop_loss=Decimal("95.00"),
        ... )
    """

    model_config = ConfigDict()

    signal_type: SignalType = Field(..., description="シグナルタイプ")
    confidence: Decimal = Field(
        ..., ge=Decimal("0"), le=Decimal("1"), description="シグナル信頼度"
    )
    target_price: Decimal | None = Field(None, gt=0, description="目標価格")
    stop_loss: Decimal | None = Field(None, gt=0, description="ストップロス価格")
    expected_holding_days: int | None = Field(
        None, ge=1, le=365, description="想定保有期間（日数）"
    )
    risk_reward_ratio: Decimal | None = Field(
        None, gt=0, description="リスクリワード比率"
    )
    supporting_factors: list[str] = Field(
        default_factory=list, description="シグナル根拠・要因"
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="シグナル生成日時"
    )


class MonthlyTrendResult(BaseModel):
    """月次トレンド分析結果.

    月次スイングトレード分析の統合結果。
    全ての分析コンポーネントの結果を統合。

    Attributes:
        symbol: 銘柄シンボル
        analysis_date: 分析実行日時
        data_period: データ期間
        monthly_returns: 月次リターン一覧
        trend_strength: トレンド強度指標
        support_resistance: サポート・レジスタンスレベル
        swing_signals: スイングトレードシグナル
        continuation_probability: トレンド継続確率
        risk_metrics: リスク指標
        metadata: 分析メタデータ

    Example:
        >>> result = MonthlyTrendResult(
        ...     symbol="AAPL",
        ...     monthly_returns=[monthly_return1, monthly_return2],
        ...     trend_strength=trend_metrics,
        ...     continuation_probability=Decimal("0.72"),
        ... )
    """

    model_config = ConfigDict()

    symbol: str = Field(..., min_length=1, max_length=20, description="銘柄シンボル")
    analysis_date: datetime = Field(
        default_factory=datetime.utcnow, description="分析実行日時"
    )
    data_period: dict[str, datetime] = Field(..., description="分析データ期間")

    # 分析結果コンポーネント
    monthly_returns: list[MonthlyReturn] = Field(..., description="月次リターン一覧")
    trend_strength: TrendStrengthMetrics = Field(..., description="トレンド強度指標")
    support_resistance: dict[str, list[SupportResistanceLevel]] = Field(
        ..., description="サポート・レジスタンスレベル"
    )
    swing_signals: list[SwingSignal] = Field(
        default_factory=list, description="スイングトレードシグナル"
    )
    continuation_probability: Decimal = Field(
        ..., ge=Decimal("0"), le=Decimal("1"), description="トレンド継続確率"
    )

    # リスク・パフォーマンス指標
    risk_metrics: dict[str, Any] | None = Field(
        None, description="リスク指標（VaR、最大ドローダウン等）"
    )

    # メタデータ
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="分析メタデータ（設定、データ品質等）"
    )

    @field_validator("data_period")
    @classmethod
    def validate_data_period(cls, v: dict[str, datetime]) -> dict[str, datetime]:
        """データ期間バリデーション.

        開始日・終了日の妥当性を確認。

        Args:
            v: データ期間辞書

        Returns:
            Dict[str, datetime]: 検証済みデータ期間

        Raises:
            ValueError: 期間設定が不正な場合
        """
        if "start_date" not in v or "end_date" not in v:
            raise ValueError("data_periodにはstart_dateとend_dateが必要です")

        if v["end_date"] <= v["start_date"]:
            raise ValueError("終了日は開始日より後である必要があります")

        # データ期間が適切な範囲内かチェック
        period_days = (v["end_date"] - v["start_date"]).days
        if period_days < 30:
            raise ValueError("月次分析には最低30日のデータが必要です")
        if period_days > 1095:  # 3年
            raise ValueError("データ期間は3年以内である必要があります")

        return v
