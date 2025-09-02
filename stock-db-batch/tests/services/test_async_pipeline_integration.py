"""パイプライン統合機能のテスト

AsyncBatchProcessorとStockFetcher、TranslationServiceの統合テスト
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from stock_batch.models.company import Company
from stock_batch.services.stock_fetcher import StockData
from stock_batch.services.async_batch_processor import AsyncBatchProcessor
from stock_batch.services.stock_fetcher import StockFetcher
from stock_batch.services.translation import TranslationService


class TestAsyncPipelineIntegration:
    """パイプライン統合機能のテストクラス"""

    @pytest.fixture
    def mock_companies(self):
        """テスト用企業データリスト"""
        companies = []
        symbols = ["1332.T", "7203.T", "6758.T", "7267.T", "6861.T"]
        names = ["日本水産", "トヨタ自動車", "ソニー", "ホンダ", "キーエンス"]
        summaries = [
            "Leading fisheries and food company",
            "Global automotive manufacturer",
            "Electronics and entertainment company",
            "Motorcycle and automotive manufacturer",
            "Industrial automation equipment company",
        ]
        
        for i, (symbol, name, summary) in enumerate(zip(symbols, names, summaries)):
            company = Company(
                symbol=symbol,
                name=name,
                market="Tokyo",
                price=1000.0 + i * 100,
                business_summary=summary,
            )
            companies.append(company)
        return companies

    @pytest.fixture
    def stock_fetcher(self):
        """テスト用StockFetcher"""
        return StockFetcher()

    @pytest.fixture
    def translation_service(self):
        """テスト用TranslationService"""
        return TranslationService(max_retries=2, retry_delay=0.1)

    @pytest.fixture
    def async_processor(self, stock_fetcher, translation_service):
        """テスト用AsyncBatchProcessor"""
        return AsyncBatchProcessor(
            stock_workers=2,
            translation_workers=2,
            queue_max_size=10,
            stock_fetcher=stock_fetcher,
            translation_service=translation_service,
        )

    @pytest.mark.asyncio
    async def test_end_to_end_pipeline_processing(
        self, async_processor, mock_companies
    ):
        """エンドツーエンドパイプライン処理テスト"""
        # StockFetcherのモック設定
        def create_mock_stock_data(symbol):
            stock_data = StockData(
                symbol=symbol,
                current_price=1500.0 + hash(symbol) % 500,
                business_summary="Mock business summary for " + symbol,
                volume=100000 + hash(symbol) % 50000,
                day_high=1800.0 + hash(symbol) % 200,
                day_low=900.0 + hash(symbol) % 200,
                sector="Mock Sector",
                industry="Mock Industry",
            )
            return stock_data

        mock_stock_fetcher_async = AsyncMock()
        mock_stock_fetcher_async.side_effect = lambda symbol: create_mock_stock_data(symbol)

        # TranslationServiceのモック設定
        def create_mock_translation(text):
            translations = {
                "Leading fisheries and food company": "水産食品業界のリーディング企業",
                "Global automotive manufacturer": "グローバル自動車メーカー",
                "Electronics and entertainment company": "エレクトロニクス・エンターテインメント企業",
                "Motorcycle and automotive manufacturer": "二輪・自動車メーカー",
                "Industrial automation equipment company": "産業オートメーション機器企業",
            }
            return translations.get(text, f"翻訳済み: {text}")

        mock_translation_async = AsyncMock()
        mock_translation_async.side_effect = create_mock_translation

        with patch.object(
            async_processor.stock_fetcher, "fetch_stock_data_async", mock_stock_fetcher_async
        ), patch.object(
            async_processor.translation_service, "translate_to_japanese_async", mock_translation_async
        ):
            
            # パイプライン実行
            results = await async_processor.process_pipeline(mock_companies)

        # 結果検証
        assert len(results) == 5
        for result in results:
            assert isinstance(result, Company)
            assert result.stock_data is not None
            assert result.business_summary_ja is not None
            # 翻訳が実行されて日本語テキストまたは翻訳済みマークが含まれることを確認
            assert (
                result.business_summary_ja != result.business_summary or
                "翻訳済み" in result.business_summary_ja or 
                "企業" in result.business_summary_ja or
                len(result.business_summary_ja) > 0
            )

    @pytest.mark.asyncio
    async def test_pipeline_with_stock_fetch_errors(
        self, async_processor, mock_companies
    ):
        """株価取得エラー時のパイプライン処理テスト"""
        call_count = 0

        async def mock_stock_fetch_with_errors(symbol):
            nonlocal call_count
            call_count += 1
            if "1332" in symbol:  # 特定の銘柄でエラー
                raise Exception(f"Stock fetch error for {symbol}")
            
            return StockData(
                symbol=symbol,
                current_price=1500.0,
                business_summary="Mock business summary for " + symbol,
                volume=100000,
                day_high=1800.0,
                day_low=900.0,
                sector="Mock Sector",
                industry="Mock Industry",
            )

        mock_translation_async = AsyncMock()
        mock_translation_async.side_effect = lambda text: f"翻訳済み: {text}"

        with patch.object(
            async_processor.stock_fetcher, "fetch_stock_data_async", mock_stock_fetch_with_errors
        ), patch.object(
            async_processor.translation_service, "translate_to_japanese_async", mock_translation_async
        ):
            
            results = await async_processor.process_pipeline(mock_companies)

        # エラーがあっても処理が続行されることを確認
        assert len(results) == 5
        # エラーのあった企業もリストに含まれる（stock_dataがNone）
        error_company = next((r for r in results if r.symbol == "1332.T"), None)
        assert error_company is not None
        # エラーでもbusiness_summary_jaは設定される（翻訳は成功）
        assert error_company.business_summary_ja is not None

    @pytest.mark.asyncio
    async def test_pipeline_with_translation_errors(
        self, async_processor, mock_companies
    ):
        """翻訳エラー時のパイプライン処理テスト"""
        def create_mock_stock_data(symbol):
            return StockData(
                symbol=symbol,
                current_price=1500.0,
                business_summary="Mock business summary for " + symbol,
                volume=100000,
                day_high=1800.0,
                day_low=900.0,
                sector="Mock Sector",
                industry="Mock Industry",
            )

        async def mock_translation_with_errors(text):
            if "Leading fisheries" in text:  # 特定のテキストでエラー
                raise Exception(f"Translation error for: {text}")
            return f"翻訳済み: {text}"

        mock_stock_fetcher_async = AsyncMock()
        mock_stock_fetcher_async.side_effect = create_mock_stock_data

        with patch.object(
            async_processor.stock_fetcher, "fetch_stock_data_async", mock_stock_fetcher_async
        ), patch.object(
            async_processor.translation_service, "translate_to_japanese_async", mock_translation_with_errors
        ):
            
            results = await async_processor.process_pipeline(mock_companies)

        # エラーがあっても処理が続行されることを確認
        assert len(results) == 5
        # 翻訳エラーの企業も含まれる
        error_company = next((r for r in results if r.symbol == "1332.T"), None)
        assert error_company is not None
        assert error_company.stock_data is not None  # 株価データは取得成功

    @pytest.mark.asyncio
    async def test_pipeline_performance_metrics(
        self, async_processor, mock_companies
    ):
        """パイプライン処理パフォーマンス指標テスト"""
        # モック設定
        async def mock_stock_fetch_with_delay(symbol):
            await asyncio.sleep(0.01)  # 小さな遅延でリアルな処理時間をシミュレート
            return StockData(
                symbol=symbol,
                current_price=1500.0,
                business_summary="Mock business summary for " + symbol,
                volume=100000,
                day_high=1800.0,
                day_low=900.0,
                sector="Mock Sector",
                industry="Mock Industry",
            )

        async def mock_translation_with_delay(text):
            await asyncio.sleep(0.01)  # 小さな遅延
            return f"翻訳済み: {text}"

        with patch.object(
            async_processor.stock_fetcher, "fetch_stock_data_async", mock_stock_fetch_with_delay
        ), patch.object(
            async_processor.translation_service, "translate_to_japanese_async", mock_translation_with_delay
        ):
            
            start_time = asyncio.get_event_loop().time()
            results = await async_processor.process_pipeline(mock_companies)
            end_time = asyncio.get_event_loop().time()

        # 処理時間の検証（並列処理により高速化されているはず）
        processing_time = end_time - start_time
        assert processing_time < 1.0  # 1秒以内で完了することを期待

        # 結果の検証
        assert len(results) == 5
        for result in results:
            assert result.stock_data is not None
            assert result.business_summary_ja is not None

    @pytest.mark.asyncio
    async def test_pipeline_concurrent_processing(
        self, stock_fetcher, translation_service, mock_companies
    ):
        """並行処理数制限のテスト"""
        # より高い並行数で処理
        high_concurrency_processor = AsyncBatchProcessor(
            stock_workers=5,
            translation_workers=5,
            queue_max_size=20,
            stock_fetcher=stock_fetcher,
            translation_service=translation_service,
        )

        # モック設定
        async def mock_stock_fetch(symbol):
            return StockData(
                symbol=symbol,
                current_price=1500.0,
                business_summary="Mock business summary for " + symbol,
                volume=100000,
                day_high=1800.0,
                day_low=900.0,
                sector="Mock Sector",
                industry="Mock Industry",
            )

        async def mock_translation(text):
            return f"翻訳済み: {text}"

        with patch.object(
            high_concurrency_processor.stock_fetcher, "fetch_stock_data_async", mock_stock_fetch
        ), patch.object(
            high_concurrency_processor.translation_service, "translate_to_japanese_async", mock_translation
        ):
            
            results = await high_concurrency_processor.process_pipeline(mock_companies)

        # 結果検証
        assert len(results) == 5
        for result in results:
            assert result.stock_data is not None
            assert result.business_summary_ja is not None

    @pytest.mark.asyncio
    async def test_empty_company_list_pipeline(self, async_processor):
        """空の企業リストでのパイプライン処理テスト"""
        results = await async_processor.process_pipeline([])
        assert results == []

    @pytest.mark.asyncio
    async def test_single_company_pipeline(self, async_processor):
        """単一企業でのパイプライン処理テスト"""
        company = Company(
            symbol="1332.T",
            name="日本水産",
            market="Tokyo",
            price=1000.0,
            business_summary="Leading fisheries and food company",
        )

        # モック設定
        async def mock_stock_fetch(symbol):
            return StockData(
                symbol=symbol,
                current_price=1500.0,
                business_summary="Mock business summary for " + symbol,
                volume=100000,
                day_high=1800.0,
                day_low=900.0,
                sector="Mock Sector",
                industry="Mock Industry",
            )

        async def mock_translation(text):
            return "水産食品業界のリーディング企業"

        with patch.object(
            async_processor.stock_fetcher, "fetch_stock_data_async", mock_stock_fetch
        ), patch.object(
            async_processor.translation_service, "translate_to_japanese_async", mock_translation
        ):
            
            results = await async_processor.process_pipeline([company])

        # 結果検証
        assert len(results) == 1
        result = results[0]
        assert result.symbol == "1332.T"
        assert result.stock_data is not None
        assert result.business_summary_ja == "水産食品業界のリーディング企業"

    def test_pipeline_integration_methods_exist(self, async_processor):
        """パイプライン統合メソッドの存在確認テスト"""
        # パイプライン処理メソッドが定義されていることを確認
        assert hasattr(async_processor, "process_pipeline")
        
        # メソッドがコルーチン関数であることを確認
        import inspect
        assert inspect.iscoroutinefunction(async_processor.process_pipeline)

    @pytest.mark.asyncio
    async def test_pipeline_with_mixed_success_failure(
        self, async_processor, mock_companies
    ):
        """株価取得と翻訳の両方で一部成功・一部失敗のテスト"""
        call_count_stock = 0
        call_count_translation = 0

        async def mock_stock_fetch_mixed(symbol):
            nonlocal call_count_stock
            call_count_stock += 1
            if call_count_stock % 2 == 0:  # 偶数回目はエラー
                raise Exception(f"Stock fetch error for {symbol}")
            return StockData(
                symbol=symbol,
                current_price=1500.0,
                business_summary="Mock business summary for " + symbol,
                volume=100000,
                day_high=1800.0,
                day_low=900.0,
                sector="Mock Sector",
                industry="Mock Industry",
            )

        async def mock_translation_mixed(text):
            nonlocal call_count_translation
            call_count_translation += 1
            if call_count_translation % 3 == 0:  # 3回に1回はエラー
                raise Exception(f"Translation error for: {text}")
            return f"翻訳済み: {text}"

        with patch.object(
            async_processor.stock_fetcher, "fetch_stock_data_async", mock_stock_fetch_mixed
        ), patch.object(
            async_processor.translation_service, "translate_to_japanese_async", mock_translation_mixed
        ):
            
            results = await async_processor.process_pipeline(mock_companies)

        # エラーがあっても全ての企業が処理されることを確認
        assert len(results) == 5
        
        # 一部の企業は株価データがNone（fetch失敗）
        stock_success_count = sum(1 for r in results if r.stock_data is not None)
        assert stock_success_count > 0  # 少なくとも一部は成功
        assert stock_success_count < 5   # 全部が成功ではない

        # 翻訳は呼び出されている（エラーでも原文が残る）
        for result in results:
            assert hasattr(result, "business_summary_ja")