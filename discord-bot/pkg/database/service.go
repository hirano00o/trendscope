package database

import (
	"fmt"

	"github.com/hirano00o/trendscope/discord-bot/configs"
)

// Statistics represents database statistics
//
// @description データベースの統計情報を表現する構造体
type Statistics struct {
	// TotalCompanies is the total number of companies in the database
	TotalCompanies int `json:"total_companies"`
	// CompaniesWithPrice is the number of companies with valid price data
	CompaniesWithPrice int `json:"companies_with_price"`
	// MarketDistribution shows the distribution of companies by market
	MarketDistribution map[string]int `json:"market_distribution"`
	// AveragePrice is the average stock price (companies with price data only)
	AveragePrice float64 `json:"average_price"`
	// PriceRange shows the min and max prices
	PriceRange struct {
		Min float64 `json:"min"`
		Max float64 `json:"max"`
	} `json:"price_range"`
}

// Service provides high-level business logic for stock data operations
//
// @description 株式データ操作のための高レベルビジネスロジックを提供するサービス
// 設定に基づいたフィルタリング、統計情報の取得、データベース操作の抽象化
//
// @example
// ```go
// config := configs.Load()
// service, err := NewService(config)
// if err != nil {
//     log.Fatal(err)
// }
// defer service.Close()
//
// companies, err := service.GetFilteredCompanies()
// if err != nil {
//     log.Printf("Failed to get filtered companies: %v", err)
// }
// ```
type Service struct {
	// config holds the application configuration
	config *configs.Config
	// conn manages the database connection
	conn *Connection
	// repo provides CRUD operations
	repo *Repository
}

// NewService creates a new service instance
//
// @description 新しいサービスインスタンスを作成する
// 設定に基づいてデータベース接続を確立し、テーブルを作成する
//
// @param {*configs.Config} config アプリケーション設定
// @returns {*Service} サービスインスタンス
// @throws {error} サービスの初期化に失敗した場合
//
// @example
// ```go
// config := configs.Load()
// service, err := NewService(config)
// if err != nil {
//     log.Fatalf("Failed to create service: %v", err)
// }
// defer service.Close()
// ```
func NewService(config *configs.Config) (*Service, error) {
	if config == nil {
		return nil, fmt.Errorf("config cannot be nil")
	}

	// Create database connection
	conn, err := NewConnection(config.DatabasePath)
	if err != nil {
		return nil, fmt.Errorf("failed to create database connection: %w", err)
	}

	// Establish connection
	if err := conn.Connect(); err != nil {
		return nil, fmt.Errorf("failed to connect to database: %w", err)
	}

	// Create repository
	repo, err := NewRepository(conn)
	if err != nil {
		conn.Close()
		return nil, fmt.Errorf("failed to create repository: %w", err)
	}

	return &Service{
		config: config,
		conn:   conn,
		repo:   repo,
	}, nil
}

// GetFilteredCompanies retrieves companies based on configuration filters
//
// @description 設定に基づいてフィルタリングされた企業データを取得する
// 価格フィルタリングが有効な場合は価格範囲でフィルタリング、
// 無効な場合は全ての企業を返す
//
// @returns {[]Company} フィルタリングされた企業データのスライス
// @throws {error} データ取得に失敗した場合
//
// @example
// ```go
// companies, err := service.GetFilteredCompanies()
// if err != nil {
//     log.Printf("Failed to get filtered companies: %v", err)
//     return
// }
// fmt.Printf("Found %d companies matching filter criteria", len(companies))
// ```
func (s *Service) GetFilteredCompanies() ([]Company, error) {
	if s.config.IsPriceFilterEnabled() {
		minPrice, maxPrice := s.config.GetPriceRange()
		return s.repo.FilterByPriceRange(minPrice, maxPrice)
	}
	
	return s.repo.GetAll()
}

// GetCompaniesByMarket retrieves companies by market segment
//
// @description 市場区分で企業をフィルタリングして取得する
//
// @param {string} market 市場区分（例：東P、東S、東G）
// @returns {[]Company} 指定市場の企業データ
// @throws {error} データ取得に失敗した場合
//
// @example
// ```go
// primeCompanies, err := service.GetCompaniesByMarket("東P")
// if err != nil {
//     log.Printf("Failed to get prime market companies: %v", err)
// }
// ```
func (s *Service) GetCompaniesByMarket(market string) ([]Company, error) {
	return s.repo.FilterByMarket(market)
}

// GetCompaniesWithPriceAndMarketFilter retrieves companies with combined filtering
//
// @description 価格範囲と市場区分の組み合わせでフィルタリングして企業を取得する
//
// @param {string} market 市場区分
// @param {float64} minPrice 最小価格
// @param {float64} maxPrice 最大価格
// @returns {[]Company} フィルタリングされた企業データ
// @throws {error} データ取得に失敗した場合
//
// @example
// ```go
// companies, err := service.GetCompaniesWithPriceAndMarketFilter("東P", 100.0, 5000.0)
// ```
func (s *Service) GetCompaniesWithPriceAndMarketFilter(market string, minPrice, maxPrice float64) ([]Company, error) {
	// First filter by market
	marketCompanies, err := s.repo.FilterByMarket(market)
	if err != nil {
		return nil, fmt.Errorf("failed to filter by market: %w", err)
	}

	// Then filter by price range
	var filteredCompanies []Company
	for _, company := range marketCompanies {
		if company.HasPrice() {
			price := *company.Price
			if price >= minPrice && price <= maxPrice {
				filteredCompanies = append(filteredCompanies, company)
			}
		}
	}

	return filteredCompanies, nil
}

// GetCompanyBySymbol retrieves a specific company by symbol
//
// @description 株式シンボルで特定の企業を取得する
//
// @param {string} symbol 株式シンボル
// @returns {*Company} 企業データ（見つからない場合はnil）
// @throws {error} データ取得に失敗した場合
//
// @example
// ```go
// company, err := service.GetCompanyBySymbol("7203.T")
// if err != nil {
//     log.Printf("Failed to get company: %v", err)
// }
// if company != nil {
//     fmt.Printf("Found company: %s", company.Name)
// }
// ```
func (s *Service) GetCompanyBySymbol(symbol string) (*Company, error) {
	return s.repo.GetBySymbol(symbol)
}

// GetCompanyCount returns the total number of companies in the database
//
// @description データベース内の総企業数を取得する
//
// @returns {int} 企業数
// @throws {error} データ取得に失敗した場合
//
// @example
// ```go
// count, err := service.GetCompanyCount()
// if err != nil {
//     log.Printf("Failed to get company count: %v", err)
// }
// fmt.Printf("Total companies: %d", count)
// ```
func (s *Service) GetCompanyCount() (int, error) {
	return s.repo.Count()
}

// ValidateConnection validates the database connection
//
// @description データベース接続の妥当性を検証する
// 接続テストとテーブルの存在確認を行う
//
// @throws {error} 接続が無効な場合
//
// @example
// ```go
// if err := service.ValidateConnection(); err != nil {
//     log.Fatalf("Database connection is invalid: %v", err)
// }
// ```
func (s *Service) ValidateConnection() error {
	if !s.conn.IsConnected() {
		return fmt.Errorf("database connection is not active")
	}

	// Test with a simple query
	count, err := s.repo.Count()
	if err != nil {
		return fmt.Errorf("failed to execute test query: %w", err)
	}

	configs.LogDebug(s.config, "Database connection validated successfully, companies: %d", count)
	return nil
}

// GetStatistics returns comprehensive database statistics
//
// @description データベースの包括的な統計情報を取得する
// 企業数、価格分布、市場分布等の情報を含む
//
// @returns {Statistics} 統計情報
// @throws {error} 統計情報の取得に失敗した場合
//
// @example
// ```go
// stats, err := service.GetStatistics()
// if err != nil {
//     log.Printf("Failed to get statistics: %v", err)
// }
// fmt.Printf("Total companies: %d", stats.TotalCompanies)
// ```
func (s *Service) GetStatistics() (Statistics, error) {
	stats := Statistics{
		MarketDistribution: make(map[string]int),
	}

	// Get all companies for statistics
	companies, err := s.repo.GetAll()
	if err != nil {
		return stats, fmt.Errorf("failed to get companies for statistics: %w", err)
	}

	stats.TotalCompanies = len(companies)

	var totalPrice float64
	var priceCount int
	var minPrice, maxPrice float64
	var firstPriceSet bool

	// Calculate statistics
	for _, company := range companies {
		// Market distribution
		if company.Market != "" {
			stats.MarketDistribution[company.Market]++
		}

		// Price statistics
		if company.HasPrice() {
			price := *company.Price
			stats.CompaniesWithPrice++
			totalPrice += price
			priceCount++

			if !firstPriceSet {
				minPrice = price
				maxPrice = price
				firstPriceSet = true
			} else {
				if price < minPrice {
					minPrice = price
				}
				if price > maxPrice {
					maxPrice = price
				}
			}
		}
	}

	// Calculate average price
	if priceCount > 0 {
		stats.AveragePrice = totalPrice / float64(priceCount)
		stats.PriceRange.Min = minPrice
		stats.PriceRange.Max = maxPrice
	}

	return stats, nil
}

// CreateTables creates the necessary database tables
//
// @description 必要なデータベーステーブルを作成する
// 初回起動時やマイグレーション用途に使用
//
// @throws {error} テーブル作成に失敗した場合
//
// @example
// ```go
// if err := service.CreateTables(); err != nil {
//     log.Fatalf("Failed to create tables: %v", err)
// }
// ```
func (s *Service) CreateTables() error {
	return s.repo.CreateTables()
}

// Close closes the service and all associated resources
//
// @description サービスと関連するリソースを閉じる
// データベース接続を適切にクリーンアップする
//
// @throws {error} リソースの解放に失敗した場合
//
// @example
// ```go
// defer service.Close()
// ```
func (s *Service) Close() error {
	if s.repo != nil {
		return s.repo.Close()
	}
	return nil
}

// GetConfig returns the service configuration
//
// @description サービスの設定を取得する
//
// @returns {*configs.Config} 設定オブジェクト
func (s *Service) GetConfig() *configs.Config {
	return s.config
}

// GetRepository returns the underlying repository
//
// @description 基礎となるリポジトリを取得する
// テストやデバッグ用途
//
// @returns {*Repository} リポジトリインスタンス
func (s *Service) GetRepository() *Repository {
	return s.repo
}

// String returns a string representation of the service
//
// @description サービスの文字列表現を返す
//
// @returns {string} サービスの概要
func (s *Service) String() string {
	return fmt.Sprintf("DatabaseService{Path: %s, PriceFilter: %v}",
		s.config.DatabasePath,
		s.config.IsPriceFilterEnabled(),
	)
}