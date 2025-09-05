package database

import (
	"testing"
	"time"
)

func setupTestRepository(t *testing.T) *Repository {
	t.Helper()
	
	conn, err := NewConnection(":memory:")
	if err != nil {
		t.Fatalf("Failed to create connection: %v", err)
	}

	if err := conn.Connect(); err != nil {
		t.Fatalf("Failed to connect: %v", err)
	}

	repo, err := NewRepository(conn)
	if err != nil {
		t.Fatalf("Failed to create repository: %v", err)
	}

	if err := repo.CreateTables(); err != nil {
		t.Fatalf("Failed to create tables: %v", err)
	}

	return repo
}

func createTestCompany() Company {
	price := 2500.0
	now := time.Now()
	
	return Company{
		Symbol:          "7203.T",
		Name:            "トヨタ自動車",
		Market:          "東P",
		BusinessSummary: stringPtr("自動車製造業"),
		Price:           &price,
		CreatedAt:       &now,
		LastUpdated:     &now,
	}
}

func TestRepositoryCreateTables(t *testing.T) {
	conn, err := NewConnection(":memory:")
	if err != nil {
		t.Fatalf("Failed to create connection: %v", err)
	}

	if err := conn.Connect(); err != nil {
		t.Fatalf("Failed to connect: %v", err)
	}
	defer conn.Close()

	repo, err := NewRepository(conn)
	if err != nil {
		t.Fatalf("Failed to create repository: %v", err)
	}

	if err := repo.CreateTables(); err != nil {
		t.Errorf("CreateTables() failed: %v", err)
	}

	// Test table exists
	db, _ := conn.DB()
	rows, err := db.Query("SELECT name FROM sqlite_master WHERE type='table' AND name='company'")
	if err != nil {
		t.Errorf("Failed to query table existence: %v", err)
	}
	defer rows.Close()

	if !rows.Next() {
		t.Error("Company table was not created")
	}
}

func TestRepositoryInsert(t *testing.T) {
	repo := setupTestRepository(t)
	defer repo.Close()

	company := createTestCompany()

	id, err := repo.Insert(&company)
	if err != nil {
		t.Errorf("Insert() failed: %v", err)
	}

	if id <= 0 {
		t.Errorf("Insert() returned invalid ID: %d", id)
	}

	// Test duplicate insert
	_, err = repo.Insert(&company)
	if err == nil {
		t.Error("Insert() should fail on duplicate symbol")
	}
}

func TestRepositoryGetBySymbol(t *testing.T) {
	repo := setupTestRepository(t)
	defer repo.Close()

	company := createTestCompany()
	_, err := repo.Insert(&company)
	if err != nil {
		t.Fatalf("Failed to insert test company: %v", err)
	}

	// Test successful retrieval
	retrieved, err := repo.GetBySymbol(company.Symbol)
	if err != nil {
		t.Errorf("GetBySymbol() failed: %v", err)
	}

	if retrieved == nil {
		t.Error("GetBySymbol() returned nil")
		return
	}

	if retrieved.Symbol != company.Symbol {
		t.Errorf("GetBySymbol() symbol = %v, want %v", retrieved.Symbol, company.Symbol)
	}
	if retrieved.Name != company.Name {
		t.Errorf("GetBySymbol() name = %v, want %v", retrieved.Name, company.Name)
	}

	// Test non-existent symbol
	nonExistent, err := repo.GetBySymbol("NONEXISTENT.T")
	if err != nil {
		t.Errorf("GetBySymbol() for non-existent symbol failed: %v", err)
	}
	if nonExistent != nil {
		t.Error("GetBySymbol() should return nil for non-existent symbol")
	}
}

func TestRepositoryUpdate(t *testing.T) {
	repo := setupTestRepository(t)
	defer repo.Close()

	company := createTestCompany()
	id, err := repo.Insert(&company)
	if err != nil {
		t.Fatalf("Failed to insert test company: %v", err)
	}

	// Update the company
	newPrice := 3000.0
	company.ID = id
	company.Price = &newPrice
	company.Name = "トヨタ自動車株式会社"

	err = repo.Update(&company)
	if err != nil {
		t.Errorf("Update() failed: %v", err)
	}

	// Verify update
	updated, err := repo.GetBySymbol(company.Symbol)
	if err != nil {
		t.Errorf("Failed to get updated company: %v", err)
	}

	if updated.Name != company.Name {
		t.Errorf("Update() name not updated: got %v, want %v", updated.Name, company.Name)
	}
	if updated.Price == nil || *updated.Price != *company.Price {
		t.Errorf("Update() price not updated: got %v, want %v", updated.Price, company.Price)
	}
}

func TestRepositoryDelete(t *testing.T) {
	repo := setupTestRepository(t)
	defer repo.Close()

	company := createTestCompany()
	_, err := repo.Insert(&company)
	if err != nil {
		t.Fatalf("Failed to insert test company: %v", err)
	}

	// Delete the company
	err = repo.Delete(company.Symbol)
	if err != nil {
		t.Errorf("Delete() failed: %v", err)
	}

	// Verify deletion
	deleted, err := repo.GetBySymbol(company.Symbol)
	if err != nil {
		t.Errorf("Failed to check deleted company: %v", err)
	}
	if deleted != nil {
		t.Error("Delete() did not remove the company")
	}

	// Test deleting non-existent company
	err = repo.Delete("NONEXISTENT.T")
	if err != nil {
		t.Errorf("Delete() should not fail for non-existent symbol: %v", err)
	}
}

func TestRepositoryGetAll(t *testing.T) {
	repo := setupTestRepository(t)
	defer repo.Close()

	// Insert multiple companies
	companies := []Company{
		createTestCompany(),
		{
			Symbol: "1332.T",
			Name:   "ニッスイ",
			Market: "東P",
		},
		{
			Symbol: "8267.T",
			Name:   "イオン",
			Market: "東P",
		},
	}

	for i := range companies {
		_, err := repo.Insert(&companies[i])
		if err != nil {
			t.Fatalf("Failed to insert company %d: %v", i, err)
		}
	}

	// Get all companies
	all, err := repo.GetAll()
	if err != nil {
		t.Errorf("GetAll() failed: %v", err)
	}

	if len(all) != len(companies) {
		t.Errorf("GetAll() returned %d companies, want %d", len(all), len(companies))
	}
}

func TestRepositoryFilterByPriceRange(t *testing.T) {
	repo := setupTestRepository(t)
	defer repo.Close()

	// Insert companies with different prices
	companies := []Company{
		{
			Symbol: "LOW.T",
			Name:   "Low Price Stock",
			Price:  float64Ptr(50.0),
		},
		{
			Symbol: "MID.T", 
			Name:   "Mid Price Stock",
			Price:  float64Ptr(500.0),
		},
		{
			Symbol: "HIGH.T",
			Name:   "High Price Stock", 
			Price:  float64Ptr(5000.0),
		},
		{
			Symbol: "NO_PRICE.T",
			Name:   "No Price Stock",
			Price:  nil,
		},
	}

	for i := range companies {
		_, err := repo.Insert(&companies[i])
		if err != nil {
			t.Fatalf("Failed to insert company %d: %v", i, err)
		}
	}

	// Test price filtering
	filtered, err := repo.FilterByPriceRange(100.0, 1000.0)
	if err != nil {
		t.Errorf("FilterByPriceRange() failed: %v", err)
	}

	// Should only return MID.T
	if len(filtered) != 1 {
		t.Errorf("FilterByPriceRange() returned %d companies, want 1", len(filtered))
	}

	if len(filtered) > 0 && filtered[0].Symbol != "MID.T" {
		t.Errorf("FilterByPriceRange() returned wrong company: %s", filtered[0].Symbol)
	}
}

func TestRepositoryFilterByMarket(t *testing.T) {
	repo := setupTestRepository(t)
	defer repo.Close()

	// Insert companies in different markets
	companies := []Company{
		{
			Symbol: "PRIME1.T",
			Name:   "Prime Stock 1",
			Market: "東P",
		},
		{
			Symbol: "PRIME2.T",
			Name:   "Prime Stock 2", 
			Market: "東P",
		},
		{
			Symbol: "STANDARD.T",
			Name:   "Standard Stock",
			Market: "東S",
		},
	}

	for i := range companies {
		_, err := repo.Insert(&companies[i])
		if err != nil {
			t.Fatalf("Failed to insert company %d: %v", i, err)
		}
	}

	// Test market filtering
	primeStocks, err := repo.FilterByMarket("東P")
	if err != nil {
		t.Errorf("FilterByMarket() failed: %v", err)
	}

	if len(primeStocks) != 2 {
		t.Errorf("FilterByMarket() returned %d companies, want 2", len(primeStocks))
	}
}