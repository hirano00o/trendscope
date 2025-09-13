"""エラーハンドリングユーティリティ

月次スイングトレードシステムの堅牢なエラーハンドリングを提供。
リトライ機能、ログ機能、エラー分類機能を含む。

主要機能:
- 自動リトライ機能付きデコレータ
- エラー分類とマッピング
- 構造化ログ出力
- エラー復旧戦略
"""

import asyncio
import functools
import time
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

import pandas as pd
import structlog
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout

from ..exceptions import (
    CalculationError,
    DataNotFoundError,
    DataValidationError,
    ExternalServiceError,
    InsufficientDataError,
    MonthlySwingError,
    NetworkError,
    SignalGenerationError,
    TrendAnalysisError,
    YFinanceError,
)

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class ErrorClassifier:
    """エラー分類器.
    
    様々な例外を適切なカスタム例外に分類・変換する。
    外部ライブラリの例外を統一されたエラー階層にマッピング。
    """
    
    # yfinance関連エラーのマッピング
    YFINANCE_ERROR_PATTERNS = [
        "ticker",
        "yahoo",
        "yfinance",
        "data not found",
        "no data found",
        "delisted",
    ]
    
    # ネットワーク関連エラーのマッピング
    NETWORK_ERROR_TYPES = (
        ConnectionError,
        Timeout,
        HTTPError,
        RequestException,
    )
    
    # データ不足関連エラーパターン
    INSUFFICIENT_DATA_PATTERNS = [
        "insufficient data",
        "not enough data",
        "minimum",
        "データ不足",
        "不十分",
    ]
    
    @classmethod
    def classify_error(
        cls, 
        exc: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> MonthlySwingError:
        """例外を適切なカスタム例外に分類.
        
        Args:
            exc: 元の例外
            context: エラーコンテキスト
            
        Returns:
            MonthlySwingError: 分類されたカスタム例外
            
        Example:
            >>> import requests
            >>> exc = requests.exceptions.ConnectionError("Connection failed")
            >>> classified = ErrorClassifier.classify_error(exc)
            >>> isinstance(classified, NetworkError)
            True
        """
        context = context or {}
        error_message = str(exc).lower()
        
        # ネットワーク関連エラー
        if isinstance(exc, cls.NETWORK_ERROR_TYPES):
            return NetworkError(
                f"ネットワークエラー: {exc}",
                context={"original_error": str(exc), **context}
            )
        
        # yfinance関連エラー
        if any(pattern in error_message for pattern in cls.YFINANCE_ERROR_PATTERNS):
            symbol = context.get("symbol", "unknown")
            return YFinanceError(
                f"yfinanceデータ取得エラー: {exc}",
                symbol=symbol,
                context={"original_error": str(exc), **context}
            )
        
        # データ不足エラー
        if any(pattern in error_message for pattern in cls.INSUFFICIENT_DATA_PATTERNS):
            return InsufficientDataError(
                f"データ不足エラー: {exc}",
                required_points=context.get("required_points", 30),
                available_points=context.get("available_points", 0),
                context={"original_error": str(exc), **context}
            )
        
        # 値エラー → データ検証エラー
        if isinstance(exc, ValueError):
            return DataValidationError(
                f"データ検証エラー: {exc}",
                validation_type="value_error",
                context={"original_error": str(exc), **context}
            )
        
        # キーエラー → データ検証エラー
        if isinstance(exc, KeyError):
            return DataValidationError(
                f"必要なデータフィールドが見つかりません: {exc}",
                validation_type="missing_field",
                context={"original_error": str(exc), **context}
            )
        
        # ゼロ除算エラー → 計算エラー
        if isinstance(exc, ZeroDivisionError):
            return CalculationError(
                f"ゼロ除算エラー: {exc}",
                calculation_type="division",
                context={"original_error": str(exc), **context}
            )
        
        # その他の例外は一般的なMonthlySwingErrorとして処理
        return MonthlySwingError(
            f"予期しないエラー: {exc}",
            error_code="UNEXPECTED_ERROR",
            context={"original_error": str(exc), "error_type": type(exc).__name__, **context}
        )


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    retry_on: Optional[List[Type[Exception]]] = None,
    context_key: str = "operation"
) -> Callable:
    """エラー時の自動リトライデコレータ.
    
    指定された例外が発生した場合に自動的にリトライを実行。
    指数バックオフによる待機時間調整をサポート。
    
    Args:
        max_retries: 最大リトライ回数
        delay: 初期待機時間（秒）
        backoff_factor: バックオフ係数
        retry_on: リトライ対象の例外タイプリスト
        context_key: ログのコンテキストキー
        
    Returns:
        Callable: デコレータ関数
        
    Example:
        >>> @retry_on_error(max_retries=3, delay=1.0)
        ... async def fetch_data(symbol: str) -> pd.DataFrame:
        ...     # データ取得処理
        ...     pass
    """
    if retry_on is None:
        retry_on = [NetworkError, YFinanceError, ExternalServiceError]
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                        
                except Exception as exc:
                    last_exception = exc
                    
                    # リトライ対象外の例外は即座に再発生
                    if not any(isinstance(exc, retry_type) for retry_type in retry_on):
                        logger.error(
                            "リトライ対象外のエラーが発生",
                            error=str(exc),
                            error_type=type(exc).__name__,
                            **{context_key: func.__name__}
                        )
                        raise
                    
                    # 最後の試行でもエラーの場合は例外を再発生
                    if attempt == max_retries:
                        logger.error(
                            f"最大リトライ回数({max_retries})に達しました",
                            error=str(exc),
                            attempts=attempt + 1,
                            **{context_key: func.__name__}
                        )
                        raise
                    
                    # リトライ待機
                    wait_time = delay * (backoff_factor ** attempt)
                    logger.warning(
                        f"リトライ実行中 ({attempt + 1}/{max_retries})",
                        error=str(exc),
                        wait_time=wait_time,
                        next_attempt=attempt + 2,
                        **{context_key: func.__name__}
                    )
                    
                    await asyncio.sleep(wait_time)
            
            # ここには到達しないはずだが、念のため
            if last_exception:
                raise last_exception
                
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                        
                except Exception as exc:
                    last_exception = exc
                    
                    # リトライ対象外の例外は即座に再発生
                    if not any(isinstance(exc, retry_type) for retry_type in retry_on):
                        logger.error(
                            "リトライ対象外のエラーが発生",
                            error=str(exc),
                            error_type=type(exc).__name__,
                            **{context_key: func.__name__}
                        )
                        raise
                    
                    # 最後の試行でもエラーの場合は例外を再発生
                    if attempt == max_retries:
                        logger.error(
                            f"最大リトライ回数({max_retries})に達しました",
                            error=str(exc),
                            attempts=attempt + 1,
                            **{context_key: func.__name__}
                        )
                        raise
                    
                    # リトライ待機
                    wait_time = delay * (backoff_factor ** attempt)
                    logger.warning(
                        f"リトライ実行中 ({attempt + 1}/{max_retries})",
                        error=str(exc),
                        wait_time=wait_time,
                        next_attempt=attempt + 2,
                        **{context_key: func.__name__}
                    )
                    
                    time.sleep(wait_time)
            
            # ここには到達しないはずだが、念のため
            if last_exception:
                raise last_exception
                
        # 関数がasyncかどうかで適切なラッパーを返す
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator


def handle_errors(
    operation_name: str,
    symbol: Optional[str] = None,
    log_level: str = "error"
) -> Callable:
    """統一されたエラーハンドリングデコレータ.
    
    例外を適切に分類し、構造化ログを出力し、
    統一されたエラー形式で再発生させる。
    
    Args:
        operation_name: 操作名（ログ用）
        symbol: 関連するシンボル
        log_level: ログレベル
        
    Returns:
        Callable: デコレータ関数
        
    Example:
        >>> @handle_errors("月次トレンド分析", symbol="AAPL")
        ... async def analyze_trend(data: pd.DataFrame) -> dict:
        ...     # 分析処理
        ...     pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            start_time = time.time()
            
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                    
                # 成功時のログ
                execution_time = time.time() - start_time
                logger.info(
                    f"{operation_name}が正常に完了しました",
                    symbol=symbol,
                    execution_time=execution_time,
                    operation=operation_name
                )
                
                return result
                
            except MonthlySwingError:
                # 既にカスタム例外の場合はそのまま再発生
                raise
                
            except Exception as exc:
                # 例外を分類してカスタム例外に変換
                context = {
                    "symbol": symbol,
                    "operation": operation_name,
                    "execution_time": time.time() - start_time
                }
                
                classified_error = ErrorClassifier.classify_error(exc, context)
                
                # 構造化ログ出力
                log_func = getattr(logger, log_level, logger.error)
                log_func(
                    f"{operation_name}でエラーが発生しました",
                    error_type=type(classified_error).__name__,
                    error_code=classified_error.error_code,
                    error_message=str(classified_error),
                    original_error=str(exc),
                    **context
                )
                
                raise classified_error
                
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                    
                # 成功時のログ
                execution_time = time.time() - start_time
                logger.info(
                    f"{operation_name}が正常に完了しました",
                    symbol=symbol,
                    execution_time=execution_time,
                    operation=operation_name
                )
                
                return result
                
            except MonthlySwingError:
                # 既にカスタム例外の場合はそのまま再発生
                raise
                
            except Exception as exc:
                # 例外を分類してカスタム例外に変換
                context = {
                    "symbol": symbol,
                    "operation": operation_name,
                    "execution_time": time.time() - start_time
                }
                
                classified_error = ErrorClassifier.classify_error(exc, context)
                
                # 構造化ログ出力
                log_func = getattr(logger, log_level, logger.error)
                log_func(
                    f"{operation_name}でエラーが発生しました",
                    error_type=type(classified_error).__name__,
                    error_code=classified_error.error_code,
                    error_message=str(classified_error),
                    original_error=str(exc),
                    **context
                )
                
                raise classified_error
                
        # 関数がasyncかどうかで適切なラッパーを返す
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator


def validate_dataframe(
    df: pd.DataFrame,
    required_columns: List[str],
    min_rows: int = 30,
    operation_name: str = "データ検証"
) -> None:
    """DataFrame検証ユーティリティ.
    
    必要な列の存在、最小行数、データ品質を検証。
    
    Args:
        df: 検証対象のDataFrame
        required_columns: 必要な列名のリスト
        min_rows: 最小行数
        operation_name: 操作名（エラーメッセージ用）
        
    Raises:
        DataValidationError: データが無効な場合
        InsufficientDataError: データ量が不足している場合
        
    Example:
        >>> validate_dataframe(
        ...     stock_data,
        ...     ["open", "high", "low", "close", "volume"],
        ...     min_rows=30
        ... )
    """
    # 空のDataFrameチェック
    if df.empty:
        raise InsufficientDataError(
            f"{operation_name}: データが空です",
            required_points=min_rows,
            available_points=0
        )
    
    # 必要な列の存在確認
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise DataValidationError(
            f"{operation_name}: 必要な列が不足しています: {missing_columns}",
            validation_type="missing_columns",
            context={
                "missing_columns": missing_columns,
                "available_columns": list(df.columns),
                "required_columns": required_columns
            }
        )
    
    # 最小行数チェック
    if len(df) < min_rows:
        raise InsufficientDataError(
            f"{operation_name}: データ量が不足しています",
            required_points=min_rows,
            available_points=len(df)
        )
    
    # NaN値の存在確認
    for col in required_columns:
        nan_count = df[col].isna().sum()
        if nan_count > 0:
            logger.warning(
                f"{operation_name}: 列 '{col}' にNaN値が含まれています",
                column=col,
                nan_count=nan_count,
                total_rows=len(df)
            )


def safe_divide(
    numerator: float, 
    denominator: float, 
    default: float = 0.0,
    operation_name: str = "除算"
) -> float:
    """安全な除算実行.
    
    ゼロ除算を回避し、適切なデフォルト値を返す。
    
    Args:
        numerator: 分子
        denominator: 分母  
        default: ゼロ除算時のデフォルト値
        operation_name: 操作名（ログ用）
        
    Returns:
        float: 除算結果またはデフォルト値
        
    Example:
        >>> result = safe_divide(10.0, 2.0)  # 5.0
        >>> result = safe_divide(10.0, 0.0, default=float('inf'))  # inf
    """
    if denominator == 0:
        logger.warning(
            f"{operation_name}: ゼロ除算が発生しました。デフォルト値を使用します",
            numerator=numerator,
            denominator=denominator,
            default=default
        )
        return default
    
    return numerator / denominator


def log_performance_metrics(
    operation_name: str,
    start_time: float,
    data_points: Optional[int] = None,
    symbol: Optional[str] = None,
    **additional_metrics
) -> None:
    """パフォーマンス指標をログ出力.
    
    処理時間、データポイント数、スループットなどの指標を記録。
    
    Args:
        operation_name: 操作名
        start_time: 開始時刻
        data_points: 処理したデータポイント数
        symbol: 関連するシンボル
        **additional_metrics: 追加の指標
        
    Example:
        >>> start = time.time()
        >>> # 処理実行
        >>> log_performance_metrics(
        ...     "データ取得", 
        ...     start, 
        ...     data_points=100,
        ...     symbol="AAPL"
        ... )
    """
    execution_time = time.time() - start_time
    
    metrics = {
        "operation": operation_name,
        "execution_time": execution_time,
        "timestamp": time.time()
    }
    
    if symbol:
        metrics["symbol"] = symbol
    
    if data_points:
        metrics["data_points"] = data_points
        metrics["throughput"] = data_points / execution_time if execution_time > 0 else 0
    
    metrics.update(additional_metrics)
    
    logger.info(f"{operation_name} パフォーマンス指標", **metrics)