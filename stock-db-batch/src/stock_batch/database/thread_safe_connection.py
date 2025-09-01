"""スレッドセーフなSQLiteデータベース接続管理

各スレッドで独立したSQLite接続を管理するThreadLocal Storageアプローチを実装
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from typing import Any

logger = logging.getLogger(__name__)


class ThreadSafeDatabaseConnection:
    """スレッドセーフなSQLiteデータベース接続管理クラス

    Thread Local Storageを使用して各スレッドで独立したSQLite接続を管理する。
    SQLiteの"objects created in a thread can only be used in that same thread"制約を
    回避しながら、真のマルチスレッド処理を可能にする。

    Attributes:
        db_path: データベースファイルのパス
        _local: スレッドローカルストレージ
        _connections: アクティブな接続の追跡用辞書
        _lock: スレッドセーフな操作のためのロック

    Example:
        >>> # 基本的な使用方法
        >>> conn = ThreadSafeDatabaseConnection("/data/stocks.db")
        >>> connection = conn.get_connection()
        >>> cursor = connection.execute("SELECT * FROM company")

        >>> # マルチスレッド環境での使用
        >>> def worker():
        ...     connection = conn.get_connection()  # 各スレッドで独立した接続
        ...     cursor = connection.execute("SELECT COUNT(*) FROM company")
        ...     return cursor.fetchone()[0]
        >>>
        >>> with ThreadPoolExecutor(max_workers=4) as executor:
        ...     results = list(executor.map(lambda _: worker(), range(4)))
    """

    def __init__(self, db_path: str) -> None:
        """ThreadSafeDatabaseConnection を初期化する

        Args:
            db_path: データベースファイルのパス（":memory:" でメモリDB）

        Example:
            >>> conn = ThreadSafeDatabaseConnection("/data/stocks.db")
            >>> conn.db_path
            '/data/stocks.db'
        """
        self.db_path = db_path
        self._local = threading.local()
        self._connections: dict[int, sqlite3.Connection] = {}
        self._lock = threading.Lock()

        logger.debug("ThreadSafeDatabaseConnection初期化: %s", db_path)

    def get_connection(self) -> sqlite3.Connection:
        """現在のスレッド用のSQLite接続を取得する

        スレッドローカルストレージを使用して、各スレッドで独立した接続を管理。
        接続が存在しない場合は新しく作成し、適切なSQLite設定を適用する。

        Returns:
            現在のスレッド専用のSQLite接続オブジェクト

        Raises:
            sqlite3.Error: データベース接続に失敗した場合

        Example:
            >>> conn = ThreadSafeDatabaseConnection(":memory:")
            >>> connection1 = conn.get_connection()
            >>> connection2 = conn.get_connection()
            >>> connection1 is connection2  # 同じスレッドでは同じオブジェクト
            True
        """
        # スレッドローカル接続が存在するかチェック
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self._local.connection = self._create_connection()

            # アクティブな接続を追跡（デバッグ用）
            thread_id = threading.get_ident()
            with self._lock:
                self._connections[thread_id] = self._local.connection
                logger.debug(
                    "新しいスレッド接続作成: thread_id=%s, path=%s",
                    thread_id,
                    self.db_path,
                )

        return self._local.connection

    def _create_connection(self) -> sqlite3.Connection:
        """新しいSQLite接続を作成し、最適化設定を適用する

        Returns:
            設定済みのSQLite接続オブジェクト

        Raises:
            sqlite3.Error: データベース接続または設定に失敗した場合

        Example:
            >>> conn = ThreadSafeDatabaseConnection(":memory:")
            >>> connection = conn._create_connection()
            >>> isinstance(connection, sqlite3.Connection)
            True
        """
        try:
            # SQLite接続を作成
            connection = sqlite3.connect(self.db_path)

            # SQLite設定の最適化を適用
            self._apply_sqlite_settings(connection)

            logger.debug("SQLite接続作成成功: %s", self.db_path)
            return connection

        except sqlite3.Error as e:
            logger.error("SQLite接続作成失敗: %s - %s", self.db_path, e)
            raise e

    def _apply_sqlite_settings(self, connection: sqlite3.Connection) -> None:
        """SQLite接続に最適化設定を適用する

        パフォーマンスとデータ整合性のバランスを取った設定を適用:
        - 外部キー制約を有効化（データ整合性）
        - WALモードを有効化（同時アクセス性能向上）
        - NORMAL同期モード（パフォーマンスとデータ安全性のバランス）

        Args:
            connection: 設定を適用するSQLite接続

        Raises:
            sqlite3.Error: 設定適用に失敗した場合

        Example:
            >>> conn = ThreadSafeDatabaseConnection(":memory:")
            >>> connection = sqlite3.connect(":memory:")
            >>> conn._apply_sqlite_settings(connection)
            >>> # 設定が適用される
        """
        try:
            # 外部キー制約有効化（データ整合性向上）
            connection.execute("PRAGMA foreign_keys = ON")

            # WALモード有効化（Write-Ahead Logging：同時アクセス性能向上）
            connection.execute("PRAGMA journal_mode = WAL")

            # NORMAL同期モード（パフォーマンスとデータ安全性のバランス）
            connection.execute("PRAGMA synchronous = NORMAL")

            # 設定をコミット
            connection.commit()

            logger.debug(
                "SQLite設定適用完了: foreign_keys=ON, journal_mode=WAL, synchronous=NORMAL"
            )

        except sqlite3.Error as e:
            logger.warning("SQLite設定適用に一部失敗: %s - 処理を継続", e)
            # 設定失敗は警告レベルとし、接続自体は使用可能とする

    def get_connection_info(self) -> dict[str, Any]:
        """現在のスレッドの接続情報を取得する

        デバッグやモニタリング用に接続の状態情報を返す。

        Returns:
            接続情報の辞書

        Example:
            >>> conn = ThreadSafeDatabaseConnection(":memory:")
            >>> connection = conn.get_connection()
            >>> info = conn.get_connection_info()
            >>> info['database_path']
            ':memory:'
            >>> info['connected']
            True
        """
        thread_id = threading.get_ident()
        has_connection = (
            hasattr(self._local, "connection") and self._local.connection is not None
        )

        info = {
            "database_path": self.db_path,
            "thread_id": thread_id,
            "connected": has_connection,
            "total_active_connections": len(self._connections),
        }

        if has_connection:
            try:
                cursor = self._local.connection.execute("SELECT sqlite_version()")
                version = cursor.fetchone()
                info["sqlite_version"] = version[0] if version else "unknown"

                # PRAGMA設定の確認
                foreign_keys = self._local.connection.execute(
                    "PRAGMA foreign_keys"
                ).fetchone()[0]
                journal_mode = self._local.connection.execute(
                    "PRAGMA journal_mode"
                ).fetchone()[0]
                synchronous = self._local.connection.execute(
                    "PRAGMA synchronous"
                ).fetchone()[0]

                info["settings"] = {
                    "foreign_keys": bool(foreign_keys),
                    "journal_mode": journal_mode,
                    "synchronous": synchronous,
                }

            except sqlite3.Error as e:
                info["error"] = str(e)

        return info

    def cleanup_connection(self) -> None:
        """現在のスレッドの接続をクリーンアップする

        明示的な接続クリーンアップが必要な場合に使用。
        通常はスレッド終了時に自動的にクリーンアップされる。

        Example:
            >>> conn = ThreadSafeDatabaseConnection(":memory:")
            >>> connection = conn.get_connection()
            >>> conn.cleanup_connection()
            >>> # 次のget_connection()呼び出しで新しい接続が作成される
        """
        thread_id = threading.get_ident()

        if hasattr(self._local, "connection") and self._local.connection is not None:
            try:
                self._local.connection.close()
                logger.debug("スレッド接続クローズ: thread_id=%s", thread_id)
            except sqlite3.Error as e:
                logger.warning("接続クローズ時にエラー: %s", e)
            finally:
                self._local.connection = None

                # 追跡辞書からも削除
                with self._lock:
                    self._connections.pop(thread_id, None)

    def get_active_connections_count(self) -> int:
        """アクティブな接続数を取得する

        Returns:
            現在アクティブな接続の数

        Example:
            >>> conn = ThreadSafeDatabaseConnection(":memory:")
            >>> conn.get_active_connections_count()
            0
            >>> connection = conn.get_connection()
            >>> conn.get_active_connections_count()
            1
        """
        with self._lock:
            return len(self._connections)

    def __repr__(self) -> str:
        """文字列表現を返す"""
        return (
            f"ThreadSafeDatabaseConnection("
            f"db_path='{self.db_path}', "
            f"active_connections={self.get_active_connections_count()})"
        )
