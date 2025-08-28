"""SQLiteデータベース接続管理

SQLiteデータベースへの接続、切断、クエリ実行を管理するクラスを提供
"""

from __future__ import annotations

import sqlite3
from typing import Any


class DatabaseConnection:
    """SQLiteデータベース接続管理クラス

    SQLiteデータベースへの接続を管理し、クエリ実行機能を提供する。
    コンテキストマネージャーとしても使用可能で、自動的な接続・切断をサポート。

    Attributes:
        db_path: データベースファイルのパス
        connection: SQLite接続オブジェクト

    Example:
        >>> # ファイルベースのデータベース
        >>> conn = DatabaseConnection("/data/stocks.db")
        >>> with conn as db:
        ...     cursor = conn.execute_query("SELECT * FROM company")
        ...     results = cursor.fetchall()

        >>> # メモリデータベース
        >>> conn = DatabaseConnection(":memory:")
        >>> conn.connect()
        >>> conn.execute_query("CREATE TABLE test (id INTEGER)")
        >>> conn.disconnect()
    """

    def __init__(self, db_path: str) -> None:
        """DatabaseConnection を初期化する

        Args:
            db_path: データベースファイルのパス（":memory:" でメモリDB）

        Example:
            >>> conn = DatabaseConnection("/data/stocks.db")
            >>> conn.db_path
            "/data/stocks.db"
        """
        self.db_path = db_path
        self.connection: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        """データベースに接続する

        既に接続がある場合は既存の接続を返す。
        SQLiteの設定を最適化（外部キー制約有効、WALモード等）。

        Returns:
            SQLite接続オブジェクト

        Raises:
            sqlite3.Error: データベース接続に失敗した場合

        Example:
            >>> conn = DatabaseConnection(":memory:")
            >>> db = conn.connect()
            >>> isinstance(db, sqlite3.Connection)
            True
        """
        if self.connection is not None:
            return self.connection

        try:
            self.connection = sqlite3.connect(self.db_path)

            # SQLite設定の最適化
            self.connection.execute("PRAGMA foreign_keys = ON")  # 外部キー制約有効
            self.connection.execute("PRAGMA journal_mode = WAL")  # WALモード
            self.connection.execute(
                "PRAGMA synchronous = NORMAL"
            )  # パフォーマンス最適化

            return self.connection

        except sqlite3.Error as e:
            self.connection = None
            raise e

    def disconnect(self) -> None:
        """データベース接続を切断する

        接続がない場合は何もしない（エラーにならない）。

        Example:
            >>> conn = DatabaseConnection(":memory:")
            >>> conn.connect()
            >>> conn.is_connected()
            True
            >>> conn.disconnect()
            >>> conn.is_connected()
            False
        """
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def is_connected(self) -> bool:
        """接続状態を確認する

        Returns:
            接続中の場合True、未接続の場合False

        Example:
            >>> conn = DatabaseConnection(":memory:")
            >>> conn.is_connected()
            False
            >>> conn.connect()
            >>> conn.is_connected()
            True
        """
        return self.connection is not None

    def execute_query(
        self, query: str, parameters: tuple[Any, ...] = ()
    ) -> sqlite3.Cursor:
        """SQLクエリを実行する

        Args:
            query: 実行するSQLクエリ
            parameters: クエリパラメータ（プリペアドステートメント用）

        Returns:
            実行結果のカーソル

        Raises:
            RuntimeError: データベースに接続されていない場合
            sqlite3.Error: SQL実行エラーの場合

        Example:
            >>> conn = DatabaseConnection(":memory:")
            >>> conn.connect()
            >>> cursor = conn.execute_query("SELECT 1 as test")
            >>> result = cursor.fetchone()
            >>> result[0]
            1
        """
        if self.connection is None:
            raise RuntimeError("データベースに接続されていません")

        try:
            cursor = self.connection.execute(query, parameters)
            self.connection.commit()  # 自動コミット
            return cursor
        except sqlite3.Error as e:
            self.connection.rollback()  # エラー時はロールバック
            raise e

    def execute_many(
        self, query: str, parameters_list: list[tuple[Any, ...]]
    ) -> sqlite3.Cursor:
        """バッチでSQLクエリを実行する

        大量データの挿入・更新時に効率的な処理を提供。

        Args:
            query: 実行するSQLクエリ
            parameters_list: パラメータのリスト

        Returns:
            実行結果のカーソル

        Raises:
            RuntimeError: データベースに接続されていない場合
            sqlite3.Error: SQL実行エラーの場合

        Example:
            >>> conn = DatabaseConnection(":memory:")
            >>> conn.connect()
            >>> conn.execute_query("CREATE TABLE test (id INTEGER, name TEXT)")
            >>> data = [(1, "テスト1"), (2, "テスト2")]
            >>> cursor = conn.execute_many("INSERT INTO test VALUES (?, ?)", data)
        """
        if self.connection is None:
            raise RuntimeError("データベースに接続されていません")

        try:
            cursor = self.connection.executemany(query, parameters_list)
            self.connection.commit()  # 自動コミット
            return cursor
        except sqlite3.Error as e:
            self.connection.rollback()  # エラー時はロールバック
            raise e

    def get_database_info(self) -> dict[str, Any]:
        """データベース情報を取得する

        デバッグやモニタリング用にデータベースの状態情報を返す。

        Returns:
            データベース情報の辞書

        Example:
            >>> conn = DatabaseConnection(":memory:")
            >>> conn.connect()
            >>> info = conn.get_database_info()
            >>> "sqlite_version" in info
            True
            >>> info["connected"]
            True
        """
        info = {
            "database_path": self.db_path,
            "connected": self.is_connected(),
        }

        if self.is_connected() and self.connection is not None:
            cursor = self.connection.execute("SELECT sqlite_version()")
            version = cursor.fetchone()
            info["sqlite_version"] = version[0] if version else "unknown"

        return info

    def __enter__(self) -> sqlite3.Connection:
        """コンテキストマネージャーのenter処理

        withブロック開始時に自動的にデータベースに接続する。

        Returns:
            SQLite接続オブジェクト

        Example:
            >>> conn = DatabaseConnection(":memory:")
            >>> with conn as db:
            ...     cursor = db.execute("SELECT 1")
        """
        return self.connect()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """コンテキストマネージャーのexit処理

        withブロック終了時に自動的にデータベース接続を切断する。
        例外が発生した場合はロールバックを実行。

        Args:
            exc_type: 例外の型
            exc_val: 例外のインスタンス
            exc_tb: トレースバック情報

        Example:
            >>> conn = DatabaseConnection(":memory:")
            >>> with conn as db:
            ...     # 何らかの処理
            ...     pass
            # ここで自動的に切断される
        """
        if exc_type is not None and self.connection is not None:
            # 例外発生時はロールバック
            self.connection.rollback()

        self.disconnect()
