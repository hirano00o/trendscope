# 🚀 TrendScope 開発環境セットアップ

このガイドでは、TrendScopeアプリケーションの開発環境を設定する方法を説明します。

## 📋 前提条件

- **Node.js**: 18.x以降
- **Bun**: パッケージマネージャー（フロントエンド用）
- **Python**: 3.12以降
- **uv**: Pythonパッケージマネージャー（バックエンド用）

## 🔧 初回セットアップ

### 1. リポジトリのクローン
```bash
git clone <repository-url>
cd trendscope
```

### 2. フロントエンドのセットアップ
```bash
cd frontend
bun install
```

### 3. バックエンドのセットアップ
```bash
cd backend
uv sync
```

## 🚀 開発サーバーの起動

### オプション A: 手動で両方のサーバーを起動

**ターミナル1 - バックエンド起動:**
```bash
cd backend
./start-dev.sh
```

**ターミナル2 - フロントエンド起動:**
```bash
cd frontend
bun dev
```

### オプション B: Docker Composeを使用
```bash
docker-compose up
```

## 🌐 アクセスURL

- **フロントエンド**: http://localhost:3000
- **バックエンドAPI**: http://localhost:8000
- **API ドキュメント**: http://localhost:8000/docs
- **ヘルスチェック**: http://localhost:8000/health

## 🐛 トラブルシューティング

### "Something went wrong" エラーが表示される場合
1. バックエンドサーバーが起動していることを確認
2. `http://localhost:8000/health`にアクセスしてAPIが応答することを確認
3. ブラウザの開発者ツールでネットワークエラーを確認

### ポートが使用中の場合
```bash
# ポート8000を使用しているプロセスを確認
lsof -i :8000

# プロセスを終了
kill -9 <PID>
```

## 📝 開発コマンド

### フロントエンド
```bash
bun dev          # 開発サーバー起動
bun build        # プロダクションビルド
bun lint         # コードリンティング
bun format       # コードフォーマット
```

### バックエンド
```bash
uv run --frozen pytest          # テスト実行
uv run --frozen ruff format .   # コードフォーマット
uv run --frozen ruff check .    # リンティング
```

## 🔍 デバッグ情報

- フロントエンドは`http://localhost:3000`で実行
- バックエンドは`http://localhost:8000`で実行
- 環境変数は`.env.local`ファイルで設定
- API呼び出しは`NEXT_PUBLIC_API_URL`環境変数で制御