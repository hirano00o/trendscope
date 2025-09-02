package database

import (
	"testing"

	"github.com/hirano00o/trendscope/discord-bot/configs"
)

func setupTestService(t *testing.T) (*Service, *configs.Config) {
	t.Helper()

	config := &configs.Config{
		DatabasePath:       ":memory:",
		PriceFilterEnabled: true,
		MinStockPrice:      100.0,
		MaxStockPrice:      5000.0,
		CSVFallbackEnabled: false,
	}

	service, err := NewService(config)
	if err != nil {
		t.Fatalf("Failed to create service: %v", err)
	}

	// Create tables
	if err := service.repo.CreateTables(); err != nil {
		t.Fatalf("Failed to create tables: %v", err)
	}

	return service, config
}

func insertTestCompanies(t *testing.T, service *Service) {
	t.Helper()

	companies := []Company{
		{
			Symbol: "LOW.T",
			Name:   "Low Price Stock",
			Market: "東P",
			Price:  float64Ptr(50.0), // Below filter range
		},
		{
			Symbol: "MID1.T",
			Name:   "Mid Price Stock 1",
			Market: "東P", 
			Price:  float64Ptr(500.0), // Within filter range
		},
		{
			Symbol: "MID2.T",
			Name:   "Mid Price Stock 2",
			Market: "東S",
			Price:  float64Ptr(1500.0), // Within filter range
		},
		{
			Symbol: "HIGH.T",
			Name:   "High Price Stock", 
			Market: "東G",
			Price:  float64Ptr(10000.0), // Above filter range
		},
		{
			Symbol: "NO_PRICE.T",
			Name:   "No Price Stock",
			Market: "東P",
			Price:  nil, // No price
		},
	}

	for i := range companies {
		_, err := service.repo.Insert(&companies[i])
		if err != nil {
			t.Fatalf("Failed to insert company %d: %v", i, err)
		}
	}
}

func TestNewService(t *testing.T) {
	config := &configs.Config{
		DatabasePath: ":memory:",
	}

	service, err := NewService(config)
	if err != nil {
		t.Errorf("NewService() failed: %v", err)
	}

	if service == nil {
		t.Error("NewService() returned nil")
	}

	service.Close()
}

func TestServiceGetFilteredCompanies(t *testing.T) {
	service, config := setupTestService(t)
	defer service.Close()

	insertTestCompanies(t, service)

	// Test with price filter enabled
	companies, err := service.GetFilteredCompanies()
	if err != nil {
		t.Errorf("GetFilteredCompanies() failed: %v", err)
	}

	// Should return only MID1.T and MID2.T (within price range)
	if len(companies) != 2 {
		t.Errorf("GetFilteredCompanies() returned %d companies, want 2", len(companies))
	}

	// Check that returned companies are within price range
	for _, company := range companies {
		if company.Price == nil {
			t.Error("Filtered company should have a price")
			continue
		}
		price := *company.Price
		if price < config.MinStockPrice || price > config.MaxStockPrice {
			t.Errorf("Company %s price %.2f is outside filter range %.2f-%.2f",
				company.Symbol, price, config.MinStockPrice, config.MaxStockPrice)
		}
	}
}

func TestServiceGetFilteredCompaniesDisabled(t *testing.T) {
	service, config := setupTestService(t)
	defer service.Close()
	
	// Disable price filter
	config.PriceFilterEnabled = false

	insertTestCompanies(t, service)

	companies, err := service.GetFilteredCompanies()
	if err != nil {
		t.Errorf("GetFilteredCompanies() failed: %v", err)
	}

	// Should return all companies when filter is disabled
	if len(companies) != 5 {
		t.Errorf("GetFilteredCompanies() with filter disabled returned %d companies, want 5", len(companies))
	}
}

func TestServiceGetCompaniesByMarket(t *testing.T) {
	service, _ := setupTestService(t)
	defer service.Close()

	insertTestCompanies(t, service)

	// Test filtering by Prime market
	primeCompanies, err := service.GetCompaniesByMarket("東P")
	if err != nil {
		t.Errorf("GetCompaniesByMarket() failed: %v", err)
	}

	expectedPrime := 3 // LOW.T, MID1.T, NO_PRICE.T
	if len(primeCompanies) != expectedPrime {
		t.Errorf("GetCompaniesByMarket('東P') returned %d companies, want %d", len(primeCompanies), expectedPrime)
	}

	// Test filtering by Standard market
	standardCompanies, err := service.GetCompaniesByMarket("東S")
	if err != nil {
		t.Errorf("GetCompaniesByMarket() failed: %v", err)
	}

	expectedStandard := 1 // MID2.T
	if len(standardCompanies) != expectedStandard {
		t.Errorf("GetCompaniesByMarket('東S') returned %d companies, want %d", len(standardCompanies), expectedStandard)
	}
}

func TestServiceGetCompaniesWithPriceAndMarketFilter(t *testing.T) {
	service, _ := setupTestService(t)
	defer service.Close()

	insertTestCompanies(t, service)

	// Test combined filtering
	companies, err := service.GetCompaniesWithPriceAndMarketFilter("東P", 100.0, 1000.0)
	if err != nil {
		t.Errorf("GetCompaniesWithPriceAndMarketFilter() failed: %v", err)
	}

	// Should return only MID1.T (東P market, within price range 100-1000)
	if len(companies) != 1 {
		t.Errorf("GetCompaniesWithPriceAndMarketFilter() returned %d companies, want 1", len(companies))
	}

	if len(companies) > 0 && companies[0].Symbol != "MID1.T" {
		t.Errorf("GetCompaniesWithPriceAndMarketFilter() returned wrong company: %s", companies[0].Symbol)
	}
}

func TestServiceGetCompanyCount(t *testing.T) {
	service, _ := setupTestService(t)
	defer service.Close()

	// Test empty database
	count, err := service.GetCompanyCount()
	if err != nil {
		t.Errorf("GetCompanyCount() failed: %v", err)
	}
	if count != 0 {
		t.Errorf("GetCompanyCount() on empty database = %d, want 0", count)
	}

	insertTestCompanies(t, service)

	// Test with data
	count, err = service.GetCompanyCount()
	if err != nil {
		t.Errorf("GetCompanyCount() failed: %v", err)
	}
	if count != 5 {
		t.Errorf("GetCompanyCount() = %d, want 5", count)
	}
}

func TestServiceValidateConnection(t *testing.T) {
	service, _ := setupTestService(t)
	defer service.Close()

	err := service.ValidateConnection()
	if err != nil {
		t.Errorf("ValidateConnection() failed: %v", err)
	}
}

func TestServiceGetStatistics(t *testing.T) {
	service, _ := setupTestService(t)
	defer service.Close()

	insertTestCompanies(t, service)

	stats, err := service.GetStatistics()
	if err != nil {
		t.Errorf("GetStatistics() failed: %v", err)
	}

	if stats.TotalCompanies != 5 {
		t.Errorf("GetStatistics() TotalCompanies = %d, want 5", stats.TotalCompanies)
	}

	if stats.CompaniesWithPrice != 4 {
		t.Errorf("GetStatistics() CompaniesWithPrice = %d, want 4", stats.CompaniesWithPrice)
	}

	expectedMarkets := map[string]int{
		"東P": 3,
		"東S": 1, 
		"東G": 1,
	}

	for market, expectedCount := range expectedMarkets {
		if actualCount, exists := stats.MarketDistribution[market]; !exists || actualCount != expectedCount {
			t.Errorf("GetStatistics() MarketDistribution[%s] = %d, want %d", market, actualCount, expectedCount)
		}
	}
}