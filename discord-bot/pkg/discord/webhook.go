package discord

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/hirano00o/trendscope/discord-bot/pkg/api"
	"github.com/hirano00o/trendscope/discord-bot/pkg/csv"
)

// StockResult represents a stock analysis result for Discord notification
//
// @description Discord通知用の株式分析結果を表現する構造体
// CSV情報とAPI分析結果を組み合わせる
//
// @example
// ```go
//
//	result := &StockResult{
//	    Symbol:      "7203.T",
//	    CompanyName: "トヨタ自動車",
//	    Confidence:  0.8,
//	    Score:       0.75,
//	    KabutanURL:  "https://kabutan.jp/stock/?code=7203",
//	}
//
// ```
type StockResult struct {
	// Symbol is the stock symbol with .T suffix
	Symbol string
	// CompanyName is the company name from CSV
	CompanyName string
	// Confidence is the confidence level from analysis
	Confidence float64
	// Score is the overall score from analysis
	Score float64
	// KabutanURL is the Kabutan URL for the stock
	KabutanURL string
}

// WebhookMessage represents a Discord webhook message
//
// @description Discord Webhookに送信するメッセージの構造体
// 埋め込み形式でリッチなメッセージを送信
type WebhookMessage struct {
	Content string  `json:"content,omitempty"`
	Embeds  []Embed `json:"embeds,omitempty"`
}

// Embed represents a Discord embed
//
// @description Discordの埋め込みメッセージを表現する構造体
type Embed struct {
	Title       string  `json:"title"`
	Description string  `json:"description"`
	Color       int     `json:"color"`
	Fields      []Field `json:"fields,omitempty"`
	Footer      *Footer `json:"footer,omitempty"`
	Timestamp   string  `json:"timestamp,omitempty"`
}

// Field represents a field in a Discord embed
//
// @description 埋め込みメッセージのフィールドを表現する構造体
type Field struct {
	Name   string `json:"name"`
	Value  string `json:"value"`
	Inline bool   `json:"inline"`
}

// Footer represents a footer in a Discord embed
//
// @description 埋め込みメッセージのフッターを表現する構造体
type Footer struct {
	Text string `json:"text"`
}

// WebhookClient represents a Discord webhook client
//
// @description Discord Webhookクライアント
// 株式分析結果を整形してDiscordに通知する
//
// @example
// ```go
// client := NewWebhookClient("https://discord.com/api/webhooks/...")
// err := client.SendStockAnalysis(ctx, results)
// ```
type WebhookClient struct {
	// webhookURL is the Discord webhook URL
	webhookURL string
	// httpClient is the underlying HTTP client
	httpClient *http.Client
}

// NewWebhookClient creates a new Discord webhook client
//
// @description 指定されたWebhook URLでDiscordクライアントを作成する
// タイムアウトを15秒に設定
//
// @param {string} webhookURL Discord WebhookのURL
// @returns {*WebhookClient} 設定済みのWebhookクライアントインスタンス
//
// @example
// ```go
// client := NewWebhookClient("https://discord.com/api/webhooks/123/abc")
// ```
func NewWebhookClient(webhookURL string) *WebhookClient {
	return &WebhookClient{
		webhookURL: webhookURL,
		httpClient: &http.Client{
			Timeout: 15 * time.Second,
		},
	}
}

// SendStockAnalysis sends stock analysis results to Discord
//
// @description 株式分析結果をDiscordに送信する
// TOP15の結果を整形してリッチな埋め込みメッセージとして送信
// 要件に従ったフォーマット：シンボル,企業名,信頼度,スコア,URL
//
// @param {context.Context} ctx リクエストのコンテキスト
// @param {[]StockResult} results 分析結果のスライス（TOP15）
// @throws {error} Discord API呼び出しに失敗した場合
//
// @example
// ```go
//
//	results := []StockResult{{
//	    Symbol: "7203.T",
//	    CompanyName: "トヨタ自動車",
//	    Confidence: 0.8,
//	    Score: 0.75,
//	    KabutanURL: "https://kabutan.jp/stock/?code=7203",
//	}}
//
// err := client.SendStockAnalysis(ctx, results)
// ```
func (c *WebhookClient) SendStockAnalysis(ctx context.Context, results []StockResult) error {
	if len(results) == 0 {
		return fmt.Errorf("no results to send")
	}

	embed := c.createAnalysisEmbed(results)
	message := WebhookMessage{
		Content: "📈 **本日の上昇トレンド株 TOP15**",
		Embeds:  []Embed{embed},
	}

	return c.sendMessage(ctx, message)
}

// createAnalysisEmbed creates a Discord embed for stock analysis results
//
// @description 株式分析結果用のDiscord埋め込みメッセージを作成する
// 要件に従ったフォーマットでデータを整形
//
// @param {[]StockResult} results 分析結果のスライス
// @returns {Embed} Discord埋め込みメッセージ
func (c *WebhookClient) createAnalysisEmbed(results []StockResult) Embed {
	var description strings.Builder
	description.WriteString("```\n")
	description.WriteString("シンボル,企業名,信頼度,スコア,URL\n")

	for _, result := range results {
		line := fmt.Sprintf("%s,%s,%.1f,%.1f,%s\n",
			result.Symbol,
			result.CompanyName,
			result.Confidence,
			result.Score,
			result.KabutanURL,
		)
		description.WriteString(line)
	}
	description.WriteString("```")

	// Color: Green for positive trend
	color := 0x00FF00

	return Embed{
		Title:       "TrendScope 株価上昇トレンド分析",
		Description: description.String(),
		Color:       color,
		Footer: &Footer{
			Text: "TrendScope Discord Bot",
		},
		Timestamp: time.Now().Format(time.RFC3339),
	}
}

// sendMessage sends a message to Discord via webhook
//
// @description Discord Webhookにメッセージを送信する
// JSON形式でHTTP POSTリクエストを送信
//
// @param {context.Context} ctx リクエストのコンテキスト
// @param {WebhookMessage} message 送信するメッセージ
// @throws {error} HTTPリクエストまたはレスポンス処理に失敗した場合
func (c *WebhookClient) sendMessage(ctx context.Context, message WebhookMessage) error {
	jsonData, err := json.Marshal(message)
	if err != nil {
		return fmt.Errorf("failed to marshal message: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", c.webhookURL, bytes.NewBuffer(jsonData))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send webhook: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("webhook request failed with status %d", resp.StatusCode)
	}

	return nil
}

// CreateStockResults creates StockResult slice from CSV stocks and API analysis results
//
// @description CSV株式データとAPI分析結果から通知用のStockResultを作成する
// 分析結果をスコアと信頼度でソートし、TOP15を選択
//
// @param {[]*csv.Stock} stocks CSV株式データ
// @param {[]*api.AnalysisResult} analysisResults API分析結果
// @param {int} topCount 上位何件を取得するか
// @returns {[]StockResult} 通知用結果のスライス
//
// @example
// ```go
// stocks, _ := csv.ReadStocksFromCSV("screener.csv")
// results := []*api.AnalysisResult{...}
// topResults := CreateStockResults(stocks, results, 15)
// ```
func CreateStockResults(stocks []*csv.Stock, analysisResults []*api.AnalysisResult, topCount int) []StockResult {
	// Create a map for quick stock lookup by symbol
	stockMap := make(map[string]*csv.Stock)
	for _, stock := range stocks {
		stockMap[stock.GetSymbol()] = stock
	}

	// Create results slice
	var results []StockResult
	for _, analysis := range analysisResults {
		if stock, exists := stockMap[analysis.Symbol]; exists {
			// Extract stock code from symbol (remove .T suffix)
			stockCode := strings.TrimSuffix(analysis.Symbol, ".T")
			kabutanURL := fmt.Sprintf("https://kabutan.jp/stock/?code=%s", stockCode)

			result := StockResult{
				Symbol:      analysis.Symbol,
				CompanyName: stock.Name,
				Confidence:  analysis.Confidence,
				Score:       analysis.OverallScore,
				KabutanURL:  kabutanURL,
			}
			results = append(results, result)
		}
	}

	// Sort by overall_score and confidence (descending)
	// First by score, then by confidence
	for i := 0; i < len(results)-1; i++ {
		for j := i + 1; j < len(results); j++ {
			// Compare by score first
			if results[i].Score < results[j].Score {
				results[i], results[j] = results[j], results[i]
			} else if results[i].Score == results[j].Score {
				// If scores are equal, compare by confidence
				if results[i].Confidence < results[j].Confidence {
					results[i], results[j] = results[j], results[i]
				}
			}
		}
	}

	// Return top N results
	if len(results) > topCount {
		results = results[:topCount]
	}

	return results
}
