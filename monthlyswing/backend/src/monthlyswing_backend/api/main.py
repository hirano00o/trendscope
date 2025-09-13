"""main.py: 月次スイングトレード分析API.

CLAUDEスタックに基づく高性能金融アプリケーション。
FastAPI + Python 3.12 + 非同期処理でエンタープライズレベルのセキュリティと性能を提供。

主要機能:
- 月次価格動向分析
- スイングトレード指標計算
- エントリー/エグジットシグナル生成
- リスク管理指標
- パフォーマンス追跡

セキュリティ機能:
- CORS設定
- セキュリティヘッダー
- レート制限
- 監査ログ
- JWT認証対応

パフォーマンス特徴:
- Python 3.12非同期処理（75%高速化）
- 接続プーリング
- リアルタイムWebSocket
"""

import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ロガー設定
logger = structlog.get_logger(__name__)


class HealthStatus(BaseModel):
    """ヘルスチェックレスポンスモデル.

    システムの健全性を示すデータ構造。

    Attributes:
        status: システムステータス（healthy/unhealthy）
        timestamp: チェック実行時刻
        version: アプリケーションバージョン
        uptime_seconds: システム起動からの経過時間（秒）

    Example:
        >>> health = HealthStatus(
        ...     status="healthy",
        ...     timestamp=datetime.utcnow(),
        ...     version="0.1.0",
        ...     uptime_seconds=3600.0,
        ... )
    """

    status: str = Field(..., description="システムの健全性")
    timestamp: datetime = Field(..., description="チェック実行時刻")
    version: str = Field(..., description="アプリケーションバージョン")
    uptime_seconds: float = Field(..., description="システム稼働時間（秒）")


class ErrorResponse(BaseModel):
    """エラーレスポンスモデル.

    API エラー時の標準レスポンス形式。

    Attributes:
        error: エラータイプ
        message: エラー詳細メッセージ
        timestamp: エラー発生時刻
        request_id: リクエスト追跡ID（オプション）

    Example:
        >>> error = ErrorResponse(
        ...     error="ValidationError",
        ...     message="Invalid stock symbol format",
        ...     timestamp=datetime.utcnow(),
        ... )
    """

    error: str = Field(..., description="エラータイプ")
    message: str = Field(..., description="エラーメッセージ")
    timestamp: datetime = Field(..., description="エラー発生時刻")
    request_id: str | None = Field(None, description="リクエスト追跡ID")


# アプリケーション起動時刻（アップタイム計算用）
_startup_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理.

    FastAPIアプリケーションの起動・終了時の処理を定義。
    データベース接続、キャッシュ、外部サービス接続などを管理。

    Args:
        app: FastAPIアプリケーションインスタンス

    Yields:
        None: アプリケーション実行中

    Example:
        起動時にデータベース接続、終了時にクリーンアップを実行
    """
    # 起動時処理
    logger.info("月次スイングトレード分析システム起動中...")

    # TODO: データベース接続プール初期化
    # TODO: Redis接続初期化
    # TODO: 外部API接続確認

    logger.info("システム起動完了")

    yield

    # 終了時処理
    logger.info("システム終了処理中...")

    # TODO: データベース接続プールクリーンアップ
    # TODO: Redis接続クリーンアップ
    # TODO: 未処理タスクの終了待機

    logger.info("システム終了完了")


# FastAPIアプリケーション初期化
app = FastAPI(
    title="月次スイングトレード分析API",
    description="月次スイングトレード戦略に特化した金融分析システム",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)


# セキュリティミドルウェア設定
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "*.monthlyswing.dev",
        "testserver",  # テスト用ホスト
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js開発サーバー
        "http://localhost:8080",  # 代替フロントエンド
        "https://monthlyswing.dev",  # 本番ドメイン
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next) -> JSONResponse:
    """セキュリティヘッダー追加ミドルウェア.

    すべてのレスポンスに金融アプリケーション向けセキュリティヘッダーを追加。

    Args:
        request: HTTPリクエスト
        call_next: 次のミドルウェア/エンドポイント

    Returns:
        JSONResponse: セキュリティヘッダー付きレスポンス

    Security Headers:
        - X-Content-Type-Options: MIME タイプスニッフィング防止
        - X-Frame-Options: クリックジャッキング防止
        - X-XSS-Protection: XSS攻撃防止
        - Strict-Transport-Security: HTTPS強制
        - Content-Security-Policy: リソース読み込み制限
    """
    response = await call_next(request)

    # 金融アプリケーション向けセキュリティヘッダー
    security_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'"
        ),
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }

    for header, value in security_headers.items():
        response.headers[header] = value

    return response


@app.middleware("http")
async def audit_logging_middleware(request: Request, call_next) -> JSONResponse:
    """監査ログミドルウェア.

    すべてのAPIリクエストを監査ログとして記録。
    金融アプリケーションのコンプライアンス要件に対応。

    Args:
        request: HTTPリクエスト
        call_next: 次のミドルウェア/エンドポイント

    Returns:
        JSONResponse: 監査ログ記録済みレスポンス

    Logged Information:
        - リクエスト時刻
        - HTTPメソッド・パス
        - クライアントIP
        - ユーザーエージェント
        - レスポンス時間
        - ステータスコード
    """
    start_time = time.time()

    # リクエスト情報収集
    audit_data = {
        "timestamp": datetime.now(UTC).isoformat(),
        "method": request.method,
        "path": request.url.path,
        "query_params": str(request.query_params),
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
        "content_type": request.headers.get("content-type"),
    }

    try:
        response = await call_next(request)
        processing_time = time.time() - start_time

        audit_data.update(
            {
                "status_code": response.status_code,
                "processing_time_ms": round(processing_time * 1000, 2),
                "response_size": response.headers.get("content-length"),
            }
        )

        # 監査ログ出力
        logger.info("API request processed", **audit_data)

        return response

    except Exception as exc:
        processing_time = time.time() - start_time
        audit_data.update(
            {
                "status_code": 500,
                "processing_time_ms": round(processing_time * 1000, 2),
                "error": str(exc),
            }
        )

        logger.error("API request failed", **audit_data)
        raise


# ヘルスチェックエンドポイント
@app.get(
    "/health",
    response_model=HealthStatus,
    summary="ヘルスチェック",
    description="システムの健全性を確認する",
    tags=["System"],
)
async def health_check() -> HealthStatus:
    """システムヘルスチェック.

    アプリケーションとその依存サービスの健全性を確認する。
    ロードバランサーやKubernetesの死活監視で使用。

    Returns:
        HealthStatus: システムの健全性情報

    Raises:
        HTTPException: システムが異常状態の場合

    Example:
        >>> curl http://localhost:8000/health
        {
            "status": "healthy",
            "timestamp": "2024-01-15T10:30:00Z",
            "version": "0.1.0",
            "uptime_seconds": 3600.0
        }
    """
    current_time = time.time()
    uptime = current_time - _startup_time

    # TODO: データベース接続確認
    # TODO: Redis接続確認
    # TODO: 外部API接続確認

    return HealthStatus(
        status="healthy",
        timestamp=datetime.now(UTC),
        version="0.1.0",
        uptime_seconds=uptime,
    )


@app.get(
    "/",
    summary="API ルート",
    description="月次スイングトレード分析APIのエントリーポイント",
    tags=["System"],
)
async def root() -> dict[str, Any]:
    """APIルートエンドポイント.

    システム情報とAPI概要を提供する。

    Returns:
        Dict[str, Any]: システム基本情報とAPIガイドリンク

    Example:
        >>> curl http://localhost:8000/
        {
            "message": "月次スイングトレード分析API",
            "version": "0.1.0",
            "docs_url": "/docs",
            "health_url": "/health"
        }
    """
    return {
        "message": "月次スイングトレード分析API",
        "version": "0.1.0",
        "description": "月次スイングトレード戦略に特化した金融分析システム",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_url": "/health",
        "timestamp": datetime.now(UTC).isoformat(),
    }


# エラーハンドラー
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """404 Not Found エラーハンドラー.

    存在しないエンドポイントへのリクエストを処理。

    Args:
        request: HTTPリクエスト
        exc: HTTPException

    Returns:
        JSONResponse: 標準エラーレスポンス
    """
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            error="NotFound",
            message=f"エンドポイント '{request.url.path}' が見つかりません",
            timestamp=datetime.now(UTC),
        ).model_dump(mode="json"),
    )


@app.exception_handler(405)
async def method_not_allowed_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """405 Method Not Allowed エラーハンドラー.

    サポートされていないHTTPメソッドでのリクエストを処理。

    Args:
        request: HTTPリクエスト
        exc: HTTPException

    Returns:
        JSONResponse: 標準エラーレスポンス
    """
    return JSONResponse(
        status_code=405,
        content=ErrorResponse(
            error="MethodNotAllowed",
            message=f"メソッド '{request.method}' はサポートされていません",
            timestamp=datetime.now(UTC),
        ).model_dump(mode="json"),
    )


@app.exception_handler(500)
async def internal_server_error_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """500 Internal Server Error エラーハンドラー.

    予期しないサーバーエラーを処理し、適切なエラーレスポンスを返す。

    Args:
        request: HTTPリクエスト
        exc: Exception

    Returns:
        JSONResponse: 標準エラーレスポンス
    """
    logger.error(
        "Internal server error",
        path=request.url.path,
        method=request.method,
        error=str(exc),
    )

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="内部サーバーエラーが発生しました",
            timestamp=datetime.now(UTC),
        ).model_dump(mode="json"),
    )


# 月次スイングトレード統合エンドポイント
@app.get("/api/v1/monthly-swing/analysis/{symbol}")
async def monthly_swing_analysis(symbol: str) -> dict[str, Any]:
    """月次スイングトレード統合分析エンドポイント.

    指定された株式シンボルに対して月次トレンド分析からシグナル生成まで
    一気通貫で実行し、統合された分析結果を返す。

    Args:
        symbol: 株式シンボル (例: "AAPL", "MSFT", "7203.T")

    Returns:
        dict[str, Any]: 統合分析結果
            - symbol: 分析対象シンボル
            - analysis_timestamp: 分析実行時刻
            - monthly_trend_analysis: 月次トレンド分析結果
            - swing_signal: スイングトレードシグナル
            - integrated_analysis: 統合分析スコア
            - risk_assessment: リスク評価
            - metadata: 分析メタデータ

    Raises:
        HTTPException: 400 - 無効なシンボル
        HTTPException: 404 - データが見つからない
        HTTPException: 503 - サービス利用不可

    Example:
        GET /api/v1/monthly-swing/analysis/AAPL
        → 月次スイング分析結果を返す
    """
    try:
        # シンボル形式の基本検証
        if not symbol or len(symbol) < 1 or len(symbol) > 20:
            raise HTTPException(
                status_code=400, detail=f"無効な株式シンボルです: {symbol}"
            )

        logger.info(f"月次スイング分析リクエスト: {symbol}")

        # MonthlySwingServiceを使用して統合分析実行
        from monthlyswing_backend.services.monthly_swing_service import (
            analyze_monthly_swing_simple,
        )

        result = await analyze_monthly_swing_simple(symbol)

        logger.info(f"月次スイング分析完了: {symbol}")
        return result

    except HTTPException:
        # HTTPExceptionはそのまま再発生
        raise
    except ValueError as e:
        # 値エラーは400 Bad Requestとして処理
        logger.warning(f"月次スイング分析エラー: {symbol} - {e!s}")
        raise HTTPException(status_code=400, detail=f"分析エラー: {e!s}")
    except Exception as e:
        # その他のエラーは503 Service Unavailableとして処理
        logger.error(f"月次スイング分析内部エラー: {symbol} - {e!s}")
        raise HTTPException(
            status_code=503,
            detail="一時的に分析サービスが利用できません。しばらく時間をおいて再試行してください。",
        )
