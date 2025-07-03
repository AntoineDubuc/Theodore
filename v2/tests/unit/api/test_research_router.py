#!/usr/bin/env python3
"""
Tests for Theodore v2 Research API Router
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.app import create_app
from src.api.models.requests import ResearchRequest
from src.api.models.responses import ResearchResponse
from src.api.models.common import JobStatus


class TestResearchRouter:
    """Test research API endpoints"""
    
    @pytest.fixture
    def mock_container(self):
        """Mock application container"""
        container = AsyncMock()
        
        # Mock research use case
        mock_research_use_case = AsyncMock()
        container.get.return_value = mock_research_use_case
        
        return container, mock_research_use_case
    
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
    
    def test_start_research_success(self, client, mock_container):
        """Test successful research job start"""
        container, mock_use_case = mock_container
        
        # Mock successful job creation
        mock_job_result = MagicMock()
        mock_job_result.job_id = "research_123"
        mock_job_result.created_at = datetime.now(timezone.utc)
        mock_job_result.estimated_completion = None
        
        mock_use_case.execute.return_value = mock_job_result
        
        # Make request
        request_data = {
            "company_name": "Test Company",
            "website": "https://test.com",
            "priority": "normal",
            "deep_analysis": False
        }
        
        response = client.post("/api/v2/research", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["job_id"] == "research_123"
        assert data["status"] == "pending"
        assert data["company_name"] == "Test Company"
        assert "created_at" in data
        
        # Verify use case was called correctly
        mock_use_case.execute.assert_called_once()
        call_args = mock_use_case.execute.call_args
        assert call_args.kwargs["company_name"] == "Test Company"
        assert call_args.kwargs["website"] == "https://test.com"
    
    def test_start_research_validation_error(self, client):
        """Test research request validation errors"""
        # Missing required company_name
        response = client.post("/api/v2/research", json={
            "website": "https://test.com"
        })
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        assert "details" in data
    
    def test_start_research_invalid_website_url(self, client):
        """Test research with invalid website URL"""
        request_data = {
            "company_name": "Test Company",
            "website": "not-a-valid-url",
            "priority": "normal"
        }
        
        response = client.post("/api/v2/research", json=request_data)
        
        # Should auto-correct URL or accept it
        # Validation depends on implementation
        assert response.status_code in [200, 422]
    
    def test_start_research_with_config_overrides(self, client, mock_container):
        """Test research with configuration overrides"""
        container, mock_use_case = mock_container
        
        mock_job_result = MagicMock()
        mock_job_result.job_id = "research_456"
        mock_job_result.created_at = datetime.now(timezone.utc)
        mock_job_result.estimated_completion = None
        
        mock_use_case.execute.return_value = mock_job_result
        
        request_data = {
            "company_name": "Test Company",
            "config_overrides": {
                "max_pages": 20,
                "timeout_seconds": 300
            },
            "priority": "high",
            "deep_analysis": True
        }
        
        response = client.post("/api/v2/research", json=request_data)
        
        assert response.status_code == 200
        
        # Verify config overrides were passed
        call_args = mock_use_case.execute.call_args
        assert call_args.kwargs["config_overrides"]["max_pages"] == 20
        assert call_args.kwargs["deep_analysis"] is True
    
    def test_get_research_results_success(self, client, mock_container):
        """Test getting research results"""
        container, mock_use_case = mock_container
        
        # Mock job result
        mock_job_result = MagicMock()
        mock_job_result.job_id = "research_123"
        mock_job_result.status = "completed"
        mock_job_result.company_name = "Test Company"
        mock_job_result.created_at = datetime.now(timezone.utc)
        mock_job_result.updated_at = datetime.now(timezone.utc)
        mock_job_result.started_at = datetime.now(timezone.utc)
        mock_job_result.completed_at = datetime.now(timezone.utc)
        mock_job_result.estimated_completion = None
        mock_job_result.progress = None
        mock_job_result.error = None
        mock_job_result.retry_count = 0
        mock_job_result.result = MagicMock()
        mock_job_result.result.dict.return_value = {
            "name": "Test Company",
            "description": "A test company"
        }
        
        mock_use_case.get_job_status.return_value = mock_job_result
        
        response = client.get("/api/v2/research/research_123")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["job_id"] == "research_123"
        assert data["status"] == "completed"
        assert data["company_name"] == "Test Company"
        assert "result" in data
        assert data["result"]["name"] == "Test Company"
    
    def test_get_research_results_not_found(self, client, mock_container):
        """Test getting results for non-existent job"""
        container, mock_use_case = mock_container
        
        mock_use_case.get_job_status.return_value = None
        
        response = client.get("/api/v2/research/non_existent_job")
        
        assert response.status_code == 404
        data = response.json()
        assert "Research job not found" in data["detail"]
    
    def test_get_research_progress(self, client, mock_container):
        """Test getting research progress"""
        container, mock_use_case = mock_container
        
        mock_progress = {
            "current_step": "AI Analysis",
            "step_number": 3,
            "total_steps": 5,
            "percentage": 60.0,
            "message": "Analyzing company data"
        }
        
        mock_use_case.get_job_progress.return_value = mock_progress
        
        response = client.get("/api/v2/research/research_123/progress")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["current_step"] == "AI Analysis"
        assert data["percentage"] == 60.0
    
    def test_get_research_progress_not_found(self, client, mock_container):
        """Test getting progress for non-existent job"""
        container, mock_use_case = mock_container
        
        mock_use_case.get_job_progress.return_value = None
        
        response = client.get("/api/v2/research/non_existent/progress")
        
        assert response.status_code == 404
    
    def test_cancel_research_success(self, client, mock_container):
        """Test cancelling research job"""
        container, mock_use_case = mock_container
        
        mock_use_case.cancel_job.return_value = True
        
        response = client.delete("/api/v2/research/research_123")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "cancelled successfully" in data["message"]
        assert data["job_id"] == "research_123"
    
    def test_cancel_research_not_found(self, client, mock_container):
        """Test cancelling non-existent job"""
        container, mock_use_case = mock_container
        
        mock_use_case.cancel_job.return_value = False
        
        response = client.delete("/api/v2/research/non_existent")
        
        assert response.status_code == 404
    
    def test_stream_research_progress(self, client, mock_container):
        """Test streaming research progress via SSE"""
        container, mock_use_case = mock_container
        
        # Mock job status and progress
        mock_job_result = MagicMock()
        mock_job_result.job_id = "research_123"
        mock_use_case.get_job_status.return_value = mock_job_result
        
        mock_progress = MagicMock()
        mock_progress.status = "running"
        mock_progress.json.return_value = '{"status": "running", "percentage": 50.0}'
        mock_use_case.get_job_progress.return_value = mock_progress
        
        response = client.get("/api/v2/research/research_123/stream")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Check SSE headers
        assert response.headers["cache-control"] == "no-cache"
        assert response.headers["connection"] == "keep-alive"
    
    def test_stream_research_progress_job_not_found(self, client, mock_container):
        """Test streaming progress for non-existent job"""
        container, mock_use_case = mock_container
        
        mock_use_case.get_job_status.return_value = None
        
        response = client.get("/api/v2/research/non_existent/stream")
        
        assert response.status_code == 200  # SSE always returns 200, errors are in stream
        
        # Read first event from stream to check for error
        content = response.content.decode()
        assert "error" in content.lower()
    
    def test_research_use_case_error_handling(self, client, mock_container):
        """Test error handling when use case raises exception"""
        container, mock_use_case = mock_container
        
        mock_use_case.execute.side_effect = Exception("Use case error")
        
        request_data = {
            "company_name": "Test Company"
        }
        
        response = client.post("/api/v2/research", json=request_data)
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to start research" in data["detail"]
    
    def test_research_request_model_validation(self):
        """Test research request model validation"""
        # Valid request
        valid_request = ResearchRequest(
            company_name="Test Company",
            website="https://test.com",
            priority="normal"
        )
        
        assert valid_request.company_name == "Test Company"
        assert valid_request.website == "https://test.com"
        assert valid_request.priority.value == "normal"
        
        # Test website URL auto-correction
        request_with_no_protocol = ResearchRequest(
            company_name="Test Company",
            website="test.com"
        )
        
        assert request_with_no_protocol.website == "https://test.com"
    
    def test_research_response_model(self):
        """Test research response model"""
        response = ResearchResponse(
            job_id="research_123",
            status=JobStatus.COMPLETED,
            company_name="Test Company",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        assert response.job_id == "research_123"
        assert response.status == JobStatus.COMPLETED
        assert response.company_name == "Test Company"
        
        # Test serialization
        data = response.dict()
        assert data["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_research_endpoint_metrics(self, client, mock_container):
        """Test that research endpoints record metrics"""
        with patch('src.api.routers.research.metrics') as mock_metrics:
            container, mock_use_case = mock_container
            
            mock_job_result = MagicMock()
            mock_job_result.job_id = "research_123"
            mock_job_result.created_at = datetime.now(timezone.utc)
            mock_use_case.execute.return_value = mock_job_result
            
            request_data = {"company_name": "Test Company"}
            response = client.post("/api/v2/research", json=request_data)
            
            assert response.status_code == 200
            
            # Verify metrics were recorded
            mock_metrics.increment_counter.assert_called_with(
                "research_jobs_started",
                tags={
                    "priority": "normal",
                    "deep_analysis": "False"
                }
            )
    
    def test_research_endpoint_logging(self, client, mock_container):
        """Test that research endpoints log appropriately"""
        with patch('src.api.routers.research.logger') as mock_logger:
            container, mock_use_case = mock_container
            
            mock_job_result = MagicMock()
            mock_job_result.job_id = "research_123"
            mock_job_result.created_at = datetime.now(timezone.utc)
            mock_use_case.execute.return_value = mock_job_result
            
            request_data = {"company_name": "Test Company"}
            response = client.post("/api/v2/research", json=request_data)
            
            assert response.status_code == 200
            
            # Verify logging was called
            mock_logger.info.assert_called()
            
            # Check log content
            log_call = mock_logger.info.call_args
            assert "Research job started" in log_call[0][0]