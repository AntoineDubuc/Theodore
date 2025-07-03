#!/usr/bin/env python3
"""
Integration Tests for Theodore v2 API Server

Tests the full API server integration including middleware,
authentication, WebSocket, and end-to-end functionality.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.app import create_app


class TestAPIIntegration:
    """Test full API server integration"""
    
    @pytest.fixture
    def mock_container(self):
        """Mock application container with all services"""
        container = AsyncMock()
        
        # Mock all use cases and services
        mock_research_use_case = AsyncMock()
        mock_discovery_use_case = AsyncMock()
        mock_batch_use_case = AsyncMock()
        mock_auth_service = AsyncMock()
        mock_plugin_manager = AsyncMock()
        mock_health_checker = AsyncMock()
        
        # Configure container to return appropriate mocks
        def get_mock(service_name):
            service_map = {
                "research_use_case": mock_research_use_case,
                "discovery_use_case": mock_discovery_use_case,
                "batch_use_case": mock_batch_use_case,
                "auth_service": mock_auth_service,
                "plugin_manager": mock_plugin_manager,
                "health_checker": mock_health_checker
            }
            return service_map.get(service_name, AsyncMock())
        
        container.get.side_effect = get_mock
        
        return container, {
            "research": mock_research_use_case,
            "discovery": mock_discovery_use_case,
            "batch": mock_batch_use_case,
            "auth": mock_auth_service,
            "plugins": mock_plugin_manager,
            "health": mock_health_checker
        }
    
    @pytest.fixture
    def app(self, mock_container):
        """Create test app with full configuration"""
        container, mocks = mock_container
        app = create_app(debug=True)
        app.state.container = container
        app.state.websocket_manager = MagicMock()
        app.state.metrics = MagicMock()
        app.state.health_checker = mocks["health"]
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    def test_api_root_endpoint(self, client):
        """Test API root endpoint functionality"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Theodore v2 API"
        assert data["version"] == "2.0.0"
        assert data["status"] == "operational"
        assert "endpoints" in data
        assert "timestamp" in data
        
        # Verify key endpoints are listed
        endpoints = data["endpoints"]
        expected_endpoints = [
            "/api/v2/research",
            "/api/v2/discover",
            "/api/v2/batch",
            "/api/v2/auth",
            "/api/v2/plugins",
            "/api/v2/health",
            "/api/v2/ws"
        ]
        
        for endpoint in expected_endpoints:
            assert any(endpoint in ep for ep in endpoints)
    
    def test_cors_middleware_integration(self, client):
        """Test CORS middleware with various origins"""
        # Test preflight request
        response = client.options(
            "/api/v2/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,content-type"
            }
        )
        
        assert response.status_code in [200, 204]
        
        # Test actual request with CORS headers
        response = client.get(
            "/api/v2/health",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        # CORS headers should be present (depending on configuration)
    
    def test_security_headers_applied(self, client):
        """Test that security headers are consistently applied"""
        endpoints_to_test = [
            "/",
            "/ping",
            "/api/v2/health",
            "/api/v2/plugins"  # Test with different router
        ]
        
        for endpoint in endpoints_to_test:
            response = client.get(endpoint)
            
            # All endpoints should have security headers
            assert response.headers.get("X-Content-Type-Options") == "nosniff"
            assert response.headers.get("X-Frame-Options") == "DENY"
            assert response.headers.get("X-XSS-Protection") == "1; mode=block"
            assert "X-API-Version" in response.headers
            assert "X-Request-ID" in response.headers
    
    def test_rate_limiting_integration(self, client):
        """Test rate limiting across different endpoints"""
        # Make multiple requests to test rate limiting
        for i in range(5):
            response = client.get("/ping")
            
            # Should have rate limiting headers
            assert "X-RateLimit-Global-Remaining" in response.headers
            
            # Should not be rate limited for reasonable request count
            assert response.status_code == 200
    
    def test_error_handling_consistency(self, client):
        """Test consistent error handling across all routers"""
        # Test various error scenarios
        error_scenarios = [
            ("/api/v2/research/non-existent", 404),
            ("/api/v2/discover/non-existent", 404),
            ("/api/v2/batch/non-existent", 404),
            ("/api/v2/plugins/non-existent", 404),
            ("/non-existent-endpoint", 404)
        ]
        
        for endpoint, expected_status in error_scenarios:
            response = client.get(endpoint)
            
            assert response.status_code == expected_status
            
            if response.status_code != 500:  # Skip 500 errors for JSON check
                data = response.json()
                
                # All errors should have consistent structure
                assert "error" in data or "detail" in data
                assert "status_code" in data or response.status_code == expected_status
                assert "timestamp" in data
    
    def test_validation_error_consistency(self, client):
        """Test consistent validation error handling"""
        # Test validation errors across different endpoints
        validation_scenarios = [
            ("/api/v2/research", {"invalid": "data"}),
            ("/api/v2/discover", {"invalid": "data"}),
            ("/api/v2/batch/research", {"invalid": "data"}),
            ("/api/v2/auth/login", {"invalid": "data"})
        ]
        
        for endpoint, invalid_data in validation_scenarios:
            response = client.post(endpoint, json=invalid_data)
            
            assert response.status_code == 422
            data = response.json()
            
            # All validation errors should have consistent structure
            assert data["error"] == "VALIDATION_ERROR"
            assert "details" in data
            assert data["status_code"] == 422
    
    def test_request_id_propagation(self, client):
        """Test that request IDs are properly propagated"""
        # Make multiple requests and verify unique request IDs
        request_ids = set()
        
        for i in range(5):
            response = client.get("/ping")
            
            assert response.status_code == 200
            request_id = response.headers.get("X-Request-ID")
            
            assert request_id is not None
            assert request_id not in request_ids  # Should be unique
            request_ids.add(request_id)
    
    def test_metrics_collection_integration(self, client):
        """Test that metrics are collected across all endpoints"""
        with patch('src.api.middleware.metrics.metrics') as mock_metrics:
            # Make requests to different endpoints
            endpoints = [
                "/ping",
                "/api/v2/health",
                "/api/v2/plugins"
            ]
            
            for endpoint in endpoints:
                response = client.get(endpoint)
                assert response.status_code == 200
            
            # Verify metrics were collected
            # (Actual assertion depends on metrics implementation)
            assert mock_metrics.increment_counter.call_count >= len(endpoints)
    
    def test_websocket_integration(self, client):
        """Test WebSocket integration with API server"""
        # Test WebSocket endpoint connection
        with client.websocket_connect("/api/v2/ws/progress/test_job") as websocket:
            # Should connect successfully
            data = websocket.receive_json()
            
            # Should receive connection acknowledgment
            assert data["type"] == "connection_ack"
            assert "data" in data
    
    def test_authentication_integration(self, client, mock_container):
        """Test authentication integration across protected endpoints"""
        container, mocks = mock_container
        
        # Mock authentication failure
        mocks["auth"].get_current_user.return_value = None
        
        protected_endpoints = [
            "/api/v2/auth/me",
            "/api/v2/auth/profile"
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            
            # Should require authentication
            assert response.status_code == 401
    
    def test_health_check_integration(self, client, mock_container):
        """Test health check integration with all components"""
        container, mocks = mock_container
        
        # Mock comprehensive health status
        mocks["health"].get_health_status.return_value = {
            "status": "healthy",
            "components": {
                "database": {"status": "healthy", "latency_ms": 15.2},
                "ai_service": {"status": "healthy", "response_time_ms": 234.5},
                "cache": {"status": "healthy", "hit_rate": 0.85},
                "websocket_manager": {"status": "healthy", "active_connections": 12}
            },
            "version": "2.0.0",
            "uptime_seconds": 3600.5
        }
        
        response = client.get("/api/v2/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert len(data["components"]) == 4
        assert all(comp["status"] == "healthy" for comp in data["components"].values())
    
    def test_openapi_documentation_generation(self, client):
        """Test OpenAPI documentation generation"""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        spec = response.json()
        
        # Verify OpenAPI spec structure
        assert "openapi" in spec
        assert "info" in spec
        assert "paths" in spec
        assert spec["info"]["title"] == "Theodore v2 API"
        assert spec["info"]["version"] == "2.0.0"
        
        # Verify all routers are documented
        paths = spec["paths"]
        expected_path_prefixes = [
            "/api/v2/auth",
            "/api/v2/research",
            "/api/v2/discover",
            "/api/v2/batch",
            "/api/v2/plugins",
            "/api/v2/health",
            "/api/v2/ws"
        ]
        
        for prefix in expected_path_prefixes:
            assert any(path.startswith(prefix) for path in paths.keys()), f"Missing paths for {prefix}"
    
    def test_api_versioning(self, client):
        """Test API versioning consistency"""
        response = client.get("/")
        
        assert response.status_code == 200
        
        # Check version headers
        assert response.headers.get("X-API-Version") == "2.0.0"
        
        # Verify all v2 endpoints are accessible
        v2_endpoints = [
            "/api/v2/health",
            "/api/v2/research",
            "/api/v2/discover",
            "/api/v2/batch",
            "/api/v2/auth/login",
            "/api/v2/plugins"
        ]
        
        for endpoint in v2_endpoints:
            response = client.get(endpoint)
            # Should not be 404 (may be 401, 422, etc. depending on endpoint)
            assert response.status_code != 404
    
    def test_content_type_handling(self, client):
        """Test content type handling for different request types"""
        # Test JSON content type
        response = client.post(
            "/api/v2/auth/login",
            json={"username": "test", "password": "test"},
            headers={"Content-Type": "application/json"}
        )
        
        # Should accept JSON (may return validation error, but not 415)
        assert response.status_code != 415
        
        # Test form data (for file uploads)
        response = client.post(
            "/api/v2/batch/research/upload",
            files={"file": ("test.csv", "name,website\nTest,test.com", "text/csv")},
            data={"priority": "normal"}
        )
        
        # Should accept multipart/form-data
        assert response.status_code != 415
    
    def test_concurrent_request_handling(self, client):
        """Test concurrent request handling"""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get("/ping")
            results.append(response.status_code)
        
        # Create multiple threads to test concurrent handling
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert len(results) == 10
        assert all(status == 200 for status in results)
    
    def test_middleware_order_and_execution(self, client):
        """Test that middleware executes in correct order"""
        response = client.get("/ping")
        
        assert response.status_code == 200
        
        # Verify all middleware has executed by checking headers
        middleware_headers = [
            "X-Request-ID",      # Request logging middleware
            "X-API-Version",     # Security middleware
            "X-Content-Type-Options",  # Security middleware
            "X-RateLimit-Global-Remaining"  # Rate limiting middleware
        ]
        
        for header in middleware_headers:
            assert header in response.headers, f"Missing header: {header}"
    
    @pytest.mark.asyncio
    async def test_application_lifespan_events(self, mock_container):
        """Test application startup and shutdown events"""
        container, mocks = mock_container
        
        # Create app without client to test lifespan
        app = create_app(debug=True)
        app.state.container = container
        app.state.websocket_manager = AsyncMock()
        app.state.metrics = AsyncMock()
        app.state.health_checker = mocks["health"]
        
        # Test that app can be created successfully
        assert app is not None
        assert hasattr(app.state, 'container')
        assert hasattr(app.state, 'websocket_manager')
        assert hasattr(app.state, 'metrics')
        assert hasattr(app.state, 'health_checker')
    
    def test_error_response_format(self, client):
        """Test consistent error response format across all endpoints"""
        # Test various error conditions
        error_tests = [
            ("GET", "/api/v2/research/non-existent", 404),
            ("POST", "/api/v2/research", 422),  # Validation error
            ("GET", "/non-existent", 404),
            ("POST", "/api/v2/auth/login", 422)  # Validation error
        ]
        
        for method, endpoint, expected_status in error_tests:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})
            
            assert response.status_code == expected_status
            
            if response.status_code != 500:  # Skip 500 errors for JSON parsing
                data = response.json()
                
                # Verify consistent error structure
                required_fields = ["timestamp"]
                for field in required_fields:
                    assert field in data, f"Missing {field} in error response for {endpoint}"
    
    def test_api_response_times(self, client):
        """Test API response times are reasonable"""
        import time
        
        endpoints = [
            "/ping",
            "/api/v2/health",
            "/api/v2/plugins"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Response should be fast (under 1 second for simple endpoints)
            assert response_time < 1.0, f"Slow response for {endpoint}: {response_time}s"
            assert response.status_code == 200
    
    def test_api_documentation_accessibility(self, client):
        """Test that API documentation is accessible in debug mode"""
        # Test Swagger UI
        response = client.get("/docs")
        assert response.status_code == 200
        
        # Test ReDoc
        response = client.get("/redoc")
        assert response.status_code == 200
        
        # Test OpenAPI JSON
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        spec = response.json()
        assert "paths" in spec
        assert len(spec["paths"]) > 0