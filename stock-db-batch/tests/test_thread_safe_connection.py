"""ThreadSafeDatabaseConnectionのテスト

スレッドセーフなSQLite接続管理機能をテストする
"""

import os
import sqlite3
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest

from stock_batch.database.thread_safe_connection import ThreadSafeDatabaseConnection


class TestThreadSafeDatabaseConnection:
    """ThreadSafeDatabaseConnection のテストクラス"""

    def test_init_with_memory_db(self) -> None:
        """メモリデータベースで初期化できることをテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        assert conn.db_path == ":memory:"
        assert hasattr(conn, '_local')
        assert hasattr(conn, '_connections')
        assert hasattr(conn, '_lock')

    def test_init_with_file_db(self) -> None:
        """ファイルデータベースで初期化できることをテストする"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        try:
            conn = ThreadSafeDatabaseConnection(db_path)
            assert conn.db_path == db_path
            assert hasattr(conn, '_local')
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_get_connection_single_thread(self) -> None:
        """シングルスレッドで接続を取得できることをテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        connection = conn.get_connection()
        
        try:
            assert isinstance(connection, sqlite3.Connection)
            
            # 同じスレッドでは同じ接続オブジェクトが返されることを確認
            connection2 = conn.get_connection()
            assert connection is connection2
        finally:
            conn.cleanup_connection()

    def test_multiple_threads_independent_connections(self) -> None:
        """複数スレッドで独立した接続が作成されることをテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        results = []
        errors = []
        
        def worker(worker_id: int) -> None:
            try:
                connection = conn.get_connection()
                thread_id = threading.get_ident()
                connection_id = id(connection)
                results.append((worker_id, thread_id, connection_id))
                
                # 接続が実際に使用可能であることを確認
                cursor = connection.execute("SELECT 1")
                assert cursor.fetchone()[0] == 1
                
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # 4つのワーカースレッドで同時実行
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(worker, i) for i in range(4)]
            for future in as_completed(futures):
                future.result()  # 例外があれば再発生
        
        # エラーが発生しなかったことを確認
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 4
        
        # 異なるスレッドでは異なる接続が使用されることを確認
        # （ThreadPoolExecutorではスレッドが再利用される場合があるため、
        #  ユニークなスレッドID数に応じて接続数も変わる）
        connection_ids = [r[2] for r in results]
        thread_ids = [r[1] for r in results]
        unique_thread_ids = set(thread_ids)
        unique_connection_ids = set(connection_ids)
        
        # 少なくとも2つ以上のスレッドで実行されていることを確認
        assert len(unique_thread_ids) >= 2, f"Should have at least 2 different threads, got {len(unique_thread_ids)}"
        
        # スレッド数と接続数が一致することを確認
        assert len(unique_connection_ids) == len(unique_thread_ids), f"Connection count {len(unique_connection_ids)} should match thread count {len(unique_thread_ids)}"

    def test_connection_persistence_in_thread(self) -> None:
        """同一スレッド内で接続が永続化されることをテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        results = []
        
        def worker() -> None:
            # 同じスレッド内で複数回接続取得
            conn1 = conn.get_connection()
            conn2 = conn.get_connection()
            conn3 = conn.get_connection()
            
            # 全て同じオブジェクトであることを確認
            results.append(conn1 is conn2 is conn3)
            results.append((id(conn1), id(conn2), id(conn3)))
        
        thread = threading.Thread(target=worker)
        thread.start()
        thread.join()
        
        assert results[0] is True, "Connections in same thread should be identical"
        ids = results[1]
        assert ids[0] == ids[1] == ids[2], "Connection IDs should be identical"

    def test_connection_isolation_between_threads(self) -> None:
        """スレッド間での接続が分離されていることをテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        results = []
        
        def worker(worker_id: int) -> None:
            connection = conn.get_connection()
            # 各スレッドで独自のテーブルを作成
            table_name = f"test_table_{worker_id}"
            connection.execute(f"CREATE TABLE {table_name} (id INTEGER, value TEXT)")
            connection.execute(f"INSERT INTO {table_name} VALUES (?, ?)", (worker_id, f"value_{worker_id}"))
            
            # データを取得して確認
            cursor = connection.execute(f"SELECT * FROM {table_name}")
            row = cursor.fetchone()
            results.append((worker_id, row))
        
        # 3つのスレッドで同時実行
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 各スレッドが正しくデータを処理できたことを確認
        assert len(results) == 3
        for worker_id, row in results:
            assert row == (worker_id, f"value_{worker_id}")

    def test_sqlite_pragma_settings(self) -> None:
        """SQLite設定が正しく適用されることをテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        connection = conn.get_connection()
        
        try:
            # PRAGMA設定を確認
            foreign_keys = connection.execute("PRAGMA foreign_keys").fetchone()[0]
            assert foreign_keys == 1, "Foreign keys should be enabled"
            
            journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
            # メモリDBではWALモードがサポートされないため、MEMORYまたはWALを許可
            assert journal_mode.upper() in ["WAL", "MEMORY"], f"Journal mode should be WAL or MEMORY, got {journal_mode}"
            
            synchronous = connection.execute("PRAGMA synchronous").fetchone()[0]
            assert synchronous == 1, "Synchronous should be NORMAL"
        finally:
            conn.cleanup_connection()

    def test_connection_error_handling(self) -> None:
        """接続エラーのハンドリングをテストする"""
        # 存在しないディレクトリのパスを指定
        invalid_path = "/nonexistent/directory/test.db"
        conn = ThreadSafeDatabaseConnection(invalid_path)
        
        with pytest.raises(sqlite3.OperationalError):
            conn.get_connection()

    def test_concurrent_connection_creation(self) -> None:
        """同時接続作成の安全性をテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        results = []
        start_event = threading.Event()
        
        def worker(worker_id: int) -> None:
            # 全スレッドが準備完了まで待機
            start_event.wait()
            
            connection = conn.get_connection()
            thread_id = threading.get_ident()
            results.append((worker_id, thread_id, id(connection)))
        
        # 10個のワーカーを準備
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 短時間待機してから全スレッドを同時開始
        time.sleep(0.1)
        start_event.set()
        
        # 全スレッドの完了を待機
        for thread in threads:
            thread.join()
        
        # 全スレッドが正常に完了したことを確認
        assert len(results) == 10
        
        # 各スレッドが異なる接続を持つことを確認
        connection_ids = [r[2] for r in results]
        assert len(set(connection_ids)) == 10

    def test_database_operations_thread_safety(self) -> None:
        """データベース操作のスレッドセーフ性をテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        results = []
        errors = []
        
        def worker(worker_id: int) -> None:
            try:
                connection = conn.get_connection()
                
                # 各スレッドで独自のテーブル作成と操作
                table_name = f"worker_{worker_id}"
                connection.execute(f"""
                    CREATE TABLE {table_name} (
                        id INTEGER PRIMARY KEY,
                        worker_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # データ挿入
                for i in range(5):
                    connection.execute(
                        f"INSERT INTO {table_name} (worker_id) VALUES (?)",
                        (worker_id,)
                    )
                
                # データ取得
                cursor = connection.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                results.append((worker_id, count))
                
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # 5つのワーカーで並列実行
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker, i) for i in range(5)]
            for future in as_completed(futures):
                future.result()
        
        # エラーが発生しなかったことを確認
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        
        # 各ワーカーが正しくデータを挿入できたことを確認
        for worker_id, count in results:
            assert count == 5, f"Worker {worker_id} should have inserted 5 records"

    def test_cleanup_and_resource_management(self) -> None:
        """リソース管理とクリーンアップをテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        
        def worker() -> None:
            connection = conn.get_connection()
            try:
                # 何らかの処理を実行
                connection.execute("CREATE TABLE test (id INTEGER)")
                connection.execute("INSERT INTO test VALUES (1)")
            finally:
                # ワーカースレッドで明示的にクリーンアップ
                # （通常はスレッド終了時に自動的に行われる）
                pass
        
        thread = threading.Thread(target=worker)
        thread.start()
        thread.join()
        
        # スレッド終了後、メインスレッドから新しい接続を取得
        main_connection = conn.get_connection()
        
        try:
            # メインスレッドの接続は別のオブジェクトであることを確認
            assert isinstance(main_connection, sqlite3.Connection)
            
            # メインスレッドでは前のテーブルは見えない（別のメモリDB）
            with pytest.raises(sqlite3.OperationalError):
                main_connection.execute("SELECT * FROM test")
        finally:
            conn.cleanup_connection()