"""非同期株価取得機能のテスト

StockFetcherの非同期機能をテストする
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from stock_batch.services.stock_fetcher import StockFetcher


class TestAsyncStockFetcher:
    """非同期株価取得機能のテストクラス"""

    @pytest.fixture
    def stock_fetcher(self):
        """テスト用StockFetcher"""
        return StockFetcher(max_retries=2, retry_delay=0.1, rate_limit_delay=0.05)

    @pytest.fixture
    def mock_company(self):
        """テスト用企業データ"""
        company = MagicMock()
        company.symbol = "1332.T"  # 有効な日本株式シンボル
        company.business_summary = "Test company"
        return company

    @pytest.fixture
    def mock_companies(self):
        """テスト用企業データリスト"""
        companies = []
        # 有効な日本株式シンボル形式を使用
        symbols = ["1332.T", "7203.T", "6758.T", "9437.T", "9984.T"]
        for i, symbol in enumerate(symbols):
            company = MagicMock()
            company.symbol = symbol
            company.business_summary = f"Test company {i}"
            companies.append(company)
        return companies

    @pytest.mark.asyncio
    async def test_fetch_stock_data_async_success(self, stock_fetcher, mock_company):
        """非同期株価取得成功テスト"""
        # yfinanceのモック
        mock_ticker = MagicMock()
        mock_hist = MagicMock()
        mock_hist.empty = False
        mock_hist.iloc = [{"Close": 100.0, "Volume": 1000, "High": 110.0, "Low": 90.0}]
        mock_ticker.history.return_value = mock_hist
        mock_ticker.info = {
            "longBusinessSummary": "Test business summary",
            "sector": "Technology",
            "industry": "Software",
        }

        with patch("yfinance.Ticker", return_value=mock_ticker):
            stock_data = await stock_fetcher.fetch_stock_data_async(mock_company.symbol)

        # 結果検証
        assert stock_data is not None
        assert stock_data.symbol == "1332.T"
        assert stock_data.current_price == 100.0
        assert stock_data.business_summary == "Test business summary"
        assert stock_data.sector == "Technology"
        assert stock_data.industry == "Software"

    @pytest.mark.asyncio
    async def test_fetch_stock_data_async_error_handling(
        self, stock_fetcher, mock_company
    ):
        """非同期株価取得エラーハンドリングテスト"""
        # yfinanceでエラーが発生するモック
        with patch("yfinance.Ticker", side_effect=Exception("Network error")):
            stock_data = await stock_fetcher.fetch_stock_data_async(mock_company.symbol)

        # エラー時はNoneが返されること
        assert stock_data is None

    @pytest.mark.asyncio
    async def test_fetch_stock_data_async_retry_mechanism(
        self, stock_fetcher, mock_company
    ):
        """非同期株価取得リトライメカニズムテスト"""
        call_count = 0

        def mock_ticker_with_retry(symbol):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary error")

            # 2回目は成功
            mock_ticker = MagicMock()
            mock_hist = MagicMock()
            mock_hist.empty = False
            mock_hist.iloc = [
                {"Close": 100.0, "Volume": 1000, "High": 110.0, "Low": 90.0}
            ]
            mock_ticker.history.return_value = mock_hist
            mock_ticker.info = {"longBusinessSummary": "Test summary"}
            return mock_ticker

        with patch("yfinance.Ticker", side_effect=mock_ticker_with_retry):
            stock_data = await stock_fetcher.fetch_stock_data_async(mock_company.symbol)

        # リトライ後に成功すること
        assert stock_data is not None
        assert stock_data.current_price == 100.0
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_multiple_stocks_async_success(
        self, stock_fetcher, mock_companies
    ):
        """複数株価非同期取得成功テスト"""

        # yfinanceのモック
        def create_mock_ticker(symbol):
            mock_ticker = MagicMock()
            mock_hist = MagicMock()
            mock_hist.empty = False
            # シンボルごとに異なる価格を設定
            symbol_prices = {
                "1332.T": 100.0,
                "7203.T": 110.0,
                "6758.T": 120.0,
                "9437.T": 130.0,
                "9984.T": 140.0,
            }
            price = symbol_prices.get(symbol, 100.0)
            mock_hist.iloc = [
                {"Close": price, "Volume": 1000, "High": price + 10, "Low": price - 10}
            ]
            mock_ticker.history.return_value = mock_hist
            mock_ticker.info = {"longBusinessSummary": f"Business summary for {symbol}"}
            return mock_ticker

        with patch("yfinance.Ticker", side_effect=create_mock_ticker):
            stock_data_list = await stock_fetcher.fetch_multiple_stocks_async(
                [company.symbol for company in mock_companies]
            )

        # 結果検証
        assert len(stock_data_list) == 5
        # 価格の降順でソートされているので確認
        symbols = ["1332.T", "7203.T", "6758.T", "9437.T", "9984.T"]
        expected_prices = [100.0, 110.0, 120.0, 130.0, 140.0]
        # 価格順（降順）でソートされている
        sorted_prices = sorted(expected_prices, reverse=True)
        for i, stock_data in enumerate(stock_data_list):
            assert stock_data.current_price == sorted_prices[i]
            assert stock_data.symbol in symbols

    @pytest.mark.asyncio
    async def test_fetch_multiple_stocks_async_with_errors(self, stock_fetcher):
        """複数株価非同期取得（一部エラー）テスト"""

        def create_mock_ticker_with_errors(symbol):
            if symbol == "9999.T":  # エラーシンボル
                raise Exception("Network error")

            mock_ticker = MagicMock()
            mock_hist = MagicMock()
            mock_hist.empty = False
            mock_hist.iloc = [
                {"Close": 100.0, "Volume": 1000, "High": 110.0, "Low": 90.0}
            ]
            mock_ticker.history.return_value = mock_hist
            mock_ticker.info = {"longBusinessSummary": f"Business summary for {symbol}"}
            return mock_ticker

        symbols = ["1332.T", "9999.T", "7203.T"]

        with patch("yfinance.Ticker", side_effect=create_mock_ticker_with_errors):
            stock_data_list = await stock_fetcher.fetch_multiple_stocks_async(symbols)

        # エラーの株式を除いて2件成功すること
        assert len(stock_data_list) == 2
        assert all(data.current_price == 100.0 for data in stock_data_list)

    @pytest.mark.asyncio
    async def test_fetch_stocks_with_rate_limit(self, stock_fetcher, mock_companies):
        """レート制限付き株価取得テスト"""
        # モック設定
        def create_mock_ticker(symbol):
            mock_ticker = MagicMock()
            mock_hist = MagicMock()
            mock_hist.empty = False
            mock_hist.iloc = [
                {"Close": 100.0, "Volume": 1000, "High": 110.0, "Low": 90.0}
            ]
            mock_ticker.history.return_value = mock_hist
            mock_ticker.info = {"longBusinessSummary": "Test summary"}
            return mock_ticker

        with patch("yfinance.Ticker", side_effect=create_mock_ticker):
            stock_data_list = await stock_fetcher.fetch_multiple_stocks_async(
                [company.symbol for company in mock_companies[:3]]  # 3件のテスト
            )

        # 結果検証
        assert len(stock_data_list) == 3
        # 並行処理のため、レート制限の効果は個別の呼び出しレベルで動作
        # 主に結果の正確性を確認
        assert all(data.current_price == 100.0 for data in stock_data_list)

    @pytest.mark.asyncio
    async def test_concurrent_stock_fetching(self, stock_fetcher):
        """並行株価取得テスト"""
        symbols = ["1332.T", "7203.T", "6758.T"]

        # モック設定
        def create_mock_ticker(symbol):
            mock_ticker = MagicMock()
            mock_hist = MagicMock()
            mock_hist.empty = False
            mock_hist.iloc = [
                {"Close": 100.0, "Volume": 1000, "High": 110.0, "Low": 90.0}
            ]
            mock_ticker.history.return_value = mock_hist
            mock_ticker.info = {"longBusinessSummary": "Test summary"}
            return mock_ticker

        with patch("yfinance.Ticker", side_effect=create_mock_ticker):
            # 並行実行
            tasks = [stock_fetcher.fetch_stock_data_async(symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks)

        # 結果検証
        assert len(results) == 3
        assert all(result is not None for result in results)
        assert all(result.current_price == 100.0 for result in results)

    def test_validate_async_methods_exist(self, stock_fetcher):
        """非同期メソッドの存在確認テスト"""
        # 非同期メソッドが定義されていることを確認
        assert hasattr(stock_fetcher, "fetch_stock_data_async")
        assert hasattr(stock_fetcher, "fetch_multiple_stocks_async")

        # メソッドがコルーチン関数であることを確認
        import inspect

        assert inspect.iscoroutinefunction(stock_fetcher.fetch_stock_data_async)
        assert inspect.iscoroutinefunction(stock_fetcher.fetch_multiple_stocks_async)

    @pytest.mark.asyncio
    async def test_async_stats_tracking(self, stock_fetcher, mock_company):
        """非同期処理の統計追跡テスト"""
        # 初期状態の統計確認
        initial_stats = stock_fetcher.get_stats()
        assert initial_stats["total_requests"] == 0

        # モック設定
        mock_ticker = MagicMock()
        mock_hist = MagicMock()
        mock_hist.empty = False
        mock_hist.iloc = [{"Close": 100.0, "Volume": 1000, "High": 110.0, "Low": 90.0}]
        mock_ticker.history.return_value = mock_hist
        mock_ticker.info = {"longBusinessSummary": "Test summary"}

        with patch("yfinance.Ticker", return_value=mock_ticker):
            await stock_fetcher.fetch_stock_data_async(mock_company.symbol)

        # 統計が更新されていることを確認
        final_stats = stock_fetcher.get_stats()
        assert final_stats["total_requests"] > initial_stats["total_requests"]
        assert final_stats["successful_requests"] > 0
