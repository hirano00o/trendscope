# TrendScope Discord Bot

TrendScope Discord Bot は、SBI証券のスクリーニング結果CSVから株式データを読み取り、TrendScopeバックエンドAPIで分析を行い、上昇トレンドの株式情報をDiscordに通知するアプリケーションです。

## 機能

- **CSV読み取り**: SBI証券スクリーニング結果（1,452銘柄）の読み取り
- **並列分析**: 省メモリWorker Pool による効率的な並列処理
- **TrendScope API連携**: 6カテゴリー包括分析の取得
- **Discord通知**: 上位15銘柄の分析結果をリッチフォーマットで通知
- **スケジュール実行**: 平日朝10時の定時実行（Cron対応）

## アーキテクチャ

```
discord-bot/
├── cmd/discord-bot/main.go     # メインアプリケーション
├── pkg/
│   ├── csv/reader.go           # CSV読み取り
│   ├── api/client.go           # バックエンドAPI連携
│   ├── discord/webhook.go      # Discord通知
│   └── scheduler/cron.go       # Cronスケジューラー
├── internal/worker/pool.go     # Worker Pool（並列処理）
├── configs/config.go           # 設定管理
└── Dockerfile                  # Dockerイメージ
```

## 設定

### 環境変数

| 変数名                   | デフォルト値                  | 説明                  |
|-----------------------|-------------------------|---------------------|
| `DISCORD_WEBHOOK_URL` | **必須**                  | Discord Webhook URL |
| `BACKEND_API_URL`     | `http://localhost:8000` | TrendScopeバックエンドAPI |
| `CSV_PATH`            | `./screener_result.csv` | CSVファイルパス           |
| `CRON_SCHEDULE`       | `"0 10 * * 1-5"`        | 実行スケジュール（平日10時）     |
| `MAX_WORKERS`         | `10`                    | 並列処理ワーカー数           |
| `TOP_STOCKS_COUNT`    | `15`                    | 通知する上位銘柄数           |

## 実行方法

### 1. Docker Compose での実行

```bash
# Discord Webhook URLを環境変数に設定
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"

# サービス起動
docker-compose up -d discord-bot

# ログ確認
docker-compose logs -f discord-bot
```

### 2. Kubernetes での実行

```bash
# 1. Secret作成（Discord Webhook URL）
kubectl create secret generic trendscope-discord-bot-secret \
  --from-literal=DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL" \
  --namespace=trendscope

# 2. CSV データをConfigMapに追加
kubectl create configmap trendscope-discord-bot-csv \
  --from-file=screener_result.csv \
  --namespace=trendscope

# 3. マニフェスト適用
kubectl apply -f k8s/09-discord-bot-configmap.yaml
kubectl apply -f k8s/10-discord-bot-secret.yaml  # 既に作成済みの場合はスキップ
kubectl apply -f k8s/11-discord-bot-cronjob.yaml

# 4. CronJob状態確認
kubectl get cronjobs -n trendscope
kubectl describe cronjob trendscope-discord-bot -n trendscope
```

### 3. ローカル開発での実行

```bash
cd discord-bot

# 依存関係のインストール
go mod tidy

# 環境変数設定
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"
export BACKEND_API_URL="http://localhost:8000"
export CSV_PATH="../screener_result.csv"

# アプリケーション実行
go run ./cmd/discord-bot/
```

## 通知フォーマット

Discord通知は以下のフォーマットで送信されます：

```
📈 **本日の上昇トレンド株 TOP15**

シンボル,企業名,信頼度,スコア,URL
7203.T,トヨタ自動車,0.8,0.7,https://kabutan.jp/stock/?code=7203
6758.T,ソニー,0.7,0.6,https://kabutan.jp/stock/?code=6758
...
```

## 動作確認

### テスト実行

```bash
# 即座に分析を実行（スケジュール待機なし）
docker-compose run --rm discord-bot ./discord-bot
```

### ログ確認

```bash
# Docker Compose
docker-compose logs -f discord-bot

# Kubernetes
kubectl logs -f cronjob/trendscope-discord-bot -n trendscope
```

## トラブルシューティング

### よくある問題

1. **Discord通知が送信されない**
   - `DISCORD_WEBHOOK_URL` が正しく設定されているか確認
   - Discord Webhook URLの形式: `https://discord.com/api/webhooks/ID/TOKEN`

2. **CSV読み取りエラー**
   - ファイルパス `CSV_PATH` が正しいか確認
   - Kubernetesの場合、ConfigMapが正しく作成されているか確認

3. **API接続エラー**
   - `BACKEND_API_URL` が正しく設定されているか確認
   - バックエンドサービスが起動しているか確認

4. **メモリ不足**
   - `MAX_WORKERS` を小さい値（5-10）に調整
   - Docker/Kubernetesのメモリ制限を確認

### ログの確認方法

```bash
# Kubernetesでの詳細ログ
kubectl get jobs -n trendscope
kubectl logs job/trendscope-discord-bot-XXXXXX -n trendscope

# CronJobの履歴確認
kubectl get jobs -n trendscope --selector=job-name=trendscope-discord-bot
```

## 開発者向け情報

### ビルド

```bash
# ローカルビルド
cd discord-bot
go build -o discord-bot ./cmd/discord-bot/

# Dockerビルド
docker build -t trendscope-discord-bot .
```

### テスト

```bash
# 単体テスト
go test ./...

# カバレッジ
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

## ライセンス

このプロジェクトはTrendScopeプロジェクトの一部です。
