package csv

import (
	"bytes"
	"encoding/csv"
	"fmt"
	"io"
	"log"
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
// BOMの処理、引用符の寛容な処理、詳細なエラーハンドリングを行う
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
	// Read file content as bytes to handle BOM properly
	content, err := os.ReadFile(filepath)
	if err != nil {
		return nil, fmt.Errorf("failed to read CSV file: %w", err)
	}

	log.Printf("CSV file size: %d bytes", len(content))

	// Remove BOM if present
	content = removeBOM(content)

	// Debug: Print first few lines for troubleshooting
	lines := strings.Split(string(content), "\n")
	log.Printf("CSV file has %d lines", len(lines))

	// Print first 3 lines for debugging (with character analysis)
	for i, line := range lines {
		if i >= 3 {
			break
		}
		if line != "" {
			log.Printf("Line %d: %q (length: %d)", i+1, line, len(line))
			// Show first few bytes in hex for debugging only on first line
			if i == 0 && len(line) > 0 {
				maxBytes := 20
				if len(line) < maxBytes {
					maxBytes = len(line)
				}
				log.Printf("Line %d hex: %x", i+1, []byte(line[:maxBytes]))
			}
		}
	}

	// Create CSV reader with more lenient settings
	reader := csv.NewReader(bytes.NewReader(content))
	reader.TrimLeadingSpace = true
	reader.LazyQuotes = true    // Allow lazy quotes (more lenient parsing)
	reader.FieldsPerRecord = -1 // Allow variable number of fields per record

	var stocks []*Stock
	rowNumber := 0

	for {
		rowNumber++
		record, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Printf("CSV parse error at row %d: %v", rowNumber, err)
			log.Printf("Problematic line: %q", getLineContent(lines, rowNumber-1))
			return nil, fmt.Errorf("failed to read CSV record at row %d: %w", rowNumber, err)
		}

		// Log details only for first few rows and problematic rows
		if rowNumber <= 5 {
			log.Printf("Row %d: parsed %d fields: %v", rowNumber, len(record), record)
		}

		// Skip header row
		if rowNumber == 1 {
			log.Printf("Skipping header row: %v", record)
			continue
		}

		// Skip empty rows or rows with insufficient columns
		if len(record) < 5 {
			if rowNumber <= 10 { // Log only first few problematic rows
				log.Printf("Skipping row %d: insufficient columns (%d < 5)", rowNumber, len(record))
			}
			continue
		}

		// Clean up fields (remove quotes and extra whitespace)
		code := cleanField(record[0])
		name := cleanField(record[1])
		market := cleanField(record[2])
		currentValue := cleanField(record[3])
		changeRate := cleanField(record[4])

		// Skip if code is empty
		if code == "" {
			if rowNumber <= 10 { // Log only first few problematic rows
				log.Printf("Skipping row %d: empty stock code", rowNumber)
			}
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

		// Log details only for first few stocks
		if len(stocks) <= 5 {
			log.Printf("Added stock: %s (%s)", code, name)
		}
	}

	log.Printf("Successfully parsed %d stocks from CSV", len(stocks))
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

// removeBOM removes Byte Order Mark (BOM) from the beginning of the content
//
// @description ファイル内容の先頭からBOM（Byte Order Mark）を除去する
// UTF-8 BOM（EF BB BF）を検出して除去
//
// @param {[]byte} content ファイル内容のバイト配列
// @returns {[]byte} BOMが除去されたバイト配列
func removeBOM(content []byte) []byte {
	// UTF-8 BOM is EF BB BF
	if len(content) >= 3 && content[0] == 0xEF && content[1] == 0xBB && content[2] == 0xBF {
		log.Printf("BOM detected and removed")
		return content[3:]
	}
	return content
}

// getLineContent safely retrieves the content of a specific line
//
// @description 指定した行番号の内容を安全に取得する
// 行番号が範囲外の場合は空文字列を返す
//
// @param {[]string} lines 全行の配列
// @param {int} lineIndex 取得する行のインデックス（0ベース）
// @returns {string} 指定行の内容
func getLineContent(lines []string, lineIndex int) string {
	if lineIndex < 0 || lineIndex >= len(lines) {
		return ""
	}
	return lines[lineIndex]
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
