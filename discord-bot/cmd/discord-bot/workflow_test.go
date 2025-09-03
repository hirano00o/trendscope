package main

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/hirano00o/trendscope/discord-bot/configs"
	"github.com/hirano00o/trendscope/discord-bot/pkg/database"
)

func TestLoadStockDataFromSQLite(t *testing.T) {
	// Create test database with sample data
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test.db")

	config := &configs.Config{
		DatabasePath:       dbPath,
		PriceFilterEnabled: true,
		MinStockPrice:      100.0,
		MaxStockPrice:      5000.0,
		CSVFallbackEnabled: false,
	}

	// Create service and setup test data
	service, err := database.NewService(config)
	if err != nil {
		t.Fatalf("Failed to create service: %v", err)
	}
	defer service.Close()

	if err := service.CreateTables(); err != nil {
		t.Fatalf("Failed to create tables: %v", err)
	}

	// Insert test companies
	testCompanies := []database.Company{
		{
			Symbol: "7203.T",
			Name:   "トヨタ自動車",
			Market: "東P",
			Price:  float64Ptr(2500.0),
		},
		{
			Symbol: "1332.T",
			Name:   "ニッスイ",
			Market: "東P",
			Price:  float64Ptr(877.8),
		},
		{
			Symbol: "HIGH.T",
			Name:   "High Price Stock",
			Market: "東P",
			Price:  float64Ptr(10000.0), // Above filter range
		},
	}

	for i := range testCompanies {
		_, err := service.GetRepository().Insert(&testCompanies[i])
		if err != nil {
			t.Fatalf("Failed to insert test company %d: %v", i, err)
		}
	}

	// Test stock data loading
	stocks, source, err := loadStockData(config)
	if err != nil {
		t.Errorf("loadStockData() failed: %v", err)
	}

	if source != "SQLite" {
		t.Errorf("loadStockData() source = %v, want %v", source, "SQLite")
	}

	// Should return 2 stocks (within price range)
	if len(stocks) != 2 {
		t.Errorf("loadStockData() returned %d stocks, want 2", len(stocks))
	}

	// Verify stock compatibility
	for _, stock := range stocks {
		if stock.GetSymbol() == "" {
			t.Error("Stock has empty symbol")
		}
		if stock.Name == "" {
			t.Error("Stock has empty name")
		}
	}
}

func TestLoadStockDataFallbackToCSV(t *testing.T) {
	// Create test CSV file
	tempDir := t.TempDir()
	csvPath := filepath.Join(tempDir, "test.csv")
	
	csvContent := `"コード","銘柄名","市場","現在値","前日比(%)"
"7203","トヨタ自動車","東P","2500.00","+10(+0.40%)"
"1332","ニッスイ","東P","877.8","+3.5(+0.40%)"
`
	if err := os.WriteFile(csvPath, []byte(csvContent), 0644); err != nil {
		t.Fatalf("Failed to create test CSV: %v", err)
	}

	config := &configs.Config{
		DatabasePath:       "/nonexistent/database.db", // Invalid path
		CSVPath:           csvPath,
		PriceFilterEnabled: false,
		CSVFallbackEnabled: true,
	}

	// Test stock data loading with fallback
	stocks, source, err := loadStockData(config)
	if err != nil {
		t.Errorf("loadStockData() with CSV fallback failed: %v", err)
	}

	if source != "CSV" {
		t.Errorf("loadStockData() fallback source = %v, want %v", source, "CSV")
	}

	// Should return 2 stocks from CSV
	if len(stocks) != 2 {
		t.Errorf("loadStockData() with CSV fallback returned %d stocks, want 2", len(stocks))
	}
}

func TestDetermineDataSource(t *testing.T) {
	tests := []struct {
		name           string
		databaseExists bool
		csvExists      bool
		fallbackEnabled bool
		expected       string
	}{
		{
			name:           "SQLite available",
			databaseExists: true,
			csvExists:      true,
			fallbackEnabled: true,
			expected:       "SQLite",
		},
		{
			name:           "SQLite unavailable, CSV fallback",
			databaseExists: false,
			csvExists:      true,
			fallbackEnabled: true,
			expected:       "CSV",
		},
		{
			name:           "Both unavailable",
			databaseExists: false,
			csvExists:      false,
			fallbackEnabled: true,
			expected:       "",
		},
		{
			name:           "SQLite unavailable, CSV fallback disabled",
			databaseExists: false,
			csvExists:      true,
			fallbackEnabled: false,
			expected:       "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tempDir := t.TempDir()
			
			var dbPath string
			var csvPath string
			
			if tt.databaseExists {
				dbPath = filepath.Join(tempDir, "test.db")
				// Create empty database file
				if err := os.WriteFile(dbPath, []byte{}, 0644); err != nil {
					t.Fatalf("Failed to create test database: %v", err)
				}
			} else {
				dbPath = "/nonexistent/database.db"
			}
			
			if tt.csvExists {
				csvPath = filepath.Join(tempDir, "test.csv") 
				csvContent := `"コード","銘柄名","市場","現在値","前日比(%)"
"7203","トヨタ自動車","東P","2500.00","+10(+0.40%)"
`
				if err := os.WriteFile(csvPath, []byte(csvContent), 0644); err != nil {
					t.Fatalf("Failed to create test CSV: %v", err)
				}
			} else {
				csvPath = "/nonexistent/test.csv"
			}

			config := &configs.Config{
				DatabasePath:       dbPath,
				CSVPath:           csvPath,
				CSVFallbackEnabled: tt.fallbackEnabled,
			}

			source := determineDataSource(config)
			if source != tt.expected {
				t.Errorf("determineDataSource() = %v, want %v", source, tt.expected)
			}
		})
	}
}

func TestCreateAnalysisRequestsFromStocks(t *testing.T) {
	// Test with database adapter
	companies := []database.Company{
		{
			Symbol: "7203.T",
			Name:   "トヨタ自動車",
		},
		{
			Symbol: "1332.T", 
			Name:   "ニッスイ",
		},
	}

	adapter := database.NewStockAdapter(companies)
	stocks := adapter.GetStocks()

	requests := createAnalysisRequests(stocks)

	if len(requests) != len(companies) {
		t.Errorf("createAnalysisRequests() returned %d requests, want %d", len(requests), len(companies))
	}

	for i, request := range requests {
		if request.Symbol != companies[i].GetSymbol() {
			t.Errorf("createAnalysisRequests()[%d].Symbol = %v, want %v", i, request.Symbol, companies[i].GetSymbol())
		}
		if request.CompanyName != companies[i].Name {
			t.Errorf("createAnalysisRequests()[%d].CompanyName = %v, want %v", i, request.CompanyName, companies[i].Name)
		}
	}
}

// Helper function for tests
func float64Ptr(f float64) *float64 {
	return &f
}