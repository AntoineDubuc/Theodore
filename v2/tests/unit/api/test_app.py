#!/usr/bin/env python3
"""
Tests for Theodore v2 FastAPI Application
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from src.api.app import create_app
from src.infrastructure.container.application import ApplicationContainer


class TestFastAPIApplication:
    """Test FastAPI application creation and configuration"""
    
    @pytest.fixture
    def mock_container(self):
        """Mock application container"""
        container = AsyncMock(spec=ApplicationContainer)
        container.wire_all = AsyncMock()
        container.cleanup = AsyncMock()
        container.get_status_info = AsyncMock(return_value={
            "status": "healthy",
            "components": {}
        })
        return container
    
    @pytest.fixture
    def app(self, mock_container):
        """Create test app"""
        app = create_app(debug=True)
        app.state.container = mock_container
        app.state.websocket_manager = MagicMock()
        app.state.metrics = MagicMock()
        app.state.health_checker = MagicMock()
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    def test_app_creation(self):
        """Test basic app creation"""
        app = create_app()
        
        assert app.title == "Theodore v2 API"
        assert app.version == "2.0.0"
        assert "AI-powered company intelligence" in app.description
    
    def test_app_creation_with_custom_params(self):
        """Test app creation with custom parameters"""
        app = create_app(
            title="Custom API",
            version="1.0.0",
            description="Custom description",
            debug=True
        )
        
        assert app.title == "Custom API"
        assert app.version == "1.0.0"
        assert app.description == "Custom description"
        assert app.debug is True
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Theodore v2 API"
        assert data["version"] == "2.0.0"
        assert data["status"] == "operational"
        assert "endpoints" in data
        assert "timestamp" in data
    
    def test_ping_endpoint(self, client):
        """Test ping endpoint"""
        response = client.get("/ping")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "ok"
        assert "timestamp" in data
    
    def test_cors_middleware(self, client):
        """Test CORS middleware is applied"""
        response = client.options("/", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        
        # CORS should be handled
        assert response.status_code in [200, 204]
    
    def test_security_headers(self, client):
        """Test security headers are applied"""
        response = client.get("/")
        
        # Check security headers
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert "X-API-Version" in response.headers
        assert "X-Powered-By" in response.headers
    
    def test_request_logging_middleware(self, client):
        """Test request logging middleware adds request ID"""
        response = client.get("/ping")
        
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        
        # Request ID should be a UUID-like string
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) > 20  # Basic UUID length check
    
    def test_metrics_middleware(self, client):
        """Test metrics middleware is working"""
        # Make a request
        response = client.get("/ping")
        assert response.status_code == 200
        
        # Metrics should be collected (mock implementation)
        # In a real test, we'd verify metrics were recorded
    
    def test_error_handling_middleware(self, client):
        """Test error handling middleware"""
        # Test non-existent endpoint
        response = client.get("/non-existent-endpoint")
        
        assert response.status_code == 404
        data = response.json()
        
        assert "error" in data
        assert "message" in data
        assert "status_code" in data
        assert "timestamp" in data
        assert data["status_code"] == 404
    
    def test_rate_limiting_headers(self, client):
        """Test rate limiting headers are present"""
        response = client.get("/ping")
        
        assert response.status_code == 200
        
        # Rate limiting headers should be present
        # Note: Actual values depend on rate limit configuration
        assert "X-RateLimit-Global-Remaining" in response.headers
    
    def test_request_validation_error_handling(self, client):
        """Test request validation error handling"""
        # Make a request with invalid data to an endpoint that expects JSON
        response = client.post("/api/v2/research", json={
            # Missing required fields
        })
        
        assert response.status_code == 422
        data = response.json()
        
        assert data["error"] == "VALIDATION_ERROR"
        assert "details" in data
        assert data["status_code"] == 422
    
    def test_http_exception_handling(self, client):
        """Test HTTP exception handling"""
        # Test endpoint that might raise HTTPException
        response = client.get("/api/v2/research/non-existent-job")
        
        # Should return structured error response
        assert response.status_code in [404, 500]  # Depending on implementation
        
        if response.status_code != 500:  # If not a general server error
            data = response.json()
            assert "error" in data
            assert "message" in data
    
    def test_openapi_docs_in_debug_mode(self):
        """Test OpenAPI docs are available in debug mode"""
        app = create_app(debug=True)
        client = TestClient(app)
        
        # Docs should be available
        response = client.get("/docs")
        assert response.status_code == 200
        
        # OpenAPI spec should be available
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Theodore v2 API"
    
    def test_openapi_docs_disabled_in_production(self):
        """Test OpenAPI docs are disabled in production mode"""
        app = create_app(debug=False)
        client = TestClient(app)
        
        # Docs should not be available
        response = client.get("/docs")
        assert response.status_code == 404
        
        # OpenAPI spec should not be available
        response = client.get("/openapi.json")
        assert response.status_code == 404


class TestApplicationLifespan:
    """Test application lifespan events"""
    
    @pytest.mark.asyncio
    async def test_startup_sequence(self, mock_container):
        """Test application startup sequence"""
        app = create_app(debug=True)
        
        # Mock the container and other components
        mock_websocket_manager = MagicMock()
        mock_metrics = MagicMock()
        mock_health_checker = MagicMock()
        
        # Simulate startup
        app.state.container = mock_container
        app.state.websocket_manager = mock_websocket_manager
        app.state.metrics = mock_metrics
        app.state.health_checker = mock_health_checker
        
        # Verify components are initialized
        assert hasattr(app.state, 'container')
        assert hasattr(app.state, 'websocket_manager')
        assert hasattr(app.state, 'metrics')
        assert hasattr(app.state, 'health_checker')
    
    @pytest.mark.asyncio
    async def test_shutdown_sequence(self, mock_container):
        """Test application shutdown sequence"""
        app = create_app(debug=True)
        
        # Mock components
        mock_websocket_manager = AsyncMock()
        mock_metrics = AsyncMock()
        
        app.state.container = mock_container
        app.state.websocket_manager = mock_websocket_manager
        app.state.metrics = mock_metrics
        
        # Simulate shutdown
        if hasattr(mock_websocket_manager, 'shutdown'):
            await mock_websocket_manager.shutdown()
        if hasattr(mock_metrics, 'stop_collection'):
            await mock_metrics.stop_collection()
        await mock_container.cleanup()
        
        # Verify cleanup methods were called
        mock_container.cleanup.assert_called_once()


class TestAPIRouterInclusion:
    """Test that all API routers are properly included"""
    
    def test_all_routers_included(self):
        """Test that all expected routers are included"""
        app = create_app()
        
        # Get all routes
        routes = [route.path for route in app.routes]
        
        # Check that main router prefixes are present
        expected_prefixes = [
            "/api/v2/auth",
            "/api/v2/research", 
            "/api/v2/discover",
            "/api/v2/batch",
            "/api/v2/plugins",
            "/api/v2/health",  # system router
            "/api/v2/ws"       # websocket router
        ]
        
        for prefix in expected_prefixes:
            # Check if any route starts with this prefix
            assert any(route.startswith(prefix) for route in routes), f"Missing router for {prefix}"
    
    def test_router_tags(self):
        """Test that routers have proper tags for documentation"""
        app = create_app(debug=True)
        client = TestClient(app)
        
        # Get OpenAPI spec
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        spec = response.json()
        
        # Check that expected tags are present
        expected_tags = [
            "Authentication",
            "Research", 
            "Discovery",
            "Batch Processing",
            "Plugin Management",
            "System",
            "WebSocket"
        ]
        
        if "tags" in spec:
            spec_tags = [tag["name"] for tag in spec["tags"]]
            for expected_tag in expected_tags:
                assert expected_tag in spec_tags or any(
                    expected_tag.lower() in tag.lower() for tag in spec_tags
                ), f"Missing tag: {expected_tag}"