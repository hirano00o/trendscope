package configs

import (
	"log"
	"os"
	"strconv"
)

// Config holds all configuration values for the Discord bot
//
// @description アプリケーション全体の設定を管理するための構造体
// Discord Bot の動作に必要なパラメータを環境変数から取得し、
// デフォルト値を提供する
//
// @example
// ```go
// cfg := configs.Load()
// fmt.Printf("Execution mode: %s\n", cfg.ExecutionMode)
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
	// CSVPath is the path to the stock screener CSV file
	CSVPath string
	// MaxWorkers defines the maximum number of concurrent workers for API calls
	MaxWorkers int
	// TopStocksCount defines how many top stocks to notify
	TopStocksCount int
	// LogLevel defines the logging level ("DEBUG", "INFO", "WARN", "ERROR")
	LogLevel string
}

// Load loads configuration from environment variables with default values
//
// @description 環境変数からアプリケーション設定を読み込み、
// 設定されていない場合は適切なデフォルト値を使用する
// ExecutionModeによって動作を制御：
// - "cron": 内蔵スケジューラーを使用（Docker Compose用）
// - "once": 即座に一度だけ実行（Kubernetes CronJob用）
//
// @returns {Config} 完全な設定を含む構造体
//
// @example
// ```go
// config := Load()
// log.Printf("Backend API: %s", config.BackendAPIURL)
// ```
func Load() *Config {
	return &Config{
		ExecutionMode:     getEnv("EXECUTION_MODE", "cron"),        // "cron" or "once"
		CronSchedule:      getEnv("CRON_SCHEDULE", "0 10 * * 1-5"), // 平日10時
		DiscordWebhookURL: getEnv("DISCORD_WEBHOOK_URL", ""),
		BackendAPIURL:     getEnv("BACKEND_API_URL", "http://localhost:8000"),
		CSVPath:           getEnv("CSV_PATH", "./screener_result.csv"),
		MaxWorkers:        getEnvInt("MAX_WORKERS", 10),
		TopStocksCount:    getEnvInt("TOP_STOCKS_COUNT", 15),
		LogLevel:          getEnv("LOG_LEVEL", "INFO"), // "DEBUG", "INFO", "WARN", "ERROR"
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
