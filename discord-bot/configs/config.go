package configs

import (
	"fmt"
	"log"
	"os"
	"strconv"
)

// DataSource represents the data source type
//
// @description データソースの種類を表現する列挙型
type DataSource int

const (
	// DataSourceSQLite uses SQLite database as primary data source
	DataSourceSQLite DataSource = iota
	// DataSourceCSV uses CSV files as fallback data source
	DataSourceCSV
)

// String returns the string representation of DataSource
func (d DataSource) String() string {
	switch d {
	case DataSourceSQLite:
		return "SQLite"
	case DataSourceCSV:
		return "CSV"
	default:
		return "Unknown"
	}
}

// Config holds all configuration values for the Discord bot
//
// @description アプリケーション全体の設定を管理するための構造体
// Discord Bot の動作に必要なパラメータを環境変数から取得し、
// デフォルト値を提供する。SQLiteデータベース接続と価格フィルタリング機能を含む
//
// @example
// ```go
// cfg := configs.Load()
// fmt.Printf("Execution mode: %s\n", cfg.ExecutionMode)
// fmt.Printf("Database path: %s\n", cfg.DatabasePath)
// ```
type Config struct {
	// ExecutionMode defines how the bot should run: "cron" for internal scheduling, "once" for immediate execution
	ExecutionMode string
	// CronSchedule defines when the bot should run (only used in "cron" mode)
	CronSchedule string
	// DiscordWebhookURL is the Discord webhook URL for sending notifications
	DiscordWebhookURL string
	// BackendAPIURL is the TrendScope backend API URL
	BackendAPIURL string
	// CSVPath is the path to the stock screener CSV file (fallback)
	CSVPath string
	// MaxWorkers defines the maximum number of concurrent workers for API calls
	MaxWorkers int
	// TopStocksCount defines how many top stocks to notify
	TopStocksCount int
	// LogLevel defines the logging level ("DEBUG", "INFO", "WARN", "ERROR")
	LogLevel string

	// === SQLite Database Configuration ===
	// DatabasePath is the path to the SQLite database file
	DatabasePath string

	// === Price Filtering Configuration ===
	// PriceFilterEnabled enables or disables price range filtering
	PriceFilterEnabled bool
	// MinStockPrice is the minimum stock price for filtering
	MinStockPrice float64
	// MaxStockPrice is the maximum stock price for filtering
	MaxStockPrice float64

	// === Data Source Configuration ===
	// CSVFallbackEnabled enables CSV fallback when SQLite is unavailable
	CSVFallbackEnabled bool
}

// Load loads configuration from environment variables with default values
//
// @description 環境変数からアプリケーション設定を読み込み、
// 設定されていない場合は適切なデフォルト値を使用する
// ExecutionModeによって動作を制御：
// - "cron": 内蔵スケジューラーを使用（Docker Compose用）
// - "once": 即座に一度だけ実行（Kubernetes CronJob用）
// SQLiteデータベースと価格フィルタリング機能の設定も含む
//
// @returns {Config} 完全な設定を含む構造体
//
// @example
// ```go
// config := Load()
// log.Printf("Backend API: %s", config.BackendAPIURL)
// log.Printf("Database path: %s", config.DatabasePath)
// ```
func Load() *Config {
	return &Config{
		// Basic configuration
		ExecutionMode:     getEnv("EXECUTION_MODE", "cron"),        // "cron" or "once"
		CronSchedule:      getEnv("CRON_SCHEDULE", "0 10 * * 1-5"), // 平日10時
		DiscordWebhookURL: getEnv("DISCORD_WEBHOOK_URL", ""),
		BackendAPIURL:     getEnv("BACKEND_API_URL", "http://localhost:8000"),
		CSVPath:           getEnv("CSV_PATH", "./screener_result.csv"),
		MaxWorkers:        getEnvInt("MAX_WORKERS", 10),
		TopStocksCount:    getEnvInt("TOP_STOCKS_COUNT", 15),
		LogLevel:          getEnv("LOG_LEVEL", "INFO"), // "DEBUG", "INFO", "WARN", "ERROR"

		// SQLite database configuration
		DatabasePath: getEnv("DATABASE_PATH", "/data/stocks.db"),

		// Price filtering configuration
		PriceFilterEnabled: getEnvBool("PRICE_FILTER_ENABLED", true),
		MinStockPrice:      getEnvFloat64("MIN_STOCK_PRICE", 100.0),
		MaxStockPrice:      getEnvFloat64("MAX_STOCK_PRICE", 5000.0),

		// Data source configuration
		CSVFallbackEnabled: getEnvBool("CSV_FALLBACK_ENABLED", false),
	}
}

// getEnv retrieves an environment variable or returns a default value
//
// @description 指定された環境変数を取得し、存在しない場合はデフォルト値を返す
//
// @param {string} key 環境変数のキー名
// @param {string} defaultValue デフォルト値
// @returns {string} 環境変数の値またはデフォルト値
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// getEnvInt retrieves an environment variable as integer or returns a default value
//
// @description 指定された環境変数を整数として取得し、
// 存在しない場合や変換できない場合はデフォルト値を返す
//
// @param {string} key 環境変数のキー名
// @param {int} defaultValue デフォルト値
// @returns {int} 環境変数の整数値またはデフォルト値
func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}

// getEnvFloat64 retrieves an environment variable as float64 or returns a default value
//
// @description 指定された環境変数を浮動小数点数として取得し、
// 存在しない場合や変換できない場合はデフォルト値を返す
//
// @param {string} key 環境変数のキー名
// @param {float64} defaultValue デフォルト値
// @returns {float64} 環境変数の浮動小数点値またはデフォルト値
//
// @example
// ```go
// minPrice := getEnvFloat64("MIN_STOCK_PRICE", 100.0)
// ```
func getEnvFloat64(key string, defaultValue float64) float64 {
	if value := os.Getenv(key); value != "" {
		if floatValue, err := strconv.ParseFloat(value, 64); err == nil {
			return floatValue
		}
	}
	return defaultValue
}

// getEnvBool retrieves an environment variable as boolean or returns a default value
//
// @description 指定された環境変数を真偽値として取得し、
// 存在しない場合や変換できない場合はデフォルト値を返す
// "true", "1", "yes", "on" は true として扱われ、
// "false", "0", "no", "off" は false として扱われる
//
// @param {string} key 環境変数のキー名
// @param {bool} defaultValue デフォルト値
// @returns {bool} 環境変数の真偽値またはデフォルト値
//
// @example
// ```go
// filterEnabled := getEnvBool("PRICE_FILTER_ENABLED", true)
// ```
func getEnvBool(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		if boolValue, err := strconv.ParseBool(value); err == nil {
			return boolValue
		}
	}
	return defaultValue
}

// IsDebugEnabled checks if debug logging is enabled
//
// @description デバッグログが有効かどうかを確認する
// LOG_LEVEL環境変数がDEBUGに設定されている場合にtrueを返す
//
// @param {*Config} config 設定構造体
// @returns {bool} デバッグログが有効かどうか
//
// @example
// ```go
// config := Load()
//
//	if IsDebugEnabled(config) {
//	    log.Printf("[DEBUG] This will only show when LOG_LEVEL=DEBUG")
//	}
//
// ```
func IsDebugEnabled(config *Config) bool {
	return config.LogLevel == "DEBUG"
}

// LogDebug outputs a debug log message only if debug logging is enabled
//
// @description デバッグログが有効な場合のみログメッセージを出力する
// 環境変数LOG_LEVEL=DEBUGの場合のみ出力される
//
// @param {*Config} config 設定構造体
// @param {string} format printfフォーマット文字列
// @param {...interface{}} args フォーマット引数
//
// @example
// ```go
// config := Load()
// LogDebug(config, "[DEBUG] Processing %s with score %.3f", symbol, score)
// // LOG_LEVEL=DEBUG の場合のみ出力される
// ```
func LogDebug(config *Config, format string, args ...interface{}) {
	if IsDebugEnabled(config) {
		log.Printf(format, args...)
	}
}

// Validate validates the configuration values
//
// @description 設定値の妥当性を検証する
// 価格範囲、必須フィールド等のチェックを行う
//
// @throws {error} 設定が無効な場合
//
// @example
// ```go
// config := Load()
// if err := config.Validate(); err != nil {
//     log.Fatalf("Invalid configuration: %v", err)
// }
// ```
func (c *Config) Validate() error {
	// Validate price range
	if c.PriceFilterEnabled {
		if c.MinStockPrice >= c.MaxStockPrice {
			return fmt.Errorf("minimum stock price (%.2f) must be less than maximum stock price (%.2f)",
				c.MinStockPrice, c.MaxStockPrice)
		}
		
		if c.MinStockPrice < 0 {
			return fmt.Errorf("minimum stock price cannot be negative: %.2f", c.MinStockPrice)
		}
		
		if c.MaxStockPrice <= 0 {
			return fmt.Errorf("maximum stock price must be positive: %.2f", c.MaxStockPrice)
		}
	}

	// Validate worker count
	if c.MaxWorkers <= 0 {
		return fmt.Errorf("max workers must be positive: %d", c.MaxWorkers)
	}

	// Validate top stocks count
	if c.TopStocksCount <= 0 {
		return fmt.Errorf("top stocks count must be positive: %d", c.TopStocksCount)
	}

	return nil
}

// DetermineDataSource determines which data source to use based on configuration
//
// @description 設定に基づいて使用するデータソースを決定する
// SQLiteを優先し、利用できない場合にCSVフォールバックを検討
//
// @returns {DataSource} 使用すべきデータソース
//
// @example
// ```go
// config := Load()
// dataSource := config.DetermineDataSource()
// if dataSource == DataSourceSQLite {
//     // Use SQLite database
// } else {
//     // Use CSV fallback
// }
// ```
func (c *Config) DetermineDataSource() DataSource {
	// Always prefer SQLite if available
	// The actual availability check will be done during runtime
	return DataSourceSQLite
}

// IsPriceFilterEnabled checks if price filtering is enabled
//
// @description 価格フィルタリングが有効かどうかを確認する
//
// @returns {bool} フィルタリングが有効な場合true
func (c *Config) IsPriceFilterEnabled() bool {
	return c.PriceFilterEnabled
}

// GetPriceRange returns the configured price range for filtering
//
// @description フィルタリング用の価格範囲を取得する
//
// @returns {float64, float64} 最小価格と最大価格
//
// @example
// ```go
// config := Load()
// min, max := config.GetPriceRange()
// fmt.Printf("Price range: %.2f - %.2f", min, max)
// ```
func (c *Config) GetPriceRange() (float64, float64) {
	return c.MinStockPrice, c.MaxStockPrice
}

// String returns a string representation of the configuration
//
// @description 設定の文字列表現を返す（機密情報は除外）
//
// @returns {string} 設定の概要
func (c *Config) String() string {
	return fmt.Sprintf("Config{ExecutionMode: %s, DatabasePath: %s, PriceFilter: %v (%.2f-%.2f), CSVFallback: %v}",
		c.ExecutionMode,
		c.DatabasePath,
		c.PriceFilterEnabled,
		c.MinStockPrice,
		c.MaxStockPrice,
		c.CSVFallbackEnabled,
	)
}
