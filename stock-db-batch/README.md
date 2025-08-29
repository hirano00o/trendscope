# TrendScope 株式データベースバッチアプリケーション

TrendScopeの日本株データベースを更新する高性能バッチ処理アプリケーションです。CSV形式の株式リストから企業情報を読み取り、yfinanceを使用して株価データを取得し、Google翻訳でビジネス要約を日本語化してSQLiteデータベースに効率的に格納します。

## 主な機能

### 🚀 高性能データ処理
- **効率的差分処理**: 既存データとの差分のみ更新
- **並列処理対応**: 大量データを高速処理
- **メモリ最適化**: チャンク分割による省メモリ実行
- **リトライ機能**: ネットワークエラーに対する自動リトライ

### 🔄 包括的データフロー
1. **CSV読み取り**: マルチエンコーディング対応（UTF-8, Shift_JIS）
2. **株価データ取得**: yfinanceによる日本株データ取得（XXXX.T形式）
3. **翻訳処理**: Google翻訳による英日翻訳
4. **差分検出**: 価格・要約変更の効率的検出
5. **データベース更新**: SQLiteへの一括更新処理

### ☸️ Kubernetes完全対応
- **CronJob**: 平日17時の定期実行
- **環境変数設定**: 設定の外部化
- **永続化ストレージ**: NFS対応のデータ永続化
- **Graceful Shutdown**: 安全な処理中断対応
- **セキュリティ対応**: readOnlyRootFilesystem、非root実行

### 📊 運用機能
- **進捗報告**: リアルタイム処理状況表示
- **詳細ログ**: 構造化ログによる追跡可能性
- **統計情報**: パフォーマンス指標の収集
- **ドライランモード**: 安全な動作確認

## プロジェクト構成

```
trendscope/stock-db-batch/
├── src/stock_batch/           # メインソースコード
│   ├── models/                # データモデル（Pydantic）
│   │   └── company.py         # 企業データモデル
│   ├── database/              # データベース関連
│   │   ├── connection.py      # SQLite接続管理
│   │   └── migration.py       # スキーママイグレーション
│   ├── services/              # ビジネスロジック
│   │   ├── csv_reader.py      # CSV読み取りサービス
│   │   ├── stock_fetcher.py   # 株価取得サービス
│   │   ├── translation.py     # 翻訳サービス
│   │   ├── database_service.py # CRUD操作サービス
│   │   └── differential_processor.py # 効率的差分処理
│   └── main_batch_application.py # メインアプリケーション
├── tests/                     # テストコード
├── k8s/                       # Kubernetesマニフェスト
├── main.py                    # エントリーポイント
├── pyproject.toml             # プロジェクト設定
└── Dockerfile                 # コンテナ設定
```

## セットアップ

### 前提条件

- Python 3.12+
- uv (高速Pythonパッケージマネージャー)
- Kubernetes クラスター（本番運用時）
- NFS PersistentVolume（データ永続化用）

### ローカル開発環境

```bash
# リポジトリクローン
git clone <repository-url>
cd trendscope/stock-db-batch

# 依存関係インストール
uv sync

# テスト実行
uv run pytest

# コード品質チェック
uv run ruff check .
uv run ruff format .
```

### サンプルCSVファイル準備

以下の形式でCSVファイルを準備してください：

```csv
コード,銘柄名,市場,現在値,前日比(%)
1332,ニッスイ,東P,877.8,+2.5
1418,インターライフ,東S,405.0,-1.2
7203,トヨタ自動車,東P,2150.0,+1.1
```

### ローカル実行

```bash
# 基本実行
export BATCH_DATABASE_PATH="./stocks.db"
export BATCH_CSV_PATH="./sample_stocks.csv"
export BATCH_LOG_LEVEL="INFO"

uv run python -m stock_batch.main

# ドライランモード
export BATCH_DRY_RUN="true"
uv run python -m stock_batch.main
```

## Kubernetes デプロイ

### 1. 設定のカスタマイズ

`k8s/configmap.yaml`を編集して環境に合わせて設定を調整：

```yaml
data:
  BATCH_CHUNK_SIZE: "1000"          # チャンクサイズ
  BATCH_ENABLE_PARALLEL: "true"     # 並列処理有効化
  BATCH_MAX_WORKERS: "4"            # 並列数
  BATCH_LOG_LEVEL: "INFO"           # ログレベル
```

### 2. デプロイ実行

```bash
# デプロイ実行
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/cronjob.yaml
```

### 3. 動作確認

```bash
# CronJobの確認
kubectl get cronjob -n trendscope-stock-batch

# 手動実行テスト
kubectl create job --from=cronjob/trendscope-stock-batch-job manual-test -n trendscope-stock-batch

# ログ確認
kubectl logs -f job/manual-test -n trendscope-stock-batch

# PVC確認
kubectl get pvc -n trendscope-stock-batch
```

## 設定項目

### 環境変数

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `BATCH_DATABASE_PATH` | `/data/stocks.db` | SQLiteデータベースファイルパス |
| `BATCH_CSV_PATH` | `/data/stocks.csv` | CSVファイルパス |
| `BATCH_CHUNK_SIZE` | `1000` | チャンク処理サイズ |
| `BATCH_ENABLE_PARALLEL` | `false` | 並列処理有効化 |
| `BATCH_MAX_WORKERS` | `4` | 最大ワーカー数 |
| `BATCH_ENABLE_STOCK_FETCH` | `true` | 株価データ取得有効化 |
| `BATCH_ENABLE_TRANSLATION` | `true` | 翻訳機能有効化 |
| `BATCH_MAX_RETRIES` | `3` | 最大リトライ回数 |
| `BATCH_CONTINUE_ON_ERROR` | `true` | エラー時継続処理 |
| `BATCH_DRY_RUN` | `false` | ドライランモード |
| `BATCH_LOG_LEVEL` | `INFO` | ログレベル |

### データベーススキーマ

```sql
CREATE TABLE company (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    market TEXT,
    business_summary TEXT,
    price REAL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 監視とトラブルシューティング

### ログ監視

```bash
# CronJob実行ログ
kubectl logs -f cronjob/trendscope-stock-batch-job -n trendscope-stock-batch

# 特定Jobのログ
kubectl logs -f job/<job-name> -n trendscope-stock-batch

# 全体的な状況確認
kubectl get events -n trendscope-stock-batch --sort-by='.lastTimestamp'
```

### パフォーマンス監視

基本的な監視はKubernetesの標準機能で対応：

```bash
# リソース使用量確認
kubectl top pods -n trendscope-stock-batch

# CronJob実行履歴
kubectl get jobs -n trendscope-stock-batch

# イベント監視
kubectl get events -n trendscope-stock-batch --sort-by='.lastTimestamp'
```

### よくある問題と解決策

#### 1. CSV読み取りエラー

```bash
# エンコーディング問題
ERROR: CSV読み取りエラー - UnicodeDecodeError

# 解決策: CSVファイルのエンコーディングを確認
file -I /data/stocks.csv
iconv -f shift_jis -t utf-8 input.csv > output.csv
```

#### 2. 株価取得エラー

```bash
# ネットワークエラー
WARNING: 株価データ取得エラー: 1332.T - HTTPSConnectionPool

# 解決策: リトライ設定調整
export BATCH_MAX_RETRIES="5"
```

#### 3. データベースロック

```bash
# SQLiteロックエラー
ERROR: database is locked

# 解決策: 並列処理無効化
export BATCH_ENABLE_PARALLEL="false"
```

#### 4. メモリ不足

```bash
# メモリ不足エラー
ERROR: MemoryError

# 解決策: チャンクサイズ削減
export BATCH_CHUNK_SIZE="500"
```

## 開発

### テスト駆動開発（TDD）

本プロジェクトはTDDで開発されており、包括的なテストスイートがあります：

```bash
# 全テスト実行
uv run pytest

# 特定モジュールのテスト
uv run pytest tests/test_services_stock_fetcher.py

# カバレッジレポート
uv run pytest --cov=src --cov-report=html
```

### コード品質

```bash
# リント
uv run ruff check .

# フォーマット
uv run ruff format .

# 型チェック
uv run mypy .
```

### 新機能追加の流れ

1. **テストファースト**: 失敗するテストを作成
2. **実装**: テストを通す最小限の実装
3. **リファクタリング**: コード品質向上
4. **ドキュメント更新**: README、コメント更新

## ライセンス

このプロジェクトはTrendScopeプラットフォームの一部として開発されています。

## 貢献

1. フィーチャーブランチを作成
2. 変更を実装（TDDを遵守）
3. テストが全て通ることを確認
4. プルリクエストを作成

## サポート

問題や質問がある場合は、以下の情報と共にIssueを作成してください：

- 実行環境（Kubernetes/ローカル）
- エラーログ
- 設定内容（機密情報は除く）
- 実行手順

---

**TrendScope株式データベースバッチアプリケーション v1.0.0**  
高性能・高信頼性の日本株データ処理システム
