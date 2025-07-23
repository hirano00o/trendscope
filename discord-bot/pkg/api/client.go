package api

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

// AnalysisResult represents the comprehensive analysis result from the backend API
//
// @description バックエンドAPIから返される包括的分析結果を表現する構造体
// 6カテゴリーの分析結果を含む
//
// @example
// ```go
// result := &AnalysisResult{
//     Symbol:       "7203.T",
//     OverallScore: 0.75,
//     Confidence:   0.8,
// }
// ```
type AnalysisResult struct {
	// Symbol is the stock symbol (e.g., "7203.T")
	Symbol string `json:"symbol"`
	// OverallScore is the overall analysis score (0.0-1.0)
	OverallScore float64 `json:"overall_score"`
	// Confidence is the confidence level of the analysis (0.0-1.0)
	Confidence float64 `json:"confidence"`
	// TechnicalAnalysis contains technical indicator results
	TechnicalAnalysis struct {
		Score      float64 `json:"score"`
		Confidence float64 `json:"confidence"`
		Signal     string  `json:"signal"`
	} `json:"technical_analysis"`
	// PatternAnalysis contains pattern recognition results
	PatternAnalysis struct {
		Score      float64 `json:"score"`
		Confidence float64 `json:"confidence"`
		Signal     string  `json:"signal"`
	} `json:"pattern_analysis"`
	// VolatilityAnalysis contains volatility analysis results
	VolatilityAnalysis struct {
		Score      float64 `json:"score"`
		Confidence float64 `json:"confidence"`
		Signal     string  `json:"signal"`
	} `json:"volatility_analysis"`
	// MLPrediction contains machine learning prediction results
	MLPrediction struct {
		Score      float64 `json:"score"`
		Confidence float64 `json:"confidence"`
		Signal     string  `json:"signal"`
	} `json:"ml_prediction"`
	// IntegratedScoring contains integrated scoring results
	IntegratedScoring struct {
		Score      float64 `json:"score"`
		Confidence float64 `json:"confidence"`
		Signal     string  `json:"signal"`
	} `json:"integrated_scoring"`
}

// Client represents an HTTP client for the TrendScope backend API
//
// @description TrendScopeバックエンドAPIとの通信を行うHTTPクライアント
// タイムアウトとレート制限を考慮した安全な通信を提供
//
// @example
// ```go
// client := NewClient("http://localhost:8000")
// result, err := client.GetComprehensiveAnalysis(ctx, "7203.T")
// ```
type Client struct {
	// baseURL is the base URL of the backend API
	baseURL string
	// httpClient is the underlying HTTP client
	httpClient *http.Client
}

// NewClient creates a new API client with the specified base URL
//
// @description 指定されたベースURLでAPIクライアントを作成する
// タイムアウトを30秒に設定し、安全な通信を確保
//
// @param {string} baseURL バックエンドAPIのベースURL
// @returns {*Client} 設定済みのAPIクライアントインスタンス
//
// @example
// ```go
// client := NewClient("http://backend:8000")
// // または
// client := NewClient("http://localhost:8000")
// ```
func NewClient(baseURL string) *Client {
	return &Client{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// GetComprehensiveAnalysis retrieves comprehensive analysis for the given symbol
//
// @description 指定された株式シンボルの包括的分析結果を取得する
// バックエンドAPIの `/api/v1/comprehensive/{symbol}` エンドポイントを呼び出す
// コンテキストによるキャンセレーションとタイムアウトをサポート
//
// @param {context.Context} ctx リクエストのコンテキスト（キャンセレーション用）
// @param {string} symbol 株式シンボル（例：7203.T）
// @returns {*AnalysisResult} 分析結果
// @throws {error} API呼び出しまたはJSONパースに失敗した場合
//
// @example
// ```go
// ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
// defer cancel()
// 
// result, err := client.GetComprehensiveAnalysis(ctx, "7203.T")
// if err != nil {
//     log.Printf("分析取得失敗: %v", err)
//     return
// }
// fmt.Printf("スコア: %.2f, 信頼度: %.2f", result.OverallScore, result.Confidence)
// ```
func (c *Client) GetComprehensiveAnalysis(ctx context.Context, symbol string) (*AnalysisResult, error) {
	url := fmt.Sprintf("%s/api/v1/comprehensive/%s", c.baseURL, symbol)

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to make request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("API request failed with status %d", resp.StatusCode)
	}

	var result AnalysisResult
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	// Ensure the symbol is set in the result
	result.Symbol = symbol

	return &result, nil
}

// AnalysisRequest represents a request for stock analysis
//
// @description 株式分析要求を表現する構造体
// Worker poolで使用される
type AnalysisRequest struct {
	// Symbol is the stock symbol to analyze
	Symbol string
	// CompanyName is the company name from CSV
	CompanyName string
}

// AnalysisResponse represents the response from analysis processing
//
// @description 分析処理の結果を表現する構造体
// エラー処理を含む
type AnalysisResponse struct {
	// Request is the original analysis request
	Request AnalysisRequest
	// Result is the analysis result (nil if error occurred)
	Result *AnalysisResult
	// Error is any error that occurred during analysis
	Error error
}