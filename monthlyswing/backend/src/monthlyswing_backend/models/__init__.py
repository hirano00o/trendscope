"""models: データモデル定義.

Pydanticを使用したデータ構造とバリデーション機能を提供する。
金融データの精度を保持し、型安全性を確保する。

モデル:
- swing_models: スイングトレード関連のデータモデル
- MonthlyTrendData: 月次トレンドデータ
- SwingSignal: エントリー/エグジットシグナル
- RiskMetrics: リスク指標
- PerformanceData: パフォーマンスデータ

特徴:
- Decimal型使用（float使用禁止）
- 包括的な入力検証
- JSON互換性
"""

__all__ = [
    "swing_models",
]
