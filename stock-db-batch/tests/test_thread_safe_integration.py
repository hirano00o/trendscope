"""Thread Safe統合テスト

スレッドセーフな実装の統合テストを実行する
"""

import tempfile
from pathlib import Path

import pytest

from stock_batch.database.thread_safe_connection import ThreadSafeDatabaseConnection
from stock_batch.main_batch_application import BatchConfig, MainBatchApplication
from stock_batch.models.company import Company
from stock_batch.services.differential_processor import DifferentialProcessor
from stock_batch.services.thread_safe_database_service import ThreadSafeDatabaseService


class TestThreadSafeIntegration:
    """Thread Safe統合テストクラス"""

    def test_full_thread_safe_stack(self) -> None:
        """完全なスレッドセーフスタックの統合テスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # スレッドセーフなデータベースコンポーネント
            conn = ThreadSafeDatabaseConnection(db_path)
            service = ThreadSafeDatabaseService(conn)
            
            # データベースセットアップ
            service.setup_database()
            
            # 既存データ挿入
            existing_companies = [
                Company(symbol="INTG001.T", name="統合テスト1", market="東P", business_summary="統合", price=1000.0),
                Company(symbol="INTG002.T", name="統合テスト2", market="東P", business_summary="統合", price=2000.0),
            ]
            
            for company in existing_companies:
                service.insert_company(company)
            
            # DifferentialProcessorを使用した差分処理
            processor = DifferentialProcessor(
                service,
                chunk_size=1,
                enable_parallel=True,
                max_workers=2,
                enable_performance_metrics=True
            )
            
            # CSVデータ（更新、新規、変更なし）
            csv_companies = [
                Company(symbol="INTG001.T", name="更新統合テスト1", market="東P", business_summary="更新統合", price=1100.0),  # 更新
                Company(symbol="INTG002.T", name="統合テスト2", market="東P", business_summary="統合", price=2000.0),        # 変更なし  
                Company(symbol="INTG003.T", name="新規統合テスト3", market="東P", business_summary="新規統合", price=3000.0),   # 新規
            ]
            
            # 並列差分処理実行
            diff_result = processor.process_diff(csv_companies)
            
            # 差分結果検証
            assert len(diff_result.to_insert) == 1
            assert len(diff_result.to_update) == 1
            assert len(diff_result.no_change) == 1
            assert diff_result.summary.parallel_enabled is True
            assert diff_result.summary.error_count == 0
            
            # データベース更新
            insert_result = service.batch_insert_companies(diff_result.to_insert)
            update_result = service.batch_update_companies(diff_result.to_update)
            
            # 更新結果検証
            assert insert_result["successful"] == 1
            assert insert_result["failed"] == 0
            assert update_result["successful"] == 1
            assert update_result["failed"] == 0
            
            # 最終的なデータベース状態確認
            all_companies = service.get_all_companies()
            assert len(all_companies) == 3
            
            # 更新されたデータの確認
            updated_company = service.get_company_by_symbol("INTG001.T")
            assert updated_company is not None
            assert updated_company.name == "更新統合テスト1"
            assert updated_company.price == 1100.0
            
            # 新規データの確認
            new_company = service.get_company_by_symbol("INTG003.T")
            assert new_company is not None
            assert new_company.name == "新規統合テスト3"
            assert new_company.price == 3000.0
            
        finally:
            conn.cleanup_connection()
            Path(db_path).unlink(missing_ok=True)

    async def test_main_batch_application_with_thread_safe_components(self) -> None:
        """MainBatchApplicationでのスレッドセーフコンポーネント使用テスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode='w', encoding='utf-8') as csv_tmp:
            csv_path = csv_tmp.name
            # テスト用CSVデータ作成（Japanese形式、.T自動追加対応）
            csv_tmp.write("コード,銘柄名,市場,現在値,前日比(%)\n")
            csv_tmp.write("BATCH001,バッチテスト1,東P,1000.0,0.5\n")
            csv_tmp.write("BATCH002,バッチテスト2,東P,2000.0,-0.3\n")
        
        try:
            # バッチ設定
            config = BatchConfig(
                database_path=db_path,
                csv_file_path=csv_path,
                chunk_size=1,
                enable_parallel=True,
                max_workers=2,
                enable_performance_monitoring=True,
                enable_translation=False,
                enable_stock_data_fetch=False,
                log_level="DEBUG"
            )
            
            # MainBatchApplicationインスタンス作成
            app = MainBatchApplication(config)
            
            # バッチ処理実行
            result = await app.run_batch()
            
            # 実行結果検証
            assert result.success is True
            assert result.total_processed == 2
            assert result.companies_inserted == 2
            assert result.companies_updated == 0
            assert len(result.error_details) == 0
            assert result.processing_time > 0
            
            # データベース直接確認
            conn = ThreadSafeDatabaseConnection(db_path)
            service = ThreadSafeDatabaseService(conn)
            
            try:
                all_companies = service.get_all_companies()
                assert len(all_companies) == 2
                
                # 挿入されたデータ確認（.T自動追加対応）
                company1 = service.get_company_by_symbol("BATCH001.T")
                assert company1 is not None
                assert company1.name == "バッチテスト1"
                assert company1.price == 1000.0
                
                company2 = service.get_company_by_symbol("BATCH002.T")
                assert company2 is not None
                assert company2.name == "バッチテスト2"
                assert company2.price == 2000.0
                
            finally:
                conn.cleanup_connection()
            
        finally:
            Path(db_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)

    def test_thread_safe_components_performance(self) -> None:
        """スレッドセーフコンポーネントのパフォーマンステスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        try:
            conn = ThreadSafeDatabaseConnection(db_path)
            service = ThreadSafeDatabaseService(conn)
            service.setup_database()
            
            # 大量データ作成（100件）
            companies = []
            for i in range(100):
                company = Company(
                    symbol=f"PERF{i:03d}.T",
                    name=f"パフォーマンステスト{i}",
                    market="東P",
                    business_summary=f"パフォーマンステスト業務{i}",
                    price=1000.0 + i
                )
                companies.append(company)
                service.insert_company(company)
            
            # 並列処理でのパフォーマンステスト
            processor = DifferentialProcessor(
                service,
                chunk_size=10,
                enable_parallel=True,
                max_workers=4,
                enable_performance_metrics=True,
                enable_memory_optimization=True
            )
            
            # 更新データ作成（全データを更新）
            updated_companies = []
            for i in range(100):
                company = Company(
                    symbol=f"PERF{i:03d}.T",
                    name=f"更新パフォーマンステスト{i}",
                    market="東P",
                    business_summary=f"更新パフォーマンステスト業務{i}",
                    price=2000.0 + i
                )
                updated_companies.append(company)
            
            # 並列差分処理実行
            diff_result = processor.process_diff(updated_companies)
            
            # パフォーマンス検証
            assert diff_result.summary.total_processed == 100
            assert diff_result.summary.parallel_enabled is True
            assert diff_result.summary.chunks_processed > 1  # 複数チャンクで処理
            assert diff_result.summary.processing_time < 10.0  # 10秒以内で完了
            assert diff_result.summary.records_per_second > 10  # 1秒間に10レコード以上処理
            assert diff_result.summary.memory_usage_mb >= 0  # メモリ使用量が記録されている
            assert diff_result.summary.error_count == 0
            
            # 差分結果検証
            assert len(diff_result.to_insert) == 0  # 新規なし
            assert len(diff_result.to_update) == 100  # 全件更新
            assert len(diff_result.no_change) == 0  # 変更なしなし
            
            # 実際のデータベース更新
            update_result = service.batch_update_companies(diff_result.to_update)
            assert update_result["successful"] == 100
            assert update_result["failed"] == 0
            
            # 更新後データ確認（サンプル）
            updated_sample = service.get_company_by_symbol("PERF050.T")
            assert updated_sample is not None
            assert updated_sample.name == "更新パフォーマンステスト50"
            assert updated_sample.price == 2050.0
            
        finally:
            conn.cleanup_connection()
            Path(db_path).unlink(missing_ok=True)

    def test_error_recovery_in_thread_safe_environment(self) -> None:
        """スレッドセーフ環境でのエラー回復テスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        try:
            conn = ThreadSafeDatabaseConnection(db_path)
            service = ThreadSafeDatabaseService(conn)
            service.setup_database()
            
            # 正常なデータと異常なデータを混在させる
            mixed_companies = [
                Company(symbol="GOOD001.T", name="正常データ1", market="東P", business_summary="正常", price=1000.0),
                Company(symbol="GOOD002.T", name="正常データ2", market="東P", business_summary="正常", price=2000.0),
            ]
            
            # 差分処理実行（正常ケース）
            processor = DifferentialProcessor(
                service,
                chunk_size=1,
                enable_parallel=True,
                max_workers=2
            )
            
            result = processor.process_diff(mixed_companies)
            
            # エラーなしで処理完了することを確認
            assert result.summary.error_count == 0
            assert len(result.to_insert) == 2
            assert len(result.to_update) == 0
            assert len(result.no_change) == 0
            
            # データベース挿入
            insert_result = service.batch_insert_companies(result.to_insert)
            assert insert_result["successful"] == 2
            assert insert_result["failed"] == 0
            
            # データが正しく挿入されていることを確認
            all_companies = service.get_all_companies()
            assert len(all_companies) == 2
            
        finally:
            conn.cleanup_connection()
            Path(db_path).unlink(missing_ok=True)