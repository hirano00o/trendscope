package configs

import (
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
// fmt.Printf("Cron schedule: %s\n", cfg.CronSchedule)
// ```
type Config struct {
	// CronSchedule defines when the bot should run (default: weekdays at 10 AM)
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
}

// Load loads configuration from environment variables with default values
//
// @description 環境変数からアプリケーション設定を読み込み、
// 設定されていない場合は適切なデフォルト値を使用する
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
		CronSchedule:      getEnv("CRON_SCHEDULE", "0 10 * * 1-5"), // 平日10時
		DiscordWebhookURL: getEnv("DISCORD_WEBHOOK_URL", ""),
		BackendAPIURL:     getEnv("BACKEND_API_URL", "http://localhost:8000"),
		CSVPath:           getEnv("CSV_PATH", "./screener_result.csv"),
		MaxWorkers:        getEnvInt("MAX_WORKERS", 10),
		TopStocksCount:    getEnvInt("TOP_STOCKS_COUNT", 15),
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