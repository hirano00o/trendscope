# 月次スイングトレード分析システム

月次スイングトレード戦略に特化した金融分析APIシステム。
CLAUDEスタック（Python 3.12 + FastAPI + uv + ruff）を使用した高性能・高セキュリティの金融アプリケーション。

## 主要機能

- **月次価格動向分析**: トレンド強度と方向性の評価
- **スイングトレード指標**: 高値・安値検出とボラティリティ調整
- **エントリー/エグジットシグナル**: 売買タイミングの判定
- **リスク管理**: ポジションサイズとドローダウン予測
- **パフォーマンス追跡**: 取引履歴と勝率分析

## 技術仕様

- **バックエンド**: FastAPI + Python 3.12 + 非同期処理
- **パッケージ管理**: uv (10-100倍高速)
- **コード品質**: ruff (100-200倍高速)
- **テストフレームワーク**: pytest + coverage
- **セキュリティ**: JWT認証、監査ログ、CORS設定

## セットアップ

```bash
# 依存関係のインストール
uv sync

# 開発サーバー起動
uv run python main.py

# テスト実行
uv run pytest

# コード品質チェック
uv run ruff check --fix .
uv run ruff format .
```

## API エンドポイント

- `GET /health` - ヘルスチェック
- `POST /api/v1/monthly-analysis/{symbol}` - 月次分析
- `GET /docs` - API ドキュメント

## 開発ガイドライン

- TDD（テスト駆動開発）の厳格な適用
- Decimal型使用による金融計算精度保持
- 包括的ドキュメンテーション（Google形式docstring）
- 型安全性（TypeHint 100%適用）

## ライセンス

MIT License