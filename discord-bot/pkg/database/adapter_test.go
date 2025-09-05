package database

import (
	"testing"

	"github.com/hirano00o/trendscope/discord-bot/pkg/csv"
)

func TestCompanyToStock(t *testing.T) {
	price := 2500.0
	company := Company{
		Symbol: "7203.T",
		Name:   "トヨタ自動車",
		Market: "東P",
		Price:  &price,
	}

	stock := CompanyToStock(company)

	if stock.Code != "7203" {
		t.Errorf("CompanyToStock() Code = %v, want %v", stock.Code, "7203")
	}

	if stock.Name != company.Name {
		t.Errorf("CompanyToStock() Name = %v, want %v", stock.Name, company.Name)
	}

	if stock.Market != company.Market {
		t.Errorf("CompanyToStock() Market = %v, want %v", stock.Market, company.Market)
	}

	expectedValue := "2500.00"
	if stock.CurrentValue != expectedValue {
		t.Errorf("CompanyToStock() CurrentValue = %v, want %v", stock.CurrentValue, expectedValue)
	}

	// Test GetSymbol compatibility
	if stock.GetSymbol() != company.Symbol {
		t.Errorf("Stock.GetSymbol() = %v, want %v", stock.GetSymbol(), company.Symbol)
	}
}

func TestCompanyToStockWithoutPrice(t *testing.T) {
	company := Company{
		Symbol: "1332.T",
		Name:   "ニッスイ",
		Market: "東P",
		Price:  nil, // No price
	}

	stock := CompanyToStock(company)

	if stock.CurrentValue != "N/A" {
		t.Errorf("CompanyToStock() with no price CurrentValue = %v, want %v", stock.CurrentValue, "N/A")
	}

	if stock.ChangeRate != "" {
		t.Errorf("CompanyToStock() with no price ChangeRate = %v, want empty", stock.ChangeRate)
	}
}

func TestCompaniesToStocks(t *testing.T) {
	companies := []Company{
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
			Symbol: "NO_PRICE.T",
			Name:   "No Price Stock",
			Market: "東S",
			Price:  nil,
		},
	}

	stocks := CompaniesToStocks(companies)

	if len(stocks) != len(companies) {
		t.Errorf("CompaniesToStocks() returned %d stocks, want %d", len(stocks), len(companies))
	}

	// Test first stock
	if stocks[0].Code != "7203" {
		t.Errorf("CompaniesToStocks() first stock Code = %v, want %v", stocks[0].Code, "7203")
	}

	if stocks[0].GetSymbol() != "7203.T" {
		t.Errorf("CompaniesToStocks() first stock GetSymbol() = %v, want %v", stocks[0].GetSymbol(), "7203.T")
	}

	// Test stock with no price
	if stocks[2].CurrentValue != "N/A" {
		t.Errorf("CompaniesToStocks() stock without price CurrentValue = %v, want %v", stocks[2].CurrentValue, "N/A")
	}
}

func TestStockAdapter(t *testing.T) {
	companies := []Company{
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
	}

	adapter := NewStockAdapter(companies)

	if adapter == nil {
		t.Error("NewStockAdapter() returned nil")
	}

	stocks := adapter.GetStocks()
	if len(stocks) != len(companies) {
		t.Errorf("StockAdapter.GetStocks() returned %d stocks, want %d", len(stocks), len(companies))
	}

	symbols := adapter.GetSymbols()
	if len(symbols) != len(companies) {
		t.Errorf("StockAdapter.GetSymbols() returned %d symbols, want %d", len(symbols), len(companies))
	}

	expectedSymbols := []string{"7203.T", "1332.T"}
	for i, symbol := range symbols {
		if symbol != expectedSymbols[i] {
			t.Errorf("StockAdapter.GetSymbols()[%d] = %v, want %v", i, symbol, expectedSymbols[i])
		}
	}

	count := adapter.Count()
	if count != len(companies) {
		t.Errorf("StockAdapter.Count() = %d, want %d", count, len(companies))
	}
}

func TestStockAdapterEmpty(t *testing.T) {
	adapter := NewStockAdapter([]Company{})

	stocks := adapter.GetStocks()
	if len(stocks) != 0 {
		t.Errorf("Empty StockAdapter.GetStocks() returned %d stocks, want 0", len(stocks))
	}

	symbols := adapter.GetSymbols()
	if len(symbols) != 0 {
		t.Errorf("Empty StockAdapter.GetSymbols() returned %d symbols, want 0", len(symbols))
	}

	count := adapter.Count()
	if count != 0 {
		t.Errorf("Empty StockAdapter.Count() = %d, want 0", count)
	}
}

func TestStockCompatibility(t *testing.T) {
	// Test that our adapted stocks work with existing functions that expect csv.Stock
	company := Company{
		Symbol: "7203.T",
		Name:   "トヨタ自動車",
		Market: "東P",
		Price:  float64Ptr(2500.0),
	}

	stock := CompanyToStock(company)

	// Test that it implements the same interface as csv.Stock
	testStockInterface(t, *stock)
}

// testStockInterface tests that a stock implements the expected interface
func testStockInterface(t *testing.T, stock csv.Stock) {
	t.Helper()

	// Test GetSymbol method
	symbol := stock.GetSymbol()
	if symbol == "" {
		t.Error("Stock.GetSymbol() returned empty string")
	}

	// Test that all required fields are accessible
	if stock.Code == "" {
		t.Error("Stock.Code is empty")
	}

	if stock.Name == "" {
		t.Error("Stock.Name is empty")
	}

	// Market and other fields can be empty, so we don't test them
}

func TestExchangeCodeExtraction(t *testing.T) {
	tests := []struct {
		symbol       string
		expectedCode string
	}{
		{"7203.T", "7203"},
		{"1332.T", "1332"},
		{"3698.S", "3698"},
		{"AAPL", "AAPL"},
		{"", ""},
		{"123", "123"},
		{"123.T.EXTRA", "123"}, // Should take first part
	}

	for _, tt := range tests {
		t.Run(tt.symbol, func(t *testing.T) {
			company := Company{Symbol: tt.symbol}
			stock := CompanyToStock(company)
			if stock.Code != tt.expectedCode {
				t.Errorf("CompanyToStock(%s) Code = %v, want %v", tt.symbol, stock.Code, tt.expectedCode)
			}
		})
	}
}