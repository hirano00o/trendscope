"""データベースマイグレーション機能のテストコード

テーブル作成、スキーマ管理、マイグレーション機能をテストします。
"""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from stock_batch.database.connection import DatabaseConnection
from stock_batch.database.migration import DatabaseMigration


class TestDatabaseMigration:
    """DatabaseMigration クラスのテスト"""

    def test_create_migration_with_connection(self) -> None:
        """DatabaseConnection を使用したマイグレーション作成のテスト"""
        conn = DatabaseConnection(":memory:")
        migration = DatabaseMigration(conn)

        assert migration.db_connection is conn

    def test_get_schema_version_from_new_database(self) -> None:
        """新規データベースからのスキーマバージョン取得テスト"""
        conn = DatabaseConnection(":memory:")
        migration = DatabaseMigration(conn)

        with conn:
            version = migration.get_schema_version()
            # 新規データベースではバージョン0
            assert version == 0

    def test_set_schema_version(self) -> None:
        """スキーマバージョン設定のテスト"""
        conn = DatabaseConnection(":memory:")
        migration = DatabaseMigration(conn)

        with conn:
            migration.set_schema_version(1)
            version = migration.get_schema_version()
            assert version == 1

    def test_create_company_table(self) -> None:
        """companyテーブル作成のテスト"""
        conn = DatabaseConnection(":memory:")
        migration = DatabaseMigration(conn)

        with conn:
            migration.create_company_table()

            # テーブルが作成されたことを確認
            cursor = conn.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='company'"
            )
            tables = cursor.fetchall()
            assert len(tables) == 1
            assert tables[0][0] == "company"

    def test_create_company_table_schema(self) -> None:
        """companyテーブルのスキーマ検証テスト"""
        conn = DatabaseConnection(":memory:")
        migration = DatabaseMigration(conn)

        with conn:
            migration.create_company_table()

            # テーブルスキーマを取得
            cursor = conn.execute_query("PRAGMA table_info(company)")
            columns = cursor.fetchall()

            # カラム名と型を検証
            column_info = {col[1]: col[2] for col in columns}  # (name, type)

            expected_columns = {
                "id": "INTEGER",
                "symbol": "TEXT",
                "name": "TEXT",
                "market": "TEXT",
                "business_summary": "TEXT",
                "price": "REAL",
                "last_updated": "TIMESTAMP",
                "created_at": "TIMESTAMP",
            }

            for col_name, col_type in expected_columns.items():
                assert col_name in column_info
                assert column_info[col_name] == col_type

    def test_create_company_table_primary_key(self) -> None:
        """companyテーブルの主キー設定テスト"""
        conn = DatabaseConnection(":memory:")
        migration = DatabaseMigration(conn)

        with conn:
            migration.create_company_table()

            # 主キー情報を取得
            cursor = conn.execute_query("PRAGMA table_info(company)")
            columns = cursor.fetchall()

            # id カラムが主キーであることを確認
            id_column = next(col for col in columns if col[1] == "id")
            assert id_column[5] == 1  # pk フィールドが1（主キー）

    def test_create_company_table_unique_constraint(self) -> None:
        """companyテーブルのUNIQUE制約テスト"""
        conn = DatabaseConnection(":memory:")
        migration = DatabaseMigration(conn)

        with conn:
            migration.create_company_table()

            # 同じシンボルの挿入テスト
            conn.execute_query(
                "INSERT INTO company (symbol, name) VALUES ('1332.T', 'ニッスイ')"
            )

            # 重複挿入は失敗することを確認
            with pytest.raises((sqlite3.IntegrityError, Exception)):  # UNIQUE制約違反
                conn.execute_query(
                    "INSERT INTO company (symbol, name) VALUES ('1332.T', '重複企業')"
                )

    def test_create_schema_version_table(self) -> None:
        """schema_versionテーブル作成のテスト"""
        conn = DatabaseConnection(":memory:")
        migration = DatabaseMigration(conn)

        with conn:
            migration.create_schema_version_table()

            # テーブルが作成されたことを確認
            cursor = conn.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name='schema_version'"
            )
            tables = cursor.fetchall()
            assert len(tables) == 1
            assert tables[0][0] == "schema_version"

    def test_run_initial_migration(self) -> None:
        """初回マイグレーション実行のテスト"""
        conn = DatabaseConnection(":memory:")
        migration = DatabaseMigration(conn)

        with conn:
            migration.run_migrations()

            # スキーマバージョンが1になっていることを確認
            version = migration.get_schema_version()
            assert version == 1

            # companyテーブルが作成されていることを確認
            cursor = conn.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='company'"
            )
            tables = cursor.fetchall()
            assert len(tables) == 1

    def test_run_migrations_is_idempotent(self) -> None:
        """マイグレーションが冪等であることのテスト"""
        conn = DatabaseConnection(":memory:")
        migration = DatabaseMigration(conn)

        with conn:
            # 複数回実行してもエラーが出ない
            migration.run_migrations()
            migration.run_migrations()
            migration.run_migrations()

            # バージョンは1のまま
            version = migration.get_schema_version()
            assert version == 1

    def test_check_table_exists_true(self) -> None:
        """存在するテーブルのチェックテスト"""
        conn = DatabaseConnection(":memory:")
        migration = DatabaseMigration(conn)

        with conn:
            migration.create_company_table()

            exists = migration.table_exists("company")
            assert exists is True

    def test_check_table_exists_false(self) -> None:
        """存在しないテーブルのチェックテスト"""
        conn = DatabaseConnection(":memory:")
        migration = DatabaseMigration(conn)

        with conn:
            exists = migration.table_exists("nonexistent_table")
            assert exists is False

    def test_migration_with_file_database(self) -> None:
        """ファイルベースデータベースでのマイグレーションテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            conn = DatabaseConnection(db_path)
            migration = DatabaseMigration(conn)

            with conn:
                migration.run_migrations()

                # データベースファイルが作成され、テーブルが存在することを確認
                cursor = conn.execute_query(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
                )
                table_count = cursor.fetchone()[0]
                assert table_count >= 2  # company + schema_version テーブル

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_get_migration_info(self) -> None:
        """マイグレーション情報取得のテスト"""
        conn = DatabaseConnection(":memory:")
        migration = DatabaseMigration(conn)

        with conn:
            migration.run_migrations()

            info = migration.get_migration_info()

            assert "current_version" in info
            assert "available_migrations" in info
            assert "tables" in info

            assert info["current_version"] == 1
            assert "company" in info["tables"]
            assert "schema_version" in info["tables"]

    def test_reset_database(self) -> None:
        """データベースリセット機能のテスト"""
        conn = DatabaseConnection(":memory:")
        migration = DatabaseMigration(conn)

        with conn:
            # マイグレーション実行とデータ挿入
            migration.run_migrations()
            conn.execute_query(
                "INSERT INTO company (symbol, name) VALUES ('1332.T', 'ニッスイ')"
            )

            # データが存在することを確認
            cursor = conn.execute_query("SELECT COUNT(*) FROM company")
            count = cursor.fetchone()[0]
            assert count == 1

            # データベースリセット
            migration.reset_database()

            # テーブルが削除され、バージョンが0に戻ることを確認
            version = migration.get_schema_version()
            assert version == 0

            exists = migration.table_exists("company")
            assert exists is False
