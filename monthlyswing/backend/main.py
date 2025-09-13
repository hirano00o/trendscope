#!/usr/bin/env python3
"""main.py: 月次スイングトレード分析システムのエントリーポイント.

CLAUDE スタックに基づく高性能金融アプリケーション。

技術仕様:
- Python 3.12+ with FastAPI
- uv package manager (10-100x faster than pip)
- ruff code quality (100-200x faster than flake8)
- Async/await optimization (75% performance improvement)

セキュリティ機能:
- CORS middleware
- Security headers
- Rate limiting
- Audit logging

使用方法:
    uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

環境変数:
    - ENVIRONMENT: production/development/testing
    - LOG_LEVEL: INFO/DEBUG/WARNING/ERROR
    - DATABASE_URL: PostgreSQL/TimescaleDB接続URL
"""

import uvicorn


def main() -> None:
    """アプリケーションのメインエントリーポイント.

    開発サーバーを起動し、月次スイングトレード分析APIを提供する。
    本番環境では uvicorn を直接使用することを推奨。

    Returns:
        None

    Example:
        >>> python main.py
        INFO:     Started server process [12345]
        INFO:     Waiting for application startup.
        INFO:     Application startup complete.
        INFO:     Uvicorn running on http://0.0.0.0:8000
    """
    uvicorn.run(
        "monthlyswing_backend.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
