# 🚀 TrendScope 開発環境セットアップ

このガイドでは、TrendScopeアプリケーションの開発環境を設定する方法を説明します。

> 基本的なセットアップや使い方は [README.md](./README.md) をご覧ください。

## 📊 プロジェクトの現在の状況

**✅ 実装済み機能:**
- 包括的6カテゴリー分析システム
- 日本株・米国株対応のフロントエンド
- Rechartsベースのチャート機能
- 履歴データ取得API

**⚠️ 現在の課題:**
- テストカバレッジが9%と低い
- 一部のテストファイルに構文エラーあり
- ビジネスロジックのテストが不十分

## 🔧 開発環境の詳細設定

### プロジェクト構成
```
trendscope/
├── backend/          # Python FastAPI バックエンド
│   ├── src/              # ソースコード
│   ├── tests/            # テストコード
│   ├── pyproject.toml    # Python プロジェクト設定
│   └── start-dev.sh     # 開発サーバー起動スクリプト
├── frontend/         # Next.js フロントエンド
│   ├── src/              # ソースコード
│   ├── package.json      # Node.js プロジェクト設定
│   └── biome.json        # コードフォーマット設定
└── compose.yaml      # Docker Compose 設定
```

### インストール済みライブラリ
**バックエンド:**
- **コア**: yfinance, pandas, numpy, scikit-learn, fastapi, pydantic
- **テクニカル分析**: matplotlib, seaborn, statsmodels
- **開発ツール**: pytest, ruff, mypy, pytest-cov, pytest-asyncio

**フロントエンド:**
- **コア**: Next.js 14, React 19, TypeScript 5
- **UI**: Tailwind CSS, Radix UI, Recharts
- **状態管理**: TanStack Query
- **開発ツール**: Biome

## 🐛 トラブルシューティング

### テスト関連のエラー
#### テストが実行できない場合
```bash
# テストファイルの構文エラーを確認
cd backend
uv run --frozen ruff check tests/

# 特定のテストファイルを実行
uv run --frozen pytest tests/test_data_models.py -v
```

#### テストカバレッジが低い場合
```bash
# カバレッジレポートを生成
uv run --frozen pytest --cov=src --cov-report=html

# カバレッジレポートをブラウザで確認
open htmlcov/index.html
```

### デバッグテクニック
#### バックエンドのデバッグ
```bash
# 各モジュールのテスト実行
uv run --frozen pytest tests/test_data_models.py -v          # データモデル
uv run --frozen pytest tests/test_analysis_technical*.py -v # テクニカル分析
uv run --frozen pytest tests/test_analysis_patterns*.py -v  # パターン分析

# コンソールで直接テスト
uv run python -c "from src.trendscope_backend.data.stock_data import StockDataFetcher; print(StockDataFetcher().get_stock_data('AAPL'))"
```

#### フロントエンドのデバッグ
```bash
# タイプチェックとリントを同時実行
cd frontend
bun run type-check && bun lint

# コンポーネントのデバッグ
# ブラウザのコンソールで Network タブを確認
# React DevTools でコンポーネントの状態を確認
```

### ポート関連のエラー
```bash
# ポート使用状況の確認
lsof -i :8000  # バックエンド
lsof -i :3000  # フロントエンド

# プロセスを終了
kill -9 <PID>
```

## 📝 開発コマンド

### フロントエンド
```bash
cd frontend
bun dev          # 開発サーバー起動
bun build        # プロダクションビルド
bun lint         # コードリンティング
bun format       # コードフォーマット
bun run type-check  # TypeScript型チェック
```

### バックエンド
```bash
cd backend
./start-dev.sh                  # 開発サーバー起動

# コード品質コマンド
uv run --frozen ruff format .   # コードフォーマット
uv run --frozen ruff check .    # リンティング
uv run --frozen mypy .          # 型チェック

# テストコマンド（現在は構文エラーあり）
uv run --frozen pytest          # テスト実行
uv run --frozen pytest --cov=src --cov-report=html  # カバレッジレポート付き
uv run --frozen pytest -v       # 詳細出力付き

# 特定のテストファイルのみ実行
uv run --frozen pytest tests/test_data_models.py
```

### バッチ分析スクリプト
```bash
cd backend
# 複数の株式を一括で分析しCSV出力
uv run python scripts/batch_analysis.py
```

### Dockerを使用した起動
```bash
# プロジェクトルートで実行
docker-compose up          # フォアグラウンドで起動
docker-compose up -d       # バックグラウンドで起動
docker-compose down        # コンテナ停止
```

## 🚀 開発ワークフロー

### 通常の開発フロー
1. **サーバー起動**
   ```bash
   # ターミナル1: バックエンド
   cd backend && ./start-dev.sh
   
   # ターミナル2: フロントエンド
   cd frontend && bun dev
   ```

2. **コード品質チェック**
   ```bash
   # バックエンド
   cd backend
   uv run --frozen ruff format .
   uv run --frozen ruff check .
   uv run --frozen mypy .
   
   # フロントエンド
   cd frontend
   bun format
   bun lint
   bun run type-check
   ```

3. **機能テスト**
   - フロントエンドで株式コードを入力
   - 米国株例: `AAPL`, `GOOGL`, `MSFT`
   - 日本株例: `7203.T`, `6758.T`, `7267.T`

## 🔍 デバッグ情報

### テスト状況
- **全体カバレッジ**: 9% (1,833行中159行のみテスト済み)
- **モジュール別カバレッジ**:
  - データモデル: 68% (テスト済み)
  - パターン認識: 29% (部分的にテスト済み)
  - テクニカル指標: 0% (テスト未実装)
  - ボラティリティ分析: 0% (テスト未実装)
  - 機械学習予測: 0% (テスト未実装)

### 環境変数
- フロントエンド: `.env.local`ファイルで設定
- API呼び出し: `NEXT_PUBLIC_API_URL`環境変数で制御
- バックエンド: `pyproject.toml`で設定管理

### ログ確認
```bash
# バックエンドログ確認
cd backend
./start-dev.sh  # コンソールにログが表示されます

# フロントエンドログ確認
cd frontend
bun dev  # コンソールにログが表示されます

# ブラウザのコンソールでネットワークタブを確認
```

## 🔧 現在の課題と解決策

### 優先度高: テスト品質の向上
1. **構文エラーの修正**
   - `tests/test_data_models.py`の重複定義を修正
   - テストが実行できる状態にする

2. **テストカバレッジの向上**
   - テクニカル指標モジュールのテスト実装
   - ボラティリティ分析モジュールのテスト実装
   - 機械学習予測モジュールのテスト実装

3. **統合テストの実装**
   - エンドツーエンドテストの実装
   - APIエンドポイントの統合テスト

### 優先度中: 機能拡張
1. **フロントエンドテストの実装**
   - コンポーネントテスト
   - フックテスト

2. **パフォーマンス最適化**
   - キャッシュ機能の実装
   - レートリミットの実装

### 優先度低: 未来の機能
1. **リアルタイム機能**
   - WebSocket接続
   - ライブデータストリーミング

2. **高度なMLモデル**
   - ディープラーニングモデル
   - センチメント分析
   - ニュース統合

## 📈 パフォーマンス監視

### フロントエンド
```bash
# ビルドサイズ分析
cd frontend
bun run build
# Build analyzer で bundle size を確認

# Lighthouse監査
# Chrome DevTools の Lighthouse タブで実行
```

### バックエンド
```bash
# メモリ使用量監視
cd backend
uv run python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"

# API応答時間測定
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/api/v1/comprehensive/AAPL"
```

## 🎯 開発のベストプラクティス

### コードレビュー
- 新機能は必ずテストを含める
- コードフォーマットとリントを必ず実行
- 型チェックを通す
- 適切なコメントとドキュメントを追加

### Git ワークフロー
```bash
# 機能ブランチを作成
git checkout -b feature/new-feature

# 変更をコミット
git add .
git commit -m "Add new feature"

# テストとリントを実行
cd backend && uv run --frozen pytest && uv run --frozen ruff check .
cd frontend && bun run type-check && bun lint

# プッシュ前に最新のmainをマージ
git checkout main
git pull origin main
git checkout feature/new-feature
git merge main

# プッシュ
git push origin feature/new-feature
```

### セキュリティ
- APIキーは環境変数に格納
- 秘密情報をGitにコミットしない
- 依存関係の脆弱性を定期的にチェック

```bash
# Python依存関係の脆弱性チェック
cd backend
uv run pip-audit

# Node.js依存関係の脆弱性チェック
cd frontend
bun audit
```
