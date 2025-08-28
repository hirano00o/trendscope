"""データベース接続管理のテストコード

SQLite接続の作成、管理、切断の機能をテストします。
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from stock_batch.database.connection import DatabaseConnection


class TestDatabaseConnection:
    """DatabaseConnection クラスのテスト"""

    def test_create_connection_with_file_path(self) -> None:
        """ファイルパスを指定したデータベース接続作成のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            assert conn.db_path == db_path
            assert conn.connection is None  # 初期状態では未接続
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_create_connection_with_memory_database(self) -> None:
        """メモリデータベース接続作成のテスト"""
        conn = DatabaseConnection(":memory:")
        assert conn.db_path == ":memory:"
        assert conn.connection is None

    def test_connect_creates_sqlite_connection(self) -> None:
        """connect()でSQLite接続が作成されることのテスト"""
        conn = DatabaseConnection(":memory:")

        connection = conn.connect()

        assert connection is not None
        assert isinstance(connection, sqlite3.Connection)
        assert conn.connection is connection  # インスタンス変数に保存される
        assert conn.is_connected() is True

    def test_connect_returns_existing_connection(self) -> None:
        """既存の接続が存在する場合は同じ接続を返すことのテスト"""
        conn = DatabaseConnection(":memory:")

        first_connection = conn.connect()
        second_connection = conn.connect()

        assert first_connection is second_connection

    def test_disconnect_closes_connection(self) -> None:
        """disconnect()で接続が閉じられることのテスト"""
        conn = DatabaseConnection(":memory:")
        conn.connect()

        conn.disconnect()

        assert conn.connection is None
        assert conn.is_connected() is False

    def test_disconnect_when_not_connected(self) -> None:
        """未接続状態でdisconnect()を呼んでもエラーが発生しないテスト"""
        conn = DatabaseConnection(":memory:")

        # エラーが発生せずに完了する
        conn.disconnect()

        assert conn.connection is None
        assert conn.is_connected() is False

    def test_context_manager_auto_connects_and_disconnects(self) -> None:
        """コンテキストマネージャーで自動接続・切断されることのテスト"""
        conn = DatabaseConnection(":memory:")

        with conn as connection:
            assert connection is not None
            assert isinstance(connection, sqlite3.Connection)
            assert conn.is_connected() is True

        # withブロックを出ると自動的に切断される
        assert conn.is_connected() is False

    def test_context_manager_handles_existing_connection(self) -> None:
        """既存接続があるときのコンテキストマネージャーのテスト"""
        conn = DatabaseConnection(":memory:")
        original_connection = conn.connect()

        with conn as connection:
            assert connection is original_connection
            assert conn.is_connected() is True

        # withブロックを出ると自動的に切断される
        assert conn.is_connected() is False

    def test_execute_query_with_connection(self) -> None:
        """接続状態でクエリ実行のテスト"""
        conn = DatabaseConnection(":memory:")
        conn.connect()

        # テーブル作成クエリを実行
        result = conn.execute_query("CREATE TABLE test (id INTEGER, name TEXT)")

        assert result is not None
        # テーブルが作成されたことを確認
        cursor = conn.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='test'"
        )
        assert cursor is not None
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "test"

    def test_execute_query_without_connection_raises_error(self) -> None:
        """未接続状態でのクエリ実行エラーのテスト"""
        conn = DatabaseConnection(":memory:")

        with pytest.raises(RuntimeError, match="データベースに接続されていません"):
            conn.execute_query("SELECT 1")

    def test_execute_query_with_invalid_sql_raises_error(self) -> None:
        """無効なSQLでのクエリ実行エラーのテスト"""
        conn = DatabaseConnection(":memory:")
        conn.connect()

        with pytest.raises(sqlite3.Error):
            conn.execute_query("INVALID SQL STATEMENT")

    def test_execute_many_with_parameters(self) -> None:
        """パラメータ付きバッチ実行のテスト"""
        conn = DatabaseConnection(":memory:")
        conn.connect()

        # テーブル作成
        conn.execute_query("CREATE TABLE companies (symbol TEXT, name TEXT)")

        # バッチ挿入
        data = [("1332.T", "ニッスイ"), ("1418.T", "インターライフ")]
        cursor = conn.execute_many(
            "INSERT INTO companies (symbol, name) VALUES (?, ?)", data
        )

        assert cursor is not None

        # データが挿入されたことを確認
        result = conn.execute_query("SELECT COUNT(*) FROM companies")
        assert result is not None
        count = result.fetchone()[0]
        assert count == 2

    def test_execute_many_without_connection_raises_error(self) -> None:
        """未接続状態でのバッチ実行エラーのテスト"""
        conn = DatabaseConnection(":memory:")

        with pytest.raises(RuntimeError, match="データベースに接続されていません"):
            conn.execute_many("INSERT INTO test VALUES (?, ?)", [("a", "b")])

    @patch("sqlite3.connect")
    def test_connection_error_handling(self, mock_connect: Mock) -> None:
        """データベース接続エラーのハンドリングテスト"""
        mock_connect.side_effect = sqlite3.Error("Database connection failed")

        conn = DatabaseConnection("/invalid/path/database.db")

        with pytest.raises(sqlite3.Error, match="Database connection failed"):
            conn.connect()

    def test_get_database_info(self) -> None:
        """データベース情報取得のテスト"""
        conn = DatabaseConnection(":memory:")
        conn.connect()

        info = conn.get_database_info()

        assert "sqlite_version" in info
        assert "database_path" in info
        assert info["database_path"] == ":memory:"
        assert "connected" in info
        assert info["connected"] is True

    def test_get_database_info_disconnected(self) -> None:
        """未接続時のデータベース情報取得のテスト"""
        conn = DatabaseConnection("/path/to/db.sqlite")

        info = conn.get_database_info()

        assert info["database_path"] == "/path/to/db.sqlite"
        assert info["connected"] is False
        assert "sqlite_version" not in info  # 未接続時は取得できない
