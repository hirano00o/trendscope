package csv

import (
	"encoding/csv"
	"fmt"
	"io"
	"os"
	"strings"
)

// Stock represents a stock entry from the CSV file
//
// @description CSVファイルから読み取った株式情報を表現する構造体
// SBI証券のスクリーニング結果CSVの各行に対応
//
// @example
// ```go
//
//	stock := &Stock{
//	    Code:        "7203",
//	    Name:        "トヨタ自動車",
//	    Market:      "東P",
//	    CurrentValue: "2500",
//	    ChangeRate:  "+10(+0.40%)",
//	}
//
// ```
type Stock struct {
	// Code is the stock code (e.g., "7203")
	Code string
	// Name is the company name
	Name string
	// Market is the market segment (e.g., "東P", "東G", "東S")
	Market string
	// CurrentValue is the current stock price as string
	CurrentValue string
	// ChangeRate is the price change rate as string
	ChangeRate string
}

// GetSymbol returns the symbol in the format required by the API (.T suffix for Japanese stocks)
//
// @description API呼び出し用のシンボルを生成する
// 日本株の場合は末尾に ".T" を追加してyfinance形式にする
//
// @returns {string} API用のシンボル（例：7203.T）
//
// @example
// ```go
// stock := &Stock{Code: "7203"}
// symbol := stock.GetSymbol() // "7203.T"
// ```
func (s *Stock) GetSymbol() string {
	return s.Code + ".T"
}

// ReadStocksFromCSV reads stock data from the specified CSV file
//
// @description SBI証券のスクリーニング結果CSVファイルから株式データを読み取る
// CSV形式："コード","銘柄名","市場","現在値","前日比(%)"
// BOMの処理と空行のスキップを行う
//
// @param {string} filepath CSVファイルのパス
// @returns {[]*Stock} 読み取った株式データのスライス
// @throws {error} ファイルの読み取りまたはCSVパースに失敗した場合
//
// @example
// ```go
// stocks, err := ReadStocksFromCSV("./screener_result.csv")
//
//	if err != nil {
//	    log.Fatal(err)
//	}
//
// fmt.Printf("読み取った株式数: %d\n", len(stocks))
// ```
func ReadStocksFromCSV(filepath string) ([]*Stock, error) {
	file, err := os.Open(filepath)
	if err != nil {
		return nil, fmt.Errorf("failed to open CSV file: %w", err)
	}
	defer file.Close()

	reader := csv.NewReader(file)
	reader.TrimLeadingSpace = true

	var stocks []*Stock
	isFirstRow := true

	for {
		record, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, fmt.Errorf("failed to read CSV record: %w", err)
		}

		// Skip header row
		if isFirstRow {
			isFirstRow = false
			continue
		}

		// Skip empty rows or rows with insufficient columns
		if len(record) < 5 {
			continue
		}

		// Clean up fields (remove quotes and BOM)
		code := cleanField(record[0])
		name := cleanField(record[1])
		market := cleanField(record[2])
		currentValue := cleanField(record[3])
		changeRate := cleanField(record[4])

		// Skip if code is empty
		if code == "" {
			continue
		}

		stock := &Stock{
			Code:         code,
			Name:         name,
			Market:       market,
			CurrentValue: currentValue,
			ChangeRate:   changeRate,
		}

		stocks = append(stocks, stock)
	}

	return stocks, nil
}

// cleanField removes BOM, quotes, and trims whitespace from CSV fields
//
// @description CSVフィールドをクリーンアップする
// BOM（Byte Order Mark）、引用符、前後の空白を除去
//
// @param {string} field クリーンアップ対象の文字列
// @returns {string} クリーンアップ済みの文字列
func cleanField(field string) string {
	// Remove BOM if present
	field = strings.TrimPrefix(field, "\ufeff")
	// Remove surrounding quotes
	field = strings.Trim(field, "\"")
	// Trim whitespace
	field = strings.TrimSpace(field)
	return field
}

// GetStockSymbols returns a slice of symbols (.T format) from the stock list
//
// @description 株式データのリストからAPI呼び出し用のシンボル一覧を取得する
// 全ての株式コードに .T を付加して返す
//
// @param {[]*Stock} stocks 株式データのスライス
// @returns {[]string} API用シンボルのスライス
//
// @example
// ```go
// stocks, _ := ReadStocksFromCSV("screener.csv")
// symbols := GetStockSymbols(stocks)
// // ["7203.T", "6758.T", ...]
// ```
func GetStockSymbols(stocks []*Stock) []string {
	symbols := make([]string, 0, len(stocks))
	for _, stock := range stocks {
		symbols = append(symbols, stock.GetSymbol())
	}
	return symbols
}
