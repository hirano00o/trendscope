package database

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"

	_ "github.com/mattn/go-sqlite3"
)

// Connection represents a SQLite database connection manager
//
// @description SQLite3データベース接続を管理するための構造体
// データベースの接続、切断、基本的なクエリ実行機能を提供
//
// @example
// ```go
// conn, err := NewConnection("/data/stocks.db")
// if err != nil {
//     log.Fatal(err)
// }
// defer conn.Close()
//
// if err := conn.Connect(); err != nil {
//     log.Fatal(err)
// }
// ```
type Connection struct {
	// databasePath is the path to the SQLite database file
	databasePath string
	// db is the underlying database connection
	db *sql.DB
}

// NewConnection creates a new database connection instance
//
// @description 新しいデータベース接続インスタンスを作成する
// データベースファイルのディレクトリが存在しない場合は作成する
//
// @param {string} databasePath SQLiteデータベースファイルのパス
// @returns {*Connection} データベース接続インスタンス
// @throws {error} データベースパスが無効な場合
//
// @example
// ```go
// conn, err := NewConnection("/data/stocks.db")
// if err != nil {
//     log.Printf("Failed to create connection: %v", err)
//     return
// }
// ```
func NewConnection(databasePath string) (*Connection, error) {
	if databasePath == "" {
		return nil, fmt.Errorf("database path cannot be empty")
	}

	// Create directory if it doesn't exist (except for :memory:)
	if databasePath != ":memory:" {
		dir := filepath.Dir(databasePath)
		if err := os.MkdirAll(dir, 0755); err != nil {
			return nil, fmt.Errorf("failed to create database directory: %w", err)
		}
	}

	return &Connection{
		databasePath: databasePath,
	}, nil
}

// Connect establishes a connection to the SQLite database
//
// @description SQLiteデータベースへの接続を確立する
// 接続が既に存在する場合は何もしない
//
// @throws {error} データベース接続に失敗した場合
//
// @example
// ```go
// conn, _ := NewConnection("/data/stocks.db")
// if err := conn.Connect(); err != nil {
//     log.Printf("Failed to connect: %v", err)
// }
// ```
func (c *Connection) Connect() error {
	if c.db != nil {
		return nil // Already connected
	}

	db, err := sql.Open("sqlite3", c.databasePath)
	if err != nil {
		return fmt.Errorf("failed to open database: %w", err)
	}

	// Test the connection
	if err := db.Ping(); err != nil {
		db.Close()
		return fmt.Errorf("failed to ping database: %w", err)
	}

	c.db = db
	return nil
}

// Close closes the database connection
//
// @description データベース接続を閉じる
// 接続が存在しない場合は何もしない
//
// @throws {error} 接続の切断に失敗した場合
//
// @example
// ```go
// defer conn.Close()
// ```
func (c *Connection) Close() error {
	if c.db == nil {
		return nil // Already closed or never connected
	}

	if err := c.db.Close(); err != nil {
		return fmt.Errorf("failed to close database: %w", err)
	}

	c.db = nil
	return nil
}

// DB returns the underlying database connection
//
// @description 基礎となるsql.DB接続を取得する
// 高度なクエリ操作や他のライブラリとの連携に使用
//
// @returns {*sql.DB} sql.DB接続インスタンス
// @throws {error} 接続が確立されていない場合
//
// @example
// ```go
// conn, _ := NewConnection("/data/stocks.db")
// conn.Connect()
// db := conn.DB()
// rows, err := db.Query("SELECT * FROM company")
// ```
func (c *Connection) DB() (*sql.DB, error) {
	if c.db == nil {
		return nil, fmt.Errorf("database connection is not established")
	}
	return c.db, nil
}

// IsConnected checks if the database connection is active
//
// @description データベース接続がアクティブかどうかを確認する
//
// @returns {bool} 接続がアクティブな場合true
//
// @example
// ```go
// if conn.IsConnected() {
//     // Use connection
// }
// ```
func (c *Connection) IsConnected() bool {
	return c.db != nil
}

// GetPath returns the database file path
//
// @description データベースファイルのパスを取得する
//
// @returns {string} データベースファイルのパス
func (c *Connection) GetPath() string {
	return c.databasePath
}