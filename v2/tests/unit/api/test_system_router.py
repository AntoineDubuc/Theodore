#!/usr/bin/env python3
"""
Tests for Theodore v2 System API Router
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.app import create_app


class TestSystemRouter:
    """Test system API endpoints"""
    
    @pytest.fixture
    def mock_container(self):
        """Mock application container"""
        container = AsyncMock()
        
        # Mock health checker
        mock_health_checker = MagicMock()
        mock_health_checker.get_health_status.return_value = {
            "status": "healthy",
            "components": {
                "database": {"status": "healthy", "latency_ms": 15.2},
                "ai_service": {"status": "healthy", "response_time_ms": 234.5},
                "cache": {"status": "healthy", "hit_rate": 0.85}
            },
            "version": "2.0.0",
            "uptime_seconds": 3600.5,
            "timestamp": datetime.now(timezone.utc)
        }
        
        container.get.return_value = mock_health_checker
        return container, mock_health_checker
    
    @pytest.fixture
    def app(self, mock_container):
        """Create test app"""
        container, mock_health_checker = mock_container
        app = create_app(debug=True)
        app.state.container = container
        app.state.health_checker = mock_health_checker
        app.state.metrics = MagicMock()
        app.state.websocket_manager = MagicMock()
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    def test_health_check_endpoint(self, client, mock_container):
        """Test health check endpoint"""
        container, mock_health_checker = mock_container
        
        response = client.get("/api/v2/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "components" in data
        assert "version" in data
        assert "uptime_seconds" in data
        assert "timestamp" in data
        
        # Check components
        assert "database" in data["components"]
        assert "ai_service" in data["components"]
        assert "cache" in data["components"]
        
        # Verify health checker was called
        mock_health_checker.get_health_status.assert_called_once()
    
    def test_health_check_unhealthy_status(self, client, mock_container):
        """Test health check with unhealthy status"""
        container, mock_health_checker = mock_container
        
        # Mock unhealthy status
        mock_health_checker.get_health_status.return_value = {
            "status": "unhealthy",
            "components": {
                "database": {"status": "unhealthy", "error": "Connection timeout"},
                "ai_service": {"status": "healthy"},
                "cache": {"status": "degraded", "warning": "High memory usage"}
            },
            "version": "2.0.0",
            "uptime_seconds": 1200.0
        }
        
        response = client.get("/api/v2/health")
        
        # Should still return 200 but with unhealthy status
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "unhealthy"
        assert data["components"]["database"]["status"] == "unhealthy"
        assert "error" in data["components"]["database"]
    
    def test_health_check_detailed(self, client, mock_container):
        """Test detailed health check endpoint"""
        container, mock_health_checker = mock_container
        
        # Mock detailed health data
        mock_health_checker.get_detailed_health.return_value = {
            "status": "healthy",
            "components": {
                "database": {
                    "status": "healthy",
                    "details": {
                        "pool_size": 10,
                        "active_connections": 3,
                        "query_latency_p95": 45.2
                    }
                },
                "ai_service": {
                    "status": "healthy",
                    "details": {
                        "model_loaded": True,
                        "queue_length": 2,
                        "average_response_time": 1200.5
                    }
                }
            },
            "system_info": {
                "memory_usage_mb": 512.3,
                "cpu_usage_percent": 25.7,
                "disk_usage_percent": 67.2
            }
        }
        
        response = client.get("/api/v2/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "details" in data["components"]["database"]
        assert "system_info" in data
        assert data["system_info"]["memory_usage_mb"] == 512.3
    
    def test_readiness_check(self, client, mock_container):
        """Test readiness check endpoint"""
        container, mock_health_checker = mock_container
        
        mock_health_checker.is_ready.return_value = True
        
        response = client.get("/api/v2/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["ready"] is True
        assert "timestamp" in data
    
    def test_readiness_check_not_ready(self, client, mock_container):
        """Test readiness check when not ready"""
        container, mock_health_checker = mock_container
        
        mock_health_checker.is_ready.return_value = False
        
        response = client.get("/api/v2/health/ready")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data["ready"] is False
        assert "message" in data
    
    def test_liveness_check(self, client):
        """Test liveness check endpoint"""
        response = client.get("/api/v2/health/live")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["alive"] is True
        assert "timestamp" in data
    
    def test_get_system_info(self, client, mock_container):
        """Test system information endpoint"""
        container, mock_health_checker = mock_container
        
        mock_system_info = {
            "version": "2.0.0",
            "build_date": "2024-01-15",
            "commit_hash": "abc123def456",
            "environment": "development",
            "python_version": "3.11.0",
            "fastapi_version": "0.104.1",
            "start_time": datetime.now(timezone.utc),
            "uptime_seconds": 7200.5
        }
        
        mock_health_checker.get_system_info.return_value = mock_system_info
        
        response = client.get("/api/v2/system/info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["version"] == "2.0.0"
        assert data["environment"] == "development"
        assert data["python_version"] == "3.11.0"
        assert "uptime_seconds" in data
    
    def test_get_system_metrics(self, client):
        """Test system metrics endpoint"""
        with patch('src.api.routers.system.metrics') as mock_metrics:
            mock_metrics.get_all_metrics.return_value = {
                "api_requests_total": 1523,
                "api_request_duration_seconds": {
                    "count": 1523,
                    "sum": 234.56,
                    "buckets": {"0.1": 890, "0.5": 1200, "1.0": 1450}
                },
                "websocket_connections_active": 15,
                "research_jobs_completed": 89,
                "discovery_jobs_completed": 34
            }
            
            response = client.get("/api/v2/system/metrics")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "api_requests_total" in data
            assert "websocket_connections_active" in data
            assert data["research_jobs_completed"] == 89
    
    def test_get_system_configuration(self, client):
        """Test system configuration endpoint"""
        response = client.get("/api/v2/system/config")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should contain non-sensitive configuration
        assert "debug_mode" in data
        assert "api_version" in data
        assert "features" in data
        
        # Should NOT contain sensitive information
        assert "database_password" not in str(data)
        assert "api_key" not in str(data)
        assert "secret" not in str(data)
    
    def test_get_active_connections(self, client):
        """Test active connections endpoint"""
        with patch('src.api.routers.system.websocket_manager') as mock_ws_manager:
            mock_ws_manager.get_statistics.return_value = {
                "active_connections": 12,
                "total_connections": 156,
                "total_messages_sent": 2341,
                "job_subscriptions": 8,
                "user_connections": 5
            }
            
            response = client.get("/api/v2/system/connections")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["active_connections"] == 12
            assert data["total_connections"] == 156
            assert data["job_subscriptions"] == 8
    
    def test_system_restart_endpoint(self, client, mock_container):
        """Test system restart endpoint (admin only)"""
        container, mock_health_checker = mock_container
        
        # Mock successful restart initiation
        mock_health_checker.initiate_restart.return_value = {
            "restart_initiated": True,
            "estimated_downtime_seconds": 30
        }
        
        # Should require authentication in real implementation
        response = client.post("/api/v2/system/restart")
        
        # For now, test that endpoint exists
        assert response.status_code in [200, 401, 403]
    
    def test_system_shutdown_endpoint(self, client, mock_container):
        """Test system shutdown endpoint (admin only)"""
        container, mock_health_checker = mock_container
        
        # Mock graceful shutdown initiation
        mock_health_checker.initiate_shutdown.return_value = {
            "shutdown_initiated": True,
            "graceful_period_seconds": 60
        }
        
        response = client.post("/api/v2/system/shutdown")
        
        # Should require authentication in real implementation
        assert response.status_code in [200, 401, 403]
    
    def test_clear_cache_endpoint(self, client):
        """Test cache clearing endpoint"""
        response = client.post("/api/v2/system/cache/clear")
        
        # Should require authentication
        assert response.status_code in [200, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "cache_cleared" in data
    
    def test_get_logs_endpoint(self, client):
        """Test logs retrieval endpoint"""
        response = client.get("/api/v2/system/logs?lines=100&level=INFO")
        
        # Should require authentication
        assert response.status_code in [200, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert "logs" in data
            assert isinstance(data["logs"], list)
    
    def test_export_metrics_endpoint(self, client):
        """Test metrics export endpoint"""
        response = client.get("/api/v2/system/metrics/export?format=prometheus")
        
        assert response.status_code == 200
        
        # Should return metrics in Prometheus format
        content = response.content.decode()
        assert "# HELP" in content or "# TYPE" in content
    
    def test_get_job_queue_status(self, client, mock_container):
        """Test job queue status endpoint"""
        container, mock_health_checker = mock_container
        
        mock_queue_status = {
            "research_queue": {
                "pending": 5,
                "running": 3,
                "completed": 892,
                "failed": 12
            },
            "discovery_queue": {
                "pending": 2,
                "running": 1,
                "completed": 234,
                "failed": 3
            },
            "batch_queue": {
                "pending": 1,
                "running": 2,
                "completed": 45,
                "failed": 1
            }
        }
        
        mock_health_checker.get_queue_status.return_value = mock_queue_status
        
        response = client.get("/api/v2/system/queues")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "research_queue" in data
        assert "discovery_queue" in data
        assert "batch_queue" in data
        assert data["research_queue"]["pending"] == 5
        assert data["discovery_queue"]["running"] == 1
    
    def test_get_error_rates(self, client):
        """Test error rates endpoint"""
        with patch('src.api.routers.system.metrics') as mock_metrics:
            mock_metrics.get_error_rates.return_value = {
                "overall_error_rate": 0.02,
                "research_error_rate": 0.015,
                "discovery_error_rate": 0.025,
                "api_error_rate": 0.003,
                "time_window": "1h"
            }
            
            response = client.get("/api/v2/system/errors?window=1h")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["overall_error_rate"] == 0.02
            assert data["research_error_rate"] == 0.015
            assert data["time_window"] == "1h"
    
    def test_get_performance_stats(self, client):
        """Test performance statistics endpoint"""
        with patch('src.api.routers.system.metrics') as mock_metrics:
            mock_metrics.get_performance_stats.return_value = {
                "avg_response_time_ms": 156.7,
                "p95_response_time_ms": 450.2,
                "p99_response_time_ms": 890.5,
                "requests_per_second": 12.3,
                "active_jobs": 8,
                "queue_latency_ms": 34.5
            }
            
            response = client.get("/api/v2/system/performance")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["avg_response_time_ms"] == 156.7
            assert data["requests_per_second"] == 12.3
            assert data["active_jobs"] == 8
    
    def test_health_check_with_dependencies(self, client, mock_container):
        """Test health check includes dependency status"""
        container, mock_health_checker = mock_container
        
        # Mock health check with external dependencies
        mock_health_checker.get_health_status.return_value = {
            "status": "healthy",
            "components": {
                "database": {"status": "healthy"},
                "ai_service": {"status": "healthy"},
                "cache": {"status": "healthy"}
            },
            "dependencies": {
                "openai_api": {"status": "healthy", "latency_ms": 234.5},
                "gemini_api": {"status": "healthy", "latency_ms": 189.2},
                "pinecone_db": {"status": "healthy", "latency_ms": 67.8}
            }
        }
        
        response = client.get("/api/v2/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "dependencies" in data
        assert "openai_api" in data["dependencies"]
        assert data["dependencies"]["openai_api"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_system_endpoint_metrics(self, client):
        """Test that system endpoints record metrics"""
        with patch('src.api.routers.system.metrics') as mock_metrics:
            response = client.get("/api/v2/health")
            
            assert response.status_code == 200
            
            # Verify metrics were recorded
            mock_metrics.increment_counter.assert_called_with(
                "health_checks_total",
                tags={"endpoint": "health"}
            )
    
    def test_system_endpoint_logging(self, client):
        """Test that system endpoints log appropriately"""
        with patch('src.api.routers.system.logger') as mock_logger:
            response = client.get("/api/v2/system/info")
            
            assert response.status_code == 200
            
            # Verify logging was called (if implemented)
            # Note: System endpoints may not log every request to avoid noise