#!/usr/bin/env python3
"""
Tests for Theodore v2 Batch Processing API Router
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.app import create_app
from src.api.models.requests import BatchResearchRequest
from src.api.models.responses import BatchJobResponse
from src.api.models.common import JobStatus, JobPriority


class TestBatchRouter:
    """Test batch processing API endpoints"""
    
    @pytest.fixture
    def mock_container(self):
        """Mock application container"""
        container = AsyncMock()
        
        # Mock batch use case
        mock_batch_use_case = AsyncMock()
        container.get.return_value = mock_batch_use_case
        
        return container, mock_batch_use_case
    
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
    
    def test_start_batch_research_success(self, client, mock_container):
        """Test successful batch research job start"""
        container, mock_use_case = mock_container
        
        # Mock successful batch job creation
        mock_batch_result = MagicMock()
        mock_batch_result.batch_id = "batch_123"
        mock_batch_result.total_companies = 5
        mock_batch_result.status = "running"
        mock_batch_result.created_at = datetime.now(timezone.utc)
        mock_batch_result.estimated_completion = None
        
        mock_use_case.execute.return_value = mock_batch_result
        
        # Make request
        request_data = {
            "companies": [
                {"name": "Company A", "website": "https://companya.com"},
                {"name": "Company B", "website": "https://companyb.com"},
                {"name": "Company C"}
            ],
            "priority": "normal",
            "config_overrides": {
                "max_pages": 15,
                "timeout_seconds": 180
            }
        }
        
        response = client.post("/api/v2/batch/research", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["batch_id"] == "batch_123"
        assert data["total_companies"] == 5  # Might include auto-discovered companies
        assert data["status"] == "running"
        assert "created_at" in data
        
        # Verify use case was called correctly
        mock_use_case.execute.assert_called_once()
        call_args = mock_use_case.execute.call_args
        assert len(call_args.kwargs["companies"]) == 3
        assert call_args.kwargs["priority"] == JobPriority.NORMAL
    
    def test_start_batch_research_validation_error(self, client):
        """Test batch research request validation errors"""
        # Empty companies list
        response = client.post("/api/v2/batch/research", json={
            "companies": []
        })
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        assert "details" in data
    
    def test_start_batch_research_with_file_upload(self, client, mock_container):
        """Test batch research with file upload"""
        container, mock_use_case = mock_container
        
        mock_batch_result = MagicMock()
        mock_batch_result.batch_id = "batch_456"
        mock_batch_result.total_companies = 10
        mock_batch_result.status = "queued"
        mock_batch_result.created_at = datetime.now(timezone.utc)
        
        mock_use_case.execute_from_file.return_value = mock_batch_result
        
        # Create a mock CSV file
        csv_content = "name,website\nCompany A,https://a.com\nCompany B,https://b.com"
        
        files = {"file": ("companies.csv", csv_content, "text/csv")}
        data = {"priority": "high"}
        
        response = client.post(
            "/api/v2/batch/research/upload",
            files=files,
            data=data
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["batch_id"] == "batch_456"
        assert response_data["total_companies"] == 10
    
    def test_get_batch_status_success(self, client, mock_container):
        """Test getting batch job status"""
        container, mock_use_case = mock_container
        
        # Mock batch status
        mock_status = MagicMock()
        mock_status.batch_id = "batch_123"
        mock_status.status = "running"
        mock_status.total_companies = 5
        mock_status.completed_companies = 2
        mock_status.failed_companies = 0
        mock_status.progress_percentage = 40.0
        mock_status.created_at = datetime.now(timezone.utc)
        mock_status.started_at = datetime.now(timezone.utc)
        mock_status.estimated_completion = None
        mock_status.current_company = "Company C"
        
        mock_use_case.get_batch_status.return_value = mock_status
        
        response = client.get("/api/v2/batch/batch_123")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["batch_id"] == "batch_123"
        assert data["status"] == "running"
        assert data["total_companies"] == 5
        assert data["completed_companies"] == 2
        assert data["progress_percentage"] == 40.0
        assert data["current_company"] == "Company C"
    
    def test_get_batch_status_not_found(self, client, mock_container):
        """Test getting status for non-existent batch job"""
        container, mock_use_case = mock_container
        
        mock_use_case.get_batch_status.return_value = None
        
        response = client.get("/api/v2/batch/non_existent_batch")
        
        assert response.status_code == 404
        data = response.json()
        assert "Batch job not found" in data["detail"]
    
    def test_get_batch_results_success(self, client, mock_container):
        """Test getting batch job results"""
        container, mock_use_case = mock_container
        
        # Mock batch results
        mock_results = MagicMock()
        mock_results.batch_id = "batch_123"
        mock_results.status = "completed"
        mock_results.results = [
            {
                "company_name": "Company A",
                "status": "completed",
                "result": {"name": "Company A", "industry": "Technology"}
            },
            {
                "company_name": "Company B", 
                "status": "completed",
                "result": {"name": "Company B", "industry": "Finance"}
            }
        ]
        mock_results.total_companies = 2
        mock_results.completed_companies = 2
        mock_results.failed_companies = 0
        mock_results.created_at = datetime.now(timezone.utc)
        mock_results.completed_at = datetime.now(timezone.utc)
        
        mock_use_case.get_batch_results.return_value = mock_results
        
        response = client.get("/api/v2/batch/batch_123/results")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["batch_id"] == "batch_123"
        assert data["status"] == "completed"
        assert len(data["results"]) == 2
        assert data["completed_companies"] == 2
        assert data["failed_companies"] == 0
    
    def test_get_batch_results_with_format(self, client, mock_container):
        """Test getting batch results in specific format"""
        container, mock_use_case = mock_container
        
        mock_results = MagicMock()
        mock_results.batch_id = "batch_123"
        mock_results.results = []
        mock_use_case.get_batch_results.return_value = mock_results
        
        # Test CSV format
        response = client.get("/api/v2/batch/batch_123/results?format=csv")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        
        # Test Excel format
        response = client.get("/api/v2/batch/batch_123/results?format=xlsx")
        
        assert response.status_code == 200
        assert "excel" in response.headers["content-type"] or "spreadsheet" in response.headers["content-type"]
    
    def test_cancel_batch_job_success(self, client, mock_container):
        """Test cancelling batch job"""
        container, mock_use_case = mock_container
        
        mock_use_case.cancel_batch.return_value = True
        
        response = client.delete("/api/v2/batch/batch_123")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "cancelled successfully" in data["message"]
        assert data["batch_id"] == "batch_123"
    
    def test_cancel_batch_job_not_found(self, client, mock_container):
        """Test cancelling non-existent batch job"""
        container, mock_use_case = mock_container
        
        mock_use_case.cancel_batch.return_value = False
        
        response = client.delete("/api/v2/batch/non_existent")
        
        assert response.status_code == 404
    
    def test_pause_batch_job(self, client, mock_container):
        """Test pausing batch job"""
        container, mock_use_case = mock_container
        
        mock_use_case.pause_batch.return_value = True
        
        response = client.post("/api/v2/batch/batch_123/pause")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "paused successfully" in data["message"]
        assert data["batch_id"] == "batch_123"
    
    def test_resume_batch_job(self, client, mock_container):
        """Test resuming batch job"""
        container, mock_use_case = mock_container
        
        mock_use_case.resume_batch.return_value = True
        
        response = client.post("/api/v2/batch/batch_123/resume")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "resumed successfully" in data["message"]
        assert data["batch_id"] == "batch_123"
    
    def test_retry_failed_jobs(self, client, mock_container):
        """Test retrying failed jobs in batch"""
        container, mock_use_case = mock_container
        
        mock_retry_result = MagicMock()
        mock_retry_result.retried_count = 3
        mock_retry_result.new_job_ids = ["job_1", "job_2", "job_3"]
        
        mock_use_case.retry_failed_jobs.return_value = mock_retry_result
        
        response = client.post("/api/v2/batch/batch_123/retry-failed")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["retried_count"] == 3
        assert len(data["new_job_ids"]) == 3
    
    def test_get_active_batches(self, client, mock_container):
        """Test getting list of active batch jobs"""
        container, mock_use_case = mock_container
        
        mock_active_batches = [
            {
                "batch_id": "batch_1",
                "status": "running",
                "total_companies": 10,
                "completed_companies": 5,
                "created_at": datetime.now(timezone.utc)
            },
            {
                "batch_id": "batch_2",
                "status": "queued",
                "total_companies": 20,
                "completed_companies": 0,
                "created_at": datetime.now(timezone.utc)
            }
        ]
        
        mock_use_case.get_active_batches.return_value = mock_active_batches
        
        response = client.get("/api/v2/batch/active")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["batches"]) == 2
        assert data["batches"][0]["batch_id"] == "batch_1"
        assert data["batches"][1]["status"] == "queued"
    
    def test_get_batch_history(self, client, mock_container):
        """Test getting batch job history"""
        container, mock_use_case = mock_container
        
        mock_history = [
            {
                "batch_id": "batch_old",
                "status": "completed",
                "total_companies": 5,
                "completed_companies": 5,
                "created_at": datetime.now(timezone.utc),
                "completed_at": datetime.now(timezone.utc)
            }
        ]
        
        mock_use_case.get_batch_history.return_value = mock_history
        
        response = client.get("/api/v2/batch/history?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["batches"]) == 1
        assert data["batches"][0]["status"] == "completed"
    
    def test_batch_research_request_model_validation(self):
        """Test batch research request model validation"""
        # Valid request
        valid_request = BatchResearchRequest(
            companies=[
                {"name": "Company A", "website": "https://a.com"},
                {"name": "Company B"}
            ],
            priority=JobPriority.NORMAL,
            config_overrides={
                "max_pages": 10
            }
        )
        
        assert len(valid_request.companies) == 2
        assert valid_request.priority == JobPriority.NORMAL
        assert valid_request.config_overrides["max_pages"] == 10
        
        # Test with auto-correction of websites
        request_with_correction = BatchResearchRequest(
            companies=[
                {"name": "Company A", "website": "companya.com"}  # Missing protocol
            ]
        )
        
        # Should auto-correct to https://
        assert request_with_correction.companies[0]["website"] == "https://companya.com"
    
    def test_batch_job_response_model(self):
        """Test batch job response model"""
        response = BatchJobResponse(
            batch_id="batch_123",
            status=JobStatus.RUNNING,
            total_companies=10,
            completed_companies=5,
            failed_companies=1,
            progress_percentage=50.0,
            created_at=datetime.now(timezone.utc)
        )
        
        assert response.batch_id == "batch_123"
        assert response.status == JobStatus.RUNNING
        assert response.total_companies == 10
        assert response.progress_percentage == 50.0
        
        # Test serialization
        data = response.dict()
        assert data["status"] == "running"
        assert data["completed_companies"] == 5
    
    def test_batch_endpoint_error_handling(self, client, mock_container):
        """Test error handling when batch use case raises exception"""
        container, mock_use_case = mock_container
        
        mock_use_case.execute.side_effect = Exception("Batch processing error")
        
        request_data = {
            "companies": [
                {"name": "Company A"}
            ]
        }
        
        response = client.post("/api/v2/batch/research", json=request_data)
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to start batch research" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_batch_endpoint_metrics(self, client, mock_container):
        """Test that batch endpoints record metrics"""
        with patch('src.api.routers.batch.metrics') as mock_metrics:
            container, mock_use_case = mock_container
            
            mock_batch_result = MagicMock()
            mock_batch_result.batch_id = "batch_123"
            mock_batch_result.total_companies = 3
            mock_batch_result.created_at = datetime.now(timezone.utc)
            mock_use_case.execute.return_value = mock_batch_result
            
            request_data = {
                "companies": [
                    {"name": "Company A"},
                    {"name": "Company B"},
                    {"name": "Company C"}
                ]
            }
            response = client.post("/api/v2/batch/research", json=request_data)
            
            assert response.status_code == 200
            
            # Verify metrics were recorded
            mock_metrics.increment_counter.assert_called_with(
                "batch_jobs_started",
                tags={
                    "priority": "normal",
                    "company_count": "3"
                }
            )
    
    def test_batch_endpoint_logging(self, client, mock_container):
        """Test that batch endpoints log appropriately"""
        with patch('src.api.routers.batch.logger') as mock_logger:
            container, mock_use_case = mock_container
            
            mock_batch_result = MagicMock()
            mock_batch_result.batch_id = "batch_123"
            mock_batch_result.total_companies = 2
            mock_batch_result.created_at = datetime.now(timezone.utc)
            mock_use_case.execute.return_value = mock_batch_result
            
            request_data = {
                "companies": [
                    {"name": "Company A"},
                    {"name": "Company B"}
                ]
            }
            response = client.post("/api/v2/batch/research", json=request_data)
            
            assert response.status_code == 200
            
            # Verify logging was called
            mock_logger.info.assert_called()
            
            # Check log content
            log_call = mock_logger.info.call_args
            assert "Batch research job started" in log_call[0][0]
    
    def test_stream_batch_progress(self, client, mock_container):
        """Test streaming batch progress via SSE"""
        container, mock_use_case = mock_container
        
        # Mock batch status
        mock_batch_status = MagicMock()
        mock_batch_status.batch_id = "batch_123"
        mock_use_case.get_batch_status.return_value = mock_batch_status
        
        mock_progress = MagicMock()
        mock_progress.status = "running"
        mock_progress.json.return_value = '{"status": "running", "progress": 60.0}'
        mock_use_case.get_batch_progress_stream.return_value = mock_progress
        
        response = client.get("/api/v2/batch/batch_123/stream")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Check SSE headers
        assert response.headers["cache-control"] == "no-cache"
        assert response.headers["connection"] == "keep-alive"
    
    def test_batch_job_priority_handling(self, client, mock_container):
        """Test batch job priority handling"""
        container, mock_use_case = mock_container
        
        mock_batch_result = MagicMock()
        mock_batch_result.batch_id = "batch_priority"
        mock_batch_result.total_companies = 1
        mock_batch_result.created_at = datetime.now(timezone.utc)
        mock_use_case.execute.return_value = mock_batch_result
        
        # Test high priority
        request_data = {
            "companies": [{"name": "Urgent Company"}],
            "priority": "high"
        }
        
        response = client.post("/api/v2/batch/research", json=request_data)
        
        assert response.status_code == 200
        
        # Verify priority was passed correctly
        call_args = mock_use_case.execute.call_args
        assert call_args.kwargs["priority"] == JobPriority.HIGH