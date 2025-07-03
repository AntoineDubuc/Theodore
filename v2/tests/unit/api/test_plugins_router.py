#!/usr/bin/env python3
"""
Tests for Theodore v2 Plugin Management API Router
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.app import create_app


class TestPluginsRouter:
    """Test plugin management API endpoints"""
    
    @pytest.fixture
    def mock_container(self):
        """Mock application container"""
        container = AsyncMock()
        
        # Mock plugin manager
        mock_plugin_manager = AsyncMock()
        container.get.return_value = mock_plugin_manager
        
        return container, mock_plugin_manager
    
    @pytest.fixture
    def app(self, mock_container):
        """Create test app"""
        container, _ = mock_container
        app = create_app(debug=True)
        app.state.container = container
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    def test_list_plugins_success(self, client, mock_container):
        """Test successful plugin listing"""
        container, mock_plugin_manager = mock_container
        
        # Mock plugin list
        mock_plugins = [
            {
                "id": "email-integration",
                "name": "Email Integration Plugin",
                "version": "1.0.0",
                "status": "active",
                "description": "Integrates with email services",
                "author": "Theodore Team",
                "capabilities": ["email_sending", "contact_extraction"],
                "dependencies": ["requests>=2.25.0"],
                "installed_at": datetime.now(timezone.utc),
                "last_updated": datetime.now(timezone.utc)
            },
            {
                "id": "custom-scraper",
                "name": "Custom Web Scraper",
                "version": "2.1.0",
                "status": "inactive",
                "description": "Custom scraping capabilities",
                "author": "Community",
                "capabilities": ["web_scraping", "data_extraction"],
                "dependencies": ["beautifulsoup4>=4.9.0"],
                "installed_at": datetime.now(timezone.utc),
                "last_updated": datetime.now(timezone.utc)
            }
        ]
        
        mock_plugin_manager.list_plugins.return_value = mock_plugins
        
        response = client.get("/api/v2/plugins")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["plugins"]) == 2
        assert data["plugins"][0]["id"] == "email-integration"
        assert data["plugins"][0]["status"] == "active"
        assert data["plugins"][1]["id"] == "custom-scraper"
        assert data["plugins"][1]["status"] == "inactive"
    
    def test_list_plugins_with_filters(self, client, mock_container):
        """Test plugin listing with status filter"""
        container, mock_plugin_manager = mock_container
        
        mock_active_plugins = [
            {
                "id": "active-plugin",
                "name": "Active Plugin",
                "status": "active",
                "version": "1.0.0"
            }
        ]
        
        mock_plugin_manager.list_plugins.return_value = mock_active_plugins
        
        response = client.get("/api/v2/plugins?status=active")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["plugins"]) == 1
        assert data["plugins"][0]["status"] == "active"
        
        # Verify filter was applied
        call_args = mock_plugin_manager.list_plugins.call_args
        assert call_args.kwargs.get("status") == "active"
    
    def test_get_plugin_details_success(self, client, mock_container):
        """Test getting plugin details"""
        container, mock_plugin_manager = mock_container
        
        # Mock plugin details
        mock_plugin_details = {
            "id": "email-integration",
            "name": "Email Integration Plugin",
            "version": "1.0.0",
            "status": "active",
            "description": "Comprehensive email integration capabilities",
            "author": "Theodore Team",
            "homepage": "https://theodore.ai/plugins/email",
            "repository": "https://github.com/theodore/email-plugin",
            "license": "MIT",
            "capabilities": ["email_sending", "contact_extraction", "email_validation"],
            "dependencies": [
                {"name": "requests", "version": ">=2.25.0"},
                {"name": "email-validator", "version": ">=1.1.0"}
            ],
            "configuration": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "use_tls": True
            },
            "permissions": ["network", "email"],
            "installed_at": datetime.now(timezone.utc),
            "last_updated": datetime.now(timezone.utc),
            "last_used": datetime.now(timezone.utc),
            "usage_stats": {
                "total_invocations": 156,
                "success_rate": 0.98,
                "avg_execution_time_ms": 234.5
            }
        }
        
        mock_plugin_manager.get_plugin_details.return_value = mock_plugin_details
        
        response = client.get("/api/v2/plugins/email-integration")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == "email-integration"
        assert data["name"] == "Email Integration Plugin"
        assert data["status"] == "active"
        assert len(data["capabilities"]) == 3
        assert "usage_stats" in data
        assert data["usage_stats"]["total_invocations"] == 156
    
    def test_get_plugin_details_not_found(self, client, mock_container):
        """Test getting details for non-existent plugin"""
        container, mock_plugin_manager = mock_container
        
        mock_plugin_manager.get_plugin_details.return_value = None
        
        response = client.get("/api/v2/plugins/non-existent-plugin")
        
        assert response.status_code == 404
        data = response.json()
        assert "Plugin not found" in data["detail"]
    
    def test_install_plugin_success(self, client, mock_container):
        """Test successful plugin installation"""
        container, mock_plugin_manager = mock_container
        
        # Mock successful installation
        mock_install_result = {
            "plugin_id": "new-plugin",
            "status": "installed",
            "version": "1.0.0",
            "installed_at": datetime.now(timezone.utc),
            "dependencies_installed": 3,
            "installation_log": [
                "Downloading plugin package...",
                "Installing dependencies...",
                "Validating plugin...",
                "Plugin installed successfully"
            ]
        }
        
        mock_plugin_manager.install_plugin.return_value = mock_install_result
        
        install_data = {
            "source": "https://plugins.theodore.ai/new-plugin-1.0.0.tar.gz",
            "verify_signature": True,
            "auto_activate": True
        }
        
        response = client.post("/api/v2/plugins/install", json=install_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["plugin_id"] == "new-plugin"
        assert data["status"] == "installed"
        assert data["dependencies_installed"] == 3
        assert len(data["installation_log"]) == 4
    
    def test_install_plugin_from_file(self, client, mock_container):
        """Test plugin installation from uploaded file"""
        container, mock_plugin_manager = mock_container
        
        mock_install_result = {
            "plugin_id": "uploaded-plugin",
            "status": "installed",
            "version": "2.0.0",
            "installed_at": datetime.now(timezone.utc)
        }
        
        mock_plugin_manager.install_plugin_from_file.return_value = mock_install_result
        
        # Create mock plugin file
        plugin_content = b"fake plugin zip content"
        files = {"file": ("plugin.zip", plugin_content, "application/zip")}
        data = {"auto_activate": "true"}
        
        response = client.post("/api/v2/plugins/upload", files=files, data=data)
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["plugin_id"] == "uploaded-plugin"
        assert response_data["status"] == "installed"
    
    def test_install_plugin_validation_error(self, client, mock_container):
        """Test plugin installation with validation errors"""
        container, mock_plugin_manager = mock_container
        
        # Mock validation failure
        mock_plugin_manager.install_plugin.side_effect = ValueError("Invalid plugin package")
        
        install_data = {
            "source": "invalid-url"
        }
        
        response = client.post("/api/v2/plugins/install", json=install_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid plugin package" in data["detail"]
    
    def test_activate_plugin_success(self, client, mock_container):
        """Test successful plugin activation"""
        container, mock_plugin_manager = mock_container
        
        mock_plugin_manager.activate_plugin.return_value = True
        
        response = client.post("/api/v2/plugins/email-integration/activate")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "activated successfully" in data["message"]
        assert data["plugin_id"] == "email-integration"
    
    def test_activate_plugin_not_found(self, client, mock_container):
        """Test activating non-existent plugin"""
        container, mock_plugin_manager = mock_container
        
        mock_plugin_manager.activate_plugin.return_value = False
        
        response = client.post("/api/v2/plugins/non-existent/activate")
        
        assert response.status_code == 404
    
    def test_deactivate_plugin_success(self, client, mock_container):
        """Test successful plugin deactivation"""
        container, mock_plugin_manager = mock_container
        
        mock_plugin_manager.deactivate_plugin.return_value = True
        
        response = client.post("/api/v2/plugins/email-integration/deactivate")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "deactivated successfully" in data["message"]
        assert data["plugin_id"] == "email-integration"
    
    def test_uninstall_plugin_success(self, client, mock_container):
        """Test successful plugin uninstallation"""
        container, mock_plugin_manager = mock_container
        
        mock_uninstall_result = {
            "plugin_id": "email-integration",
            "status": "uninstalled",
            "cleanup_completed": True,
            "files_removed": 23,
            "dependencies_removed": 2
        }
        
        mock_plugin_manager.uninstall_plugin.return_value = mock_uninstall_result
        
        response = client.delete("/api/v2/plugins/email-integration")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["plugin_id"] == "email-integration"
        assert data["status"] == "uninstalled"
        assert data["cleanup_completed"] is True
        assert data["files_removed"] == 23
    
    def test_update_plugin_success(self, client, mock_container):
        """Test successful plugin update"""
        container, mock_plugin_manager = mock_container
        
        mock_update_result = {
            "plugin_id": "email-integration",
            "old_version": "1.0.0",
            "new_version": "1.1.0",
            "status": "updated",
            "updated_at": datetime.now(timezone.utc),
            "changelog": [
                "Fixed email validation bug",
                "Added support for OAuth2",
                "Improved error handling"
            ]
        }
        
        mock_plugin_manager.update_plugin.return_value = mock_update_result
        
        response = client.post("/api/v2/plugins/email-integration/update")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["plugin_id"] == "email-integration"
        assert data["old_version"] == "1.0.0"
        assert data["new_version"] == "1.1.0"
        assert len(data["changelog"]) == 3
    
    def test_get_plugin_configuration(self, client, mock_container):
        """Test getting plugin configuration"""
        container, mock_plugin_manager = mock_container
        
        mock_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "use_tls": True,
            "max_retries": 3,
            "timeout_seconds": 30,
            "default_from_address": "noreply@theodore.ai"
        }
        
        mock_plugin_manager.get_plugin_configuration.return_value = mock_config
        
        response = client.get("/api/v2/plugins/email-integration/config")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["smtp_server"] == "smtp.gmail.com"
        assert data["smtp_port"] == 587
        assert data["use_tls"] is True
    
    def test_update_plugin_configuration(self, client, mock_container):
        """Test updating plugin configuration"""
        container, mock_plugin_manager = mock_container
        
        mock_plugin_manager.update_plugin_configuration.return_value = True
        
        config_data = {
            "smtp_server": "smtp.sendgrid.net",
            "smtp_port": 465,
            "use_tls": True,
            "api_key": "new_api_key_123"
        }
        
        response = client.put("/api/v2/plugins/email-integration/config", json=config_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "Configuration updated successfully" in data["message"]
    
    def test_get_available_plugins(self, client, mock_container):
        """Test getting available plugins from registry"""
        container, mock_plugin_manager = mock_container
        
        mock_available_plugins = [
            {
                "id": "social-media-scraper",
                "name": "Social Media Scraper",
                "version": "1.5.0",
                "description": "Extract data from social media platforms",
                "author": "Community Developer",
                "rating": 4.2,
                "downloads": 1250,
                "last_updated": datetime.now(timezone.utc),
                "tags": ["scraping", "social-media", "data-extraction"],
                "license": "MIT",
                "compatibility": ">=2.0.0"
            },
            {
                "id": "ai-analysis-plugin",
                "name": "Advanced AI Analysis",
                "version": "2.0.0",
                "description": "Enhanced AI-powered company analysis",
                "author": "Theodore Team",
                "rating": 4.8,
                "downloads": 3400,
                "last_updated": datetime.now(timezone.utc),
                "tags": ["ai", "analysis", "machine-learning"],
                "license": "Proprietary",
                "compatibility": ">=2.0.0"
            }
        ]
        
        mock_plugin_manager.get_available_plugins.return_value = mock_available_plugins
        
        response = client.get("/api/v2/plugins/available")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["plugins"]) == 2
        assert data["plugins"][0]["id"] == "social-media-scraper"
        assert data["plugins"][1]["rating"] == 4.8
    
    def test_search_plugins(self, client, mock_container):
        """Test searching available plugins"""
        container, mock_plugin_manager = mock_container
        
        mock_search_results = [
            {
                "id": "scraper-plugin-1",
                "name": "Web Scraper Pro",
                "relevance_score": 0.95,
                "description": "Professional web scraping capabilities"
            }
        ]
        
        mock_plugin_manager.search_plugins.return_value = mock_search_results
        
        response = client.get("/api/v2/plugins/search?query=scraper&category=data-extraction")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["results"]) == 1
        assert data["results"][0]["relevance_score"] == 0.95
        
        # Verify search parameters
        call_args = mock_plugin_manager.search_plugins.call_args
        assert call_args.kwargs["query"] == "scraper"
        assert call_args.kwargs["category"] == "data-extraction"
    
    def test_get_plugin_logs(self, client, mock_container):
        """Test getting plugin execution logs"""
        container, mock_plugin_manager = mock_container
        
        mock_logs = [
            {
                "timestamp": datetime.now(timezone.utc),
                "level": "INFO",
                "message": "Plugin execution started",
                "plugin_id": "email-integration",
                "execution_id": "exec_123"
            },
            {
                "timestamp": datetime.now(timezone.utc),
                "level": "ERROR",
                "message": "SMTP connection failed",
                "plugin_id": "email-integration",
                "execution_id": "exec_123",
                "error_details": "Connection timeout after 30 seconds"
            }
        ]
        
        mock_plugin_manager.get_plugin_logs.return_value = mock_logs
        
        response = client.get("/api/v2/plugins/email-integration/logs?limit=50&level=INFO")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["logs"]) == 2
        assert data["logs"][0]["level"] == "INFO"
        assert data["logs"][1]["level"] == "ERROR"
    
    def test_get_plugin_metrics(self, client, mock_container):
        """Test getting plugin performance metrics"""
        container, mock_plugin_manager = mock_container
        
        mock_metrics = {
            "plugin_id": "email-integration",
            "total_executions": 1523,
            "successful_executions": 1489,
            "failed_executions": 34,
            "success_rate": 0.978,
            "avg_execution_time_ms": 234.5,
            "p95_execution_time_ms": 450.2,
            "p99_execution_time_ms": 890.1,
            "memory_usage_mb": 45.2,
            "cpu_usage_percent": 12.3,
            "last_24h_executions": 89,
            "error_rate_24h": 0.02
        }
        
        mock_plugin_manager.get_plugin_metrics.return_value = mock_metrics
        
        response = client.get("/api/v2/plugins/email-integration/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_executions"] == 1523
        assert data["success_rate"] == 0.978
        assert data["avg_execution_time_ms"] == 234.5
    
    def test_plugin_security_scan(self, client, mock_container):
        """Test plugin security scanning"""
        container, mock_plugin_manager = mock_container
        
        mock_scan_result = {
            "plugin_id": "email-integration",
            "scan_timestamp": datetime.now(timezone.utc),
            "security_score": 8.5,
            "vulnerabilities": [
                {
                    "severity": "medium",
                    "type": "dependency_vulnerability",
                    "description": "Outdated requests library",
                    "recommendation": "Update requests to version >=2.28.0"
                }
            ],
            "permissions_check": {
                "status": "passed",
                "excessive_permissions": []
            },
            "code_analysis": {
                "status": "passed",
                "suspicious_patterns": []
            }
        }
        
        mock_plugin_manager.scan_plugin_security.return_value = mock_scan_result
        
        response = client.post("/api/v2/plugins/email-integration/security-scan")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["security_score"] == 8.5
        assert len(data["vulnerabilities"]) == 1
        assert data["permissions_check"]["status"] == "passed"
    
    @pytest.mark.asyncio
    async def test_plugin_endpoint_metrics(self, client, mock_container):
        """Test that plugin endpoints record metrics"""
        with patch('src.api.routers.plugins.metrics') as mock_metrics:
            container, mock_plugin_manager = mock_container
            
            mock_plugin_manager.list_plugins.return_value = []
            
            response = client.get("/api/v2/plugins")
            
            assert response.status_code == 200
            
            # Verify metrics were recorded
            mock_metrics.increment_counter.assert_called_with(
                "plugin_api_requests_total",
                tags={"endpoint": "list_plugins"}
            )
    
    def test_plugin_endpoint_logging(self, client, mock_container):
        """Test that plugin endpoints log appropriately"""
        with patch('src.api.routers.plugins.logger') as mock_logger:
            container, mock_plugin_manager = mock_container
            
            mock_plugin_manager.activate_plugin.return_value = True
            
            response = client.post("/api/v2/plugins/test-plugin/activate")
            
            assert response.status_code == 200
            
            # Verify logging was called
            mock_logger.info.assert_called()
            
            # Check log content
            log_call = mock_logger.info.call_args
            assert "Plugin activation" in log_call[0][0] or "test-plugin" in log_call[0][0]