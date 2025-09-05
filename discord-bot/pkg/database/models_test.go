package database

import (
	"testing"
	"time"
)

func TestCompanyValidation(t *testing.T) {
	tests := []struct {
		name    string
		company Company
		valid   bool
	}{
		{
			name: "Valid company with all fields",
			company: Company{
				ID:              1,
				Symbol:          "7203.T",
				Name:            "トヨタ自動車",
				Market:          "東P",
				BusinessSummary: stringPtr("自動車製造業"),
				Price:           float64Ptr(2500.0),
				LastUpdated:     timePtr(time.Now()),
				CreatedAt:       timePtr(time.Now()),
			},
			valid: true,
		},
		{
			name: "Valid company with minimal fields",
			company: Company{
				Symbol: "1332.T",
				Name:   "ニッスイ",
			},
			valid: true,
		},
		{
			name: "Invalid company - empty symbol",
			company: Company{
				Symbol: "",
				Name:   "Test Company",
			},
			valid: false,
		},
		{
			name: "Invalid company - empty name",
			company: Company{
				Symbol: "1234.T",
				Name:   "",
			},
			valid: false,
		},
		{
			name: "Invalid company - negative price",
			company: Company{
				Symbol: "1234.T",
				Name:   "Test Company",
				Price:  float64Ptr(-100.0),
			},
			valid: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.company.Validate()
			if tt.valid && err != nil {
				t.Errorf("Validate() expected valid but got error: %v", err)
			}
			if !tt.valid && err == nil {
				t.Errorf("Validate() expected invalid but got no error")
			}
		})
	}
}

func TestCompanyGetSymbol(t *testing.T) {
	company := Company{
		Symbol: "7203.T",
		Name:   "トヨタ自動車",
	}

	symbol := company.GetSymbol()
	expected := "7203.T"
	if symbol != expected {
		t.Errorf("GetSymbol() = %v, want %v", symbol, expected)
	}
}

func TestCompanyGetCode(t *testing.T) {
	tests := []struct {
		name     string
		symbol   string
		expected string
	}{
		{
			name:     "Tokyo Stock Exchange",
			symbol:   "7203.T",
			expected: "7203",
		},
		{
			name:     "Sapporo Stock Exchange",
			symbol:   "3698.S",
			expected: "3698",
		},
		{
			name:     "Symbol without exchange",
			symbol:   "1234",
			expected: "1234",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			company := Company{Symbol: tt.symbol}
			code := company.GetCode()
			if code != tt.expected {
				t.Errorf("GetCode() = %v, want %v", code, tt.expected)
			}
		})
	}
}

func TestCompanyMarketType(t *testing.T) {
	tests := []struct {
		name     string
		market   string
		expected MarketType
	}{
		{
			name:     "Prime market",
			market:   "東P",
			expected: MarketTypePrime,
		},
		{
			name:     "Standard market",
			market:   "東S",
			expected: MarketTypeStandard,
		},
		{
			name:     "Growth market",
			market:   "東G",
			expected: MarketTypeGrowth,
		},
		{
			name:     "Unknown market",
			market:   "未知",
			expected: MarketTypeOther,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			company := Company{Market: tt.market}
			marketType := company.GetMarketType()
			if marketType != tt.expected {
				t.Errorf("GetMarketType() = %v, want %v", marketType, tt.expected)
			}
		})
	}
}

func TestCompanySetTimestamps(t *testing.T) {
	company := Company{
		Symbol: "7203.T",
		Name:   "トヨタ自動車",
	}

	now := time.Now()
	company.SetTimestamps(now, now)

	if company.CreatedAt == nil {
		t.Errorf("SetTimestamps() CreatedAt is nil")
	}
	if company.LastUpdated == nil {
		t.Errorf("SetTimestamps() LastUpdated is nil")
	}

	if !company.CreatedAt.Equal(now) {
		t.Errorf("SetTimestamps() CreatedAt = %v, want %v", company.CreatedAt, now)
	}
	if !company.LastUpdated.Equal(now) {
		t.Errorf("SetTimestamps() LastUpdated = %v, want %v", company.LastUpdated, now)
	}
}

// Helper functions for test data
func stringPtr(s string) *string {
	return &s
}

func float64Ptr(f float64) *float64 {
	return &f
}

func timePtr(t time.Time) *time.Time {
	return &t
}