"""メイン処理統合機能のテスト

main_batch_application.pyとAsyncBatchProcessorの統合テスト
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from stock_batch.models.company import Company
from stock_batch.services.async_batch_processor import AsyncBatchProcessor
from stock_batch.services.stock_fetcher import StockData, StockFetcher
from stock_batch.services.translation import TranslationService
from stock_batch.main_batch_application import MainBatchApplication, BatchConfig, BatchResult


class TestAsyncMainIntegration:
    """メイン処理統合機能のテストクラス"""

    @pytest.fixture
    def mock_companies(self):
        """テスト用企業データリスト"""
        companies = []
        symbols_data = [
            ("1332.T", "日本水産", "Leading fisheries and food company"),
            ("7203.T", "トヨタ自動車", "Global automotive manufacturer"),
            ("6758.T", "ソニー", "Electronics and entertainment company"),
        ]
        
        for symbol, name, summary in symbols_data:
            company = Company(
                symbol=symbol,
                name=name,
                market="Tokyo",
                business_summary=summary,
                price=1000.0,
            )
            companies.append(company)
        return companies

    @pytest.fixture
    def batch_application(self):
        """テスト用MainBatchApplication"""
        import tempfile
        
        # 一時ファイルパスを作成
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            csv_path = tmp_csv.name
            tmp_csv.write("コード,銘柄名,市場区分,現在値,前日比\n1332,テスト,東P,1000,+1.0\n".encode())

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_path = tmp_db.name

        config = BatchConfig(
            database_path=db_path,
            csv_file_path=csv_path,
            chunk_size=10,
            enable_parallel=False,
            max_workers=2,
            enable_stock_data_fetch=True,
            enable_translation=True,
            dry_run=True,  # テスト時はドライラン
            continue_on_error=True,
        )
        
        return MainBatchApplication(config)

    @pytest.mark.asyncio
    async def test_async_batch_processing_integration(
        self, batch_application, mock_companies
    ):
        """非同期バッチ処理統合テスト"""
        
        # 実際のrun_batch_asyncメソッドをテスト
        # CSV読み込みをモック
        with patch.object(batch_application, '_read_csv_data') as mock_read_csv:
            mock_read_csv.return_value = mock_companies
            
            # 非同期バッチ処理実行
            result = await batch_application.run_batch_async()

        # 結果検証
        assert isinstance(result, BatchResult)
        assert result.success == True
        assert result.total_processed == 3
        assert result.parallel_processing_used == True

    @pytest.mark.asyncio
    async def test_async_batch_with_database_operations(
        self, batch_application, mock_companies
    ):
        """データベース操作を含む非同期バッチ処理テスト"""
        
        # CSV読み込みをモック
        with patch.object(batch_application, '_read_csv_data') as mock_read_csv:
            mock_read_csv.return_value = mock_companies
            
            # 非同期バッチ処理実行（ドライランなのでデータベース操作は実行されない）
            result = await batch_application.run_batch_async()

        # 結果検証
        assert isinstance(result, BatchResult)
        assert result.success == True
        assert result.total_processed == 3
        # ドライランなので挿入・更新件数は0
        assert result.companies_inserted == 0
        assert result.companies_updated == 0

    @pytest.mark.asyncio
    async def test_async_batch_error_handling(
        self, batch_application, mock_companies
    ):
        """非同期バッチ処理エラーハンドリングテスト"""
        
        # CSV読み込みでエラーが発生するケースをテスト
        with patch.object(batch_application, '_read_csv_data') as mock_read_csv:
            mock_read_csv.side_effect = Exception("CSV読み取りエラー")
            
            # エラーハンドリング付きバッチ処理実行
            result = await batch_application.run_batch_async()

        # エラーがあっても結果が返されることを確認
        assert isinstance(result, BatchResult)
        assert result.success == False  # エラーにより失敗
        assert len(result.error_details) > 0  # エラー詳細が記録されている

    @pytest.mark.asyncio
    async def test_performance_comparison_async_vs_sync(
        self, batch_application, mock_companies
    ):
        """非同期処理と同期処理のパフォーマンス比較テスト"""
        
        # 非同期バッチ処理の実行時間を測定
        with patch.object(batch_application, '_read_csv_data') as mock_read_csv:
            mock_read_csv.return_value = mock_companies
            
            start_time = asyncio.get_event_loop().time()
            async_result = await batch_application.run_batch_async()
            async_time = asyncio.get_event_loop().time() - start_time
            
            # 同期バッチ処理の実行時間を測定
            start_time = asyncio.get_event_loop().time()
            sync_result = await batch_application.run_batch()
            sync_time = asyncio.get_event_loop().time() - start_time

        # 結果検証
        assert isinstance(async_result, BatchResult)
        assert isinstance(sync_result, BatchResult)
        assert async_result.success == True
        assert sync_result.success == True
        
        # 非同期処理が並列処理を使用していることを確認
        assert async_result.parallel_processing_used == True
        
        print(f"非同期処理時間: {async_time:.3f}秒")
        print(f"同期処理時間: {sync_time:.3f}秒")

    def test_async_methods_integration_availability(self, batch_application):
        """非同期メソッド統合可用性テスト"""
        # 非同期メソッドがMainBatchApplicationに存在することを確認
        assert hasattr(batch_application, 'run_batch_async')
        
        # メソッドがコルーチン関数であることを確認
        import inspect
        assert inspect.iscoroutinefunction(batch_application.run_batch_async)
        assert inspect.iscoroutinefunction(batch_application._run_async_pipeline)

    @pytest.mark.asyncio
    async def test_resource_management_in_async_processing(
        self, batch_application, mock_companies
    ):
        """非同期処理でのリソース管理テスト"""
        
        # CSV読み込みをモック
        with patch.object(batch_application, '_read_csv_data') as mock_read_csv:
            mock_read_csv.return_value = mock_companies
            
            # 非同期バッチ処理実行
            result = await batch_application.run_batch_async()

        # 結果検証（リソースが適切に管理されたことを確認）
        assert isinstance(result, BatchResult)
        assert result.success == True
        assert result.total_processed == 3
        assert result.processing_time > 0  # 処理時間が記録されている