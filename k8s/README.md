# TrendScope Kubernetes デプロイメントガイド

このディレクトリには、TrendScopeアプリケーションをKubernetes環境にデプロイするためのマニフェストが含まれています。

## 📁 ディレクトリ構造

```
k8s/
├── README.md                               # このファイル
├── 01-namespace.yaml                       # Namespace定義
├── 02-configmap.yaml                       # ConfigMapとSecret定義
├── 03-backend-deployment.yaml              # Backend Deployment
├── 04-frontend-deployment.yaml             # Frontend Deployment
├── 05-backend-service.yaml                # Backend Service
├── 06-frontend-service.yaml               # Frontend Service
├── 07-cilium-l2-announcement.yaml         # Cilium L2 Announcement Policy
├── 08-cilium-loadbalancer-ippool.yaml     # Cilium LoadBalancer IP Pool
├── 09-discord-bot-configmap.yaml          # Discord Bot ConfigMap (設定のみ)
└── 10-discord-bot-cronjob.yaml            # Discord Bot CronJob
```

## 🚀 デプロイメント手順

### 前提条件

1. **Kubernetesクラスタ**が利用可能であること
2. **kubectl**がインストールされ、クラスタに接続されていること
3. **Cilium CNI**がインストールされ、L2 Announcementが有効であること

### 1. Cilium L2 Announcement 有効化

Ciliumで L2 Announcement が有効になっていることを確認してください：

```bash
# Cilium設定の確認
kubectl get configmap cilium-config -n kube-system -o yaml | grep l2-announcements

# L2 Announcementが無効の場合、有効化
kubectl patch configmap cilium-config -n kube-system --patch '{"data":{"enable-l2-announcements":"true"}}'

# Cilium ポッドの再起動
kubectl rollout restart daemonset/cilium -n kube-system
```

### 2. IPプール設定の調整

`08-cilium-loadbalancer-ippool.yaml` でIPアドレス範囲を実際のネットワーク環境に合わせて調整してください：

```yaml
spec:
  blocks:
    - cidr: "192.168.1.100/32"  # 実際のIPアドレスに変更
```

### 3. アプリケーションのデプロイ

```bash
# TrendScopeアプリケーション（Backend/Frontend）の一括適用
kubectl apply -f k8s/01-namespace.yaml
kubectl apply -f k8s/02-configmap.yaml
kubectl apply -f k8s/03-backend-deployment.yaml
kubectl apply -f k8s/04-frontend-deployment.yaml
kubectl apply -f k8s/05-backend-service.yaml
kubectl apply -f k8s/06-frontend-service.yaml
kubectl apply -f k8s/07-cilium-l2-announcement.yaml
kubectl apply -f k8s/08-cilium-loadbalancer-ippool.yaml

# Discord Bot は手動設定が必要なため、個別に実行
# 詳細は後述の「Discord Bot設定」セクションを参照
```

**📋 適用対象ファイル:**
- ✅ **自動適用**: 01-08 のファイル（Backend/Frontend/Network設定）
- ⚙️ **手動設定**: Discord Bot関連（事前準備が必要）

**⚠️ 注意**: `kubectl apply -f k8s/` での一括適用は使用しないでください。Discord Bot関連の設定ConfigMapは含まれますが、Secret・CSVデータが未作成のためエラーになります。

### 4. デプロイメント状況の確認

```bash
# ポッドの状況確認
kubectl get pods -n trendscope

# サービスの状況確認（EXTERNAL-IPが割り当てられることを確認）
kubectl get services -n trendscope

# Cilium設定の確認
kubectl get ciliuml2announcementpolicy -n trendscope
kubectl get ciliumloadbalancerippool
```

## 🔧 運用コマンド

### ログ確認

```bash
# リアルタイムログ
kubectl logs -f deployment/trendscope-backend -n trendscope
kubectl logs -f deployment/trendscope-frontend -n trendscope

# 全ポッドのログ
kubectl logs -l app.kubernetes.io/name=trendscope -n trendscope
```

### スケーリング

```bash
# 手動スケーリング
kubectl scale deployment trendscope-backend --replicas=5 -n trendscope
kubectl scale deployment trendscope-frontend --replicas=4 -n trendscope

# デプロイメント状況の詳細確認
kubectl describe deployment trendscope-backend -n trendscope
```

### 更新とローリングアップデート

```bash
# イメージの更新
kubectl set image deployment/trendscope-backend backend=ghcr.io/hirano00o/trendscope-api:v1.1.0 -n trendscope
kubectl set image deployment/trendscope-frontend frontend=ghcr.io/hirano00o/trendscope-ui:v1.1.0 -n trendscope

# ローリングアップデートの状況確認
kubectl rollout status deployment/trendscope-backend -n trendscope
kubectl rollout status deployment/trendscope-frontend -n trendscope

# ロールバック
kubectl rollout undo deployment/trendscope-backend -n trendscope
```

## 🌐 ネットワーク設定

### LoadBalancer IP の確認

```bash
# 割り当てられたIPの確認
kubectl get service trendscope-frontend-service -n trendscope -o wide

# Cilium L2 Announcement の状況確認
kubectl logs -l k8s-app=cilium -n kube-system | grep "L2 announcement"
```

### アクセス確認

```bash
# Frontend サービスのIPを取得
FRONTEND_IP=$(kubectl get service trendscope-frontend-service -n trendscope -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# アクセステスト
curl http://$FRONTEND_IP
```

## 🏗️ アーキテクチャ設定

### 本番環境仕様

- **高可用性**: Backend 2レプリカ、Frontend 2レプリカ
- **スケーリング**: 手動スケーリング（必要に応じて）
- **ネットワーク**: Cilium L2 Announcement による LoadBalancer IP
- **レジストリ**: GitHub Container Registry（ghcr.io）
- **セキュリティ**: 非root実行、最小権限、リソース制限

### リソース配分

#### Backend
- **CPU**: 250m（要求）/ 500m（制限）
- **Memory**: 512Mi（要求）/ 1Gi（制限）

#### Frontend  
- **CPU**: 100m（要求）/ 300m（制限）
- **Memory**: 256Mi（要求）/ 512Mi（制限）

## ⚠️ 注意事項

1. **Cilium設定**: L2 Announcementが有効であることを確認してください
2. **IPアドレス**: LoadBalancer IP Pool は実際のネットワーク環境に合わせて調整してください
3. **リソース監視**: 本番環境では適切な監視とアラートを設定してください
4. **バックアップ**: 重要な設定は定期的にバックアップしてください

## 🆘 トラブルシューティング

### Cilium関連

```bash
# Cilium ポッドの状況確認
kubectl get pods -n kube-system -l k8s-app=cilium

# L2 Announcement の設定確認
kubectl get ciliuml2announcementpolicy -A
kubectl describe ciliuml2announcementpolicy trendscope-l2-announcement -n trendscope

# IP Pool の状況確認
kubectl get ciliumloadbalancerippool
kubectl describe ciliumloadbalancerippool trendscope-ippool
```

### LoadBalancer IP が割り当てられない場合

```bash
# サービスの詳細確認
kubectl describe service trendscope-frontend-service -n trendscope

# Cilium Agent のログ確認
kubectl logs -l k8s-app=cilium -n kube-system | grep -i "load.*balance\|l2.*announce"

# IP Pool の競合確認
kubectl get services --all-namespaces -o wide | grep LoadBalancer
```

## 🔧 Discord Bot デプロイ

Discord BotのKubernetesデプロイメント手順です。アプリケーションの詳細については[discord-bot/README.md](../discord-bot/README.md)を参照してください。

### 前提条件

- TrendScopeアプリケーション（Backend）が既にデプロイされていること
- SBI証券スクリーニング結果CSVファイルが準備されていること

### デプロイ手順（3ステップ）

#### ステップ1: 事前準備（手動作成）

```bash
# 1. Discord Webhook URLでSecretを作成
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"
kubectl create secret generic trendscope-discord-bot-secret \
  --from-literal=DISCORD_WEBHOOK_URL="$DISCORD_WEBHOOK_URL" \
  --namespace=trendscope

# 2. CSVデータをConfigMapに登録
kubectl create configmap trendscope-discord-bot-csv \
  --from-file=screener_result.csv \
  --namespace=trendscope
```

### ステップ2: マニフェスト適用

```bash
# Discord Bot関連のマニフェストを適用
kubectl apply -f k8s/09-discord-bot-configmap.yaml  # 設定ConfigMap
kubectl apply -f k8s/10-discord-bot-cronjob.yaml    # CronJob定義
```

**📋 適用されるリソース:**
- 設定用ConfigMap: 実行モード、API URL、並列数などの設定
- CronJob: 平日朝10時の自動実行スケジュール

### ステップ3: 動作確認

```bash
# CronJobの状態確認
kubectl get cronjobs -n trendscope
kubectl describe cronjob trendscope-discord-bot -n trendscope

# 手動実行テスト（任意）
kubectl create job trendscope-discord-bot-test \
  --from=cronjob/trendscope-discord-bot \
  -n trendscope

# ログ確認
kubectl logs job/trendscope-discord-bot-test -n trendscope -f
```

### 運用コマンド

```bash
# ログ確認
kubectl logs -l job-name=trendscope-discord-bot -n trendscope --tail=50

# 手動実行
kubectl create job trendscope-discord-bot-manual \
  --from=cronjob/trendscope-discord-bot \
  -n trendscope

# CSVファイル更新
kubectl create configmap trendscope-discord-bot-csv \
  --from-file=screener_result.csv \
  --namespace=trendscope \
  --dry-run=client -o yaml | kubectl apply -f -

# 設定変更
kubectl patch configmap trendscope-discord-bot-config -n trendscope \
  --type merge -p '{"data":{"MAX_WORKERS":"15"}}'
```

**詳細情報**: アプリケーション機能・設定・トラブルシューティングについては[discord-bot/README.md](../discord-bot/README.md)を参照してください。
