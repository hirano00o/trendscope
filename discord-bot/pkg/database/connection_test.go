package database

import (
	"os"
	"path/filepath"
	"testing"
)

func TestNewConnection(t *testing.T) {
	tests := []struct {
		name         string
		databasePath string
		wantError    bool
	}{
		{
			name:         "Valid database path",
			databasePath: ":memory:",
			wantError:    false,
		},
		{
			name:         "Empty database path",
			databasePath: "",
			wantError:    true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			conn, err := NewConnection(tt.databasePath)
			if tt.wantError {
				if err == nil {
					t.Errorf("NewConnection() expected error but got none")
				}
				return
			}

			if err != nil {
				t.Errorf("NewConnection() error = %v", err)
				return
			}

			if conn == nil {
				t.Errorf("NewConnection() returned nil connection")
				return
			}

			// Test connection
			if err := conn.Connect(); err != nil {
				t.Errorf("Connect() error = %v", err)
			}

			// Test close
			if err := conn.Close(); err != nil {
				t.Errorf("Close() error = %v", err)
			}
		})
	}
}

func TestConnectionFileCreation(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test.db")

	conn, err := NewConnection(dbPath)
	if err != nil {
		t.Fatalf("NewConnection() error = %v", err)
	}

	if err := conn.Connect(); err != nil {
		t.Fatalf("Connect() error = %v", err)
	}

	// Check if database file was created
	if _, err := os.Stat(dbPath); os.IsNotExist(err) {
		t.Errorf("Database file was not created at %s", dbPath)
	}

	conn.Close()
}

func TestConnectionWithContext(t *testing.T) {
	conn, err := NewConnection(":memory:")
	if err != nil {
		t.Fatalf("NewConnection() error = %v", err)
	}

	if err := conn.Connect(); err != nil {
		t.Fatalf("Connect() error = %v", err)
	}
	defer conn.Close()

	// Test simple query
	rows, err := conn.db.Query("SELECT 1")
	if err != nil {
		t.Errorf("Query() error = %v", err)
	}
	defer rows.Close()

	if !rows.Next() {
		t.Errorf("Query() should return at least one row")
	}

	var result int
	if err := rows.Scan(&result); err != nil {
		t.Errorf("Scan() error = %v", err)
	}

	if result != 1 {
		t.Errorf("Expected result 1, got %d", result)
	}
}