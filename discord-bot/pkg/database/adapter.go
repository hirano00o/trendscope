package database

import (
	"fmt"

	"github.com/hirano00o/trendscope/discord-bot/pkg/csv"
)

// StockAdapter provides compatibility layer between database Company and CSV Stock
//
// @description データベースのCompanyとCSV StockReader間の互換性レイヤー
// 既存のCSV読み込みワークフローを変更せずにSQLiteデータを使用可能にする
//
// @example
// ```go
// companies := []Company{{Symbol: "7203.T", Name: "トヨタ自動車"}}
// adapter := NewStockAdapter(companies)
// stocks := adapter.GetStocks()
// symbols := adapter.GetSymbols()
// ```
type StockAdapter struct {
	// companies holds the original company data
	companies []Company
	// stocks holds the converted stock data
	stocks []*csv.Stock
}

// NewStockAdapter creates a new stock adapter
//
// @description 新しいStockAdapterインスタンスを作成する
// Company配列をcsv.Stock配列に変換し、既存のワークフローとの互換性を提供
//
// @param {[]Company} companies 変換する企業データの配列
// @returns {*StockAdapter} アダプターインスタンス
//
// @example
// ```go
// companies, _ := service.GetFilteredCompanies()
// adapter := NewStockAdapter(companies)
// 
// // 既存のコードがそのまま使える
// stocks := adapter.GetStocks()
// for _, stock := range stocks {
//     fmt.Printf("Processing %s (%s)\n", stock.GetSymbol(), stock.Name)
// }
// ```
func NewStockAdapter(companies []Company) *StockAdapter {
	stocks := CompaniesToStocks(companies)
	return &StockAdapter{
		companies: companies,
		stocks:    stocks,
	}
}

// GetStocks returns the converted stock array
//
// @description 変換された株式配列を取得する
// csv.ReadStocksFromCSV()の戻り値と同じ形式
//
// @returns {[]*csv.Stock} CSV株式データの配列
//
// @example
// ```go
// adapter := NewStockAdapter(companies)
// stocks := adapter.GetStocks()
// 
// // 既存のコードと互換
// for _, stock := range stocks {
//     symbol := stock.GetSymbol()
//     // ... existing processing logic
// }
// ```
func (sa *StockAdapter) GetStocks() []*csv.Stock {
	return sa.stocks
}

// GetSymbols returns array of stock symbols
//
// @description 株式シンボルの配列を取得する
// csv.GetStockSymbols()と同等の機能
//
// @returns {[]string} 株式シンボルの配列
//
// @example
// ```go
// adapter := NewStockAdapter(companies)
// symbols := adapter.GetSymbols()
// // ["7203.T", "1332.T", ...]
// ```
func (sa *StockAdapter) GetSymbols() []string {
	symbols := make([]string, len(sa.stocks))
	for i, stock := range sa.stocks {
		symbols[i] = stock.GetSymbol()
	}
	return symbols
}

// Count returns the number of stocks
//
// @description 株式数を取得する
//
// @returns {int} 株式数
func (sa *StockAdapter) Count() int {
	return len(sa.stocks)
}

// GetCompanies returns the original company data
//
// @description 元の企業データを取得する
// デバッグや詳細情報アクセス用
//
// @returns {[]Company} 企業データの配列
func (sa *StockAdapter) GetCompanies() []Company {
	return sa.companies
}

// CompanyToStock converts a Company to csv.Stock
//
// @description Company構造体をcsv.Stock構造体に変換する
// 価格情報の適切な変換とフォーマットを行う
//
// @param {Company} company 変換する企業データ
// @returns {*csv.Stock} 変換されたCSV株式データ
//
// @example
// ```go
// company := Company{Symbol: "7203.T", Name: "トヨタ自動車", Price: &price}
// stock := CompanyToStock(company)
// fmt.Printf("Stock: %s (%s) - %s\n", stock.Code, stock.Name, stock.CurrentValue)
// ```
func CompanyToStock(company Company) *csv.Stock {
	// Extract stock code from symbol (remove exchange suffix)
	code := company.GetCode()

	// Format current value
	var currentValue string
	if company.HasPrice() {
		currentValue = fmt.Sprintf("%.2f", *company.Price)
	} else {
		currentValue = "N/A"
	}

	// Create CSV Stock with compatibility
	stock := &csv.Stock{
		Code:         code,
		Name:         company.Name,
		Market:       company.Market,
		CurrentValue: currentValue,
		ChangeRate:   "", // Not available from database
	}

	return stock
}

// CompaniesToStocks converts a slice of Company to slice of csv.Stock
//
// @description Company配列をcsv.Stock配列に一括変換する
//
// @param {[]Company} companies 変換する企業データの配列
// @returns {[]*csv.Stock} 変換されたCSV株式データの配列
//
// @example
// ```go
// companies, _ := service.GetFilteredCompanies()
// stocks := CompaniesToStocks(companies)
// 
// // 既存のワークフローで使用
// for _, stock := range stocks {
//     requests = append(requests, api.AnalysisRequest{
//         Symbol:      stock.GetSymbol(),
//         CompanyName: stock.Name,
//     })
// }
// ```
func CompaniesToStocks(companies []Company) []*csv.Stock {
	if len(companies) == 0 {
		return []*csv.Stock{}
	}

	stocks := make([]*csv.Stock, len(companies))
	for i, company := range companies {
		stocks[i] = CompanyToStock(company)
	}

	return stocks
}

// CreateAnalysisRequests creates analysis requests from companies
//
// @description 企業データから分析リクエストを作成する
// 既存のcreateAnalysisRequests関数との互換性を提供
//
// @param {[]Company} companies 分析対象の企業データ
// @returns {[]AnalysisRequest} 分析リクエストの配列（仮の型）
//
// @example
// ```go
// companies, _ := service.GetFilteredCompanies()
// requests := CreateAnalysisRequests(companies)
// ```
func CreateAnalysisRequests(companies []Company) []AnalysisRequest {
	if len(companies) == 0 {
		return []AnalysisRequest{}
	}

	requests := make([]AnalysisRequest, len(companies))
	for i, company := range companies {
		requests[i] = AnalysisRequest{
			Symbol:      company.GetSymbol(),
			CompanyName: company.Name,
		}
	}

	return requests
}

// AnalysisRequest represents a stock analysis request
//
// @description 株式分析リクエストを表現する構造体
// 既存のapi.AnalysisRequestとの互換性を提供
type AnalysisRequest struct {
	// Symbol is the stock symbol for API calls
	Symbol string
	// CompanyName is the company name
	CompanyName string
}

// DatabaseSourceInfo provides information about the data source
//
// @description データソース情報を提供する構造体
type DatabaseSourceInfo struct {
	// TotalCompanies is the total number of companies in the database
	TotalCompanies int
	// FilteredCompanies is the number of companies after filtering
	FilteredCompanies int
	// FilterCriteria describes the applied filters
	FilterCriteria string
	// DatabasePath is the path to the database
	DatabasePath string
}

// GetSourceInfo returns information about the data source
//
// @description データソースの情報を取得する
// デバッグやログ出力用の詳細情報
//
// @param {*Service} service データベースサービス
// @returns {DatabaseSourceInfo} データソース情報
//
// @example
// ```go
// adapter := NewStockAdapter(companies)
// info := GetSourceInfo(service)
// fmt.Printf("Loaded %d companies from %s\n", info.FilteredCompanies, info.DatabasePath)
// ```
func GetSourceInfo(service *Service) DatabaseSourceInfo {
	if service == nil {
		return DatabaseSourceInfo{}
	}

	config := service.GetConfig()
	totalCount, _ := service.GetCompanyCount()

	var filterCriteria string
	if config.IsPriceFilterEnabled() {
		minPrice, maxPrice := config.GetPriceRange()
		filterCriteria = fmt.Sprintf("Price: %.2f-%.2f", minPrice, maxPrice)
	} else {
		filterCriteria = "No filters"
	}

	return DatabaseSourceInfo{
		TotalCompanies:    totalCount,
		FilteredCompanies: -1, // Will be set by caller
		FilterCriteria:    filterCriteria,
		DatabasePath:      config.DatabasePath,
	}
}

// ValidateStockCompatibility validates that converted stocks are compatible
//
// @description 変換された株式データの互換性を検証する
//
// @param {[]*csv.Stock} stocks 検証する株式データ
// @throws {error} 互換性に問題がある場合
//
// @example
// ```go
// stocks := CompaniesToStocks(companies)
// if err := ValidateStockCompatibility(stocks); err != nil {
//     log.Printf("Compatibility issue: %v", err)
// }
// ```
func ValidateStockCompatibility(stocks []*csv.Stock) error {
	if len(stocks) == 0 {
		return nil // Empty is valid
	}

	for i, stock := range stocks {
		if stock == nil {
			return fmt.Errorf("stock at index %d is nil", i)
		}

		if stock.Code == "" {
			return fmt.Errorf("stock at index %d has empty code", i)
		}

		if stock.Name == "" {
			return fmt.Errorf("stock at index %d has empty name", i)
		}

		// Test GetSymbol method
		symbol := stock.GetSymbol()
		if symbol == "" {
			return fmt.Errorf("stock at index %d GetSymbol() returns empty", i)
		}
	}

	return nil
}