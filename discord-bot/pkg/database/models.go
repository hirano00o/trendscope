package database

import (
	"fmt"
	"strings"
	"time"
)

// MarketType represents different stock market types
//
// @description 株式市場区分を表現する列挙型
// 東京証券取引所の市場区分（プライム、スタンダード、グロース等）を分類
type MarketType int

const (
	// MarketTypePrime represents Prime Market (プライム市場)
	MarketTypePrime MarketType = iota
	// MarketTypeStandard represents Standard Market (スタンダード市場)
	MarketTypeStandard
	// MarketTypeGrowth represents Growth Market (グロース市場)
	MarketTypeGrowth
	// MarketTypeOther represents other markets
	MarketTypeOther
)

// String returns the string representation of MarketType
//
// @description MarketTypeの文字列表現を返す
//
// @returns {string} 市場区分の文字列
func (m MarketType) String() string {
	switch m {
	case MarketTypePrime:
		return "Prime"
	case MarketTypeStandard:
		return "Standard"
	case MarketTypeGrowth:
		return "Growth"
	default:
		return "Other"
	}
}

// Company represents a stock company with comprehensive information
//
// @description 株式企業の包括的な情報を表現する構造体
// stock-db-batchのPydanticモデルとの互換性を保ちつつ、
// Go言語での使用に最適化された設計
//
// @example
// ```go
// company := Company{
//     Symbol: "7203.T",
//     Name:   "トヨタ自動車",
//     Market: "東P",
//     Price:  &price,
// }
// ```
type Company struct {
	// ID is the database primary key
	ID int `db:"id" json:"id"`

	// Symbol is the yfinance-compatible stock symbol (e.g., "7203.T")
	Symbol string `db:"symbol" json:"symbol"`

	// Name is the company name
	Name string `db:"name" json:"name"`

	// Market is the market segment (e.g., "東P", "東S", "東G")
	Market string `db:"market" json:"market"`

	// BusinessSummary is the business description in Japanese
	BusinessSummary *string `db:"business_summary" json:"business_summary"`

	// Price is the current stock price
	Price *float64 `db:"price" json:"price"`

	// LastUpdated is the last update timestamp
	LastUpdated *time.Time `db:"last_updated" json:"last_updated"`

	// CreatedAt is the creation timestamp
	CreatedAt *time.Time `db:"created_at" json:"created_at"`
}

// Validate validates the Company data
//
// @description 企業データの妥当性を検証する
// 必須フィールドの存在、価格の妥当性等をチェック
//
// @throws {error} データが無効な場合
//
// @example
// ```go
// company := Company{Symbol: "7203.T", Name: "トヨタ自動車"}
// if err := company.Validate(); err != nil {
//     log.Printf("Invalid company data: %v", err)
// }
// ```
func (c *Company) Validate() error {
	if strings.TrimSpace(c.Symbol) == "" {
		return fmt.Errorf("symbol cannot be empty")
	}

	if strings.TrimSpace(c.Name) == "" {
		return fmt.Errorf("name cannot be empty")
	}

	if c.Price != nil && *c.Price < 0 {
		return fmt.Errorf("price cannot be negative: %f", *c.Price)
	}

	return nil
}

// GetSymbol returns the stock symbol for API calls
//
// @description API呼び出し用の株式シンボルを取得する
// csv.StockのGetSymbol()メソッドとの互換性を保つ
//
// @returns {string} yfinance形式の株式シンボル
//
// @example
// ```go
// company := Company{Symbol: "7203.T"}
// symbol := company.GetSymbol() // "7203.T"
// ```
func (c *Company) GetSymbol() string {
	return c.Symbol
}

// GetCode extracts the stock code from the symbol
//
// @description シンボルから株式コード部分を抽出する
// "7203.T" → "7203" のように取引所識別子を除去
//
// @returns {string} 株式コード
//
// @example
// ```go
// company := Company{Symbol: "7203.T"}
// code := company.GetCode() // "7203"
// ```
func (c *Company) GetCode() string {
	parts := strings.Split(c.Symbol, ".")
	return parts[0]
}

// GetMarketType returns the market type based on the market string
//
// @description 市場区分文字列から MarketType を判定する
//
// @returns {MarketType} 市場区分の列挙値
//
// @example
// ```go
// company := Company{Market: "東P"}
// marketType := company.GetMarketType() // MarketTypePrime
// ```
func (c *Company) GetMarketType() MarketType {
	switch c.Market {
	case "東P":
		return MarketTypePrime
	case "東S":
		return MarketTypeStandard
	case "東G":
		return MarketTypeGrowth
	default:
		return MarketTypeOther
	}
}

// HasPrice checks if the company has a valid price
//
// @description 企業が有効な価格情報を持っているかチェックする
//
// @returns {bool} 有効な価格を持つ場合true
//
// @example
// ```go
// if company.HasPrice() {
//     fmt.Printf("Price: %.2f", *company.Price)
// }
// ```
func (c *Company) HasPrice() bool {
	return c.Price != nil && *c.Price > 0
}

// SetTimestamps sets the created and updated timestamps
//
// @description 作成日時と更新日時を設定する
//
// @param {time.Time} createdAt 作成日時
// @param {time.Time} updatedAt 更新日時
//
// @example
// ```go
// now := time.Now()
// company.SetTimestamps(now, now)
// ```
func (c *Company) SetTimestamps(createdAt, updatedAt time.Time) {
	c.CreatedAt = &createdAt
	c.LastUpdated = &updatedAt
}

// String returns a string representation of the Company
//
// @description Company構造体の文字列表現を返す
//
// @returns {string} 企業情報の文字列
func (c *Company) String() string {
	priceStr := "N/A"
	if c.Price != nil {
		priceStr = fmt.Sprintf("%.2f", *c.Price)
	}

	return fmt.Sprintf("Company{Symbol: %s, Name: %s, Market: %s, Price: %s}",
		c.Symbol, c.Name, c.Market, priceStr)
}

// Clone creates a deep copy of the Company
//
// @description Company構造体の深いコピーを作成する
//
// @returns {Company} コピーされた企業情報
//
// @example
// ```go
// original := Company{Symbol: "7203.T", Name: "トヨタ自動車"}
// copy := original.Clone()
// ```
func (c *Company) Clone() Company {
	clone := Company{
		ID:     c.ID,
		Symbol: c.Symbol,
		Name:   c.Name,
		Market: c.Market,
	}

	if c.BusinessSummary != nil {
		summary := *c.BusinessSummary
		clone.BusinessSummary = &summary
	}

	if c.Price != nil {
		price := *c.Price
		clone.Price = &price
	}

	if c.LastUpdated != nil {
		updated := *c.LastUpdated
		clone.LastUpdated = &updated
	}

	if c.CreatedAt != nil {
		created := *c.CreatedAt
		clone.CreatedAt = &created
	}

	return clone
}

// CompanyList represents a collection of companies with utility methods
//
// @description 企業のコレクションと便利なメソッドを提供する
type CompanyList []Company

// FilterByPriceRange filters companies by price range
//
// @description 価格範囲で企業をフィルタリングする
//
// @param {float64} minPrice 最小価格
// @param {float64} maxPrice 最大価格
// @returns {CompanyList} フィルタリング結果
//
// @example
// ```go
// companies := CompanyList{...}
// filtered := companies.FilterByPriceRange(100.0, 5000.0)
// ```
func (cl CompanyList) FilterByPriceRange(minPrice, maxPrice float64) CompanyList {
	var filtered CompanyList
	for _, company := range cl {
		if company.HasPrice() {
			price := *company.Price
			if price >= minPrice && price <= maxPrice {
				filtered = append(filtered, company)
			}
		}
	}
	return filtered
}

// FilterByMarket filters companies by market type
//
// @description 市場区分で企業をフィルタリングする
//
// @param {string} market 市場区分
// @returns {CompanyList} フィルタリング結果
func (cl CompanyList) FilterByMarket(market string) CompanyList {
	var filtered CompanyList
	for _, company := range cl {
		if company.Market == market {
			filtered = append(filtered, company)
		}
	}
	return filtered
}

// Symbols returns a slice of symbols from the company list
//
// @description 企業リストから株式シンボルの配列を取得する
//
// @returns {[]string} 株式シンボルの配列
//
// @example
// ```go
// companies := CompanyList{...}
// symbols := companies.Symbols() // ["7203.T", "1332.T", ...]
// ```
func (cl CompanyList) Symbols() []string {
	symbols := make([]string, len(cl))
	for i, company := range cl {
		symbols[i] = company.Symbol
	}
	return symbols
}