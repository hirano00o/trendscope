# 📈 TrendScope

**株価トレンド分析プラットフォーム**

TrendScopeは、複数の分析手法を統合して株価の上昇トレンドを予測する高度な分析ウェブアプリケーションです。米国株・日本株の両方に対応し、6つのカテゴリーで包括的な分析を提供します。

## ✨ 主要機能

### 🔍 6カテゴリー統合分析
- **テクニカル分析**: 移動平均線、RSI、MACD、ボリンジャーバンドなどの主要指標
- **パターン分析**: ローソク足パターン、サポート/レジスタンスライン、トレンドライン
- **ボラティリティ分析**: ATR、標準偏差、ボラティリティレジーム検出
- **機械学習予測**: Random Forest、SVM、ARIMAモデルを使用したアンサンブル予測
- **ファンダメンタル要素**: 出来高分析、セクター/市場相関
- **統合スコアリング**: 全分析結果を統合した総合的な上昇確率算出

### 🌍 グローバル市場対応
- **米国株**: AAPL, GOOGL, MSFT, TSLA, NVDA, AMZN, META など
- **日本株**: トヨタ(7203.T), ソニー(6758.T), ホンダ(7267.T), キーエンス(6861.T) など
- **リアルタイムデータ**: Yahoo Finance API (yfinance) を使用

### 📊 高度な可視化機能
- **インタラクティブチャート**: Recharts を使用した高性能チャート
- **価格チャート**: ローソク足、出来高バー、移動平均線、ボリンジャーバンド
- **テクニカル指標**: RSI、MACD、ATR などの指標を個別表示
- **パターン認識**: 検出されたパターンをチャート上に表示

### 🎯 直感的なUI/UX
- **モダンなデザイン**: Tailwind CSS + Radix UI による洗練されたインターフェース
- **レスポンシブデザイン**: デスクトップ・モバイル両対応
- **リアルタイム更新**: TanStack Query による効率的なデータ管理
- **多言語対応**: 日本語・英語のバイリンガル対応

## 🚀 クイックスタート

### 前提条件
- **Node.js**: 18.17以降
- **Python**: 3.12以降
- **Bun**: パッケージマネージャー（フロントエンド）
- **uv**: パッケージマネージャー（バックエンド）

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/hirano00o/trendscope.git
cd trendscope

# バックエンドのセットアップ
cd backend
uv sync

# フロントエンドのセットアップ
cd ../frontend
bun install
```

### 起動

```bash
# バックエンドサーバーを起動（ターミナル1）
cd backend
./start-dev.sh

# フロントエンドサーバーを起動（ターミナル2）
cd frontend
bun dev
```

### アクセス
- **フロントエンド**: http://localhost:3000
- **バックエンドAPI**: http://localhost:8000
- **APIドキュメント**: http://localhost:8000/docs

## 💡 使用方法

1. **株式コードの入力**
   - 米国株: `AAPL`, `GOOGL`, `MSFT` など
   - 日本株: `7203.T`, `6758.T`, `7267.T` など

2. **分析の実行**
   - 入力後、自動的に6カテゴリー分析が実行されます
   - 分析には数秒から数十秒かかります

3. **結果の確認**
   - 総合スコアと各カテゴリーの詳細結果を表示
   - インタラクティブチャートで視覚的に確認
   - 信頼区間付きの予測結果を提供

## 🔧 技術スタック

### フロントエンド
- **フレームワーク**: Next.js 14
- **言語**: TypeScript
- **スタイリング**: Tailwind CSS
- **UIライブラリ**: Radix UI
- **チャート**: Recharts
- **状態管理**: TanStack Query
- **パッケージマネージャー**: Bun

### バックエンド
- **フレームワーク**: FastAPI
- **言語**: Python 3.12+
- **データ取得**: yfinance
- **データ分析**: pandas, numpy
- **機械学習**: scikit-learn, statsmodels
- **可視化**: matplotlib, seaborn
- **パッケージマネージャー**: uv

### 開発・運用
- **コード品質**: Ruff (Python), Biome (TypeScript)
- **型チェック**: mypy (Python), TypeScript
- **テスト**: pytest (Python), Bun Test (TypeScript)
- **コンテナ**: Docker, Docker Compose

## 📡 API仕様

### 主要エンドポイント

#### 包括的分析
```
GET /api/v1/comprehensive/{symbol}
```
6カテゴリー統合分析を実行し、総合的な上昇確率を返します。

#### テクニカル分析のみ
```
GET /api/v1/analysis/{symbol}
```
テクニカル指標のみの分析結果を返します。

#### 履歴データ取得
```
GET /api/v1/historical/{symbol}/{period}
```
指定期間の株価履歴データを取得します。

**対応期間**: `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y`, `ytd`, `max`

### レスポンス例

```json
{
  "symbol": "AAPL",
  "analysis_date": "2025-01-18T10:00:00Z",
  "overall_score": 0.72,
  "confidence_interval": [0.65, 0.79],
  "categories": {
    "technical": {
      "score": 0.68,
      "signals": ["bullish_crossover", "oversold_rsi"]
    },
    "pattern": {
      "score": 0.75,
      "detected_patterns": ["hammer", "support_bounce"]
    },
    "volatility": {
      "score": 0.71,
      "regime": "normal"
    }
  }
}
```

## 🤝 開発への貢献

### 開発環境のセットアップ
詳細は [DEVELOPMENT.md](./DEVELOPMENT.md) をご覧ください。

### コード品質
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

### 現在の課題
- **テストカバレッジの向上**: 現在9%、目標80%以上
- **パフォーマンス最適化**: キャッシュ機能の実装
- **リアルタイム機能**: WebSocket接続の実装

### 貢献方法
1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📋 ロードマップ

### v1.0（現在）
- [x] 6カテゴリー分析システム
- [x] 米国株・日本株対応
- [x] インタラクティブチャート
- [x] レスポンシブデザイン
- [ ] テストカバレッジ80%以上

### v1.1（予定）
- [ ] リアルタイムデータ更新
- [ ] ポートフォリオ分析機能
- [ ] アラート機能
- [ ] データエクスポート機能

### v2.0（将来）
- [ ] 高度なMLモデル（LSTM、Transformer）
- [ ] センチメント分析
- [ ] ニュース統合分析
- [ ] マルチアセット対応（FX、コモディティ）

## 🔒 セキュリティ

- APIキーやクレデンシャルは環境変数で管理
- 入力データのバリデーションを実装
- CORS設定によるクロスオリジンリクエスト制御
- レート制限機能（実装予定）

## 📄 ライセンス

このプロジェクトは [MIT License](LICENSE) の下で公開されています。

## 🙏 謝辞

- **Yahoo Finance**: 株価データの提供
- **Recharts**: 高性能チャートライブラリ
- **FastAPI**: 高速なPython Webフレームワーク
- **Next.js**: 優れたReactフレームワーク

## 📞 サポート・連絡先

- **Issues**: [GitHub Issues](https://github.com/hirano00o/trendscope/issues)
- **Discussions**: [GitHub Discussions](https://github.com/hirano00o/trendscope/discussions)

---

⭐ このプロジェクトが役立つと思われましたら、ぜひスターをつけてください！

**免責事項**: このアプリケーションは教育・研究目的で提供されています。投資の意思決定は自己責任で行ってください。