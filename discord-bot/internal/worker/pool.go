package worker

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/hirano00o/trendscope/discord-bot/pkg/api"
)

// Pool represents a worker pool for processing stock analysis requests
//
// @description 株式分析要求を効率的に処理するためのワーカープール
// メモリ使用量を制限しながら並列処理を行う
// レート制限とエラー処理を含む安全な並列実行を提供
//
// @example
// ```go
// pool := NewPool(10, apiClient)
// defer pool.Close()
//
// responses := pool.ProcessStocks(ctx, requests)
//
//	for response := range responses {
//	    if response.Error != nil {
//	        log.Printf("分析エラー: %v", response.Error)
//	        continue
//	    }
//	    fmt.Printf("結果: %+v\n", response.Result)
//	}
//
// ```
type Pool struct {
	// numWorkers is the number of worker goroutines
	numWorkers int
	// apiClient is the API client for making requests
	apiClient *api.Client
	// requestCh is the channel for sending requests to workers
	requestCh chan api.AnalysisRequest
	// responseCh is the channel for receiving responses from workers
	responseCh chan api.AnalysisResponse
	// wg is the wait group for worker goroutines
	wg sync.WaitGroup
	// closed indicates if the pool is closed
	closed bool
	// requestChClosed indicates if request channel is closed
	requestChClosed bool
	// responseChClosed indicates if response channel is closed
	responseChClosed bool
	// mu protects the closed and channel closed fields
	mu sync.RWMutex
}

// NewPool creates a new worker pool with the specified number of workers
//
// @description 指定された数のワーカーでワーカープールを作成する
// 各ワーカーは独立してAPIリクエストを処理し、
// レート制限とエラーハンドリングを含む
//
// @param {int} numWorkers ワーカーゴルーチンの数（推奨：5-20）
// @param {*api.Client} apiClient TrendScope APIクライアント
// @returns {*Pool} 設定済みのワーカープールインスタンス
//
// @example
// ```go
// apiClient := api.NewClient("http://backend:8000")
// pool := NewPool(10, apiClient)
// defer pool.Close()
// ```
func NewPool(numWorkers int, apiClient *api.Client) *Pool {
	pool := &Pool{
		numWorkers: numWorkers,
		apiClient:  apiClient,
		requestCh:  make(chan api.AnalysisRequest, numWorkers*2), // Buffer size
		responseCh: make(chan api.AnalysisResponse, numWorkers*2),
	}

	// Start worker goroutines
	for i := 0; i < numWorkers; i++ {
		pool.wg.Add(1)
		go pool.worker(i)
	}

	return pool
}

// worker is the worker goroutine that processes analysis requests
//
// @description 分析要求を処理するワーカーゴルーチン
// API呼び出し、エラーハンドリング、レート制限を実装
//
// @param {int} workerID ワーカーの識別ID（ログ用）
func (p *Pool) worker(workerID int) {
	defer p.wg.Done()

	log.Printf("Worker %d started", workerID)

	for request := range p.requestCh {
		// Rate limiting: small delay between requests to avoid overwhelming the API
		time.Sleep(100 * time.Millisecond)

		// Create context with timeout for individual request
		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)

		start := time.Now()
		result, err := p.apiClient.GetComprehensiveAnalysis(ctx, request.Symbol)
		duration := time.Since(start)

		response := api.AnalysisResponse{
			Request: request,
			Result:  result,
			Error:   err,
		}

		// Log processing result
		if err != nil {
			log.Printf("Worker %d: Failed to analyze %s (%s): %v [%v]",
				workerID, request.Symbol, request.CompanyName, err, duration)
		} else {
			log.Printf("Worker %d: Analyzed %s (%s): score=%.3f, confidence=%.3f [%v]",
				workerID, request.Symbol, request.CompanyName,
				result.OverallScore, result.Confidence, duration)
		}

		cancel()

		// Send response back
		select {
		case p.responseCh <- response:
		case <-time.After(5 * time.Second):
			log.Printf("Worker %d: Timeout sending response for %s", workerID, request.Symbol)
		}
	}

	log.Printf("Worker %d stopped", workerID)
}

// ProcessStocks processes a slice of analysis requests and returns a channel of responses
//
// @description 株式分析要求のスライスを処理し、レスポンスチャネルを返す
// 全ての要求が処理された後にチャネルを自動的にクローズ
// 省メモリで大量のデータを処理するためのストリーミング処理
//
// @param {context.Context} ctx 処理のコンテキスト（キャンセレーション用）
// @param {[]api.AnalysisRequest} requests 処理する分析要求のスライス
// @returns {<-chan api.AnalysisResponse} 分析結果を受信するチャネル
// @throws {error} プールが既に閉じられている場合はパニック
//
// @example
// ```go
//
//	requests := []api.AnalysisRequest{
//	    {Symbol: "7203.T", CompanyName: "トヨタ自動車"},
//	    {Symbol: "6758.T", CompanyName: "ソニー"},
//	}
//
// responses := pool.ProcessStocks(ctx, requests)
// var results []*api.AnalysisResult
//
//	for response := range responses {
//	    if response.Error == nil {
//	        results = append(results, response.Result)
//	    }
//	}
//
// ```
func (p *Pool) ProcessStocks(ctx context.Context, requests []api.AnalysisRequest) <-chan api.AnalysisResponse {
	// Check if pool is closed
	p.mu.RLock()
	if p.closed {
		p.mu.RUnlock()
		panic("cannot process stocks on closed pool")
	}
	p.mu.RUnlock()

	// Create output channel
	outputCh := make(chan api.AnalysisResponse, len(requests))

	go func() {
		defer close(outputCh)

		// Track responses
		responseCount := 0
		totalRequests := len(requests)

		// Start sending requests
		go func() {
			for i, request := range requests {
				select {
				case p.requestCh <- request:
					log.Printf("Queued request %d/%d: %s (%s)",
						i+1, totalRequests, request.Symbol, request.CompanyName)
				case <-ctx.Done():
					log.Printf("Context cancelled, stopping request submission")
					return
				}
			}
			log.Printf("All %d requests queued", totalRequests)
		}()

		// Collect responses
		for responseCount < totalRequests {
			select {
			case response := <-p.responseCh:
				responseCount++
				log.Printf("Processing response %d/%d: %s",
					responseCount, totalRequests, response.Request.Symbol)

				select {
				case outputCh <- response:
				case <-ctx.Done():
					log.Printf("Context cancelled during response collection")
					return
				}

			case <-ctx.Done():
				log.Printf("Context cancelled, stopping response collection")
				return
			}
		}

		log.Printf("All %d responses collected", totalRequests)
	}()

	return outputCh
}

// Close gracefully shuts down the worker pool
//
// @description ワーカープールを安全に終了する
// 全てのワーカーゴルーチンの終了を待機し、
// チャネルをクローズしてリソースを解放
// 二重クローズを防ぐため、すでに閉じられている場合は何も行わない
//
// @example
// ```go
// pool := NewPool(10, apiClient)
// defer pool.Close() // 必ずリソースを解放
//
// // 処理を実行
// responses := pool.ProcessStocks(ctx, requests)
// // ...
// ```
func (p *Pool) Close() error {
	p.mu.Lock()
	if p.closed {
		p.mu.Unlock()
		return nil
	}
	p.closed = true

	log.Printf("Closing worker pool...")

	// Close request channel to signal workers to stop (only if not already closed)
	if !p.requestChClosed {
		close(p.requestCh)
		p.requestChClosed = true
	}
	p.mu.Unlock()

	// Wait for all workers to finish (outside of lock to prevent deadlock)
	p.wg.Wait()

	// Close response channel (only if not already closed)
	p.mu.Lock()
	if !p.responseChClosed {
		close(p.responseCh)
		p.responseChClosed = true
	}
	p.mu.Unlock()

	log.Printf("Worker pool closed")
	return nil
}

// Stats returns statistics about the worker pool
//
// @description ワーカープールの統計情報を返す
// デバッグとモニタリング用
//
// @returns {string} 統計情報の文字列
func (p *Pool) Stats() string {
	p.mu.RLock()
	closed := p.closed
	p.mu.RUnlock()

	return fmt.Sprintf("Pool[workers=%d, closed=%t, requestQueue=%d, responseQueue=%d]",
		p.numWorkers, closed, len(p.requestCh), len(p.responseCh))
}

// CreateAnalysisRequests creates analysis requests from CSV stocks
//
// @description CSV株式データから分析要求のスライスを作成する
// Worker poolで処理するためのリクエスト構造体に変換
//
// @param {[]*csv.Stock} stocks CSV株式データのスライス
// @returns {[]api.AnalysisRequest} 分析要求のスライス
//
// @example
// ```go
// stocks, _ := csv.ReadStocksFromCSV("screener.csv")
// requests := CreateAnalysisRequests(stocks)
// responses := pool.ProcessStocks(ctx, requests)
// ```
func CreateAnalysisRequests(stocks []interface{}) []api.AnalysisRequest {
	// Note: This function assumes the stocks parameter contains csv.Stock objects
	// Since we can't import csv package here due to circular import,
	// we'll define this as a utility function that can be called from main
	requests := make([]api.AnalysisRequest, 0)

	// This will be implemented in the main package where both csv and worker are imported

	return requests
}
