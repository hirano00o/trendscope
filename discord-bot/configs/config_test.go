package configs

import (
	"os"
	"testing"
)

func TestLoadDefaultConfig(t *testing.T) {
	// Clear environment variables to test defaults
	clearEnvVars()
	defer clearEnvVars()

	config := Load()

	// Test default values
	if config.ExecutionMode != "cron" {
		t.Errorf("ExecutionMode = %v, want %v", config.ExecutionMode, "cron")
	}

	if config.CronSchedule != "0 10 * * 1-5" {
		t.Errorf("CronSchedule = %v, want %v", config.CronSchedule, "0 10 * * 1-5")
	}

	if config.DatabasePath != "/data/stocks.db" {
		t.Errorf("DatabasePath = %v, want %v", config.DatabasePath, "/data/stocks.db")
	}

	if config.PriceFilterEnabled != true {
		t.Errorf("PriceFilterEnabled = %v, want %v", config.PriceFilterEnabled, true)
	}

	if config.MinStockPrice != 100.0 {
		t.Errorf("MinStockPrice = %v, want %v", config.MinStockPrice, 100.0)
	}

	if config.MaxStockPrice != 5000.0 {
		t.Errorf("MaxStockPrice = %v, want %v", config.MaxStockPrice, 5000.0)
	}
}

func TestLoadEnvironmentConfig(t *testing.T) {
	clearEnvVars()
	defer clearEnvVars()

	// Set environment variables
	os.Setenv("EXECUTION_MODE", "once")
	os.Setenv("DATABASE_PATH", "/custom/path/stocks.db")
	os.Setenv("PRICE_FILTER_ENABLED", "false")
	os.Setenv("MIN_STOCK_PRICE", "200.0")
	os.Setenv("MAX_STOCK_PRICE", "10000.0")
	os.Setenv("CSV_FALLBACK_ENABLED", "true")

	config := Load()

	if config.ExecutionMode != "once" {
		t.Errorf("ExecutionMode = %v, want %v", config.ExecutionMode, "once")
	}

	if config.DatabasePath != "/custom/path/stocks.db" {
		t.Errorf("DatabasePath = %v, want %v", config.DatabasePath, "/custom/path/stocks.db")
	}

	if config.PriceFilterEnabled != false {
		t.Errorf("PriceFilterEnabled = %v, want %v", config.PriceFilterEnabled, false)
	}

	if config.MinStockPrice != 200.0 {
		t.Errorf("MinStockPrice = %v, want %v", config.MinStockPrice, 200.0)
	}

	if config.MaxStockPrice != 10000.0 {
		t.Errorf("MaxStockPrice = %v, want %v", config.MaxStockPrice, 10000.0)
	}

	if config.CSVFallbackEnabled != true {
		t.Errorf("CSVFallbackEnabled = %v, want %v", config.CSVFallbackEnabled, true)
	}
}

func TestGetEnvFloat64(t *testing.T) {
	clearEnvVars()
	defer clearEnvVars()

	// Test default value when environment variable is not set
	result := getEnvFloat64("NONEXISTENT_FLOAT", 123.45)
	if result != 123.45 {
		t.Errorf("getEnvFloat64() = %v, want %v", result, 123.45)
	}

	// Test parsing valid float
	os.Setenv("VALID_FLOAT", "678.90")
	result = getEnvFloat64("VALID_FLOAT", 0.0)
	if result != 678.90 {
		t.Errorf("getEnvFloat64() = %v, want %v", result, 678.90)
	}

	// Test invalid float (should return default)
	os.Setenv("INVALID_FLOAT", "not_a_number")
	result = getEnvFloat64("INVALID_FLOAT", 999.99)
	if result != 999.99 {
		t.Errorf("getEnvFloat64() with invalid input = %v, want %v", result, 999.99)
	}
}

func TestGetEnvBool(t *testing.T) {
	clearEnvVars()
	defer clearEnvVars()

	// Test default value when environment variable is not set
	result := getEnvBool("NONEXISTENT_BOOL", true)
	if result != true {
		t.Errorf("getEnvBool() = %v, want %v", result, true)
	}

	// Test parsing "true"
	os.Setenv("TRUE_VALUE", "true")
	result = getEnvBool("TRUE_VALUE", false)
	if result != true {
		t.Errorf("getEnvBool() = %v, want %v", result, true)
	}

	// Test parsing "false"
	os.Setenv("FALSE_VALUE", "false")
	result = getEnvBool("FALSE_VALUE", true)
	if result != false {
		t.Errorf("getEnvBool() = %v, want %v", result, false)
	}

	// Test invalid boolean (should return default)
	os.Setenv("INVALID_BOOL", "maybe")
	result = getEnvBool("INVALID_BOOL", true)
	if result != true {
		t.Errorf("getEnvBool() with invalid input = %v, want %v", result, true)
	}
}

func TestConfigValidation(t *testing.T) {
	clearEnvVars()
	defer clearEnvVars()

	// Test valid configuration
	config := Load()
	err := config.Validate()
	if err != nil {
		t.Errorf("Valid config validation failed: %v", err)
	}

	// Test invalid price range
	os.Setenv("MIN_STOCK_PRICE", "1000.0")
	os.Setenv("MAX_STOCK_PRICE", "500.0")
	config = Load()
	err = config.Validate()
	if err == nil {
		t.Error("Invalid price range should fail validation")
	}
}

func TestDetermineDataSource(t *testing.T) {
	clearEnvVars()
	defer clearEnvVars()

	// Test default (SQLite preferred)
	config := Load()
	dataSource := config.DetermineDataSource()
	if dataSource != DataSourceSQLite {
		t.Errorf("DetermineDataSource() = %v, want %v", dataSource, DataSourceSQLite)
	}

	// Test CSV fallback enabled
	os.Setenv("CSV_FALLBACK_ENABLED", "true")
	config = Load()
	config.CSVFallbackEnabled = true
	dataSource = config.DetermineDataSource()
	// Should still prefer SQLite unless database is unavailable
	if dataSource != DataSourceSQLite {
		t.Errorf("DetermineDataSource() with CSV fallback = %v, want %v", dataSource, DataSourceSQLite)
	}
}

// Helper function to clear all relevant environment variables
func clearEnvVars() {
	envVars := []string{
		"EXECUTION_MODE",
		"CRON_SCHEDULE", 
		"DISCORD_WEBHOOK_URL",
		"BACKEND_API_URL",
		"CSV_PATH",
		"MAX_WORKERS",
		"TOP_STOCKS_COUNT",
		"LOG_LEVEL",
		"DATABASE_PATH",
		"PRICE_FILTER_ENABLED",
		"MIN_STOCK_PRICE",
		"MAX_STOCK_PRICE",
		"CSV_FALLBACK_ENABLED",
		"VALID_FLOAT",
		"INVALID_FLOAT",
		"TRUE_VALUE",
		"FALSE_VALUE",
		"INVALID_BOOL",
	}

	for _, envVar := range envVars {
		os.Unsetenv(envVar)
	}
}