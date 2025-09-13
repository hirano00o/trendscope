"""test_error_handling.py: エラーハンドリング機能のテスト

強化されたエラーハンドリング機能のユニットテストを実装。
カスタム例外、エラー分類、リトライ機能のテストを包括的に実行。

テスト対象:
- カスタム例外クラスの動作
- ErrorClassifierの分類機能
- retry_on_errorデコレータ
- handle_errorsデコレータ
- エラーハンドリングユーティリティ関数
"""

import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pytest
import requests

from monthlyswing_backend.exceptions import (
    CalculationError,
    DataNotFoundError,
    DataValidationError,
    InsufficientDataError,
    MonthlySwingError,
    NetworkError,
    SignalGenerationError,
    TrendAnalysisError,
    YFinanceError,
    create_exception_from_code,
)
from monthlyswing_backend.utils.error_handling import (
    ErrorClassifier,
    handle_errors,
    log_performance_metrics,
    retry_on_error,
    safe_divide,
    validate_dataframe,
)


class TestCustomExceptions:
    """カスタム例外クラスのテスト."""

    def test_monthly_swing_error_basic(self) -> None:
        """MonthlySwingError基底クラスの基本機能."""
        error = MonthlySwingError(
            "テストエラー",
            error_code="TEST_ERROR",
            context={"symbol": "AAPL", "value": 123}
        )
        
        assert str(error) == "テストエラー"
        assert error.error_code == "TEST_ERROR"
        assert error.context["symbol"] == "AAPL"
        assert error.context["value"] == 123
        
        # to_dict()メソッドのテスト
        error_dict = error.to_dict()
        assert error_dict["error_type"] == "MonthlySwingError"
        assert error_dict["error_code"] == "TEST_ERROR"
        assert error_dict["message"] == "テストエラー"
        assert error_dict["context"]["symbol"] == "AAPL"

    def test_data_not_found_error(self) -> None:
        """DataNotFoundErrorの機能テスト."""
        error = DataNotFoundError(
            "データが見つかりません",
            symbol="INVALID",
            source="yfinance",
            context={"period": "1y"}
        )
        
        assert error.error_code == "DATA_NOT_FOUND"
        assert error.context["symbol"] == "INVALID"
        assert error.context["source"] == "yfinance"
        assert error.context["period"] == "1y"

    def test_insufficient_data_error(self) -> None:
        """InsufficientDataErrorの機能テスト."""
        error = InsufficientDataError(
            "データが不足しています",
            required_points=30,
            available_points=15
        )
        
        assert error.error_code == "INSUFFICIENT_DATA"
        assert error.context["required_points"] == 30
        assert error.context["available_points"] == 15

    def test_calculation_error(self) -> None:
        """CalculationErrorの機能テスト."""
        error = CalculationError(
            "ゼロ除算エラー",
            calculation_type="risk_reward_ratio",
            context={"numerator": 10.0, "denominator": 0.0}
        )
        
        assert error.error_code == "CALCULATION_ERROR"
        assert error.context["calculation_type"] == "risk_reward_ratio"

    def test_create_exception_from_code(self) -> None:
        """エラーコードから例外作成のテスト."""
        error = create_exception_from_code(
            "DATA_NOT_FOUND",
            "テストメッセージ",
            {"symbol": "TEST", "source": "test_source"}
        )
        
        assert isinstance(error, DataNotFoundError)
        assert str(error) == "テストメッセージ"
        assert error.context["symbol"] == "TEST"
        assert error.context["source"] == "test_source"
        
        # InsufficientDataErrorのテスト
        insufficient_error = create_exception_from_code(
            "INSUFFICIENT_DATA",
            "データ不足",
            {"required_points": 30, "available_points": 10}
        )
        assert isinstance(insufficient_error, InsufficientDataError)
        assert insufficient_error.context["required_points"] == 30
        assert insufficient_error.context["available_points"] == 10
        
        # 未知のエラーコードの場合
        unknown_error = create_exception_from_code(
            "UNKNOWN_CODE",
            "未知のエラー"
        )
        assert isinstance(unknown_error, MonthlySwingError)
        assert unknown_error.error_code == "UNKNOWN_CODE"


class TestErrorClassifier:
    """ErrorClassifierクラスのテスト."""

    def test_classify_network_error(self) -> None:
        """ネットワークエラーの分類テスト."""
        connection_error = requests.exceptions.ConnectionError("Connection failed")
        classified = ErrorClassifier.classify_error(
            connection_error,
            context={"url": "https://test.com"}
        )
        
        assert isinstance(classified, NetworkError)
        assert "Connection failed" in str(classified)
        assert classified.context["url"] == "https://test.com"

    def test_classify_yfinance_error(self) -> None:
        """yfinanceエラーの分類テスト."""
        ticker_error = Exception("ticker symbol not found")
        classified = ErrorClassifier.classify_error(
            ticker_error,
            context={"symbol": "INVALID"}
        )
        
        assert isinstance(classified, YFinanceError)
        assert classified.context["symbol"] == "INVALID"

    def test_classify_value_error(self) -> None:
        """ValueErrorの分類テスト."""
        value_error = ValueError("invalid value")
        classified = ErrorClassifier.classify_error(value_error)
        
        assert isinstance(classified, DataValidationError)
        assert "invalid value" in str(classified)

    def test_classify_zero_division_error(self) -> None:
        """ZeroDivisionErrorの分類テスト."""
        zero_div_error = ZeroDivisionError("division by zero")
        classified = ErrorClassifier.classify_error(zero_div_error)
        
        assert isinstance(classified, CalculationError)
        assert classified.context["calculation_type"] == "division"

    def test_classify_key_error(self) -> None:
        """KeyErrorの分類テスト."""
        key_error = KeyError("missing_key")
        classified = ErrorClassifier.classify_error(key_error)
        
        assert isinstance(classified, DataValidationError)
        assert classified.context["validation_type"] == "missing_field"

    def test_classify_insufficient_data_error(self) -> None:
        """データ不足エラーの分類テスト."""
        insufficient_error = Exception("insufficient data for analysis")
        classified = ErrorClassifier.classify_error(
            insufficient_error,
            context={"required_points": 30, "available_points": 10}
        )
        
        assert isinstance(classified, InsufficientDataError)
        assert classified.context["required_points"] == 30

    def test_classify_unknown_error(self) -> None:
        """未知のエラーの分類テスト."""
        unknown_error = RuntimeError("unexpected error")
        classified = ErrorClassifier.classify_error(unknown_error)
        
        assert isinstance(classified, MonthlySwingError)
        assert classified.error_code == "UNEXPECTED_ERROR"


class TestRetryDecorator:
    """retry_on_errorデコレータのテスト."""

    @pytest.mark.asyncio
    async def test_retry_success_on_second_attempt(self) -> None:
        """2回目の試行で成功するテスト."""
        attempt_count = 0
        
        @retry_on_error(max_retries=3, delay=0.01)
        async def flaky_function() -> str:
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise NetworkError("Network temporarily unavailable")
            return "success"
        
        result = await flaky_function()
        assert result == "success"
        assert attempt_count == 2

    @pytest.mark.asyncio
    async def test_retry_exhausted(self) -> None:
        """リトライ回数上限でのテスト."""
        @retry_on_error(max_retries=2, delay=0.01)
        async def always_fail() -> str:
            raise NetworkError("Always fails")
        
        with pytest.raises(NetworkError):
            await always_fail()

    @pytest.mark.asyncio
    async def test_retry_non_retryable_error(self) -> None:
        """リトライ対象外エラーのテスト."""
        @retry_on_error(max_retries=3, delay=0.01)
        async def non_retryable_error() -> str:
            raise DataValidationError("Validation failed")
        
        with pytest.raises(DataValidationError):
            await non_retryable_error()

    def test_retry_sync_function(self) -> None:
        """同期関数のリトライテスト."""
        attempt_count = 0
        
        @retry_on_error(max_retries=2, delay=0.01)
        def sync_flaky_function() -> str:
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise YFinanceError("yfinance error")
            return "success"
        
        result = sync_flaky_function()
        assert result == "success"
        assert attempt_count == 2

    @pytest.mark.asyncio
    async def test_retry_backoff(self) -> None:
        """指数バックオフのテスト."""
        start_time = time.time()
        
        @retry_on_error(max_retries=2, delay=0.01, backoff_factor=2.0)
        async def always_fail() -> str:
            raise NetworkError("Always fails")
        
        with pytest.raises(NetworkError):
            await always_fail()
        
        # 最低でも0.01 + 0.02 = 0.03秒は経過しているはず
        elapsed = time.time() - start_time
        assert elapsed >= 0.025  # バッファを考慮


class TestHandleErrorsDecorator:
    """handle_errorsデコレータのテスト."""

    @pytest.mark.asyncio
    async def test_handle_errors_success(self) -> None:
        """正常実行時のテスト."""
        @handle_errors("テスト操作", symbol="AAPL")
        async def successful_function() -> str:
            return "success"
        
        result = await successful_function()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_handle_errors_classification(self) -> None:
        """エラー分類のテスト."""
        @handle_errors("テスト操作", symbol="AAPL")
        async def error_function() -> str:
            raise ValueError("Invalid input")
        
        with pytest.raises(DataValidationError):
            await error_function()

    @pytest.mark.asyncio
    async def test_handle_errors_preserves_custom_exception(self) -> None:
        """カスタム例外保持のテスト."""
        @handle_errors("テスト操作")
        async def custom_error_function() -> str:
            raise DataNotFoundError("Custom error", symbol="TEST")
        
        with pytest.raises(DataNotFoundError) as exc_info:
            await custom_error_function()
        
        assert exc_info.value.context["symbol"] == "TEST"

    def test_handle_errors_sync_function(self) -> None:
        """同期関数のハンドリングテスト."""
        @handle_errors("同期テスト操作")
        def sync_error_function() -> str:
            raise KeyError("missing_field")
        
        with pytest.raises(DataValidationError):
            sync_error_function()


class TestValidationUtilities:
    """検証ユーティリティ関数のテスト."""

    def test_validate_dataframe_success(self) -> None:
        """DataFrame検証成功テスト."""
        df = pd.DataFrame({
            "open": [100, 101, 102],
            "high": [105, 106, 107],
            "low": [99, 100, 101],
            "close": [104, 105, 106],
            "volume": [1000, 1100, 1200]
        })
        
        # 正常ケース（例外が発生しないことを確認）
        validate_dataframe(df, ["open", "high", "low", "close", "volume"], min_rows=3)

    def test_validate_dataframe_empty(self) -> None:
        """空DataFrame検証テスト."""
        df = pd.DataFrame()
        
        with pytest.raises(InsufficientDataError) as exc_info:
            validate_dataframe(df, ["close"], min_rows=1)
        
        assert exc_info.value.context["available_points"] == 0

    def test_validate_dataframe_missing_columns(self) -> None:
        """列不足検証テスト."""
        df = pd.DataFrame({"close": [100, 101, 102]})
        
        with pytest.raises(DataValidationError) as exc_info:
            validate_dataframe(df, ["close", "volume"], min_rows=3)
        
        assert "volume" in exc_info.value.context["missing_columns"]

    def test_validate_dataframe_insufficient_rows(self) -> None:
        """行数不足検証テスト."""
        df = pd.DataFrame({
            "close": [100, 101],
            "volume": [1000, 1100]
        })
        
        with pytest.raises(InsufficientDataError) as exc_info:
            validate_dataframe(df, ["close", "volume"], min_rows=5)
        
        assert exc_info.value.context["required_points"] == 5
        assert exc_info.value.context["available_points"] == 2

    def test_validate_dataframe_nan_values(self) -> None:
        """NaN値検証テスト（警告のみ）."""
        df = pd.DataFrame({
            "close": [100, None, 102],
            "volume": [1000, 1100, 1200]
        })
        
        # NaN値があっても例外は発生しない（警告のみ）
        validate_dataframe(df, ["close", "volume"], min_rows=3)

    def test_safe_divide_normal(self) -> None:
        """通常の除算テスト."""
        result = safe_divide(10.0, 2.0)
        assert result == 5.0

    def test_safe_divide_zero_denominator(self) -> None:
        """ゼロ除算テスト."""
        result = safe_divide(10.0, 0.0, default=float('inf'))
        assert result == float('inf')
        
        # デフォルト値のテスト
        result = safe_divide(10.0, 0.0)
        assert result == 0.0

    @patch('monthlyswing_backend.utils.error_handling.logger')
    def test_log_performance_metrics(self, mock_logger: Mock) -> None:
        """パフォーマンス指標ログのテスト."""
        start_time = time.time() - 1.0  # 1秒前
        
        log_performance_metrics(
            "テスト操作",
            start_time,
            data_points=100,
            symbol="AAPL",
            custom_metric=42
        )
        
        # ログが呼び出されたことを確認
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        
        # ログメッセージの確認
        assert "テスト操作 パフォーマンス指標" in call_args[0][0]
        
        # ログデータの確認
        log_data = call_args[1]
        assert log_data["operation"] == "テスト操作"
        assert log_data["data_points"] == 100
        assert log_data["symbol"] == "AAPL"
        assert log_data["custom_metric"] == 42
        assert "execution_time" in log_data
        assert "throughput" in log_data
        assert log_data["throughput"] > 0


class TestErrorHandlingIntegration:
    """エラーハンドリング統合テスト."""

    @pytest.mark.asyncio
    async def test_complete_error_handling_flow(self) -> None:
        """完全なエラーハンドリングフローのテスト."""
        attempt_count = 0
        
        @retry_on_error(max_retries=2, delay=0.01)
        @handle_errors("統合テスト", symbol="TEST")
        async def complex_function() -> str:
            nonlocal attempt_count
            attempt_count += 1
            
            if attempt_count == 1:
                raise requests.exceptions.ConnectionError("Network error")
            elif attempt_count == 2:
                raise ValueError("Validation error")
            else:
                return "success"
        
        with pytest.raises(DataValidationError):
            await complex_function()
        
        # NetworkErrorでリトライされ、ValueErrorで失敗
        assert attempt_count == 2

    @pytest.mark.asyncio
    async def test_error_context_preservation(self) -> None:
        """エラーコンテキスト保持のテスト."""
        @handle_errors("コンテキストテスト", symbol="AAPL")
        async def context_function() -> str:
            raise Exception("Original error message")
        
        with pytest.raises(MonthlySwingError) as exc_info:
            await context_function()
        
        # コンテキスト情報が保持されているか確認
        error = exc_info.value
        assert error.context["symbol"] == "AAPL"
        assert error.context["operation"] == "コンテキストテスト"
        assert "execution_time" in error.context
        assert "Original error message" in error.context["original_error"]

    def test_error_hierarchy_consistency(self) -> None:
        """エラー階層の一貫性テスト."""
        # すべてのカスタム例外がMonthlySwingErrorを継承していることを確認
        exceptions = [
            DataNotFoundError("test", "TEST"),
            DataValidationError("test"),
            InsufficientDataError("test", 10, 5),
            TrendAnalysisError("test"),
            SignalGenerationError("test"),
            CalculationError("test"),
            YFinanceError("test"),
            NetworkError("test")
        ]
        
        for exc in exceptions:
            assert isinstance(exc, MonthlySwingError)
            assert hasattr(exc, 'error_code')
            assert hasattr(exc, 'context')
            assert hasattr(exc, 'to_dict')

    @patch('monthlyswing_backend.utils.error_handling.logger')
    def test_error_logging_integration(self, mock_logger: Mock) -> None:
        """エラーログ統合のテスト."""
        @handle_errors("ログテスト", symbol="AAPL", log_level="warning")
        def logging_function() -> str:
            raise ValueError("Test error for logging")
        
        with pytest.raises(DataValidationError):
            logging_function()
        
        # 警告レベルでログが出力されることを確認
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        
        # ログ内容の確認
        assert "ログテストでエラーが発生しました" in call_args[0][0]
        log_data = call_args[1]
        assert log_data["error_type"] == "DataValidationError"
        assert log_data["error_code"] == "DATA_VALIDATION_ERROR"
        assert log_data["symbol"] == "AAPL"