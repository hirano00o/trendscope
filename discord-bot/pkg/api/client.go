package api

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"time"
)

// BackendResponse represents the complete response from the backend API
//
// @description バックエンドAPIから返される完全なレスポンス構造
// success フラグと data オブジェクトを含む
type BackendResponse struct {
	Success bool         `json:"success"`
	Data    ResponseData `json:"data"`
}

// ResponseData represents the data section of the backend response
//
// @description バックエンドAPIレスポンスのdataセクション
type ResponseData struct {
	Symbol              string              `json:"symbol"`
	Timestamp           string              `json:"timestamp"`
	CurrentPrice        float64             `json:"current_price"`
	IntegratedScore     IntegratedScore     `json:"integrated_score"`
	TechnicalAnalysis   TechnicalAnalysis   `json:"technical_analysis"`
	PatternAnalysis     PatternAnalysis     `json:"pattern_analysis"`
	VolatilityAnalysis  VolatilityAnalysis  `json:"volatility_analysis"`
	MLAnalysis          MLAnalysis          `json:"ml_analysis"`
	FundamentalAnalysis FundamentalAnalysis `json:"fundamental_analysis"`
}

// IntegratedScore represents the integrated scoring results
type IntegratedScore struct {
	OverallScore    float64 `json:"overall_score"`
	ConfidenceLevel float64 `json:"confidence_level"`
	Recommendation  string  `json:"recommendation"`
	RiskAssessment  string  `json:"risk_assessment"`
}

// TechnicalAnalysis represents technical analysis results
type TechnicalAnalysis struct {
	OverallSignal  string  `json:"overall_signal"`
	SignalStrength float64 `json:"signal_strength"`
}

// PatternAnalysis represents pattern analysis results
type PatternAnalysis struct {
	OverallSignal  string  `json:"overall_signal"`
	SignalStrength float64 `json:"signal_strength"`
	PatternScore   float64 `json:"pattern_score"`
}

// VolatilityAnalysis represents volatility analysis results
type VolatilityAnalysis struct {
	Regime          string  `json:"regime"`
	RiskLevel       string  `json:"risk_level"`
	VolatilityScore float64 `json:"volatility_score"`
}

// MLAnalysis represents machine learning analysis results
type MLAnalysis struct {
	TrendDirection string  `json:"trend_direction"`
	ConsensusScore float64 `json:"consensus_score"`
}

// FundamentalAnalysis represents fundamental analysis results
type FundamentalAnalysis struct {
	Score      float64 `json:"score"`
	Confidence float64 `json:"confidence"`
}

// AnalysisResult represents the simplified analysis result for Discord Bot
//
// @description Discord Bot用に簡略化された分析結果を表現する構造体
// バックエンドAPIの複雑な構造から必要な値を抽出
//
// @example
// ```go
//
//	result := &AnalysisResult{
//	    Symbol:       "7203.T",
//	    OverallScore: 0.75,
//	    Confidence:   0.8,
//	}
//
// ```
type AnalysisResult struct {
	// Symbol is the stock symbol (e.g., "7203.T")
	Symbol string
	// OverallScore is the overall analysis score (0.0-1.0)
	OverallScore float64
	// Confidence is the confidence level of the analysis (0.0-1.0)
	Confidence float64
	// Recommendation is the investment recommendation
	Recommendation string
	// RiskAssessment is the risk level assessment
	RiskAssessment string
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
//
//	if err != nil {
//	    log.Printf("分析取得失敗: %v", err)
//	    return
//	}
//
// fmt.Printf("スコア: %.2f, 信頼度: %.2f", result.OverallScore, result.Confidence)
// ```
func (c *Client) GetComprehensiveAnalysis(ctx context.Context, symbol string) (*AnalysisResult, error) {
	url := fmt.Sprintf("%s/api/v1/comprehensive/%s", c.baseURL, symbol)

	// Debug: Log request details
	log.Printf("[DEBUG] API Request: %s", url)

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")
	req.Header.Set("User-Agent", "TrendScope-Discord-Bot/1.0")

	// Debug: Log request headers
	log.Printf("[DEBUG] Request Headers: %v", req.Header)

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to make request: %w", err)
	}
	defer resp.Body.Close()

	// Debug: Log response status and headers
	log.Printf("[DEBUG] Response Status: %d %s", resp.StatusCode, resp.Status)
	log.Printf("[DEBUG] Response Headers: %v", resp.Header)

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("API request failed with status %d", resp.StatusCode)
	}

	// Read response body as bytes for debugging
	bodyBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	// Debug: Log raw JSON response (first 500 chars to avoid log overflow)
	responsePreview := string(bodyBytes)
	if len(responsePreview) > 500 {
		responsePreview = responsePreview[:500] + "..."
	}
	log.Printf("[DEBUG] Raw JSON Response for %s: %s", symbol, responsePreview)

	// Parse the backend response structure
	var backendResponse BackendResponse
	if err := json.Unmarshal(bodyBytes, &backendResponse); err != nil {
		log.Printf("[ERROR] JSON Unmarshal failed for %s: %v", symbol, err)
		log.Printf("[ERROR] Problematic JSON: %s", string(bodyBytes))
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	// Check if the request was successful
	if !backendResponse.Success {
		log.Printf("[ERROR] Backend API returned success=false for %s", symbol)
		return nil, fmt.Errorf("backend API returned success=false for symbol %s", symbol)
	}

	// Extract values from the nested structure
	result := &AnalysisResult{
		Symbol:         symbol,
		OverallScore:   backendResponse.Data.IntegratedScore.OverallScore,
		Confidence:     backendResponse.Data.IntegratedScore.ConfidenceLevel,
		Recommendation: backendResponse.Data.IntegratedScore.Recommendation,
		RiskAssessment: backendResponse.Data.IntegratedScore.RiskAssessment,
	}

	// Debug: Log parsed values
	log.Printf("[DEBUG] Extracted values for %s: OverallScore=%.6f, Confidence=%.6f, Recommendation=%s, Risk=%s",
		symbol, result.OverallScore, result.Confidence, result.Recommendation, result.RiskAssessment)

	return result, nil
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
