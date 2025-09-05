package database

import (
	"database/sql"
	"fmt"
	"time"
)

// Repository provides CRUD operations for Company data
//
// @description Company データのCRUD操作を提供するリポジトリ
// SQLiteデータベースへの企業データの挿入、取得、更新、削除機能
// stock-db-batch のPythonサービスと同等の機能を提供
//
// @example
// ```go
// conn, _ := NewConnection("/data/stocks.db")
// conn.Connect()
// defer conn.Close()
//
// repo, _ := NewRepository(conn)
// repo.CreateTables()
//
// company := Company{Symbol: "7203.T", Name: "トヨタ自動車"}
// id, err := repo.Insert(&company)
// ```
type Repository struct {
	// conn is the database connection
	conn *Connection
}

// NewRepository creates a new repository instance
//
// @description 新しいリポジトリインスタンスを作成する
// データベース接続を受け取り、CRUD操作の準備を行う
//
// @param {*Connection} conn データベース接続インスタンス
// @returns {*Repository} リポジトリインスタンス
// @throws {error} 接続が無効な場合
//
// @example
// ```go
// conn, _ := NewConnection("/data/stocks.db")
// repo, err := NewRepository(conn)
// if err != nil {
//     log.Fatal(err)
// }
// ```
func NewRepository(conn *Connection) (*Repository, error) {
	if conn == nil {
		return nil, fmt.Errorf("connection cannot be nil")
	}

	if !conn.IsConnected() {
		return nil, fmt.Errorf("connection is not established")
	}

	return &Repository{
		conn: conn,
	}, nil
}

// CreateTables creates the company table and indexes
//
// @description companyテーブルとインデックスを作成する
// stock-db-batch のマイグレーション機能と同等のテーブル作成
// 既にテーブルが存在する場合は何もしない
//
// @throws {error} テーブル作成に失敗した場合
//
// @example
// ```go
// repo, _ := NewRepository(conn)
// if err := repo.CreateTables(); err != nil {
//     log.Fatal(err)
// }
// ```
func (r *Repository) CreateTables() error {
	db, err := r.conn.DB()
	if err != nil {
		return fmt.Errorf("failed to get database connection: %w", err)
	}

	// Create company table
	createTableSQL := `
	CREATE TABLE IF NOT EXISTS company (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		symbol TEXT UNIQUE NOT NULL,
		name TEXT NOT NULL,
		market TEXT,
		business_summary TEXT,
		price REAL,
		last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	)`

	if _, err := db.Exec(createTableSQL); err != nil {
		return fmt.Errorf("failed to create company table: %w", err)
	}

	// Create indexes for performance
	indexes := []string{
		"CREATE INDEX IF NOT EXISTS idx_company_symbol ON company(symbol)",
		"CREATE INDEX IF NOT EXISTS idx_company_market ON company(market)",
		"CREATE INDEX IF NOT EXISTS idx_company_price ON company(price)",
	}

	for _, indexSQL := range indexes {
		if _, err := db.Exec(indexSQL); err != nil {
			return fmt.Errorf("failed to create index: %w", err)
		}
	}

	return nil
}

// Insert inserts a new company into the database
//
// @description 新しい企業をデータベースに挿入する
// シンボルの重複チェックを行い、一意制約違反を防ぐ
// 挿入成功時は自動生成されたIDを返す
//
// @param {*Company} company 挿入する企業データ
// @returns {int} 挿入された企業のID
// @throws {error} 挿入に失敗した場合（重複、バリデーションエラー等）
//
// @example
// ```go
// company := Company{Symbol: "7203.T", Name: "トヨタ自動車"}
// id, err := repo.Insert(&company)
// if err != nil {
//     log.Printf("Insert failed: %v", err)
// }
// ```
func (r *Repository) Insert(company *Company) (int, error) {
	if err := company.Validate(); err != nil {
		return 0, fmt.Errorf("validation failed: %w", err)
	}

	db, err := r.conn.DB()
	if err != nil {
		return 0, fmt.Errorf("failed to get database connection: %w", err)
	}

	now := time.Now()
	insertSQL := `
	INSERT INTO company (symbol, name, market, business_summary, price, created_at, last_updated)
	VALUES (?, ?, ?, ?, ?, ?, ?)`

	result, err := db.Exec(insertSQL,
		company.Symbol,
		company.Name,
		company.Market,
		company.BusinessSummary,
		company.Price,
		now,
		now,
	)
	if err != nil {
		return 0, fmt.Errorf("failed to insert company: %w", err)
	}

	id, err := result.LastInsertId()
	if err != nil {
		return 0, fmt.Errorf("failed to get inserted ID: %w", err)
	}

	return int(id), nil
}

// GetBySymbol retrieves a company by its symbol
//
// @description 株式シンボルで企業を取得する
//
// @param {string} symbol 株式シンボル（例：7203.T）
// @returns {*Company} 企業データ、見つからない場合はnil
// @throws {error} データベースエラー
//
// @example
// ```go
// company, err := repo.GetBySymbol("7203.T")
// if err != nil {
//     log.Printf("Get failed: %v", err)
// }
// if company != nil {
//     fmt.Printf("Found: %s", company.Name)
// }
// ```
func (r *Repository) GetBySymbol(symbol string) (*Company, error) {
	db, err := r.conn.DB()
	if err != nil {
		return nil, fmt.Errorf("failed to get database connection: %w", err)
	}

	selectSQL := `
	SELECT id, symbol, name, market, business_summary, price, last_updated, created_at
	FROM company
	WHERE symbol = ?`

	row := db.QueryRow(selectSQL, symbol)

	company := &Company{}
	err = row.Scan(
		&company.ID,
		&company.Symbol,
		&company.Name,
		&company.Market,
		&company.BusinessSummary,
		&company.Price,
		&company.LastUpdated,
		&company.CreatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, nil // Not found
		}
		return nil, fmt.Errorf("failed to scan company: %w", err)
	}

	return company, nil
}

// Update updates an existing company
//
// @description 既存の企業データを更新する
// シンボルで企業を特定し、他のフィールドを更新
//
// @param {*Company} company 更新する企業データ
// @throws {error} 更新に失敗した場合
//
// @example
// ```go
// company.Price = &newPrice
// err := repo.Update(&company)
// ```
func (r *Repository) Update(company *Company) error {
	if err := company.Validate(); err != nil {
		return fmt.Errorf("validation failed: %w", err)
	}

	db, err := r.conn.DB()
	if err != nil {
		return fmt.Errorf("failed to get database connection: %w", err)
	}

	updateSQL := `
	UPDATE company 
	SET name = ?, market = ?, business_summary = ?, price = ?, last_updated = ?
	WHERE symbol = ?`

	_, err = db.Exec(updateSQL,
		company.Name,
		company.Market,
		company.BusinessSummary,
		company.Price,
		time.Now(),
		company.Symbol,
	)

	if err != nil {
		return fmt.Errorf("failed to update company: %w", err)
	}

	return nil
}

// Delete deletes a company by symbol
//
// @description 株式シンボルで企業を削除する
//
// @param {string} symbol 削除する企業の株式シンボル
// @throws {error} 削除に失敗した場合
//
// @example
// ```go
// err := repo.Delete("7203.T")
// ```
func (r *Repository) Delete(symbol string) error {
	db, err := r.conn.DB()
	if err != nil {
		return fmt.Errorf("failed to get database connection: %w", err)
	}

	deleteSQL := "DELETE FROM company WHERE symbol = ?"
	_, err = db.Exec(deleteSQL, symbol)
	if err != nil {
		return fmt.Errorf("failed to delete company: %w", err)
	}

	return nil
}

// GetAll retrieves all companies from the database
//
// @description データベースから全ての企業を取得する
//
// @returns {[]Company} 全企業データのスライス
// @throws {error} データベースエラー
//
// @example
// ```go
// companies, err := repo.GetAll()
// if err != nil {
//     log.Printf("GetAll failed: %v", err)
// }
// fmt.Printf("Found %d companies", len(companies))
// ```
func (r *Repository) GetAll() ([]Company, error) {
	db, err := r.conn.DB()
	if err != nil {
		return nil, fmt.Errorf("failed to get database connection: %w", err)
	}

	selectSQL := `
	SELECT id, symbol, name, market, business_summary, price, last_updated, created_at
	FROM company
	ORDER BY symbol`

	rows, err := db.Query(selectSQL)
	if err != nil {
		return nil, fmt.Errorf("failed to query companies: %w", err)
	}
	defer rows.Close()

	var companies []Company
	for rows.Next() {
		company := Company{}
		err := rows.Scan(
			&company.ID,
			&company.Symbol,
			&company.Name,
			&company.Market,
			&company.BusinessSummary,
			&company.Price,
			&company.LastUpdated,
			&company.CreatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan company: %w", err)
		}
		companies = append(companies, company)
	}

	if err = rows.Err(); err != nil {
		return nil, fmt.Errorf("row iteration error: %w", err)
	}

	return companies, nil
}

// FilterByPriceRange retrieves companies within a price range
//
// @description 価格範囲で企業をフィルタリングする
// 価格がnullの企業は除外される
//
// @param {float64} minPrice 最小価格
// @param {float64} maxPrice 最大価格
// @returns {[]Company} フィルタリングされた企業データ
// @throws {error} データベースエラー
//
// @example
// ```go
// companies, err := repo.FilterByPriceRange(100.0, 5000.0)
// ```
func (r *Repository) FilterByPriceRange(minPrice, maxPrice float64) ([]Company, error) {
	db, err := r.conn.DB()
	if err != nil {
		return nil, fmt.Errorf("failed to get database connection: %w", err)
	}

	selectSQL := `
	SELECT id, symbol, name, market, business_summary, price, last_updated, created_at
	FROM company
	WHERE price IS NOT NULL AND price >= ? AND price <= ?
	ORDER BY symbol`

	rows, err := db.Query(selectSQL, minPrice, maxPrice)
	if err != nil {
		return nil, fmt.Errorf("failed to query companies by price range: %w", err)
	}
	defer rows.Close()

	var companies []Company
	for rows.Next() {
		company := Company{}
		err := rows.Scan(
			&company.ID,
			&company.Symbol,
			&company.Name,
			&company.Market,
			&company.BusinessSummary,
			&company.Price,
			&company.LastUpdated,
			&company.CreatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan company: %w", err)
		}
		companies = append(companies, company)
	}

	if err = rows.Err(); err != nil {
		return nil, fmt.Errorf("row iteration error: %w", err)
	}

	return companies, nil
}

// FilterByMarket retrieves companies by market segment
//
// @description 市場区分で企業をフィルタリングする
//
// @param {string} market 市場区分（例：東P、東S、東G）
// @returns {[]Company} 指定市場の企業データ
// @throws {error} データベースエラー
//
// @example
// ```go
// primeCompanies, err := repo.FilterByMarket("東P")
// ```
func (r *Repository) FilterByMarket(market string) ([]Company, error) {
	db, err := r.conn.DB()
	if err != nil {
		return nil, fmt.Errorf("failed to get database connection: %w", err)
	}

	selectSQL := `
	SELECT id, symbol, name, market, business_summary, price, last_updated, created_at
	FROM company
	WHERE market = ?
	ORDER BY symbol`

	rows, err := db.Query(selectSQL, market)
	if err != nil {
		return nil, fmt.Errorf("failed to query companies by market: %w", err)
	}
	defer rows.Close()

	var companies []Company
	for rows.Next() {
		company := Company{}
		err := rows.Scan(
			&company.ID,
			&company.Symbol,
			&company.Name,
			&company.Market,
			&company.BusinessSummary,
			&company.Price,
			&company.LastUpdated,
			&company.CreatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan company: %w", err)
		}
		companies = append(companies, company)
	}

	if err = rows.Err(); err != nil {
		return nil, fmt.Errorf("row iteration error: %w", err)
	}

	return companies, nil
}

// Count returns the total number of companies
//
// @description データベース内の総企業数を取得する
//
// @returns {int} 企業数
// @throws {error} データベースエラー
//
// @example
// ```go
// count, err := repo.Count()
// fmt.Printf("Total companies: %d", count)
// ```
func (r *Repository) Count() (int, error) {
	db, err := r.conn.DB()
	if err != nil {
		return 0, fmt.Errorf("failed to get database connection: %w", err)
	}

	var count int
	err = db.QueryRow("SELECT COUNT(*) FROM company").Scan(&count)
	if err != nil {
		return 0, fmt.Errorf("failed to count companies: %w", err)
	}

	return count, nil
}

// Close closes the repository connection
//
// @description リポジトリのデータベース接続を閉じる
//
// @throws {error} 接続の切断に失敗した場合
func (r *Repository) Close() error {
	return r.conn.Close()
}