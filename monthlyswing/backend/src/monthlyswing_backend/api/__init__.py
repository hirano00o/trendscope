"""api: 月次スイングトレードAPI.

FastAPIを使用したRESTful APIエンドポイントを提供する。

エンドポイント:
- /health: ヘルスチェック
- /api/v1/monthly-analysis/{symbol}: 月次分析
- /api/v1/swing-signals/{symbol}: スイングシグナル
- /api/v1/risk-assessment/{symbol}: リスク評価
- /api/v1/performance/{symbol}: パフォーマンス追跡

セキュリティ機能:
- CORS設定
- レート制限
- JWT認証対応
- 監査ログ
"""

__all__ = [
    "main",
    "monthly_analysis",
]
