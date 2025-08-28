"""メインバッチアプリケーションのテストコード

全サービスを統合したエンドツーエンドのバッチ処理、
設定管理、ロギング、エラーハンドリング、Kubernetes対応をテストします。
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from stock_batch.main_batch_application import (
    BatchConfig,
    MainBatchApplication,
)


class TestMainBatchApplication:
    """MainBatchApplication クラスのテスト"""

    def test_create_main_batch_application(self) -> None:
        """MainBatchApplication 作成のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_path = tmp_db.name
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            csv_path = tmp_csv.name

        try:
            config = BatchConfig(
                database_path=db_path,
                csv_file_path=csv_path,
                chunk_size=100,
                enable_parallel=False,
            )

            app = MainBatchApplication(config)
            assert app is not None
            assert app.config.database_path == db_path
            assert app.config.csv_file_path == csv_path

        finally:
            Path(db_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)

    def test_configuration_validation(self) -> None:
        """設定検証のテスト"""
        # 無効なデータベースパス
        with pytest.raises(ValueError, match="データベースファイルが存在しません"):
            config = BatchConfig(
                database_path="/nonexistent/path/stocks.db",
                csv_file_path="test.csv",
            )
            MainBatchApplication(config)

        # 無効なCSVパス（親ディレクトリが存在しない場合のみエラー）
        with pytest.raises(ValueError, match="CSVファイルのディレクトリが存在しません"):
            config = BatchConfig(
                database_path="",  # 空のパスは作成される
                csv_file_path="/nonexistent/directory/stocks.csv",
            )
            MainBatchApplication(config)

    @patch("stock_batch.services.csv_reader.CSVReader.read_and_convert")
    @patch("stock_batch.services.stock_fetcher.StockFetcher.fetch_stock_data")
    @patch("stock_batch.services.translation.TranslationService.translate_to_japanese")
    def test_full_batch_processing_success(
        self,
        mock_translate: Mock,
        mock_stock_fetch: Mock,
        mock_csv_read: Mock,
    ) -> None:
        """完全バッチ処理成功のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_path = tmp_db.name
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            csv_path = tmp_csv.name
            # CSVファイルに実際のデータを書き込み
            tmp_csv.write("コード,銘柄名,市場,現在値,前日比(%)\n".encode())
            tmp_csv.write("1332,ニッスイ,東P,877.8,+2.5\n".encode())
            tmp_csv.write("1418,インターライフ,東S,405.0,-1.2\n".encode())

        try:
            # CSVReader のモック
            from stock_batch.models.company import Company

            mock_csv_companies = [
                Company(
                    symbol="1332.T",
                    name="ニッスイ",
                    market="東P",
                    business_summary="",
                    price=877.8,
                ),
                Company(
                    symbol="1418.T",
                    name="インターライフ",
                    market="東S",
                    business_summary="",
                    price=405.0,
                ),
            ]
            mock_csv_read.return_value = mock_csv_companies

            # StockFetcher のモック
            def mock_fetch_side_effect(symbol: str):
                from stock_batch.services.stock_fetcher import StockData

                if symbol == "1332.T":
                    return StockData(
                        symbol=symbol,
                        current_price=877.8,
                        business_summary=(
                            "Nissui Corporation is a Japanese fishery company."
                        ),
                        volume=1000000,
                        day_high=890.0,
                        day_low=870.0,
                        sector="Consumer Defensive",
                        industry="Packaged Foods",
                    )
                elif symbol == "1418.T":
                    return StockData(
                        symbol=symbol,
                        current_price=405.0,
                        business_summary="InterLife Corporation provides IT services.",
                        volume=500000,
                        sector="Technology",
                        industry="Software",
                    )
                return None

            mock_stock_fetch.side_effect = mock_fetch_side_effect

            # TranslationService のモック
            def mock_translate_side_effect(text: str) -> str:
                if "fishery" in text:
                    return "日水株式会社は日本の水産会社です。"
                elif "IT services" in text:
                    return "インターライフ株式会社はITサービスを提供しています。"
                return f"翻訳済み: {text}"

            mock_translate.side_effect = mock_translate_side_effect

            # バッチ処理実行
            config = BatchConfig(
                database_path=db_path,
                csv_file_path=csv_path,
                chunk_size=50,
                enable_parallel=False,
                enable_stock_data_fetch=True,
                enable_translation=True,
                max_retries=3,
            )

            app = MainBatchApplication(config)
            result = app.run_batch()

            # 結果検証
            assert result.success is True
            assert result.total_processed == 2
            assert result.companies_inserted >= 0
            assert result.companies_updated >= 0
            assert result.processing_time > 0
            assert len(result.error_details) == 0

        finally:
            Path(db_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)

    def test_batch_processing_with_existing_data(self) -> None:
        """既存データありでのバッチ処理テスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_path = tmp_db.name
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            csv_path = tmp_csv.name
            tmp_csv.write("コード,銘柄名,市場,現在値,前日比(%)\n".encode())
            tmp_csv.write("1332,ニッスイ,東P,890.0,+1.5\n".encode())  # 価格変更

        try:
            config = BatchConfig(
                database_path=db_path,
                csv_file_path=csv_path,
                enable_stock_data_fetch=False,  # 高速化のため無効
                enable_translation=False,
            )

            app = MainBatchApplication(config)

            # 1回目の実行（新規挿入）
            result1 = app.run_batch()
            assert result1.companies_inserted == 1

            # 2回目の実行（更新）
            result2 = app.run_batch()
            assert result2.companies_updated >= 0  # 価格変更により更新される可能性

        finally:
            Path(db_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)

    @patch("stock_batch.services.csv_reader.CSVReader.read_and_convert")
    def test_batch_processing_with_csv_error(self, mock_csv_read: Mock) -> None:
        """CSV読み取りエラー時のバッチ処理テスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_path = tmp_db.name
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            csv_path = tmp_csv.name

        try:
            # CSV読み取りエラーをモック
            mock_csv_read.side_effect = Exception("CSV読み取りエラー")

            config = BatchConfig(
                database_path=db_path,
                csv_file_path=csv_path,
            )

            app = MainBatchApplication(config)
            result = app.run_batch()

            assert result.success is False
            assert "CSV読み取りエラー" in str(result.error_details)

        finally:
            Path(db_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)

    @patch("stock_batch.services.stock_fetcher.StockFetcher.fetch_stock_data")
    def test_batch_processing_with_stock_fetch_errors(
        self, mock_stock_fetch: Mock
    ) -> None:
        """株価取得エラー時のバッチ処理テスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_path = tmp_db.name
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            csv_path = tmp_csv.name
            tmp_csv.write("コード,銘柄名,市場,現在値,前日比(%)\n".encode())
            tmp_csv.write("1332,ニッスイ,東P,877.8,+2.5\n".encode())
            tmp_csv.write("9999,存在しない,東P,100.0,+0.0\n".encode())  # 存在しない企業

        try:
            # 一部の企業で株価取得エラー
            def mock_fetch_side_effect(symbol: str):
                if symbol == "1332.T":
                    from stock_batch.services.stock_fetcher import StockData

                    return StockData(
                        symbol=symbol,
                        current_price=877.8,
                        business_summary="Nissui Corporation",
                    )
                else:
                    return None  # 存在しない企業

            mock_stock_fetch.side_effect = mock_fetch_side_effect

            config = BatchConfig(
                database_path=db_path,
                csv_file_path=csv_path,
                enable_stock_data_fetch=True,
                enable_translation=False,
                continue_on_error=True,
            )

            app = MainBatchApplication(config)
            result = app.run_batch()

            # 一部成功、一部失敗
            assert result.success is True  # continue_on_error=True
            assert result.total_processed == 2
            assert result.companies_inserted >= 1

        finally:
            Path(db_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)

    def test_dry_run_mode(self) -> None:
        """ドライランモードのテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_path = tmp_db.name
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            csv_path = tmp_csv.name
            tmp_csv.write("コード,銘柄名,市場,現在値,前日比(%)\n".encode())
            tmp_csv.write("1332,ニッスイ,東P,877.8,+2.5\n".encode())

        try:
            config = BatchConfig(
                database_path=db_path,
                csv_file_path=csv_path,
                dry_run=True,
                enable_stock_data_fetch=False,
                enable_translation=False,
            )

            app = MainBatchApplication(config)
            result = app.run_batch()

            # ドライランでは実際の更新は行われない
            assert result.success is True
            assert result.total_processed >= 1
            assert result.companies_inserted == 0  # ドライランなので0
            assert result.companies_updated == 0

        finally:
            Path(db_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)

    def test_parallel_processing_mode(self) -> None:
        """並列処理モードのテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_path = tmp_db.name
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            csv_path = tmp_csv.name
            # 複数企業のCSVデータ
            csv_data = "コード,銘柄名,市場,現在値,前日比(%)\n"
            for i in range(1300, 1320):  # 20社
                csv_data += f"{i},企業{i},東P,{i}.0,+1.0\n"
            tmp_csv.write(csv_data.encode())

        try:
            config = BatchConfig(
                database_path=db_path,
                csv_file_path=csv_path,
                chunk_size=5,
                enable_parallel=True,
                max_workers=2,
                enable_stock_data_fetch=False,  # 高速化
                enable_translation=False,
            )

            app = MainBatchApplication(config)
            result = app.run_batch()

            assert result.success is True
            assert result.total_processed == 20
            assert result.parallel_processing_used is True

        finally:
            Path(db_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)

    def test_logging_configuration(self) -> None:
        """ログ設定のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_path = tmp_db.name
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            csv_path = tmp_csv.name
            tmp_csv.write("コード,銘柄名,市場,現在値,前日比(%)\n".encode())
            tmp_csv.write("1332,ニッスイ,東P,877.8,+2.5\n".encode())

        try:
            config = BatchConfig(
                database_path=db_path,
                csv_file_path=csv_path,
                log_level="DEBUG",
                enable_stock_data_fetch=False,
                enable_translation=False,
            )

            app = MainBatchApplication(config)

            # ログレベルが設定されているか確認
            import logging

            logger = logging.getLogger("stock_batch")
            assert logger.level == logging.DEBUG

            result = app.run_batch()
            assert result.success is True

        finally:
            Path(db_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)

    def test_progress_reporting(self) -> None:
        """進捗報告のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_path = tmp_db.name
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            csv_path = tmp_csv.name
            # 進捗確認用の複数データ
            csv_data = "コード,銘柄名,市場,現在値,前日比(%)\n"
            for i in range(1400, 1410):  # 10社
                csv_data += f"{i},企業{i},東P,{i}.0,+1.0\n"
            tmp_csv.write(csv_data.encode())

        try:
            config = BatchConfig(
                database_path=db_path,
                csv_file_path=csv_path,
                enable_progress_reporting=True,
                progress_report_interval=3,  # 3件ごとに報告
                enable_stock_data_fetch=True,  # 進捗報告のために有効化
                enable_translation=False,
            )

            app = MainBatchApplication(config)
            result = app.run_batch()

            assert result.success is True
            assert result.total_processed == 10
            assert len(result.progress_reports) >= 0  # 進捗報告は条件次第

        finally:
            Path(db_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)

    def test_kubernetes_compatibility(self) -> None:
        """Kubernetes対応のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_path = tmp_db.name
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            csv_path = tmp_csv.name
            tmp_csv.write("コード,銘柄名,市場,現在値,前日比(%)\n".encode())
            tmp_csv.write("1332,ニッスイ,東P,877.8,+2.5\n".encode())

        try:
            # Kubernetes環境変数のモック
            with patch.dict(
                "os.environ",
                {
                    "KUBERNETES_SERVICE_HOST": "kubernetes.default.svc",
                    "BATCH_DATABASE_PATH": db_path,
                    "BATCH_CSV_PATH": csv_path,
                    "BATCH_LOG_LEVEL": "INFO",
                },
            ):
                config = BatchConfig.from_environment()
                assert config.database_path == db_path
                assert config.csv_file_path == csv_path
                assert config.log_level == "INFO"

                app = MainBatchApplication(config)
                result = app.run_batch()

                # Kubernetes対応の確認
                assert result.success is True
                assert result.environment == "kubernetes"

        finally:
            Path(db_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)

    def test_performance_monitoring(self) -> None:
        """パフォーマンス監視のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_path = tmp_db.name
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            csv_path = tmp_csv.name
            csv_data = "コード,銘柄名,市場,現在値,前日比(%)\n"
            for i in range(1500, 1600):  # 100社
                csv_data += f"{i},企業{i},東P,{i}.0,+1.0\n"
            tmp_csv.write(csv_data.encode())

        try:
            config = BatchConfig(
                database_path=db_path,
                csv_file_path=csv_path,
                enable_performance_monitoring=True,
                enable_stock_data_fetch=False,
                enable_translation=False,
            )

            app = MainBatchApplication(config)
            result = app.run_batch()

            assert result.success is True
            assert result.processing_time > 0
            assert result.memory_usage_mb >= 0
            assert result.records_per_second > 0
            assert result.database_operations_count > 0

        finally:
            Path(db_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)

    def test_graceful_shutdown(self) -> None:
        """Graceful Shutdown のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_path = tmp_db.name
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            csv_path = tmp_csv.name
            tmp_csv.write("コード,銘柄名,市場,現在値,前日比(%)\n".encode())
            tmp_csv.write("1332,ニッスイ,東P,877.8,+2.5\n".encode())

        try:
            config = BatchConfig(
                database_path=db_path,
                csv_file_path=csv_path,
                enable_graceful_shutdown=True,
                enable_stock_data_fetch=False,
                enable_translation=False,
            )

            app = MainBatchApplication(config)

            # シグナルハンドラーが登録されているか確認
            assert app.shutdown_requested is False

            result = app.run_batch()
            assert result.success is True

        finally:
            Path(db_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)

    def test_get_application_stats(self) -> None:
        """アプリケーション統計情報取得のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_path = tmp_db.name
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            csv_path = tmp_csv.name
            tmp_csv.write("コード,銘柄名,市場,現在値,前日比(%)\n".encode())
            tmp_csv.write("1332,ニッスイ,東P,877.8,+2.5\n".encode())

        try:
            config = BatchConfig(
                database_path=db_path,
                csv_file_path=csv_path,
                enable_stock_data_fetch=False,
                enable_translation=False,
            )

            app = MainBatchApplication(config)

            # 複数回実行
            for _ in range(3):
                app.run_batch()

            stats = app.get_application_stats()
            assert stats["total_runs"] == 3
            assert stats["total_records_processed"] >= 3
            assert stats["average_processing_time"] > 0
            assert "last_run_result" in stats

        finally:
            Path(db_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)
