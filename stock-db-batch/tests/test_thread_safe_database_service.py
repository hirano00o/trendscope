"""ThreadSafeDatabaseServiceのテスト

スレッドセーフなデータベースサービス機能をテストする
"""

import sqlite3
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest

from stock_batch.database.thread_safe_connection import ThreadSafeDatabaseConnection
from stock_batch.models.company import Company
from stock_batch.services.thread_safe_database_service import ThreadSafeDatabaseService


class TestThreadSafeDatabaseService:
    """ThreadSafeDatabaseService のテストクラス"""

    def test_init(self) -> None:
        """初期化できることをテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        service = ThreadSafeDatabaseService(conn)
        
        try:
            assert service.db_connection == conn
        finally:
            conn.cleanup_connection()

    def test_setup_database(self) -> None:
        """データベースセットアップできることをテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        service = ThreadSafeDatabaseService(conn)
        
        try:
            # データベースセットアップ
            service.setup_database()
            
            # テーブルが作成されていることを確認
            connection = conn.get_connection()
            cursor = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='company'"
            )
            table = cursor.fetchone()
            assert table is not None
            assert table[0] == "company"
        finally:
            conn.cleanup_connection()

    def test_insert_company_single_thread(self) -> None:
        """シングルスレッドで企業データ挿入をテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        service = ThreadSafeDatabaseService(conn)
        
        try:
            service.setup_database()
            
            company = Company(
                symbol="1332.T",
                name="ニッスイ",
                market="東P",
                business_summary="水産業",
                price=1000.0
            )
            
            result = service.insert_company(company)
            assert result is True
            
            # 挿入されたデータを確認
            retrieved = service.get_company_by_symbol("1332.T")
            assert retrieved is not None
            assert retrieved.symbol == "1332.T"
            assert retrieved.name == "ニッスイ"
            assert retrieved.price == 1000.0
            
        finally:
            conn.cleanup_connection()

    def test_insert_duplicate_company(self) -> None:
        """重複企業データの挿入をテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        service = ThreadSafeDatabaseService(conn)
        
        try:
            service.setup_database()
            
            company = Company(
                symbol="1332.T",
                name="ニッスイ",
                market="東P",
                business_summary="水産業",
                price=1000.0
            )
            
            # 初回挿入は成功
            result1 = service.insert_company(company)
            assert result1 is True
            
            # 重複挿入は失敗
            result2 = service.insert_company(company)
            assert result2 is False
            
        finally:
            conn.cleanup_connection()

    def test_get_company_by_symbol_not_found(self) -> None:
        """存在しない企業データの取得をテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        service = ThreadSafeDatabaseService(conn)
        
        try:
            service.setup_database()
            
            result = service.get_company_by_symbol("NOTFOUND")
            assert result is None
            
        finally:
            conn.cleanup_connection()

    def test_update_company(self) -> None:
        """企業データの更新をテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        service = ThreadSafeDatabaseService(conn)
        
        try:
            service.setup_database()
            
            # データ挿入
            company = Company(
                symbol="1332.T",
                name="ニッスイ",
                market="東P", 
                business_summary="水産業",
                price=1000.0
            )
            service.insert_company(company)
            
            # データ更新
            updated_company = Company(
                symbol="1332.T",
                name="日本水産",
                market="東P",
                business_summary="水産加工業",
                price=1100.0
            )
            result = service.update_company(updated_company)
            assert result is True
            
            # 更新されたデータを確認
            retrieved = service.get_company_by_symbol("1332.T")
            assert retrieved is not None
            assert retrieved.name == "日本水産"
            assert retrieved.business_summary == "水産加工業"
            assert retrieved.price == 1100.0
            
        finally:
            conn.cleanup_connection()

    def test_update_nonexistent_company(self) -> None:
        """存在しない企業データの更新をテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        service = ThreadSafeDatabaseService(conn)
        
        try:
            service.setup_database()
            
            company = Company(
                symbol="NOTFOUND",
                name="存在しない会社",
                market="東P",
                business_summary="業務内容",
                price=1000.0
            )
            
            result = service.update_company(company)
            assert result is False
            
        finally:
            conn.cleanup_connection()

    def test_delete_company(self) -> None:
        """企業データの削除をテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        service = ThreadSafeDatabaseService(conn)
        
        try:
            service.setup_database()
            
            # データ挿入
            company = Company(
                symbol="1332.T",
                name="ニッスイ",
                market="東P",
                business_summary="水産業",
                price=1000.0
            )
            service.insert_company(company)
            
            # データ削除
            result = service.delete_company("1332.T")
            assert result is True
            
            # 削除されたことを確認
            retrieved = service.get_company_by_symbol("1332.T")
            assert retrieved is None
            
        finally:
            conn.cleanup_connection()

    def test_get_all_companies(self) -> None:
        """全企業データ取得をテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        service = ThreadSafeDatabaseService(conn)
        
        try:
            service.setup_database()
            
            # 複数データ挿入
            companies = [
                Company(symbol="1332.T", name="ニッスイ", market="東P", business_summary="水産業", price=1000.0),
                Company(symbol="7203.T", name="トヨタ", market="東P", business_summary="自動車", price=2000.0),
                Company(symbol="6758.T", name="ソニー", market="東P", business_summary="電機", price=3000.0),
            ]
            
            for company in companies:
                service.insert_company(company)
            
            # 全データ取得
            all_companies = service.get_all_companies()
            assert len(all_companies) == 3
            
            # ソート順の確認（シンボル順）
            symbols = [c.symbol for c in all_companies]
            assert symbols == ["1332.T", "6758.T", "7203.T"]
            
        finally:
            conn.cleanup_connection()

    def test_get_companies_by_market(self) -> None:
        """市場別企業データ取得をテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        service = ThreadSafeDatabaseService(conn)
        
        try:
            service.setup_database()
            
            # 異なる市場のデータ挿入
            companies = [
                Company(symbol="1332.T", name="ニッスイ", market="東P", business_summary="水産業", price=1000.0),
                Company(symbol="7203.T", name="トヨタ", market="東P", business_summary="自動車", price=2000.0),
                Company(symbol="3000.T", name="テスト会社", market="東S", business_summary="テスト", price=1500.0),
            ]
            
            for company in companies:
                service.insert_company(company)
            
            # 東P市場の企業取得
            prime_companies = service.get_companies_by_market("東P")
            assert len(prime_companies) == 2
            symbols = [c.symbol for c in prime_companies]
            assert "1332.T" in symbols
            assert "7203.T" in symbols
            
            # 東S市場の企業取得
            standard_companies = service.get_companies_by_market("東S")
            assert len(standard_companies) == 1
            assert standard_companies[0].symbol == "3000.T"
            
        finally:
            conn.cleanup_connection()

    def test_batch_operations(self) -> None:
        """バッチ操作をテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        service = ThreadSafeDatabaseService(conn)
        
        try:
            service.setup_database()
            
            companies = [
                Company(symbol="1332.T", name="ニッスイ", market="東P", business_summary="水産業", price=1000.0),
                Company(symbol="7203.T", name="トヨタ", market="東P", business_summary="自動車", price=2000.0),
                Company(symbol="6758.T", name="ソニー", market="東P", business_summary="電機", price=3000.0),
            ]
            
            # バッチ挿入
            result = service.batch_insert_companies(companies)
            assert result["successful"] == 3
            assert result["failed"] == 0
            assert len(result["failed_symbols"]) == 0
            
            # データが挿入されていることを確認
            all_companies = service.get_all_companies()
            assert len(all_companies) == 3
            
        finally:
            conn.cleanup_connection()

    def test_upsert_companies(self) -> None:
        """upsert操作をテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        service = ThreadSafeDatabaseService(conn)
        
        try:
            service.setup_database()
            
            # 初期データ挿入
            initial_company = Company(
                symbol="1332.T", 
                name="ニッスイ", 
                market="東P", 
                business_summary="水産業", 
                price=1000.0
            )
            service.insert_company(initial_company)
            
            # upsertデータ（既存1件の更新 + 新規2件の挿入）
            upsert_companies = [
                Company(symbol="1332.T", name="日本水産", market="東P", business_summary="水産加工業", price=1100.0),  # 更新
                Company(symbol="7203.T", name="トヨタ", market="東P", business_summary="自動車", price=2000.0),        # 新規
                Company(symbol="6758.T", name="ソニー", market="東P", business_summary="電機", price=3000.0),          # 新規
            ]
            
            result = service.upsert_companies(upsert_companies)
            assert result["inserted"] == 2
            assert result["updated"] == 1
            assert result["failed"] == 0
            
            # データ確認
            updated_company = service.get_company_by_symbol("1332.T")
            assert updated_company is not None
            assert updated_company.name == "日本水産"
            
            all_companies = service.get_all_companies()
            assert len(all_companies) == 3
            
        finally:
            conn.cleanup_connection()

    def test_multithreaded_operations(self) -> None:
        """マルチスレッド操作をテストする"""
        # メモリDBではなくファイルDBを使用（スレッド間でテーブルを共有するため）
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        try:
            conn = ThreadSafeDatabaseConnection(db_path)
            service = ThreadSafeDatabaseService(conn)
            
            # メインスレッドでデータベースセットアップ
            service.setup_database()
            
            results = []
            errors = []
            
            def worker(worker_id: int) -> None:
                try:
                    # 各スレッドで独自の企業データを作成・挿入
                    company = Company(
                        symbol=f"TEST{worker_id:04d}.T",
                        name=f"テスト会社{worker_id}",
                        market="東P",
                        business_summary=f"テスト業務{worker_id}",
                        price=1000.0 + worker_id
                    )
                    
                    success = service.insert_company(company)
                    
                    if success:
                        # 挿入したデータを取得して確認
                        retrieved = service.get_company_by_symbol(company.symbol)
                        if retrieved:
                            results.append((worker_id, company.symbol, retrieved.name))
                        else:
                            errors.append((worker_id, "Retrieved data is None"))
                    else:
                        errors.append((worker_id, "Insert failed"))
                        
                except Exception as e:
                    errors.append((worker_id, str(e)))
            
            # 10個のワーカーで並列実行
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(worker, i) for i in range(10)]
                for future in as_completed(futures):
                    future.result()  # 例外があれば再発生
            
            # エラーが発生しなかったことを確認
            assert len(errors) == 0, f"Errors occurred: {errors}"
            assert len(results) == 10
            
            # 全データが正しく挿入されていることを確認
            all_companies = service.get_all_companies()
            assert len(all_companies) == 10
            
            # 各ワーカーのデータが正しく挿入されていることを確認
            for worker_id, symbol, name in results:
                expected_symbol = f"TEST{worker_id:04d}.T"
                expected_name = f"テスト会社{worker_id}"
                assert symbol == expected_symbol
                assert name == expected_name
                
        finally:
            conn.cleanup_connection()
            # ファイルクリーンアップ
            Path(db_path).unlink(missing_ok=True)

    def test_concurrent_read_operations(self) -> None:
        """並行読み取り操作をテストする"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        try:
            conn = ThreadSafeDatabaseConnection(db_path)
            service = ThreadSafeDatabaseService(conn)
            
            # データベースセットアップとテストデータ挿入
            service.setup_database()
            
            test_companies = [
                Company(symbol=f"READ{i:03d}.T", name=f"読み取りテスト{i}", market="東P", business_summary="テスト", price=1000.0 + i)
                for i in range(20)
            ]
            
            # テストデータ挿入
            for company in test_companies:
                service.insert_company(company)
            
            results = []
            errors = []
            
            def reader_worker(worker_id: int) -> None:
                try:
                    # 各ワーカーで複数の読み取り操作
                    worker_results = []
                    
                    # 個別データ取得
                    for i in range(5):
                        symbol = f"READ{(worker_id * 5 + i) % 20:03d}.T"
                        company = service.get_company_by_symbol(symbol)
                        if company:
                            worker_results.append(f"get_{symbol}")
                    
                    # 全データ取得
                    all_companies = service.get_all_companies()
                    worker_results.append(f"all_{len(all_companies)}")
                    
                    # 市場別データ取得
                    market_companies = service.get_companies_by_market("東P")
                    worker_results.append(f"market_{len(market_companies)}")
                    
                    results.append((worker_id, worker_results))
                    
                except Exception as e:
                    errors.append((worker_id, str(e)))
            
            # 8個のワーカーで並行読み取り
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(reader_worker, i) for i in range(8)]
                for future in as_completed(futures):
                    future.result()
            
            # エラーが発生しなかったことを確認
            assert len(errors) == 0, f"Read errors occurred: {errors}"
            assert len(results) == 8
            
            # 各ワーカーが正しくデータを読み取れたことを確認
            for worker_id, worker_results in results:
                # 個別取得が成功していること
                get_results = [r for r in worker_results if r.startswith("get_")]
                assert len(get_results) == 5
                
                # 全データ取得が成功していること  
                all_results = [r for r in worker_results if r.startswith("all_")]
                assert len(all_results) == 1
                assert all_results[0] == "all_20"
                
                # 市場別取得が成功していること
                market_results = [r for r in worker_results if r.startswith("market_")]
                assert len(market_results) == 1
                assert market_results[0] == "market_20"
                
        finally:
            conn.cleanup_connection()
            # ファイルクリーンアップ
            Path(db_path).unlink(missing_ok=True)

    def test_mixed_concurrent_operations(self) -> None:
        """読み取りと書き込みの混在した並行操作をテストする"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        try:
            conn = ThreadSafeDatabaseConnection(db_path)
            service = ThreadSafeDatabaseService(conn)
            
            service.setup_database()
            
            # 初期データ挿入
            initial_companies = [
                Company(symbol=f"INIT{i:03d}.T", name=f"初期会社{i}", market="東P", business_summary="初期テスト", price=1000.0)
                for i in range(10)
            ]
            
            for company in initial_companies:
                service.insert_company(company)
            
            read_results = []
            write_results = []
            errors = []
            
            def reader_worker(worker_id: int) -> None:
                try:
                    for _ in range(10):  # 各リーダーで10回読み取り
                        all_companies = service.get_all_companies()
                        read_results.append((worker_id, len(all_companies)))
                        time.sleep(0.01)  # 短い待機
                except Exception as e:
                    errors.append((f"reader_{worker_id}", str(e)))
            
            def writer_worker(worker_id: int) -> None:
                try:
                    for i in range(5):  # 各ライターで5件挿入
                        company = Company(
                            symbol=f"WRITE{worker_id:02d}{i:02d}.T",
                            name=f"書き込み会社{worker_id}_{i}",
                            market="東P",
                            business_summary="書き込みテスト",
                            price=2000.0 + worker_id * 10 + i
                        )
                        success = service.insert_company(company)
                        write_results.append((worker_id, i, success))
                        time.sleep(0.02)  # 短い待機
                except Exception as e:
                    errors.append((f"writer_{worker_id}", str(e)))
            
            # 3個のリーダーと2個のライターを並行実行
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = []
                
                # リーダー起動
                for i in range(3):
                    futures.append(executor.submit(reader_worker, i))
                
                # ライター起動
                for i in range(2):
                    futures.append(executor.submit(writer_worker, i))
                
                # 全完了まで待機
                for future in as_completed(futures):
                    future.result()
            
            # エラーが発生しなかったことを確認
            assert len(errors) == 0, f"Mixed operation errors: {errors}"
            
            # リーダーが正常に動作したことを確認
            assert len(read_results) == 30  # 3 readers * 10 reads
            
            # ライターが正常に動作したことを確認
            assert len(write_results) == 10  # 2 writers * 5 writes
            successful_writes = [r for r in write_results if r[2] is True]
            assert len(successful_writes) == 10
            
            # 最終的なデータ数確認
            final_companies = service.get_all_companies()
            assert len(final_companies) == 20  # 初期10件 + 書き込み10件
            
        finally:
            conn.cleanup_connection()
            # ファイルクリーンアップ
            Path(db_path).unlink(missing_ok=True)

    def test_get_database_stats(self) -> None:
        """データベース統計情報取得をテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        service = ThreadSafeDatabaseService(conn)
        
        try:
            service.setup_database()
            
            # 初期状態の統計
            stats = service.get_database_stats()
            assert stats["total_companies"] == 0
            assert stats["markets"] == {}
            
            # データ挿入
            companies = [
                Company(symbol="1332.T", name="ニッスイ", market="東P", business_summary="水産業", price=1000.0),
                Company(symbol="7203.T", name="トヨタ", market="東P", business_summary="自動車", price=2000.0),
                Company(symbol="3000.T", name="テスト会社", market="東S", business_summary="テスト", price=1500.0),
            ]
            
            for company in companies:
                service.insert_company(company)
            
            # データ挿入後の統計
            stats = service.get_database_stats()
            assert stats["total_companies"] == 3
            assert stats["markets"]["東P"] == 2
            assert stats["markets"]["東S"] == 1
            assert stats["last_updated"] is not None
            
        finally:
            conn.cleanup_connection()

    def test_find_companies_needing_update(self) -> None:
        """更新が必要な企業の検出をテストする"""
        conn = ThreadSafeDatabaseConnection(":memory:")
        service = ThreadSafeDatabaseService(conn)
        
        try:
            service.setup_database()
            
            # 既存データ挿入
            existing_companies = [
                Company(symbol="1332.T", name="ニッスイ", market="東P", business_summary="水産業", price=1000.0),
                Company(symbol="7203.T", name="トヨタ", market="東P", business_summary="自動車", price=2000.0),
            ]
            
            for company in existing_companies:
                service.insert_company(company)
            
            # CSVデータ（更新、新規、変更なし）
            csv_companies = [
                Company(symbol="1332.T", name="日本水産", market="東P", business_summary="水産加工業", price=1100.0),  # 更新
                Company(symbol="7203.T", name="トヨタ", market="東P", business_summary="自動車", price=2000.0),      # 変更なし
                Company(symbol="6758.T", name="ソニー", market="東P", business_summary="電機", price=3000.0),        # 新規
            ]
            
            diff = service.find_companies_needing_update(csv_companies)
            
            assert len(diff["to_insert"]) == 1
            assert diff["to_insert"][0].symbol == "6758.T"
            
            assert len(diff["to_update"]) == 1
            assert diff["to_update"][0].symbol == "1332.T"
            assert diff["to_update"][0].name == "日本水産"
            
            assert len(diff["no_change"]) == 1
            assert diff["no_change"][0].symbol == "7203.T"
            
        finally:
            conn.cleanup_connection()

    def test_thread_safety_with_database_recreation(self) -> None:
        """データベース再作成を含むスレッドセーフ性をテストする"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        try:
            conn = ThreadSafeDatabaseConnection(db_path)
            service = ThreadSafeDatabaseService(conn)
            
            results = []
            errors = []
            
            def worker(worker_id: int) -> None:
                try:
                    # 各スレッドでデータベースセットアップを試行
                    service.setup_database()
                    
                    # データ挿入
                    company = Company(
                        symbol=f"DB{worker_id:03d}.T",
                        name=f"DB会社{worker_id}",
                        market="東P",
                        business_summary="DB テスト",
                        price=1000.0 + worker_id
                    )
                    
                    success = service.insert_company(company)
                    results.append((worker_id, success))
                    
                except Exception as e:
                    errors.append((worker_id, str(e)))
            
            # 複数スレッドで同時実行
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(worker, i) for i in range(10)]
                for future in as_completed(futures):
                    future.result()
            
            # エラーが発生しなかったことを確認
            assert len(errors) == 0, f"Database recreation errors: {errors}"
            assert len(results) == 10
            
            # 最終的なデータ確認
            final_companies = service.get_all_companies()
            assert len(final_companies) == 10
            
        finally:
            # ファイルクリーンアップ
            Path(db_path).unlink(missing_ok=True)