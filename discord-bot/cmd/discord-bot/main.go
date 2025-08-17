package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/hirano00o/trendscope/discord-bot/configs"
	"github.com/hirano00o/trendscope/discord-bot/internal/worker"
	"github.com/hirano00o/trendscope/discord-bot/pkg/api"
	"github.com/hirano00o/trendscope/discord-bot/pkg/csv"
	"github.com/hirano00o/trendscope/discord-bot/pkg/discord"
	"github.com/hirano00o/trendscope/discord-bot/pkg/scheduler"
)

// App represents the Discord Bot application
//
// @description Discord Botアプリケーションのメインクラス
// 全ての機能を統合し、スケジュール実行とDiscord通知を管理
//
// @example
// ```go
// app := NewApp()
//
//	if err := app.Run(ctx); err != nil {
//	    log.Fatal(err)
//	}
//
// ```
type App struct {
	// config holds all application configuration
	config *configs.Config
	// scheduler manages cron scheduling
	scheduler *scheduler.Scheduler
	// apiClient communicates with TrendScope backend
	apiClient *api.Client
	// webhookClient sends notifications to Discord
	webhookClient *discord.WebhookClient
}

// NewApp creates a new Discord Bot application instance
//
// @description 新しいDiscord Botアプリケーションインスタンスを作成する
// 設定を読み込み、必要なクライアントを初期化
//
// @returns {*App} 設定済みのアプリケーションインスタンス
// @throws {error} 設定の検証に失敗した場合はパニック
//
// @example
// ```go
// app := NewApp()
// defer app.Close()
// ```
func NewApp() *App {
	cfg := configs.Load()

	// Validate required configuration
	if cfg.DiscordWebhookURL == "" {
		log.Fatal("DISCORD_WEBHOOK_URL is required")
	}

	log.Printf("Initializing Discord Bot with config:")
	log.Printf("  Execution Mode: %s", cfg.ExecutionMode)
	log.Printf("  Backend API: %s", cfg.BackendAPIURL)
	log.Printf("  CSV Path: %s", cfg.CSVPath)
	log.Printf("  Cron Schedule: %s", cfg.CronSchedule)
	log.Printf("  Max Workers: %d", cfg.MaxWorkers)
	log.Printf("  Top Stocks Count: %d", cfg.TopStocksCount)
	log.Printf("  Log Level: %s", cfg.LogLevel)

	return &App{
		config:        cfg,
		scheduler:     scheduler.NewScheduler(),
		apiClient:     api.NewClient(cfg.BackendAPIURL, configs.IsDebugEnabled(cfg)),
		webhookClient: discord.NewWebhookClient(cfg.DiscordWebhookURL),
	}
}

// Run starts the Discord Bot application
//
// @description Discord Botアプリケーションを開始する
// ExecutionModeに基づいて動作を制御：
// - "once": 即座に一度だけ分析を実行（Kubernetes CronJob用）
// - "cron": スケジューラーを設定してメインループを開始（Docker Compose用）
// シグナルハンドリングによる優雅な終了をサポート
//
// @param {context.Context} ctx アプリケーションのコンテキスト
// @throws {error} アプリケーションの開始に失敗した場合
//
// @example
// ```go
// ctx := context.Background()
//
//	if err := app.Run(ctx); err != nil {
//	    log.Fatal(err)
//	}
//
// ```
func (app *App) Run(ctx context.Context) error {
	log.Printf("Starting TrendScope Discord Bot...")
	log.Printf("Execution Mode: %s", app.config.ExecutionMode)

	// Execution mode: "once" - run immediately and exit (for Kubernetes CronJob)
	if app.config.ExecutionMode == "once" {
		log.Printf("Running in 'once' mode - executing analysis immediately")

		if err := app.runStockAnalysis(ctx); err != nil {
			return fmt.Errorf("stock analysis failed in 'once' mode: %w", err)
		}

		log.Printf("Analysis completed successfully in 'once' mode")
		return nil
	}

	// Execution mode: "cron" - use internal scheduler (for Docker Compose)
	log.Printf("Running in 'cron' mode - starting scheduler")

	// Setup job
	job := &scheduler.Job{
		Name:    "stock-trend-analysis",
		Handler: app.runStockAnalysis,
	}

	// Add job to scheduler
	if err := app.scheduler.AddJob(app.config.CronSchedule, job); err != nil {
		return fmt.Errorf("failed to add job to scheduler: %w", err)
	}

	// Setup signal handling for graceful shutdown
	signalCtx, cancel := signal.NotifyContext(ctx, os.Interrupt, syscall.SIGTERM)
	defer cancel()

	// Start scheduler in a separate goroutine
	go app.scheduler.Start(signalCtx)

	log.Printf("Discord Bot started successfully! Waiting for scheduled execution...")
	log.Printf("Next execution scheduled for: %s (Cron: %s)",
		app.getNextExecutionTime(), app.config.CronSchedule)

	// Wait for shutdown signal
	<-signalCtx.Done()
	log.Printf("Shutdown signal received, stopping...")

	return app.shutdown()
}

// runStockAnalysis performs the main stock analysis workflow
//
// @description 株式分析のメインワークフローを実行する
// CSV読み込み → 並列分析 → 結果ソート → Discord通知
// エラー処理と詳細なロギングを含む
//
// @param {context.Context} ctx 分析処理のコンテキスト
// @throws {error} ワークフローの実行に失敗した場合
//
// @example
// ```go
// ctx := context.Background()
//
//	if err := runStockAnalysis(ctx); err != nil {
//	    log.Printf("分析失敗: %v", err)
//	}
//
// ```
func (app *App) runStockAnalysis(ctx context.Context) error {
	log.Printf("=== Starting Stock Analysis Workflow ===")
	startTime := time.Now()

	// Step 1: Read CSV data
	log.Printf("Step 1: Reading CSV data from %s", app.config.CSVPath)
	stocks, err := csv.ReadStocksFromCSV(app.config.CSVPath, configs.IsDebugEnabled(app.config))
	if err != nil {
		return fmt.Errorf("failed to read CSV: %w", err)
	}
	log.Printf("Successfully read %d stocks from CSV", len(stocks))

	// Step 2: Create analysis requests
	log.Printf("Step 2: Creating analysis requests")
	requests := createAnalysisRequests(stocks)
	log.Printf("Created %d analysis requests", len(requests))

	// Step 3: Process stocks with worker pool
	log.Printf("Step 3: Starting parallel analysis with %d workers", app.config.MaxWorkers)
	pool := worker.NewPool(app.config.MaxWorkers, app.apiClient)
	defer pool.Close()

	// Process all stocks
	responses := pool.ProcessStocks(ctx, requests)

	// Collect successful results
	var successfulResults []*api.AnalysisResult
	var failedCount int

	for response := range responses {
		if response.Error != nil {
			log.Printf("Analysis failed for %s: %v", response.Request.Symbol, response.Error)
			failedCount++
		} else {
			successfulResults = append(successfulResults, response.Result)
		}
	}

	log.Printf("Analysis completed: %d successful, %d failed", len(successfulResults), failedCount)

	if len(successfulResults) == 0 {
		return fmt.Errorf("no successful analysis results")
	}

	// Step 4: Create Discord notification data
	log.Printf("Step 4: Creating Discord notification for top %d stocks", app.config.TopStocksCount)
	stockResults := discord.CreateStockResults(stocks, successfulResults, app.config.TopStocksCount)

	if len(stockResults) == 0 {
		return fmt.Errorf("no stock results to notify")
	}

	// Step 5: Send Discord notification
	log.Printf("Step 5: Sending Discord notification")
	if err := app.webhookClient.SendStockAnalysis(ctx, stockResults); err != nil {
		return fmt.Errorf("failed to send Discord notification: %w", err)
	}

	duration := time.Since(startTime)
	log.Printf("=== Stock Analysis Workflow Completed Successfully in %v ===", duration)
	log.Printf("Top 3 Results:")
	for i, result := range stockResults {
		if i >= 3 {
			break
		}
		log.Printf("  %d. %s (%s) - Score: %.3f, Confidence: %.3f",
			i+1, result.Symbol, result.CompanyName, result.Score, result.Confidence)
	}

	return nil
}

// createAnalysisRequests converts CSV stocks to analysis requests
//
// @description CSV株式データを分析要求に変換する
// Worker poolで処理するためのリクエスト構造体を作成
//
// @param {[]*csv.Stock} stocks CSV株式データのスライス
// @returns {[]api.AnalysisRequest} 分析要求のスライス
func createAnalysisRequests(stocks []*csv.Stock) []api.AnalysisRequest {
	requests := make([]api.AnalysisRequest, len(stocks))
	for i, stock := range stocks {
		requests[i] = api.AnalysisRequest{
			Symbol:      stock.GetSymbol(),
			CompanyName: stock.Name,
		}
	}
	return requests
}

// getNextExecutionTime calculates the next execution time based on cron schedule
//
// @description 設定されたCron式に基づいて次回実行時刻を計算する
// scheduler.GetNextExecutionTime関数を使用して正確な次回実行時刻を計算
//
// @returns {string} 次回実行予定時刻の文字列
func (app *App) getNextExecutionTime() string {
	nextTime, err := scheduler.GetNextExecutionTime(app.config.CronSchedule)
	if err != nil {
		log.Printf("Failed to calculate next execution time: %v", err)
		return "Unknown (invalid cron expression)"
	}

	return nextTime.Format("2006-01-02 15:04:05")
}

// shutdown gracefully shuts down the application
//
// @description アプリケーションを優雅に終了する
// スケジューラーを停止し、リソースをクリーンアップ
//
// @throws {error} 終了処理に失敗した場合
func (app *App) shutdown() error {
	log.Printf("Shutting down Discord Bot...")

	// Stop scheduler
	app.scheduler.Stop()

	log.Printf("Discord Bot shutdown completed")
	return nil
}

// main is the application entry point
//
// @description アプリケーションのエントリーポイント
// アプリケーションを初期化し、実行を開始
//
// @example
// 環境変数の設定例：
// ```bash
// export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
// export BACKEND_API_URL="http://backend:8000"
// export CSV_PATH="./screener_result.csv"
// export CRON_SCHEDULE="0 10 * * 1-5"
// export MAX_WORKERS="10"
// export TOP_STOCKS_COUNT="15"
//
// ./discord-bot
// ```
func main() {
	log.SetFlags(log.LstdFlags | log.Lshortfile)
	log.Printf("TrendScope Discord Bot starting...")

	app := NewApp()

	ctx := context.Background()
	if err := app.Run(ctx); err != nil {
		log.Fatalf("Application failed: %v", err)
	}

	log.Printf("TrendScope Discord Bot exited successfully")
}
