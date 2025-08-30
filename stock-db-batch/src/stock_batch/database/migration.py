"""データベースマイグレーション管理

SQLiteデータベースのスキーマ作成、バージョン管理、マイグレーション機能を提供
"""

from __future__ import annotations

import sqlite3
from typing import Any

from stock_batch.database.connection import DatabaseConnection


class DatabaseMigration:
    """データベースマイグレーション管理クラス

    SQLiteデータベースのスキーマ作成、バージョン管理、マイグレーション実行を管理する。
    アプリケーション開始時にテーブル作成やスキーマ更新を自動実行する。

    Attributes:
        db_connection: データベース接続管理オブジェクト

    Example:
        >>> conn = DatabaseConnection(":memory:")
        >>> migration = DatabaseMigration(conn)
        >>> with conn:
        ...     migration.run_migrations()
        ...     # データベーステーブルが作成される
    """

    def __init__(self, db_connection: DatabaseConnection) -> None:
        """DatabaseMigration を初期化する

        Args:
            db_connection: データベース接続管理オブジェクト

        Example:
            >>> conn = DatabaseConnection("/data/stocks.db")
            >>> migration = DatabaseMigration(conn)
        """
        self.db_connection = db_connection

    def get_schema_version(self) -> int:
        """現在のスキーマバージョンを取得する

        schema_version テーブルから現在のバージョン番号を取得する。
        テーブルが存在しない場合は0を返す。

        Returns:
            スキーマバージョン番号

        Example:
            >>> conn = DatabaseConnection(":memory:")
            >>> migration = DatabaseMigration(conn)
            >>> with conn:
            ...     version = migration.get_schema_version()
            ...     print(version)  # 新規データベースでは0
        """
        try:
            cursor = self.db_connection.execute_query(
                "SELECT version FROM schema_version ORDER BY id DESC LIMIT 1"
            )
            result = cursor.fetchone()
            return result[0] if result else 0
        except sqlite3.Error:
            # テーブルが存在しない場合は0を返す
            return 0

    def set_schema_version(self, version: int) -> None:
        """スキーマバージョンを設定する

        schema_version テーブルに新しいバージョンを記録する。
        テーブルが存在しない場合は先に作成する。

        Args:
            version: 設定するバージョン番号

        Example:
            >>> conn = DatabaseConnection(":memory:")
            >>> migration = DatabaseMigration(conn)
            >>> with conn:
            ...     migration.set_schema_version(1)
        """
        # schema_version テーブルが存在しない場合は作成
        if not self.table_exists("schema_version"):
            self.create_schema_version_table()

        self.db_connection.execute_query(
            "INSERT INTO schema_version (version) VALUES (?)", (version,)
        )

    def create_schema_version_table(self) -> None:
        """schema_version テーブルを作成する

        マイグレーションバージョン管理用のテーブルを作成する。

        Example:
            >>> conn = DatabaseConnection(":memory:")
            >>> migration = DatabaseMigration(conn)
            >>> with conn:
            ...     migration.create_schema_version_table()
        """
        sql = """
        CREATE TABLE IF NOT EXISTS schema_version (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version INTEGER NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db_connection.execute_query(sql)

    def create_company_table(self) -> None:
        """company テーブルを作成する

        株式企業情報を格納するメインテーブルを作成する。
        symbol フィールドにUNIQUE制約を設定。

        Example:
            >>> conn = DatabaseConnection(":memory:")
            >>> migration = DatabaseMigration(conn)
            >>> with conn:
            ...     migration.create_company_table()
        """
        sql = """
        CREATE TABLE IF NOT EXISTS company (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            market TEXT,
            business_summary TEXT,
            price REAL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db_connection.execute_query(sql)

        # インデックス作成（検索パフォーマンス向上）
        self.db_connection.execute_query(
            "CREATE INDEX IF NOT EXISTS idx_company_symbol ON company(symbol)"
        )

    def table_exists(self, table_name: str) -> bool:
        """指定したテーブルが存在するかチェックする

        Args:
            table_name: チェックするテーブル名

        Returns:
            テーブルが存在する場合True、存在しない場合False

        Example:
            >>> conn = DatabaseConnection(":memory:")
            >>> migration = DatabaseMigration(conn)
            >>> with conn:
            ...     exists = migration.table_exists("company")
            ...     print(exists)  # False (テーブル未作成)
        """
        cursor = self.db_connection.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        result = cursor.fetchone()
        return result is not None

    def run_migrations(self) -> None:
        """マイグレーションを実行する

        現在のスキーマバージョンをチェックし、必要なマイグレーションを実行する。
        複数回実行しても安全（冪等性）。

        Migration versions:
        - 0 → 1: 初回テーブル作成 (company, schema_version)

        Example:
            >>> conn = DatabaseConnection(":memory:")
            >>> migration = DatabaseMigration(conn)
            >>> with conn:
            ...     migration.run_migrations()
            ...     # 必要なテーブルが作成される
        """
        current_version = self.get_schema_version()

        if current_version == 0:
            self._run_migration_v1()

        # 将来的にバージョン2、3等のマイグレーションをここに追加

    def _run_migration_v1(self) -> None:
        """マイグレーション v0 → v1 を実行

        初回テーブル作成:
        - schema_version テーブル
        - company テーブル
        """
        # schema_version テーブル作成
        self.create_schema_version_table()

        # company テーブル作成
        self.create_company_table()

        # バージョン更新
        self.set_schema_version(1)

    def get_migration_info(self) -> dict[str, Any]:
        """マイグレーション情報を取得する

        デバッグやモニタリング用にマイグレーションの状態情報を返す。

        Returns:
            マイグレーション情報の辞書

        Example:
            >>> conn = DatabaseConnection(":memory:")
            >>> migration = DatabaseMigration(conn)
            >>> with conn:
            ...     migration.run_migrations()
            ...     info = migration.get_migration_info()
            ...     print(info["current_version"])  # 1
        """
        info = {
            "current_version": self.get_schema_version(),
            "available_migrations": [1],  # 将来的に拡張
            "tables": [],
        }

        try:
            cursor = self.db_connection.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = cursor.fetchall()
            info["tables"] = [table[0] for table in tables]
        except sqlite3.Error:
            info["tables"] = []

        return info

    def reset_database(self) -> None:
        """データベースを初期状態にリセットする

        全テーブルを削除し、スキーマバージョンを0に戻す。
        開発・テスト環境での使用を想定。

        WARNING: 本番環境での使用は非推奨

        Example:
            >>> conn = DatabaseConnection(":memory:")
            >>> migration = DatabaseMigration(conn)
            >>> with conn:
            ...     migration.run_migrations()
            ...     migration.reset_database()  # 全て削除
        """
        try:
            # 全テーブルを削除
            cursor = self.db_connection.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = cursor.fetchall()

            for table in tables:
                table_name = table[0]
                if table_name != "sqlite_sequence":  # SQLiteシステムテーブル以外
                    self.db_connection.execute_query(
                        f"DROP TABLE IF EXISTS {table_name}"
                    )

        except sqlite3.Error as e:
            raise RuntimeError(f"データベースリセットに失敗しました: {e}") from e
