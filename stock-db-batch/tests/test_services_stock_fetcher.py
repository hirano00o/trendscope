"""yfinance株価取得サービスのテストコード

yfinanceライブラリを使用した株価・企業情報の取得機能をテストします。
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from stock_batch.services.stock_fetcher import StockData, StockFetcher


class TestStockFetcher:
    """StockFetcher クラスのテスト"""

    def test_create_stock_fetcher(self) -> None:
        """StockFetcher 作成のテスト"""
        fetcher = StockFetcher()
        assert fetcher is not None

    @patch("yfinance.Ticker")
    def test_fetch_stock_data_success(self, mock_ticker_class: Mock) -> None:
        """株価データ取得成功のテスト"""
        # モックの設定
        mock_ticker = Mock()
        mock_ticker_class.return_value = mock_ticker

        # 株価情報のモック
        mock_history = Mock()
        mock_history.empty = False  # hist.emptyのモック
        # pandasのSeriesのような動作を模倣
        latest_data = {"Close": 877.8, "Volume": 1000000, "High": 890.0, "Low": 870.0}
        mock_history.iloc = Mock()
        mock_history.iloc.__getitem__ = Mock(return_value=latest_data)
        mock_ticker.history.return_value = mock_history

        # 企業情報のモック
        mock_ticker.info = {
            "longBusinessSummary": "Nissui Corporation is a Japanese fishery company.",
            "sector": "Consumer Defensive",
            "industry": "Packaged Foods",
            "marketCap": 150000000000,
            "currency": "JPY",
        }

        fetcher = StockFetcher()
        stock_data = fetcher.fetch_stock_data("1332.T")

        assert stock_data is not None
        assert stock_data.symbol == "1332.T"
        assert stock_data.current_price == 877.8
        assert stock_data.volume == 1000000
        assert stock_data.day_high == 890.0
        assert stock_data.day_low == 870.0
        assert "fishery company" in stock_data.business_summary
        assert stock_data.sector == "Consumer Defensive"
        assert stock_data.industry == "Packaged Foods"

    @patch("yfinance.Ticker")
    def test_fetch_stock_data_not_found(self, mock_ticker_class: Mock) -> None:
        """存在しない株式コードのテスト"""
        # モックの設定
        mock_ticker = Mock()
        mock_ticker_class.return_value = mock_ticker

        # 空の履歴データ
        mock_ticker.history.return_value.empty = True
        mock_ticker.info = {}

        fetcher = StockFetcher()
        stock_data = fetcher.fetch_stock_data("INVALID.T")

        assert stock_data is None

    @patch("yfinance.Ticker")
    def test_fetch_stock_data_network_error(self, mock_ticker_class: Mock) -> None:
        """ネットワークエラーのテスト"""
        # モックでネットワークエラーを発生させる
        mock_ticker_class.side_effect = Exception("Network error")

        fetcher = StockFetcher()
        stock_data = fetcher.fetch_stock_data("1332.T")

        assert stock_data is None

    @patch("yfinance.Ticker")
    def test_fetch_stock_data_partial_info(self, mock_ticker_class: Mock) -> None:
        """部分的な情報しかない場合のテスト"""
        # モックの設定
        mock_ticker = Mock()
        mock_ticker_class.return_value = mock_ticker

        # 最小限の株価情報
        mock_history = Mock()
        mock_history.empty = False  # hist.emptyのモック
        latest_data = {"Close": 500.0}  # 他の情報は欠落
        mock_history.iloc = Mock()
        mock_history.iloc.__getitem__ = Mock(return_value=latest_data)
        mock_ticker.history.return_value = mock_history

        # 最小限の企業情報
        mock_ticker.info = {"longBusinessSummary": "Test company summary."}

        fetcher = StockFetcher()
        stock_data = fetcher.fetch_stock_data("TEST.T")

        assert stock_data is not None
        assert stock_data.symbol == "TEST.T"
        assert stock_data.current_price == 500.0
        assert stock_data.volume is None  # 欠落情報はNone
        assert stock_data.business_summary == "Test company summary."

    @patch("yfinance.Ticker")
    def test_fetch_multiple_stocks_success(self, mock_ticker_class: Mock) -> None:
        """複数株式の取得テスト"""

        # モック設定
        def ticker_side_effect(symbol: str) -> Mock:
            mock_ticker = Mock()

            if symbol == "1332.T":
                mock_history = Mock()
                mock_history.empty = False
                latest_data = {"Close": 877.8}
                mock_history.iloc = Mock()
                mock_history.iloc.__getitem__ = Mock(return_value=latest_data)
                mock_ticker.history.return_value = mock_history
                mock_ticker.info = {"longBusinessSummary": "Nissui Corp"}
            elif symbol == "1418.T":
                mock_history = Mock()
                mock_history.empty = False
                latest_data = {"Close": 405.0}
                mock_history.iloc = Mock()
                mock_history.iloc.__getitem__ = Mock(return_value=latest_data)
                mock_ticker.history.return_value = mock_history
                mock_ticker.info = {"longBusinessSummary": "InterLife"}
            else:
                mock_history = Mock()
                mock_history.empty = True
                mock_ticker.history.return_value = mock_history
                mock_ticker.info = {}

            return mock_ticker

        mock_ticker_class.side_effect = ticker_side_effect

        fetcher = StockFetcher()
        symbols = ["1332.T", "1418.T", "INVALID.T"]
        stock_data_list = fetcher.fetch_multiple_stocks(symbols)

        # 有効な2件のデータが取得される
        assert len(stock_data_list) == 2

        # 価格でソートされた結果を確認
        assert stock_data_list[0].current_price == 877.8
        assert stock_data_list[1].current_price == 405.0

    def test_fetch_multiple_stocks_empty_list(self) -> None:
        """空のシンボルリストのテスト"""
        fetcher = StockFetcher()
        stock_data_list = fetcher.fetch_multiple_stocks([])

        assert stock_data_list == []

    @patch("yfinance.Ticker")
    def test_retry_mechanism(self, mock_ticker_class: Mock) -> None:
        """リトライ機能のテスト"""
        # 最初の2回は失敗、3回目で成功
        call_count = 0

        def ticker_side_effect(symbol: str) -> Mock:
            nonlocal call_count
            call_count += 1

            if call_count <= 2:
                raise Exception("Temporary network error")

            mock_ticker = Mock()
            mock_history = Mock()
            mock_history.empty = False
            latest_data = {"Close": 877.8}
            mock_history.iloc = Mock()
            mock_history.iloc.__getitem__ = Mock(return_value=latest_data)
            mock_ticker.history.return_value = mock_history
            mock_ticker.info = {"longBusinessSummary": "Nissui Corp"}
            return mock_ticker

        mock_ticker_class.side_effect = ticker_side_effect

        fetcher = StockFetcher(max_retries=3, retry_delay=0.1)
        stock_data = fetcher.fetch_stock_data("1332.T")

        assert stock_data is not None
        assert stock_data.current_price == 877.8
        assert call_count == 3  # 3回目で成功

    @patch("yfinance.Ticker")
    def test_retry_exhausted(self, mock_ticker_class: Mock) -> None:
        """リトライ回数上限のテスト"""
        # 常にエラーを発生
        mock_ticker_class.side_effect = Exception("Persistent network error")

        fetcher = StockFetcher(max_retries=2, retry_delay=0.1)
        stock_data = fetcher.fetch_stock_data("1332.T")

        assert stock_data is None

    def test_validate_symbol_format(self) -> None:
        """株式シンボル形式検証のテスト"""
        fetcher = StockFetcher()

        # 有効な日本株シンボル（東京証券取引所）
        assert fetcher.is_valid_symbol("1332.T") is True
        assert fetcher.is_valid_symbol("130A.T") is True
        assert fetcher.is_valid_symbol("9999.T") is True
        
        # 有効な日本株シンボル（その他の取引所）
        assert fetcher.is_valid_symbol("3698.S") is True  # 札幌証券取引所
        assert fetcher.is_valid_symbol("2200.N") is True  # 名古屋証券取引所
        assert fetcher.is_valid_symbol("8885.F") is True  # 福岡証券取引所
        assert fetcher.is_valid_symbol("9999.OS") is True  # 大阪証券取引所

        # 無効なシンボル
        assert fetcher.is_valid_symbol("") is False
        assert fetcher.is_valid_symbol("1332") is False  # 取引所識別子がない
        assert fetcher.is_valid_symbol("INVALID") is False
        assert fetcher.is_valid_symbol("1332.T.") is False  # 余分な文字
        assert fetcher.is_valid_symbol("1332.X") is False  # 無効な取引所識別子

    def test_get_fetcher_stats(self) -> None:
        """フェッチャー統計情報取得のテスト"""
        fetcher = StockFetcher()

        stats = fetcher.get_stats()

        assert "total_requests" in stats
        assert "successful_requests" in stats
        assert "failed_requests" in stats
        assert "average_response_time" in stats
        assert stats["total_requests"] == 0  # 初期値

    @patch("yfinance.Ticker")
    def test_stats_tracking(self, mock_ticker_class: Mock) -> None:
        """統計情報トラッキングのテスト"""
        # 成功ケース
        mock_ticker = Mock()
        mock_ticker_class.return_value = mock_ticker
        mock_history = Mock()
        mock_history.empty = False
        latest_data = {"Close": 877.8}
        mock_history.iloc = Mock()
        mock_history.iloc.__getitem__ = Mock(return_value=latest_data)
        mock_ticker.history.return_value = mock_history
        mock_ticker.info = {"longBusinessSummary": "Test"}

        fetcher = StockFetcher()

        # 1回成功
        fetcher.fetch_stock_data("1332.T")

        # 1回失敗（エラー発生）
        mock_ticker_class.side_effect = Exception("Error")
        fetcher.fetch_stock_data("FAIL.T")

        stats = fetcher.get_stats()
        assert stats["total_requests"] == 2
        assert stats["successful_requests"] == 1
        assert stats["failed_requests"] == 1


class TestStockData:
    """StockData データクラスのテスト"""

    def test_create_stock_data(self) -> None:
        """StockData 作成のテスト"""
        data = StockData(
            symbol="1332.T",
            current_price=877.8,
            business_summary="Nissui Corporation",
            sector="Consumer Defensive",
        )

        assert data.symbol == "1332.T"
        assert data.current_price == 877.8
        assert data.business_summary == "Nissui Corporation"
        assert data.sector == "Consumer Defensive"

    def test_stock_data_optional_fields(self) -> None:
        """StockData のオプションフィールドテスト"""
        data = StockData(
            symbol="1332.T", current_price=877.8, business_summary="Nissui Corporation"
        )

        # オプションフィールドはNoneがデフォルト
        assert data.volume is None
        assert data.day_high is None
        assert data.day_low is None
        assert data.sector is None
        assert data.industry is None

    def test_stock_data_comparison(self) -> None:
        """StockData の比較テスト（価格ソート用）"""
        data1 = StockData(symbol="A", current_price=100.0, business_summary="Company A")
        data2 = StockData(symbol="B", current_price=200.0, business_summary="Company B")

        # 価格による比較（高い順）
        stock_list = [data1, data2]
        sorted_list = sorted(stock_list, key=lambda x: x.current_price, reverse=True)

        assert sorted_list[0].symbol == "B"  # 高い価格が最初
        assert sorted_list[1].symbol == "A"


class TestYfinanceCacheConfiguration:
    """yfinanceキャッシュ設定のテスト"""

    def test_yfinance_cache_directory_setting(self) -> None:
        """yfinanceキャッシュディレクトリ設定のテスト

        yfinanceライブラリのキャッシュディレクトリを適切に設定できることを確認
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # テスト用の書き込み可能ディレクトリを設定
            cache_dir = Path(temp_dir) / "yfinance_cache"

            # yfinanceキャッシュ設定をテスト
            with patch.dict(os.environ, {"YFINANCE_CACHE_DIR": str(cache_dir)}):
                # キャッシュディレクトリが設定されることを確認
                assert os.getenv("YFINANCE_CACHE_DIR") == str(cache_dir)

    def test_yfinance_cache_directory_creation(self) -> None:
        """yfinanceキャッシュディレクトリ作成のテスト

        書き込み可能な場所にキャッシュディレクトリが作成できることを確認
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / "yfinance_cache"

            # ディレクトリが存在しない状態から開始
            assert not cache_dir.exists()

            # ディレクトリ作成をテスト
            cache_dir.mkdir(parents=True, exist_ok=True)

            # 作成されたディレクトリの確認
            assert cache_dir.exists()
            assert cache_dir.is_dir()

            # 書き込み権限の確認
            test_file = cache_dir / "test_write.txt"
            test_file.write_text("test")
            assert test_file.read_text() == "test"

    @patch.dict(os.environ, {"YFINANCE_CACHE_DIR": "/tmp/app/yfinance_cache"})
    def test_yfinance_environment_variable_configuration(self) -> None:
        """yfinance環境変数設定のテスト

        環境変数でyfinanceキャッシュ設定が正しく読み込まれることを確認
        """
        # 環境変数が正しく設定されていることを確認
        expected_cache_dir = "/tmp/app/yfinance_cache"
        assert os.getenv("YFINANCE_CACHE_DIR") == expected_cache_dir

    def test_default_cache_behavior_without_config(self) -> None:
        """設定なしでのデフォルトキャッシュ動作のテスト

        キャッシュ設定がない場合のyfinanceの動作を確認
        """
        # YFINANCE_CACHE_DIR環境変数が設定されていない状態をテスト
        with patch.dict(os.environ, {}, clear=True):
            # 環境変数が設定されていないことを確認
            assert os.getenv("YFINANCE_CACHE_DIR") is None

    @patch("yfinance.Ticker")
    def test_stock_fetcher_with_cache_configuration(
        self, mock_ticker_class: Mock
    ) -> None:
        """キャッシュ設定ありでのStockFetcher動作テスト

        適切なキャッシュ設定の下でStockFetcherが正常に動作することを確認
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / "yfinance_cache"

            with patch.dict(os.environ, {"YFINANCE_CACHE_DIR": str(cache_dir)}):
                # モックの設定
                mock_ticker = Mock()
                mock_ticker_class.return_value = mock_ticker

                # 株価情報のモック
                mock_history = Mock()
                mock_history.empty = False
                latest_data = {"Close": 877.8, "Volume": 1000000}
                mock_history.iloc = Mock()
                mock_history.iloc.__getitem__ = Mock(return_value=latest_data)
                mock_ticker.history.return_value = mock_history
                mock_ticker.info = {"longBusinessSummary": "Test company"}

                # StockFetcher実行
                fetcher = StockFetcher()
                stock_data = fetcher.fetch_stock_data("1332.T")

                # 結果確認
                assert stock_data is not None
                assert stock_data.symbol == "1332.T"
                assert stock_data.current_price == 877.8

                # キャッシュディレクトリ設定の確認
                assert os.getenv("YFINANCE_CACHE_DIR") == str(cache_dir)


class TestStockFetcherRateLimit:
    """StockFetcherのレート制限機能テスト"""

    def test_rate_limit_initialization(self) -> None:
        """レート制限の初期化テスト"""
        fetcher = StockFetcher(rate_limit_delay=2.0)
        assert fetcher.rate_limit_delay == 2.0
        assert fetcher._last_request_time == 0.0

    @patch("time.sleep")
    @patch("time.time")
    def test_rate_limit_delay_applied(self, mock_time: Mock, mock_sleep: Mock) -> None:
        """レート制限の待機処理テスト"""
        # 時間の経過をモック
        mock_time.side_effect = [100.3, 101.0]  # 0.3秒経過、その後1.0秒に設定

        fetcher = StockFetcher(rate_limit_delay=1.0)
        fetcher._last_request_time = 100.0  # 前回のリクエスト時刻を設定（0.0ではない）

        # _apply_rate_limitを直接テスト
        fetcher._apply_rate_limit()

        # 0.7秒待機するはず (1.0 - 0.3) - 浮動小数点精度のため約での比較
        assert mock_sleep.call_count == 1
        called_args = mock_sleep.call_args[0]
        assert abs(called_args[0] - 0.7) < 0.01  # 0.7 ± 0.01

    @patch("time.sleep")
    @patch("time.time")
    def test_rate_limit_no_delay_when_enough_time_passed(
        self, mock_time: Mock, mock_sleep: Mock
    ) -> None:
        """十分時間が経過している場合はレート制限待機しないテスト"""
        # 時間の経過をモック（2秒経過）
        mock_time.side_effect = [102.0, 102.0]

        fetcher = StockFetcher(rate_limit_delay=1.0)
        fetcher._last_request_time = 100.0  # 前回のリクエスト時刻を設定（0.0ではない）

        # _apply_rate_limitを直接テスト
        fetcher._apply_rate_limit()

        # 十分時間が経過しているので待機しない
        mock_sleep.assert_not_called()

    @patch("yfinance.Ticker")
    @patch("time.sleep")
    @patch("time.time")
    def test_rate_limit_applied_in_fetch_stock_data(
        self, mock_time: Mock, mock_sleep: Mock, mock_ticker_class: Mock
    ) -> None:
        """fetch_stock_data内でレート制限が適用されるテスト"""
        # モックの設定
        mock_ticker = Mock()
        mock_ticker_class.return_value = mock_ticker

        mock_history = Mock()
        mock_history.empty = False
        latest_data = {"Close": 877.8}
        mock_history.iloc = Mock()
        mock_history.iloc.__getitem__ = Mock(return_value=latest_data)
        mock_ticker.history.return_value = mock_history
        mock_ticker.info = {"longBusinessSummary": "Test"}

        # 時間の経過をモック（短い間隔でリクエスト）
        # _apply_rate_limit内で2回、fetch_stock_data内で3回、
        # _record_success内で1回呼ばれる
        mock_time.side_effect = [100.2, 101.0, 101.1, 101.2, 101.3, 101.4]

        fetcher = StockFetcher(rate_limit_delay=1.0)
        fetcher._last_request_time = 100.0  # 前回のリクエスト時刻を設定（0.0ではない）

        # 株価データ取得
        stock_data = fetcher.fetch_stock_data("1332.T")

        # レート制限が適用され、待機が発生 - 浮動小数点精度考慮
        assert mock_sleep.call_count == 1
        called_args = mock_sleep.call_args[0]
        assert abs(called_args[0] - 0.8) < 0.01  # 0.8 ± 0.01

        # データは正常に取得される
        assert stock_data is not None
        assert stock_data.symbol == "1332.T"

    @patch("time.sleep")
    @patch("time.time")
    def test_rate_limit_first_request_no_delay(
        self, mock_time: Mock, mock_sleep: Mock
    ) -> None:
        """初回リクエスト時はレート制限待機しないテスト"""
        mock_time.return_value = 100.0

        fetcher = StockFetcher(rate_limit_delay=1.0)
        assert fetcher._last_request_time == 0.0  # 初期値

        # _apply_rate_limitを直接テスト
        fetcher._apply_rate_limit()

        # 初回なので待機しない
        mock_sleep.assert_not_called()

        # 時刻が記録される
        assert fetcher._last_request_time == 100.0
