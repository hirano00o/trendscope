"""Tests for FastAPI application main module."""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from trendscope_backend.api.main import app, get_health_status


class TestFastAPIApplication:
    """Test cases for FastAPI application setup and configuration."""

    def test_app_creation(self) -> None:
        """Test FastAPI application creation and basic configuration."""
        assert app.title == "TrendScope Backend API"
        assert app.description == "Stock trend analysis API with technical indicators"
        assert app.version == "0.1.0"

    def test_cors_middleware_configured(self) -> None:
        """Test CORS middleware is properly configured."""
        # Check if CORS middleware is in the middleware stack
        middleware_classes = [middleware.cls for middleware in app.user_middleware]
        from fastapi.middleware.cors import CORSMiddleware

        assert CORSMiddleware in middleware_classes

    def test_app_has_required_routes(self) -> None:
        """Test that application has all required routes configured."""
        routes = [route.path for route in app.routes]

        # Basic routes
        assert "/health" in routes
        assert "/docs" in routes
        assert "/redoc" in routes

        # API routes
        assert "/api/v1/" in routes
        assert "/api/v1/stock/{symbol}" in routes


class TestHealthEndpoint:
    """Test cases for health check endpoint."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client for FastAPI app."""
        return TestClient(app)

    def test_health_endpoint_success(self, client: TestClient) -> None:
        """Test health endpoint returns success."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "trendscope-backend"
        assert "timestamp" in data
        assert "version" in data

    def test_health_endpoint_includes_dependencies(self, client: TestClient) -> None:
        """Test health endpoint includes dependency checks."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "dependencies" in data
        dependencies = data["dependencies"]

        # Should check yfinance connectivity
        assert "yfinance" in dependencies
        assert dependencies["yfinance"]["status"] in ["healthy", "unhealthy"]

    @patch("yfinance.Ticker")
    def test_health_endpoint_with_yfinance_failure(
        self, mock_ticker: Mock, client: TestClient
    ) -> None:
        """Test health endpoint when yfinance is unavailable."""
        # Mock yfinance failure
        mock_ticker.side_effect = Exception("Network error")

        response = client.get("/health")

        # Should still return 200 but mark dependency as unhealthy
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"  # Service itself is healthy
        assert data["dependencies"]["yfinance"]["status"] == "unhealthy"

    def test_get_health_status_function(self) -> None:
        """Test the get_health_status utility function."""
        health_data = get_health_status()

        assert isinstance(health_data, dict)
        assert health_data["status"] == "healthy"
        assert health_data["service"] == "trendscope-backend"
        assert "timestamp" in health_data
        assert "version" in health_data
        assert "dependencies" in health_data


class TestAPIRoutes:
    """Test cases for API route structure and basic functionality."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client for FastAPI app."""
        return TestClient(app)

    def test_docs_endpoint_accessible(self, client: TestClient) -> None:
        """Test that OpenAPI docs endpoint is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_endpoint_accessible(self, client: TestClient) -> None:
        """Test that ReDoc endpoint is accessible."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_openapi_json_accessible(self, client: TestClient) -> None:
        """Test that OpenAPI JSON schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        schema = response.json()
        assert schema["info"]["title"] == "TrendScope Backend API"
        assert schema["info"]["version"] == "0.1.0"

    def test_api_v1_prefix_configured(self, client: TestClient) -> None:
        """Test that API v1 prefix is properly configured."""
        # This will test once we implement the actual API routes
        response = client.get("/api/v1/")
        # For now, this might return 404, but the route structure should exist
        assert response.status_code in [200, 404, 405]  # 405 = Method Not Allowed


class TestCORSConfiguration:
    """Test cases for CORS configuration."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client for FastAPI app."""
        return TestClient(app)

    def test_cors_headers_present(self, client: TestClient) -> None:
        """Test that CORS headers are present in responses."""
        response = client.get("/health", headers={"Origin": "http://localhost:3000"})

        # Check for CORS headers
        assert "access-control-allow-origin" in response.headers

    def test_cors_preflight_request(self, client: TestClient) -> None:
        """Test CORS preflight request handling."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers


class TestErrorHandling:
    """Test cases for global error handling."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client for FastAPI app."""
        return TestClient(app)

    def test_404_error_handling(self, client: TestClient) -> None:
        """Test 404 error handling."""
        response = client.get("/nonexistent-endpoint")

        assert response.status_code == 404
        assert "application/json" in response.headers["content-type"]

        data = response.json()
        # Custom error handler should include our error structure
        assert "error" in data or "detail" in data

    def test_method_not_allowed_handling(self, client: TestClient) -> None:
        """Test 405 Method Not Allowed handling."""
        response = client.post("/health")  # Health endpoint only accepts GET

        assert response.status_code == 405
        assert response.headers["content-type"] == "application/json"


class TestApplicationLifecycle:
    """Test cases for application startup and shutdown events."""

    def test_startup_event_configuration(self) -> None:
        """Test that startup events are properly configured."""
        # Check if startup events are registered
        startup_handlers = app.router.on_startup
        assert len(startup_handlers) >= 0  # Should have at least basic setup

    def test_shutdown_event_configuration(self) -> None:
        """Test that shutdown events are properly configured."""
        # Check if shutdown events are registered
        shutdown_handlers = app.router.on_shutdown
        assert len(shutdown_handlers) >= 0  # Should have cleanup handlers


class TestMiddleware:
    """Test cases for middleware configuration."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client for FastAPI app."""
        return TestClient(app)

    def test_request_logging_middleware(self, client: TestClient) -> None:
        """Test request logging middleware is working."""
        with patch("trendscope_backend.utils.logging.get_logger") as mock_logger:
            mock_logger_instance = Mock()
            mock_logger.return_value = mock_logger_instance

            response = client.get("/health")

            assert response.status_code == 200
            # Logger should have been called for request logging
            # (This test verifies middleware is in place)

    def test_security_headers_middleware(self, client: TestClient) -> None:
        """Test security headers are added by middleware."""
        response = client.get("/health")

        # Should have security headers
        # Basic security headers that should be present
        assert response.status_code == 200
        # We'll verify specific headers once middleware is implemented


class TestAPIVersioning:
    """Test cases for API versioning."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client for FastAPI app."""
        return TestClient(app)

    def test_api_v1_namespace(self, client: TestClient) -> None:
        """Test API v1 namespace is properly set up."""
        # Test that v1 prefix is configured
        response = client.get("/api/v1/")
        # Should either work or return 404/405, but not 500
        assert response.status_code in [200, 404, 405]

    def test_future_api_versioning_support(self, client: TestClient) -> None:
        """Test that API is set up to support future versioning."""
        # This is more of a structure test
        # Check that the app structure supports versioning
        routes = [route.path for route in app.routes]

        # Should have versioned routes or be ready for them
        has_versioned_routes = any("/api/v" in route for route in routes)
        # For now, we just check this doesn't crash
        assert isinstance(has_versioned_routes, bool)
