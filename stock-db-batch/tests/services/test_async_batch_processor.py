"""AsyncBatchProcessorのテスト

非同期バッチプロセッサの基盤機能をテストする
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from stock_batch.services.async_batch_processor import AsyncBatchProcessor


class TestAsyncBatchProcessor:
    """AsyncBatchProcessorのテストクラス"""

    @pytest.fixture
    def processor_config(self):
        """テスト用プロセッサ設定"""
        return {
            "stock_workers": 1,
            "translation_workers": 1,
            "queue_max_size": 10,
            "stock_rate_limit": 0.1,
            "translation_rate_limit": 0.1,
        }

    @pytest.fixture
    def mock_companies(self):
        """テスト用企業データ"""
        companies = []
        for i in range(5):
            mock_company = MagicMock()
            mock_company.symbol = f"TEST{i}.T"
            mock_company.business_summary = f"Test company {i}"
            companies.append(mock_company)
        return companies

    def test_async_batch_processor_initialization(self, processor_config):
        """AsyncBatchProcessor初期化テスト"""
        processor = AsyncBatchProcessor(**processor_config)

        assert processor.stock_workers == 1
        assert processor.translation_workers == 1
        assert processor.queue_max_size == 10
        assert processor.stock_rate_limit == 0.1
        assert processor.translation_rate_limit == 0.1

    def test_queue_initialization(self, processor_config):
        """キュー初期化テスト"""
        processor = AsyncBatchProcessor(**processor_config)

        # キューが初期化されていること
        assert processor.stock_queue is not None
        assert processor.translation_queue is not None
        assert processor.stock_queue.maxsize == 10
        assert processor.translation_queue.maxsize == 10

    def test_semaphore_initialization(self, processor_config):
        """セマフォ初期化テスト"""
        processor = AsyncBatchProcessor(**processor_config)

        # セマフォが正しく初期化されていること
        assert processor.stock_semaphore._value == 1
        assert processor.translation_semaphore._value == 1

    @pytest.mark.asyncio
    async def test_start_and_stop_pipeline(self, processor_config):
        """パイプライン開始・停止テスト"""
        processor = AsyncBatchProcessor(**processor_config)

        # パイプライン開始前は停止状態
        assert processor.is_running is False

        # パイプライン開始
        await processor.start_pipeline()
        assert processor.is_running is True

        # パイプライン停止
        await processor.stop_pipeline()
        assert processor.is_running is False

    @pytest.mark.asyncio
    async def test_basic_producer_consumer_flow(self, processor_config, mock_companies):
        """基本的なプロデューサー・コンシューマーフローテスト"""
        processor = AsyncBatchProcessor(**processor_config)

        # モック関数設定
        async def mock_stock_fetcher(company):
            """モック株価取得関数"""
            company.price = 100.0
            return company

        async def mock_translator(company):
            """モック翻訳関数"""
            company.business_summary = f"翻訳済み: {company.business_summary}"
            return company

        processor.stock_fetcher_func = mock_stock_fetcher
        processor.translator_func = mock_translator

        # パイプライン実行
        await processor.start_pipeline()

        # process_companies メソッドを使用してテスト
        completed_companies = await processor.process_companies(mock_companies)

        await processor.stop_pipeline()

        # 結果検証
        assert len(completed_companies) == 5
        for company in completed_companies:
            assert company.price == 100.0
            assert company.business_summary.startswith("翻訳済み:")

    @pytest.mark.asyncio
    async def test_error_handling(self, processor_config):
        """エラーハンドリングテスト"""
        processor = AsyncBatchProcessor(**processor_config)

        # エラーを発生させるモック関数
        async def failing_stock_fetcher(company):
            """常にエラーを発生させる株価取得関数"""
            raise Exception("株価取得エラー")

        processor.stock_fetcher_func = failing_stock_fetcher

        await processor.start_pipeline()

        # テストデータ投入
        mock_company = MagicMock()
        mock_company.symbol = "ERROR.T"
        await processor.stock_queue.put(mock_company)

        # 完了シグナル
        await processor.stock_queue.put(None)

        # 少し待機
        await asyncio.sleep(0.3)

        await processor.stop_pipeline()

        # エラーが記録されていること
        assert len(processor.errors) > 0
        assert "株価取得エラー" in str(processor.errors[0])

    @pytest.mark.asyncio
    async def test_progress_reporting(self, processor_config, mock_companies):
        """進捗報告テスト"""
        processor = AsyncBatchProcessor(**processor_config)

        # プログレス報告を有効化
        processor.enable_progress_reporting = True
        processor.progress_report_interval = 1  # 1件ごとに報告

        # モック関数設定
        async def mock_stock_fetcher(company):
            await asyncio.sleep(0.1)  # 処理時間をシミュレート
            company.price = 100.0
            return company

        processor.stock_fetcher_func = mock_stock_fetcher

        await processor.start_pipeline()

        # テストデータ投入
        for company in mock_companies:
            await processor.stock_queue.put(company)

        # 完了シグナル
        for _ in range(processor.stock_workers):
            await processor.stock_queue.put(None)

        # 処理完了まで待機
        await asyncio.sleep(1.0)

        await processor.stop_pipeline()

        # 進捗情報が記録されていること
        assert len(processor.progress_reports) > 0
        assert processor.progress_reports[0]["stage"] == "stock_fetch"
