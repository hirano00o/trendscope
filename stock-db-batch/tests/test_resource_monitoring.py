"""リソース使用量監視機能のテストコード

CPU、メモリ使用量の監視とログ出力機能をテストします。
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from stock_batch.main_batch_application import (
    BatchConfig,
    MainBatchApplication,
)


class TestResourceMonitoring:
    """リソース使用量監視機能のテスト"""

    def test_memory_usage_measurement(self) -> None:
        """メモリ使用量測定のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_path = tmp_db.name
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            csv_path = tmp_csv.name
            tmp_csv.write(
                "コード,銘柄名,市場,現在値,前日比(%)\n1332,テスト,東P,877.8,+2.5\n".encode()
            )

        try:
            config = BatchConfig(
                database_path=db_path,
                csv_file_path=csv_path,
                enable_performance_monitoring=True,
                enable_stock_data_fetch=False,
                enable_translation=False,
            )

            app = MainBatchApplication(config)

            # メモリ使用量測定メソッドのテスト
            memory_usage = app._get_memory_usage()

            # メモリ使用量は0以上のfloat値
            assert isinstance(memory_usage, float)
            assert memory_usage >= 0.0

        finally:
            Path(db_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)

    @patch("psutil.Process")
    def test_memory_usage_with_mock(self, mock_process_class: Mock) -> None:
        """メモリ使用量測定（モック使用）のテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_path = tmp_db.name
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            csv_path = tmp_csv.name
            tmp_csv.write(
                "コード,銘柄名,市場,現在値,前日比(%)\n1332,テスト,東P,877.8,+2.5\n".encode()
            )

        try:
            # メモリ使用量をモック（100MB）
            mock_process = Mock()
            mock_memory_info = Mock()
            mock_memory_info.rss = 104857600  # 100MB in bytes
            mock_process.memory_info.return_value = mock_memory_info
            mock_process_class.return_value = mock_process

            config = BatchConfig(
                database_path=db_path,
                csv_file_path=csv_path,
                enable_performance_monitoring=True,
                enable_stock_data_fetch=False,
                enable_translation=False,
            )

            app = MainBatchApplication(config)
            memory_usage = app._get_memory_usage()

            # 100MB = 100.0 MiB
            assert memory_usage == 100.0

        finally:
            Path(db_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)

    @patch("psutil.Process")
    def test_memory_usage_error_handling(self, mock_process_class: Mock) -> None:
        """メモリ使用量測定エラーハンドリングのテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_path = tmp_db.name
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            csv_path = tmp_csv.name
            tmp_csv.write(
                "コード,銘柄名,市場,現在値,前日比(%)\n1332,テスト,東P,877.8,+2.5\n".encode()
            )

        try:
            # psutilでエラーを発生させる
            mock_process_class.side_effect = Exception("Process error")

            config = BatchConfig(
                database_path=db_path,
                csv_file_path=csv_path,
                enable_performance_monitoring=True,
                enable_stock_data_fetch=False,
                enable_translation=False,
            )

            app = MainBatchApplication(config)
            memory_usage = app._get_memory_usage()

            # エラー時は0.0を返す
            assert memory_usage == 0.0

        finally:
            Path(db_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)

    def test_batch_result_includes_memory_usage(self) -> None:
        """バッチ結果にメモリ使用量が含まれることのテスト"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            db_path = tmp_db.name
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            csv_path = tmp_csv.name
            tmp_csv.write(
                "コード,銘柄名,市場,現在値,前日比(%)\n1332,テスト,東P,877.8,+2.5\n".encode()
            )

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

            # バッチ結果にメモリ使用量が含まれる
            assert result.success is True
            assert hasattr(result, "memory_usage_mb")
            assert isinstance(result.memory_usage_mb, float)
            assert result.memory_usage_mb >= 0.0

        finally:
            Path(db_path).unlink(missing_ok=True)
            Path(csv_path).unlink(missing_ok=True)
