"""ThreadSafeDifferentialProcessorのテスト

スレッドセーフな差分処理サービスをテストする
"""

import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest

from stock_batch.database.thread_safe_connection import ThreadSafeDatabaseConnection
from stock_batch.models.company import Company
from stock_batch.services.differential_processor import DifferentialProcessor
from stock_batch.services.thread_safe_database_service import ThreadSafeDatabaseService


class TestThreadSafeDifferentialProcessor:
    """ThreadSafeな環境でのDifferentialProcessor のテストクラス"""

    def test_init_with_thread_safe_service(self) -> None:
        """ThreadSafeDatabaseServiceでの初期化テスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        try:
            conn = ThreadSafeDatabaseConnection(db_path)
            service = ThreadSafeDatabaseService(conn)
            processor = DifferentialProcessor(service)
            
            assert processor.db_service == service
            assert processor.chunk_size == 1000
            assert processor.enable_parallel is False
            assert processor.max_workers == 4
        finally:
            conn.cleanup_connection()
            Path(db_path).unlink(missing_ok=True)

    def test_sequential_diff_processing(self) -> None:
        """シーケンシャル差分処理のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        try:
            conn = ThreadSafeDatabaseConnection(db_path)
            service = ThreadSafeDatabaseService(conn)
            processor = DifferentialProcessor(service, enable_parallel=False)
            
            # データベースセットアップ
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
            
            # 差分処理実行
            result = processor.process_diff(csv_companies)
            
            # 結果検証
            assert len(result.to_insert) == 1
            assert result.to_insert[0].symbol == "6758.T"
            
            assert len(result.to_update) == 1 
            assert result.to_update[0].symbol == "1332.T"
            assert result.to_update[0].name == "日本水産"
            
            assert len(result.no_change) == 1
            assert result.no_change[0].symbol == "7203.T"
            
            # サマリー検証
            assert result.summary.total_processed == 3
            assert result.summary.parallel_enabled is False
            assert result.summary.error_count == 0
            assert result.summary.processing_time > 0
            
        finally:
            conn.cleanup_connection()
            Path(db_path).unlink(missing_ok=True)

    def test_parallel_diff_processing(self) -> None:
        """並列差分処理のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        try:
            conn = ThreadSafeDatabaseConnection(db_path)
            service = ThreadSafeDatabaseService(conn)
            processor = DifferentialProcessor(
                service, 
                chunk_size=2, 
                enable_parallel=True, 
                max_workers=3
            )
            
            # データベースセットアップ
            service.setup_database()
            
            # 既存データ挿入（大量データ）
            existing_companies = []
            for i in range(10):
                company = Company(
                    symbol=f"EXIST{i:03d}.T",
                    name=f"既存会社{i}",
                    market="東P",
                    business_summary=f"既存業務{i}",
                    price=1000.0 + i
                )
                existing_companies.append(company)
                service.insert_company(company)
            
            # CSVデータ（更新、新規混在）
            csv_companies = []
            
            # 既存データの一部更新
            for i in range(5):
                company = Company(
                    symbol=f"EXIST{i:03d}.T",
                    name=f"更新会社{i}",
                    market="東P",
                    business_summary=f"更新業務{i}",
                    price=1100.0 + i
                )
                csv_companies.append(company)
            
            # 既存データの一部変更なし
            for i in range(5, 8):
                company = Company(
                    symbol=f"EXIST{i:03d}.T",
                    name=f"既存会社{i}",
                    market="東P",
                    business_summary=f"既存業務{i}",
                    price=1000.0 + i
                )
                csv_companies.append(company)
            
            # 新規データ
            for i in range(5):
                company = Company(
                    symbol=f"NEW{i:03d}.T",
                    name=f"新規会社{i}",
                    market="東P",
                    business_summary=f"新規業務{i}",
                    price=2000.0 + i
                )
                csv_companies.append(company)
            
            # 並列差分処理実行
            result = processor.process_diff(csv_companies)
            
            # 結果検証
            assert len(result.to_insert) == 5  # 新規5件
            assert len(result.to_update) == 5  # 更新5件
            assert len(result.no_change) == 3  # 変更なし3件
            
            # サマリー検証
            assert result.summary.total_processed == 13
            assert result.summary.parallel_enabled is True
            assert result.summary.error_count == 0
            assert result.summary.chunks_processed > 1
            assert result.summary.processing_time > 0
            
            # 新規データの確認
            new_symbols = {c.symbol for c in result.to_insert}
            expected_new = {"NEW000.T", "NEW001.T", "NEW002.T", "NEW003.T", "NEW004.T"}
            assert new_symbols == expected_new
            
            # 更新データの確認
            update_symbols = {c.symbol for c in result.to_update}
            expected_update = {"EXIST000.T", "EXIST001.T", "EXIST002.T", "EXIST003.T", "EXIST004.T"}
            assert update_symbols == expected_update
            
        finally:
            conn.cleanup_connection()
            Path(db_path).unlink(missing_ok=True)

    def test_custom_comparison_function(self) -> None:
        """カスタム比較関数のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        try:
            conn = ThreadSafeDatabaseConnection(db_path)
            service = ThreadSafeDatabaseService(conn)
            
            # 価格変更のみを無視するカスタム比較関数
            def price_insensitive_comparison(existing: Company, new: Company) -> bool:
                """価格以外の変更のみを検出する"""
                return (existing.name.strip() != new.name.strip() or
                        (existing.business_summary or "").strip() != (new.business_summary or "").strip() or
                        (existing.market or "").strip() != (new.market or "").strip())
            
            processor = DifferentialProcessor(
                service, 
                custom_comparison_func=price_insensitive_comparison
            )
            
            # データベースセットアップ
            service.setup_database()
            
            # 既存データ挿入
            existing_company = Company(
                symbol="TEST001.T", 
                name="テスト会社", 
                market="東P", 
                business_summary="テスト業務", 
                price=1000.0
            )
            service.insert_company(existing_company)
            
            # CSVデータ（価格のみ変更）
            csv_companies = [
                Company(
                    symbol="TEST001.T", 
                    name="テスト会社",  # 名前は同じ
                    market="東P", 
                    business_summary="テスト業務",  # 業務も同じ
                    price=1500.0  # 価格のみ変更
                )
            ]
            
            # 差分処理実行
            result = processor.process_diff(csv_companies)
            
            # カスタム比較関数により価格変更は無視されるため、変更なしとして判定される
            assert len(result.to_insert) == 0
            assert len(result.to_update) == 0
            assert len(result.no_change) == 1
            assert result.no_change[0].symbol == "TEST001.T"
            
        finally:
            conn.cleanup_connection()
            Path(db_path).unlink(missing_ok=True)

    def test_concurrent_diff_processing(self) -> None:
        """並行差分処理のスレッドセーフ性テスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        try:
            conn = ThreadSafeDatabaseConnection(db_path)
            service = ThreadSafeDatabaseService(conn)
            service.setup_database()
            
            # 共通の既存データ挿入
            base_companies = []
            for i in range(20):
                company = Company(
                    symbol=f"BASE{i:03d}.T",
                    name=f"基本会社{i}",
                    market="東P",
                    business_summary=f"基本業務{i}",
                    price=1000.0 + i
                )
                base_companies.append(company)
                service.insert_company(company)
            
            results = []
            errors = []
            
            def worker(worker_id: int) -> None:
                try:
                    # 各ワーカー専用のProcessorインスタンス
                    processor = DifferentialProcessor(
                        service,
                        chunk_size=5,
                        enable_parallel=True,
                        max_workers=2
                    )
                    
                    # 各ワーカーで独自のCSVデータを作成
                    csv_companies = []
                    
                    # 既存データの更新
                    for i in range(5):
                        idx = (worker_id * 5 + i) % 20
                        company = Company(
                            symbol=f"BASE{idx:03d}.T",
                            name=f"更新会社{worker_id}_{i}",
                            market="東P", 
                            business_summary=f"更新業務{worker_id}_{i}",
                            price=2000.0 + worker_id * 10 + i
                        )
                        csv_companies.append(company)
                    
                    # 新規データ
                    for i in range(3):
                        company = Company(
                            symbol=f"WORKER{worker_id:02d}NEW{i:02d}.T",
                            name=f"新規会社{worker_id}_{i}",
                            market="東P",
                            business_summary=f"新規業務{worker_id}_{i}",
                            price=3000.0 + worker_id * 10 + i
                        )
                        csv_companies.append(company)
                    
                    # 差分処理実行
                    result = processor.process_diff(csv_companies)
                    
                    results.append({
                        'worker_id': worker_id,
                        'to_insert_count': len(result.to_insert),
                        'to_update_count': len(result.to_update),
                        'no_change_count': len(result.no_change),
                        'total_processed': result.summary.total_processed,
                        'parallel_enabled': result.summary.parallel_enabled,
                        'error_count': result.summary.error_count
                    })
                    
                except Exception as e:
                    errors.append((worker_id, str(e)))
            
            # 4つのワーカーで並行実行
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(worker, i) for i in range(4)]
                for future in as_completed(futures):
                    future.result()  # 例外があれば再発生
            
            # エラーが発生しなかったことを確認
            assert len(errors) == 0, f"Errors occurred: {errors}"
            assert len(results) == 4
            
            # 各ワーカーの結果確認
            for result in results:
                assert result['to_insert_count'] == 3  # 各ワーカーで新規3件
                assert result['to_update_count'] == 5  # 各ワーカーで更新5件
                assert result['no_change_count'] == 0  # 変更なしは0件（すべて更新）
                assert result['total_processed'] == 8
                assert result['parallel_enabled'] is True
                assert result['error_count'] == 0
                
        finally:
            conn.cleanup_connection()
            Path(db_path).unlink(missing_ok=True)

    def test_memory_optimization(self) -> None:
        """メモリ最適化機能のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        try:
            conn = ThreadSafeDatabaseConnection(db_path)
            service = ThreadSafeDatabaseService(conn)
            processor = DifferentialProcessor(
                service,
                chunk_size=10,
                enable_memory_optimization=True,
                enable_performance_metrics=True
            )
            
            # データベースセットアップ
            service.setup_database()
            
            # 大量の既存データ挿入
            for i in range(50):
                company = Company(
                    symbol=f"MEM{i:03d}.T",
                    name=f"メモリテスト{i}",
                    market="東P",
                    business_summary=f"メモリ最適化テスト{i}",
                    price=1000.0 + i
                )
                service.insert_company(company)
            
            # 大量のCSVデータ作成
            csv_companies = []
            for i in range(75):  # 既存50件 + 新規25件
                company = Company(
                    symbol=f"MEM{i:03d}.T",
                    name=f"更新メモリテスト{i}",
                    market="東P",
                    business_summary=f"更新メモリ最適化テスト{i}",
                    price=1100.0 + i
                )
                csv_companies.append(company)
            
            # メモリ最適化差分処理実行
            result = processor.process_diff(csv_companies)
            
            # 結果検証
            assert len(result.to_insert) == 25  # 新規25件
            assert len(result.to_update) == 50  # 更新50件
            assert len(result.no_change) == 0
            
            # メモリ使用量が記録されていることを確認
            assert result.summary.memory_usage_mb >= 0
            assert result.summary.processing_time > 0
            assert result.summary.records_per_second > 0
            
        finally:
            conn.cleanup_connection()
            Path(db_path).unlink(missing_ok=True)

    def test_processing_stats(self) -> None:
        """処理統計情報のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        try:
            conn = ThreadSafeDatabaseConnection(db_path)
            service = ThreadSafeDatabaseService(conn)
            processor = DifferentialProcessor(service, enable_performance_metrics=True)
            
            # データベースセットアップ
            service.setup_database()
            
            # 初期統計確認
            stats = processor.get_processing_stats()
            assert stats["total_runs"] == 0
            assert stats["total_records_processed"] == 0
            assert stats["total_processing_time"] == 0.0
            assert stats["average_processing_time"] == 0.0
            assert stats["last_run_summary"] is None
            
            # テストデータ作成・処理
            csv_companies = [
                Company(symbol="STATS001.T", name="統計テスト1", market="東P", business_summary="統計", price=1000.0),
                Company(symbol="STATS002.T", name="統計テスト2", market="東P", business_summary="統計", price=2000.0),
            ]
            
            # 1回目の処理
            result1 = processor.process_diff(csv_companies)
            
            # 統計更新確認
            stats = processor.get_processing_stats()
            assert stats["total_runs"] == 1
            assert stats["total_records_processed"] == 2
            assert stats["total_processing_time"] > 0
            assert stats["average_processing_time"] > 0
            assert stats["last_run_summary"] is not None
            assert stats["last_run_summary"].total_processed == 2
            
            # 2回目の処理
            result2 = processor.process_diff(csv_companies)
            
            # 統計再更新確認
            stats = processor.get_processing_stats()
            assert stats["total_runs"] == 2
            assert stats["total_records_processed"] == 4
            assert stats["total_processing_time"] > result1.summary.processing_time
            
            # 統計リセット
            processor.reset_stats()
            stats = processor.get_processing_stats()
            assert stats["total_runs"] == 0
            assert stats["total_records_processed"] == 0
            assert stats["total_processing_time"] == 0.0
            assert stats["last_run_summary"] is None
            
        finally:
            conn.cleanup_connection()
            Path(db_path).unlink(missing_ok=True)

    def test_error_handling(self) -> None:
        """エラーハンドリングのテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        try:
            conn = ThreadSafeDatabaseConnection(db_path)
            service = ThreadSafeDatabaseService(conn)
            processor = DifferentialProcessor(service)
            
            # データベースセットアップなしで処理実行
            csv_companies = [
                Company(symbol="ERROR001.T", name="エラーテスト", market="東P", business_summary="エラー", price=1000.0)
            ]
            
            # 処理実行（テーブルがない場合でも正常に処理される）
            result = processor.process_diff(csv_companies)
            
            # テーブルが存在しない場合、すべて新規挿入として扱われる
            assert len(result.to_insert) == 1
            assert len(result.to_update) == 0
            assert len(result.no_change) == 0
            assert result.summary.total_processed == 1
            assert result.summary.error_count == 0  # エラーではなく正常な動作
            
        finally:
            conn.cleanup_connection()
            Path(db_path).unlink(missing_ok=True)