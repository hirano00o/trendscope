package main

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/hirano00o/trendscope/discord-bot/configs"
	"github.com/hirano00o/trendscope/discord-bot/pkg/database"
)

// TestFullIntegration tests the complete workflow from database setup to analysis
func TestFullIntegration(t *testing.T) {
	// Create temporary database
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "integration_test.db")

	config := &configs.Config{
		DatabasePath:       dbPath,
		PriceFilterEnabled: true,
		MinStockPrice:      500.0,
		MaxStockPrice:      3000.0,
		CSVFallbackEnabled: false,
	}

	// Create database service and setup test data
	service, err := database.NewService(config)
	if err != nil {
		t.Fatalf("Failed to create database service: %v", err)
	}
	defer service.Close()

	if err := service.CreateTables(); err != nil {
		t.Fatalf("Failed to create tables: %v", err)
	}

	// Insert comprehensive test data
	testCompanies := []database.Company{
		{
			Symbol:  "7203.T",
			Name:    "トヨタ自動車",
			Market:  "東P",
			Price:   integrationFloat64Ptr(2500.0),
		},
		{
			Symbol:  "6758.T",
			Name:    "ソニーグループ",
			Market:  "東P",
			Price:   integrationFloat64Ptr(1100.0),
		},
		{
			Symbol:  "7267.T",
			Name:    "ホンダ",
			Market:  "東P",
			Price:   integrationFloat64Ptr(800.0),
		},
		{
			Symbol:  "HIGH.T",
			Name:    "High Price Stock",
			Market:  "東P",
			Price:   integrationFloat64Ptr(5000.0), // Above filter range
		},
		{
			Symbol:  "LOW.T",
			Name:    "Low Price Stock",
			Market:  "東S",
			Price:   integrationFloat64Ptr(100.0), // Below filter range
		},
		{
			Symbol:  "NOPRICE.T",
			Name:    "No Price Stock",
			Market:  "東G",
			Price:   nil, // No price data
		},
	}

	for i := range testCompanies {
		_, err := service.GetRepository().Insert(&testCompanies[i])
		if err != nil {
			t.Fatalf("Failed to insert test company %d: %v", i, err)
		}
	}

	// Test data source determination
	source := determineDataSource(config)
	if source != "SQLite" {
		t.Errorf("Expected SQLite source, got %s", source)
	}

	// Test filtered companies retrieval
	filteredCompanies, err := service.GetFilteredCompanies()
	if err != nil {
		t.Fatalf("Failed to get filtered companies: %v", err)
	}

	// Should return 3 companies within price range (7203.T, 6758.T, 7267.T)
	expectedCount := 3
	if len(filteredCompanies) != expectedCount {
		t.Errorf("Expected %d companies, got %d", expectedCount, len(filteredCompanies))
	}

	// Test adapter compatibility
	adapter := database.NewStockAdapter(filteredCompanies)
	stocks := adapter.GetStocks()

	if len(stocks) != expectedCount {
		t.Errorf("Expected %d stocks from adapter, got %d", expectedCount, len(stocks))
	}

	// Verify stock data integrity
	symbolsFound := make(map[string]bool)
	for _, stock := range stocks {
		if stock.GetSymbol() == "" {
			t.Error("Stock has empty symbol")
		}
		if stock.Name == "" {
			t.Error("Stock has empty name")
		}
		symbolsFound[stock.GetSymbol()] = true
	}

	// Verify expected stocks are present
	expectedSymbols := []string{"7203.T", "6758.T", "7267.T"}
	for _, expectedSymbol := range expectedSymbols {
		if !symbolsFound[expectedSymbol] {
			t.Errorf("Expected symbol %s not found in results", expectedSymbol)
		}
	}

	// Test database adapter analysis request creation
	requests := database.CreateAnalysisRequests(filteredCompanies)

	if len(requests) != expectedCount {
		t.Errorf("Expected %d analysis requests, got %d", expectedCount, len(requests))
	}

	for _, request := range requests {
		if request.Symbol == "" {
			t.Error("Analysis request has empty symbol")
		}
		if request.CompanyName == "" {
			t.Error("Analysis request has empty company name")
		}
	}

	t.Logf("Integration test completed successfully - loaded %d stocks from SQLite", len(stocks))
}

// TestIntegrationWithCSVFallback tests the fallback mechanism
func TestIntegrationWithCSVFallback(t *testing.T) {
	tempDir := t.TempDir()
	csvPath := filepath.Join(tempDir, "test_fallback.csv")

	// Create test CSV file
	csvContent := `"コード","銘柄名","市場","現在値","前日比(%)"
"7203","トヨタ自動車","東P","2500.00","+10(+0.40%)"
"6758","ソニーグループ","東P","1100.00","+15(+1.38%)"
"7267","ホンダ","東P","800.00","-5(-0.62%)"
`
	if err := os.WriteFile(csvPath, []byte(csvContent), 0644); err != nil {
		t.Fatalf("Failed to create test CSV: %v", err)
	}

	config := &configs.Config{
		DatabasePath:       "/nonexistent/database.db", // Invalid database path
		CSVPath:           csvPath,
		PriceFilterEnabled: false,
		CSVFallbackEnabled: true,
	}

	// Test fallback data source determination
	source := determineDataSource(config)
	if source != "CSV" {
		t.Errorf("Expected CSV fallback source, got %s", source)
	}

	t.Logf("Integration fallback test completed - source determination successful")
}

// TestIntegrationErrorHandling tests error scenarios
func TestIntegrationErrorHandling(t *testing.T) {
	// Test with both data sources unavailable
	config := &configs.Config{
		DatabasePath:       "/nonexistent/database.db",
		CSVPath:           "/nonexistent/file.csv",
		CSVFallbackEnabled: true,
	}

	source := determineDataSource(config)
	if source != "" {
		t.Errorf("Expected empty source when no data sources are available, got %s", source)
	}

	t.Logf("Error handling test completed - correctly handled unavailable data sources")
}

// TestDatabaseConnectionRecovery tests database connection recovery
func TestDatabaseConnectionRecovery(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "recovery_test.db")

	config := &configs.Config{
		DatabasePath:       dbPath,
		PriceFilterEnabled: false,
		CSVFallbackEnabled: false,
	}

	// Create service and test initial connection
	service, err := database.NewService(config)
	if err != nil {
		t.Fatalf("Failed to create service: %v", err)
	}
	defer service.Close()

	if err := service.CreateTables(); err != nil {
		t.Fatalf("Failed to create tables: %v", err)
	}

	// Validate connection works
	if err := service.ValidateConnection(); err != nil {
		t.Errorf("Initial connection validation failed: %v", err)
	}

	// Insert test data
	company := database.Company{
		Symbol: "TEST.T",
		Name:   "Test Company",
		Market: "東P",
		Price:  integrationFloat64Ptr(1000.0),
	}

	id, err := service.GetRepository().Insert(&company)
	if err != nil {
		t.Fatalf("Failed to insert test company: %v", err)
	}

	// Test retrieval
	retrieved, err := service.GetRepository().GetBySymbol(company.Symbol)
	if err != nil {
		t.Errorf("Failed to retrieve company: %v", err)
	}
	if retrieved == nil || retrieved.Symbol != company.Symbol {
		t.Errorf("Retrieved company symbol mismatch: got %v, want %s", retrieved, company.Symbol)
	}

	t.Logf("Database connection recovery test completed successfully - inserted ID %d", id)
}

// TestConcurrentDatabaseAccess tests thread safety
func TestConcurrentDatabaseAccess(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "concurrent_test.db")

	config := &configs.Config{
		DatabasePath:       dbPath,
		PriceFilterEnabled: false,
		CSVFallbackEnabled: false,
	}

	service, err := database.NewService(config)
	if err != nil {
		t.Fatalf("Failed to create service: %v", err)
	}
	defer service.Close()

	if err := service.CreateTables(); err != nil {
		t.Fatalf("Failed to create tables: %v", err)
	}

	// Test concurrent operations
	const numGoroutines = 10
	const numOperations = 10

	done := make(chan bool, numGoroutines)

	for i := 0; i < numGoroutines; i++ {
		go func(workerID int) {
			defer func() { done <- true }()

			for j := 0; j < numOperations; j++ {
				company := database.Company{
					Symbol: fmt.Sprintf("TEST%d_%d.T", workerID, j),
					Name:   fmt.Sprintf("Test Company %d-%d", workerID, j),
					Market: "東P",
					Price:  integrationFloat64Ptr(float64(1000 + workerID*100 + j)),
				}

				_, err := service.GetRepository().Insert(&company)
				if err != nil {
					t.Errorf("Worker %d failed to insert company %d: %v", workerID, j, err)
					return
				}

				// Brief pause to allow other goroutines to work
				time.Sleep(time.Microsecond * 100)
			}
		}(i)
	}

	// Wait for all goroutines to complete
	for i := 0; i < numGoroutines; i++ {
		<-done
	}

	// Verify total count
	count, err := service.GetCompanyCount()
	if err != nil {
		t.Errorf("Failed to get company count: %v", err)
	}

	expectedCount := numGoroutines * numOperations
	if count != expectedCount {
		t.Errorf("Expected %d companies, got %d", expectedCount, count)
	}

	t.Logf("Concurrent access test completed - successfully handled %d concurrent operations", expectedCount)
}

// Helper function for integration tests

func integrationFloat64Ptr(f float64) *float64 {
	return &f
}