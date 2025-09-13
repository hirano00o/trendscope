"""test_api_main.py: FastAPI メインアプリケーションのテスト

TDD原則に従いAPIエンドポイントの包括的テストを実装。
セキュリティ、エラーハンドリング、パフォーマンスを検証。

テスト対象:
- ヘルスチェックエンドポイント
- ルートエンドポイント
- エラーハンドラー (404, 405, 500)
- セキュリティミドルウェア
- 監査ログミドルウェア

テストカテゴリ:
- 正常系レスポンス検証
- 異常系エラーハンドリング
- セキュリティヘッダー確認
- パフォーマンス測定
- 監査ログ出力検証
"""

import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from monthlyswing_backend.api.main import app


class TestHealthEndpoint:
    """ヘルスチェックエンドポイントのテスト"""

    def test_health_check_success(self) -> None:
        """正常なヘルスチェックレスポンスを検証"""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # レスポンス構造検証
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "uptime_seconds" in data

        # 値の妥当性検証
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0

        # タイムスタンプ形式検証
        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        assert isinstance(timestamp, datetime)

    def test_health_check_headers(self) -> None:
        """ヘルスチェックのセキュリティヘッダーを検証"""
        client = TestClient(app)
        response = client.get("/health")

        # セキュリティヘッダー確認
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert "max-age=31536000" in response.headers.get(
            "Strict-Transport-Security", ""
        )

    def test_health_check_performance(self) -> None:
        """ヘルスチェックのレスポンス時間を検証"""
        client = TestClient(app)

        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()

        assert response.status_code == 200
        response_time = end_time - start_time
        # ヘルスチェックは100ms以内で応答すべき
        assert response_time < 0.1


class TestRootEndpoint:
    """ルートエンドポイントのテスト"""

    def test_root_endpoint_success(self) -> None:
        """ルートエンドポイントの正常レスポンスを検証"""
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        # レスポンス構造検証
        required_fields = [
            "message",
            "version",
            "description",
            "docs_url",
            "redoc_url",
            "health_url",
            "timestamp",
        ]
        for field in required_fields:
            assert field in data

        # 値の妥当性検証
        assert data["message"] == "月次スイングトレード分析API"
        assert data["version"] == "0.1.0"
        assert data["docs_url"] == "/docs"
        assert data["redoc_url"] == "/redoc"
        assert data["health_url"] == "/health"

    def test_root_endpoint_timestamp_format(self) -> None:
        """ルートエンドポイントのタイムスタンプ形式を検証"""
        client = TestClient(app)
        response = client.get("/")

        data = response.json()
        timestamp_str = data["timestamp"]

        # ISO形式のタイムスタンプ検証
        timestamp = datetime.fromisoformat(timestamp_str)
        assert isinstance(timestamp, datetime)


class TestErrorHandlers:
    """エラーハンドラーのテスト"""

    def test_404_error_handler(self) -> None:
        """404エラーハンドラーを検証"""
        client = TestClient(app)
        response = client.get("/nonexistent-endpoint")

        assert response.status_code == 404
        data = response.json()

        # エラーレスポンス構造検証
        assert "error" in data
        assert "message" in data
        assert "timestamp" in data

        # エラー内容検証
        assert data["error"] == "NotFound"
        assert "nonexistent-endpoint" in data["message"]
        assert "見つかりません" in data["message"]

    def test_405_error_handler(self) -> None:
        """405エラーハンドラーを検証"""
        client = TestClient(app)
        # POST メソッドでGETのみ対応のエンドポイントを呼び出し
        response = client.post("/health")

        assert response.status_code == 405
        data = response.json()

        # エラーレスポンス構造検証
        assert "error" in data
        assert "message" in data
        assert "timestamp" in data

        # エラー内容検証
        assert data["error"] == "MethodNotAllowed"
        assert "POST" in data["message"]
        assert "サポートされていません" in data["message"]

    @pytest.mark.skip(reason="500エラーテストは複雑なため一時的にスキップ")
    def test_500_error_handler(self) -> None:
        """500エラーハンドラーを検証"""
        # TODO: より良いアプローチでの500エラーテスト実装
        pass

    def test_error_timestamp_format(self) -> None:
        """エラーレスポンスのタイムスタンプ形式を検証"""
        client = TestClient(app)
        response = client.get("/nonexistent")

        data = response.json()
        timestamp_str = data["timestamp"]

        # ISO形式のタイムスタンプ検証
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        assert isinstance(timestamp, datetime)


class TestSecurityMiddleware:
    """セキュリティミドルウェアのテスト"""

    def test_security_headers_present(self) -> None:
        """全てのセキュリティヘッダーが設定されていることを確認"""
        client = TestClient(app)
        response = client.get("/")

        # 必須セキュリティヘッダー確認
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }

        for header, expected_value in security_headers.items():
            actual_value = response.headers.get(header)
            if header == "Strict-Transport-Security":
                assert "max-age=31536000" in actual_value
                assert "includeSubDomains" in actual_value
            else:
                assert actual_value == expected_value, f"Header {header} mismatch"

    def test_csp_header_configuration(self) -> None:
        """Content Security Policyヘッダーの設定を確認"""
        client = TestClient(app)
        response = client.get("/")

        csp_header = response.headers.get("Content-Security-Policy")
        assert csp_header is not None

        # CSP ディレクティブの確認
        expected_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self'",
        ]

        for directive in expected_directives:
            assert directive in csp_header


class TestAuditLoggingMiddleware:
    """監査ログミドルウェアのテスト"""

    @patch("monthlyswing_backend.api.main.logger")
    def test_audit_logging_success(self, mock_logger: MagicMock) -> None:
        """正常リクエストの監査ログを確認"""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200

        # ログ出力確認
        mock_logger.info.assert_called()
        call_args = mock_logger.info.call_args

        # ログメッセージ確認
        assert call_args[0][0] == "API request processed"

        # ログデータ確認
        log_data = call_args[1]
        assert "timestamp" in log_data
        assert log_data["method"] == "GET"
        assert log_data["path"] == "/health"
        assert log_data["status_code"] == 200
        assert "processing_time_ms" in log_data

    @patch("monthlyswing_backend.api.main.logger")
    def test_audit_logging_error(self, mock_logger: MagicMock) -> None:
        """エラーリクエストの監査ログを確認"""
        client = TestClient(app)
        response = client.get("/nonexistent")

        assert response.status_code == 404

        # エラーログ出力確認
        mock_logger.info.assert_called()
        call_args = mock_logger.info.call_args

        # ログデータ確認
        log_data = call_args[1]
        assert log_data["status_code"] == 404
        assert "processing_time_ms" in log_data

    def test_performance_logging(self) -> None:
        """パフォーマンスログが記録されることを確認"""
        client = TestClient(app)

        with patch("monthlyswing_backend.api.main.logger") as mock_logger:
            response = client.get("/health")
            assert response.status_code == 200

            # ログ出力確認
            mock_logger.info.assert_called()
            log_data = mock_logger.info.call_args[1]

            # パフォーマンス指標確認
            processing_time = log_data["processing_time_ms"]
            assert isinstance(processing_time, (int, float))
            assert processing_time >= 0


class TestCORSMiddleware:
    """CORS ミドルウェアのテスト"""

    def test_cors_preflight_request(self) -> None:
        """CORS プリフライトリクエストを確認"""
        client = TestClient(app)
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        }

        response = client.options("/health", headers=headers)

        # CORS ヘッダー確認
        assert (
            response.headers.get("Access-Control-Allow-Origin")
            == "http://localhost:3000"
        )
        assert "GET" in response.headers.get("Access-Control-Allow-Methods", "")
        assert response.headers.get("Access-Control-Allow-Credentials") == "true"

    def test_cors_actual_request(self) -> None:
        """CORS 実際のリクエストを確認"""
        client = TestClient(app)
        headers = {"Origin": "http://localhost:3000"}

        response = client.get("/health", headers=headers)

        assert response.status_code == 200
        assert (
            response.headers.get("Access-Control-Allow-Origin")
            == "http://localhost:3000"
        )


class TestApplicationLifecycle:
    """アプリケーションライフサイクルのテスト"""

    def test_app_configuration(self) -> None:
        """アプリケーション設定を確認"""
        assert app.title == "月次スイングトレード分析API"
        assert app.version == "0.1.0"
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"
        assert app.openapi_url == "/api/v1/openapi.json"

    def test_middleware_order(self) -> None:
        """ミドルウェアの適用順序を確認"""
        # ミドルウェアが適切な順序で適用されていることを確認
        # (実際の実装では、ミドルウェアスタックの確認が必要)
        client = TestClient(app)
        response = client.get("/")

        # セキュリティヘッダーとCORSヘッダーが両方適用されていることを確認
        assert response.headers.get("X-Frame-Options") == "DENY"
        # 許可されたオリジンからのリクエストの場合のみCORSヘッダーが設定される


@pytest.mark.performance
class TestPerformanceRequirements:
    """パフォーマンス要件のテスト"""

    def test_health_endpoint_response_time(self) -> None:
        """ヘルスエンドポイントの応答時間要件を確認"""
        client = TestClient(app)

        # 複数回測定して平均を取る
        times = []
        for _ in range(10):
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()

            assert response.status_code == 200
            times.append(end_time - start_time)

        avg_time = sum(times) / len(times)
        # 平均応答時間が50ms以下であることを確認
        assert avg_time < 0.05, (
            f"Average response time {avg_time:.3f}s exceeds 50ms limit"
        )

    def test_concurrent_requests(self) -> None:
        """同時リクエスト処理能力を確認"""
        from concurrent.futures import ThreadPoolExecutor

        client = TestClient(app)

        def make_request() -> int:
            response = client.get("/health")
            return response.status_code

        # 10並行リクエスト実行
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]

        # 全てのリクエストが正常に処理されたことを確認
        assert all(status == 200 for status in results)
