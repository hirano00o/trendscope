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

| 変数名                   | デフォルト値                                   | 説明                                    |
|-----------------------|------------------------------------------|---------------------------------------|
| `DISCORD_WEBHOOK_URL` | **必須**                                   | Discord Webhook URL（必須）               |
| `EXECUTION_MODE`      | `"once"`                                 | 実行モード（"once": 即座実行, "cron": スケジュール実行） |
| `BACKEND_API_URL`     | `http://localhost:8000`                  | TrendScope API URL                    |
| `CSV_PATH`            | `./screener_result.csv`                  | CSVファイルのパス                            |
| `CRON_SCHEDULE`       | `"0 10 * * 1-5"`                         | 実行スケジュール（cronモード時のみ使用）                |
| `MAX_WORKERS`         | `10`                                     | 並列分析数                                 |
| `TOP_STOCKS_COUNT`    | `15`                                     | 通知する上位銘柄数                             |

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

| シンボル | 企業名 | 信頼度 | スコア |
|---------|--------|--------|--------|
| 7203.T | [トヨタ自動車](https://kabutan.jp/stock/?code=7203) | 0.786 | 0.723 |
| 6758.T | [ソニー](https://kabutan.jp/stock/?code=6758) | 0.692 | 0.654 |
| ... | ... | ... | ... |
```

**通知の特徴:**
- マークダウン表形式で見やすく表示
- 企業名がKabutan株価ページへのリンクとして表示
- 信頼度とスコアは小数点第3位まで表示（より詳細な分析結果）
- TOP15銘柄を分析スコア順で通知

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

## 運用コマンド

### ログ確認

```bash
# 最新のジョブログを確認（Kubernetes）
kubectl logs -l job-name=trendscope-discord-bot -n trendscope --tail=50

# 特定のジョブのログを確認
kubectl get jobs -n trendscope
kubectl logs job/trendscope-discord-bot-28123456 -n trendscope

# Docker Compose
docker-compose logs -f discord-bot
```

### 手動実行

```bash
# CronJobから手動でジョブを作成（Kubernetes）
kubectl create job trendscope-discord-bot-manual \
  --from=cronjob/trendscope-discord-bot \
  -n trendscope

# 実行状況を確認
kubectl get jobs -n trendscope
kubectl logs job/trendscope-discord-bot-manual -n trendscope -f

# Docker Compose（即座に実行）
docker-compose run --rm discord-bot ./discord-bot
```

### 設定変更

```bash
# 並列数変更（Kubernetes）
kubectl patch configmap trendscope-discord-bot-config -n trendscope \
  --type merge -p '{"data":{"MAX_WORKERS":"15"}}'

# Webhook URL変更
kubectl create secret generic trendscope-discord-bot-secret \
  --from-literal=DISCORD_WEBHOOK_URL="NEW_WEBHOOK_URL" \
  --namespace=trendscope --dry-run=client -o yaml | kubectl apply -f -

# CSVファイル更新
kubectl create configmap trendscope-discord-bot-csv \
  --from-file=screener_result.csv \
  --namespace=trendscope \
  --dry-run=client -o yaml | kubectl apply -f -
```

## トラブルシューティング

### よくある問題

1. **Discord通知が送信されない**
   ```bash
   # Secret確認
   kubectl get secret trendscope-discord-bot-secret -n trendscope -o yaml
   
   # Webhook URLのテスト
   curl -X POST "$DISCORD_WEBHOOK_URL" \
     -H 'Content-Type: application/json' \
     -d '{"content": "Test message"}'
   ```

2. **CSVファイルが読み込めない**
   ```bash
   # ConfigMap確認
   kubectl describe configmap trendscope-discord-bot-csv -n trendscope
   
   # Pod内でのファイル確認
   kubectl exec -it job/trendscope-discord-bot-XXXXXX -n trendscope -- ls -la /data/
   ```

3. **バックエンドAPI接続エラー**
   ```bash
   # サービス確認
   kubectl get service trendscope-backend-service -n trendscope
   
   # ネットワーク接続テスト
   kubectl exec -it job/trendscope-discord-bot-XXXXXX -n trendscope -- \
     curl http://trendscope-backend-service:8000/health
   ```

4. **CronJobが実行されない**
   ```bash
   # CronJob設定確認
   kubectl describe cronjob trendscope-discord-bot -n trendscope
   
   # タイムゾーン確認
   kubectl get cronjob trendscope-discord-bot -n trendscope -o yaml | grep timeZone
   ```

5. **メモリ不足・リソース問題**
   ```bash
   # Discord Bot用リソース使用量確認
   kubectl top pods -n trendscope -l job-name=trendscope-discord-bot
   
   # リソース制限の調整
   # k8s/11-discord-bot-cronjob.yamlのresources設定を変更
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
