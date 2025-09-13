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
	"github.com/hirano00o/trendscope/discord-bot/pkg/database"
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
// SQLite読み込み（CSVフォールバック） → 並列分析 → 結果ソート → Discord通知
// 価格フィルタリングとエラー処理、詳細なロギングを含む
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

	// Step 1: Load stock data (SQLite or CSV fallback)
	log.Printf("Step 1: Loading stock data")
	stocks, dataSource, err := loadStockData(app.config)
	if err != nil {
		return fmt.Errorf("failed to load stock data: %w", err)
	}
	log.Printf("Successfully loaded %d stocks from %s", len(stocks), dataSource)

	if len(stocks) == 0 {
		return fmt.Errorf("no stocks found after filtering")
	}

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
	log.Printf("Data Source: %s", dataSource)
	if app.config.IsPriceFilterEnabled() {
		minPrice, maxPrice := app.config.GetPriceRange()
		log.Printf("Price Filter: %.2f - %.2f", minPrice, maxPrice)
	}
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

// loadStockData loads stock data from SQLite or CSV fallback
//
// @description SQLiteデータベースまたはCSVフォールバックから株式データを読み込む
// 価格フィルタリングを適用し、データソースの自動判定を行う
//
// @param {*configs.Config} config アプリケーション設定
// @returns {[]*csv.Stock, string, error} 株式データ、データソース名、エラー
//
// @example
// ```go
// config := configs.Load()
// stocks, source, err := loadStockData(config)
// if err != nil {
//     log.Printf("Failed to load stock data: %v", err)
// }
// log.Printf("Loaded %d stocks from %s", len(stocks), source)
// ```
func loadStockData(config *configs.Config) ([]*csv.Stock, string, error) {
	dataSource := determineDataSource(config)
	
	switch dataSource {
	case "SQLite":
		return loadStockDataFromSQLite(config)
	case "CSV":
		return loadStockDataFromCSV(config)
	default:
		return nil, "", fmt.Errorf("no valid data source available (SQLite: %s, CSV: %s, Fallback: %v)",
			config.DatabasePath, config.CSVPath, config.CSVFallbackEnabled)
	}
}

// loadStockDataFromSQLite loads and filters stock data from SQLite database
//
// @description SQLiteデータベースから株式データを読み込み、フィルタリングを適用
//
// @param {*configs.Config} config アプリケーション設定
// @returns {[]*csv.Stock, string, error} 株式データ、データソース名、エラー
func loadStockDataFromSQLite(config *configs.Config) ([]*csv.Stock, string, error) {
	// Create database service
	service, err := database.NewService(config)
	if err != nil {
		return nil, "", fmt.Errorf("failed to create database service: %w", err)
	}
	defer service.Close()

	// Validate database connection and schema
	if err := service.ValidateConnection(); err != nil {
		return nil, "", fmt.Errorf("database validation failed: %w", err)
	}

	// Get filtered companies based on configuration
	companies, err := service.GetFilteredCompanies()
	if err != nil {
		return nil, "", fmt.Errorf("failed to get filtered companies: %w", err)
	}

	if len(companies) == 0 {
		configs.LogDebug(config, "No companies found after filtering")
		return []*csv.Stock{}, "SQLite", nil
	}

	// Convert to compatible stock format
	adapter := database.NewStockAdapter(companies)
	stocks := adapter.GetStocks()

	// Validate compatibility
	if err := database.ValidateStockCompatibility(stocks); err != nil {
		return nil, "", fmt.Errorf("stock compatibility validation failed: %w", err)
	}

	sourceInfo := database.GetSourceInfo(service)
	sourceInfo.FilteredCompanies = len(companies)

	configs.LogDebug(config, "SQLite data loaded: %d companies (total: %d, filter: %s)",
		sourceInfo.FilteredCompanies, sourceInfo.TotalCompanies, sourceInfo.FilterCriteria)

	return stocks, "SQLite", nil
}

// loadStockDataFromCSV loads stock data from CSV file
//
// @description CSVファイルから株式データを読み込む（フォールバック用）
//
// @param {*configs.Config} config アプリケーション設定
// @returns {[]*csv.Stock, string, error} 株式データ、データソース名、エラー
func loadStockDataFromCSV(config *configs.Config) ([]*csv.Stock, string, error) {
	stocks, err := csv.ReadStocksFromCSV(config.CSVPath, configs.IsDebugEnabled(config))
	if err != nil {
		return nil, "", fmt.Errorf("failed to read CSV: %w", err)
	}

	configs.LogDebug(config, "CSV data loaded: %d stocks from %s", len(stocks), config.CSVPath)
	return stocks, "CSV", nil
}

// determineDataSource determines which data source to use
//
// @description 利用可能なデータソースを判定する
// SQLiteを優先し、利用できない場合はCSVフォールバックを検討
//
// @param {*configs.Config} config アプリケーション設定
// @returns {string} 使用するデータソース ("SQLite", "CSV", "" if none available)
func determineDataSource(config *configs.Config) string {
	// Check SQLite database availability
	if isDatabaseAvailable(config.DatabasePath) {
		return "SQLite"
	}

	// Check CSV fallback
	if config.CSVFallbackEnabled && isCSVAvailable(config.CSVPath) {
		configs.LogDebug(config, "SQLite unavailable, falling back to CSV: %s", config.CSVPath)
		return "CSV"
	}

	return ""
}

// isDatabaseAvailable checks if SQLite database is available
//
// @description SQLiteデータベースファイルが利用可能かチェック
//
// @param {string} databasePath データベースファイルのパス
// @returns {bool} 利用可能な場合true
func isDatabaseAvailable(databasePath string) bool {
	if databasePath == "" || databasePath == ":memory:" {
		return false
	}

	// Check if file exists and is readable
	if _, err := os.Stat(databasePath); err != nil {
		return false
	}

	// Try to create a connection to validate
	conn, err := database.NewConnection(databasePath)
	if err != nil {
		return false
	}
	defer conn.Close()

	if err := conn.Connect(); err != nil {
		return false
	}

	return true
}

// isCSVAvailable checks if CSV file is available
//
// @description CSVファイルが利用可能かチェック
//
// @param {string} csvPath CSVファイルのパス
// @returns {bool} 利用可能な場合true
func isCSVAvailable(csvPath string) bool {
	if csvPath == "" {
		return false
	}

	// Check if file exists and is readable
	if _, err := os.Stat(csvPath); err != nil {
		return false
	}

	return true
}

// main is the application entry point
//
// @description アプリケーションのエントリーポイント
// アプリケーションを初期化し、実行を開始
// SQLiteデータベース統合により企業データの価格フィルタリングが可能
//
// @example
// 環境変数の設定例：
// ```bash
// export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
// export BACKEND_API_URL="http://backend:8000"
// export DATABASE_PATH="/data/stocks.db"
// export PRICE_FILTER_ENABLED="true"
// export MIN_STOCK_PRICE="100.0"
// export MAX_STOCK_PRICE="5000.0"
// export CSV_FALLBACK_ENABLED="true"
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
