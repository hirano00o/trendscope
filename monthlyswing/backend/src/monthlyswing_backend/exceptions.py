"""カスタム例外クラス定義

月次スイングトレードシステム用の例外階層を定義。
適切なエラーハンドリングと診断情報の提供を目的とする。

例外階層:
- MonthlySwingError (基底例外)
  - DataError (データ関連エラー)
    - DataNotFoundError (データ取得失敗)
    - DataValidationError (データ検証失敗)
    - InsufficientDataError (データ不足)
  - AnalysisError (分析関連エラー)
    - TrendAnalysisError (トレンド分析失敗)
    - SignalGenerationError (シグナル生成失敗)
    - CalculationError (計算エラー)
  - ExternalServiceError (外部サービスエラー)
    - YFinanceError (yfinance関連エラー)
    - NetworkError (ネットワークエラー)
"""

from typing import Any, Dict, Optional


class MonthlySwingError(Exception):
    """月次スイングトレードシステム基底例外.
    
    全てのカスタム例外の基底クラス。
    エラーコードと追加のコンテキスト情報を提供。
    
    Attributes:
        error_code: エラーを識別するコード
        context: エラーに関する追加情報
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "UNKNOWN_ERROR",
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """初期化.
        
        Args:
            message: エラーメッセージ
            error_code: エラー識別コード
            context: エラーコンテキスト情報
        """
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """例外情報を辞書形式で返す.
        
        Returns:
            Dict[str, Any]: 例外情報
        """
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": str(self),
            "context": self.context
        }


class DataError(MonthlySwingError):
    """データ関連エラー基底クラス.
    
    データ取得、検証、処理に関連するエラーの基底クラス。
    """
    pass


class DataNotFoundError(DataError):
    """データ取得失敗エラー.
    
    指定されたシンボルのデータが取得できない場合に発生。
    
    例:
        >>> raise DataNotFoundError(
        ...     "シンボル INVALID のデータが見つかりません",
        ...     error_code="DATA_NOT_FOUND",
        ...     context={"symbol": "INVALID", "source": "yfinance"}
        ... )
    """
    
    def __init__(
        self, 
        message: str, 
        symbol: str,
        source: str = "unknown",
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """初期化.
        
        Args:
            message: エラーメッセージ
            symbol: 取得に失敗したシンボル
            source: データソース
            context: 追加コンテキスト
        """
        context = context or {}
        context.update({"symbol": symbol, "source": source})
        super().__init__(message, "DATA_NOT_FOUND", context)


class DataValidationError(DataError):
    """データ検証エラー.
    
    取得したデータが期待する形式や内容でない場合に発生。
    
    例:
        >>> raise DataValidationError(
        ...     "必要な列が不足しています",
        ...     error_code="MISSING_COLUMNS",
        ...     context={"missing_columns": ["close", "volume"]}
        ... )
    """
    
    def __init__(
        self,
        message: str,
        validation_type: str = "format",
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """初期化.
        
        Args:
            message: エラーメッセージ
            validation_type: 検証タイプ (format, range, required, etc.)
            context: 追加コンテキスト
        """
        context = context or {}
        context["validation_type"] = validation_type
        super().__init__(message, "DATA_VALIDATION_ERROR", context)


class InsufficientDataError(DataError):
    """データ不足エラー.
    
    分析に必要な最小限のデータ量が不足している場合に発生。
    
    例:
        >>> raise InsufficientDataError(
        ...     "分析には最低30日分のデータが必要です",
        ...     required_points=30,
        ...     available_points=15
        ... )
    """
    
    def __init__(
        self,
        message: str,
        required_points: int,
        available_points: int,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """初期化.
        
        Args:
            message: エラーメッセージ
            required_points: 必要なデータポイント数
            available_points: 利用可能なデータポイント数
            context: 追加コンテキスト
        """
        context = context or {}
        context.update({
            "required_points": required_points,
            "available_points": available_points
        })
        super().__init__(message, "INSUFFICIENT_DATA", context)


class AnalysisError(MonthlySwingError):
    """分析関連エラー基底クラス.
    
    トレンド分析、シグナル生成、計算処理に関連するエラーの基底クラス。
    """
    pass


class TrendAnalysisError(AnalysisError):
    """トレンド分析エラー.
    
    月次トレンド分析処理で問題が発生した場合に発生。
    
    例:
        >>> raise TrendAnalysisError(
        ...     "トレンド方向の特定に失敗しました",
        ...     analysis_step="trend_direction",
        ...     context={"symbol": "AAPL", "data_points": 100}
        ... )
    """
    
    def __init__(
        self,
        message: str,
        analysis_step: str = "unknown",
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """初期化.
        
        Args:
            message: エラーメッセージ
            analysis_step: 失敗した分析ステップ
            context: 追加コンテキスト
        """
        context = context or {}
        context["analysis_step"] = analysis_step
        super().__init__(message, "TREND_ANALYSIS_ERROR", context)


class SignalGenerationError(AnalysisError):
    """シグナル生成エラー.
    
    スイングトレードシグナル生成で問題が発生した場合に発生。
    
    例:
        >>> raise SignalGenerationError(
        ...     "シグナル信頼度の計算に失敗しました",
        ...     signal_type="confidence_calculation",
        ...     context={"trend_strength": 0.7}
        ... )
    """
    
    def __init__(
        self,
        message: str,
        signal_type: str = "unknown",
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """初期化.
        
        Args:
            message: エラーメッセージ
            signal_type: シグナルタイプ
            context: 追加コンテキスト
        """
        context = context or {}
        context["signal_type"] = signal_type
        super().__init__(message, "SIGNAL_GENERATION_ERROR", context)


class CalculationError(AnalysisError):
    """計算エラー.
    
    数値計算で問題が発生した場合に発生。
    
    例:
        >>> raise CalculationError(
        ...     "ゼロ除算エラーが発生しました",
        ...     calculation_type="risk_reward_ratio",
        ...     context={"denominator": 0}
        ... )
    """
    
    def __init__(
        self,
        message: str,
        calculation_type: str = "unknown",
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """初期化.
        
        Args:
            message: エラーメッセージ
            calculation_type: 計算タイプ
            context: 追加コンテキスト
        """
        context = context or {}
        context["calculation_type"] = calculation_type
        super().__init__(message, "CALCULATION_ERROR", context)


class ExternalServiceError(MonthlySwingError):
    """外部サービスエラー基底クラス.
    
    外部API、データプロバイダー、ネットワーク関連エラーの基底クラス。
    """
    pass


class YFinanceError(ExternalServiceError):
    """yfinance関連エラー.
    
    yfinanceライブラリを使用したデータ取得で問題が発生した場合に発生。
    
    例:
        >>> raise YFinanceError(
        ...     "yfinanceからのデータ取得に失敗しました",
        ...     symbol="AAPL",
        ...     context={"period": "1y", "timeout": 30}
        ... )
    """
    
    def __init__(
        self,
        message: str,
        symbol: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """初期化.
        
        Args:
            message: エラーメッセージ
            symbol: 関連するシンボル
            context: 追加コンテキスト
        """
        context = context or {}
        if symbol:
            context["symbol"] = symbol
        super().__init__(message, "YFINANCE_ERROR", context)


class NetworkError(ExternalServiceError):
    """ネットワークエラー.
    
    ネットワーク接続、タイムアウト関連の問題が発生した場合に発生。
    
    例:
        >>> raise NetworkError(
        ...     "接続タイムアウトが発生しました",
        ...     context={"timeout_seconds": 30, "url": "https://api.example.com"}
        ... )
    """
    
    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """初期化.
        
        Args:
            message: エラーメッセージ
            context: 追加コンテキスト
        """
        super().__init__(message, "NETWORK_ERROR", context)


# エラーコードから例外クラスへのマッピング
ERROR_CODE_TO_EXCEPTION = {
    "DATA_NOT_FOUND": DataNotFoundError,
    "DATA_VALIDATION_ERROR": DataValidationError,
    "INSUFFICIENT_DATA": InsufficientDataError,
    "TREND_ANALYSIS_ERROR": TrendAnalysisError,
    "SIGNAL_GENERATION_ERROR": SignalGenerationError,
    "CALCULATION_ERROR": CalculationError,
    "YFINANCE_ERROR": YFinanceError,
    "NETWORK_ERROR": NetworkError,
}


def create_exception_from_code(
    error_code: str, 
    message: str, 
    context: Optional[Dict[str, Any]] = None
) -> MonthlySwingError:
    """エラーコードから適切な例外インスタンスを作成.
    
    Args:
        error_code: エラーコード
        message: エラーメッセージ
        context: 追加コンテキスト
        
    Returns:
        MonthlySwingError: 作成された例外インスタンス
        
    Example:
        >>> exc = create_exception_from_code(
        ...     "DATA_NOT_FOUND",
        ...     "データが見つかりません",
        ...     {"symbol": "AAPL"}
        ... )
        >>> isinstance(exc, DataNotFoundError)
        True
    """
    exception_class = ERROR_CODE_TO_EXCEPTION.get(error_code, MonthlySwingError)
    
    # 特定の例外クラスの場合、適切なコンストラクタを使用
    if exception_class == DataNotFoundError and context:
        symbol = context.get("symbol", "unknown")
        source = context.get("source", "unknown")
        return DataNotFoundError(message, symbol=symbol, source=source, context=context)
    elif exception_class == InsufficientDataError and context:
        required = context.get("required_points", 0)
        available = context.get("available_points", 0)
        return InsufficientDataError(message, required_points=required, available_points=available, context=context)
    else:
        return exception_class(message, error_code, context)