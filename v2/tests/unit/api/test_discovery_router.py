#!/usr/bin/env python3
"""
Tests for Theodore v2 Discovery API Router
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.app import create_app
from src.api.models.requests import DiscoveryRequest
from src.api.models.responses import DiscoveryResponse
from src.api.models.common import JobStatus


class TestDiscoveryRouter:
    """Test discovery API endpoints"""
    
    @pytest.fixture
    def mock_container(self):
        """Mock application container"""
        container = AsyncMock()
        
        # Mock discovery use case
        mock_discovery_use_case = AsyncMock()
        container.get.return_value = mock_discovery_use_case
        
        return container, mock_discovery_use_case
    
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
    
    def test_discover_similar_companies_success(self, client, mock_container):
        """Test successful company discovery"""
        container, mock_use_case = mock_container
        
        # Mock discovery results
        mock_results = [
            {
                "name": "Similar Company 1",
                "description": "Similar company description",
                "similarity_score": 0.85,
                "industry": "Technology",
                "business_model": "B2B SaaS"
            },
            {
                "name": "Similar Company 2", 
                "description": "Another similar company",
                "similarity_score": 0.78,
                "industry": "Technology",
                "business_model": "B2B SaaS"
            }
        ]
        
        mock_discovery_result = MagicMock()
        mock_discovery_result.job_id = "discovery_123"
        mock_discovery_result.status = "completed"
        mock_discovery_result.similar_companies = mock_results
        mock_discovery_result.total_found = len(mock_results)
        mock_discovery_result.created_at = datetime.now(timezone.utc)
        mock_discovery_result.completed_at = datetime.now(timezone.utc)
        
        mock_use_case.execute.return_value = mock_discovery_result
        
        # Make request
        request_data = {
            "company_name": "Target Company",
            "criteria": {
                "industry": "Technology",
                "business_model": "B2B",
                "min_similarity": 0.7
            },
            "limit": 10
        }
        
        response = client.post("/api/v2/discover", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["job_id"] == "discovery_123"
        assert data["status"] == "completed"
        assert data["company_name"] == "Target Company"
        assert len(data["similar_companies"]) == 2
        assert data["total_found"] == 2
        
        # Verify similarity scores
        assert data["similar_companies"][0]["similarity_score"] == 0.85
        assert data["similar_companies"][1]["similarity_score"] == 0.78
    
    def test_discover_with_filters(self, client, mock_container):
        """Test discovery with advanced filters"""
        container, mock_use_case = mock_container
        
        mock_discovery_result = MagicMock()
        mock_discovery_result.job_id = "discovery_456"
        mock_discovery_result.status = "completed"
        mock_discovery_result.similar_companies = []
        mock_discovery_result.total_found = 0
        mock_discovery_result.created_at = datetime.now(timezone.utc)
        
        mock_use_case.execute.return_value = mock_discovery_result
        
        request_data = {
            "company_name": "Target Company",
            "criteria": {
                "industry": "FinTech",
                "business_model": "B2C",
                "company_size": "startup",
                "tech_sophistication": "high",
                "min_similarity": 0.8,
                "exclude_competitors": True
            },
            "limit": 5,
            "include_analysis": True
        }
        
        response = client.post("/api/v2/discover", json=request_data)
        
        assert response.status_code == 200
        
        # Verify use case was called with correct filters
        call_args = mock_use_case.execute.call_args
        criteria = call_args.kwargs["criteria"]
        assert criteria["industry"] == "FinTech"
        assert criteria["business_model"] == "B2C"
        assert criteria["min_similarity"] == 0.8
        assert criteria["exclude_competitors"] is True
    
    def test_discover_validation_error(self, client):
        """Test discovery request validation errors"""
        # Missing required company_name
        response = client.post("/api/v2/discover", json={
            "criteria": {"industry": "Technology"}
        })
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        assert "details" in data
    
    def test_discover_invalid_criteria(self, client):
        """Test discovery with invalid criteria"""
        request_data = {
            "company_name": "Test Company",
            "criteria": {
                "min_similarity": 1.5  # Invalid: > 1.0
            }
        }
        
        response = client.post("/api/v2/discover", json=request_data)
        
        # Should either correct the value or return validation error
        assert response.status_code in [200, 422]
    
    def test_get_discovery_results_success(self, client, mock_container):
        """Test getting discovery results"""
        container, mock_use_case = mock_container
        
        # Mock discovery result
        mock_result = MagicMock()
        mock_result.job_id = "discovery_123"
        mock_result.status = "completed"
        mock_result.company_name = "Target Company"
        mock_result.similar_companies = [
            {
                "name": "Similar Co",
                "similarity_score": 0.85
            }
        ]
        mock_result.total_found = 1
        mock_result.created_at = datetime.now(timezone.utc)
        mock_result.completed_at = datetime.now(timezone.utc)
        
        mock_use_case.get_discovery_results.return_value = mock_result
        
        response = client.get("/api/v2/discover/discovery_123")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["job_id"] == "discovery_123"
        assert data["status"] == "completed"
        assert data["company_name"] == "Target Company"
        assert len(data["similar_companies"]) == 1
    
    def test_get_discovery_results_not_found(self, client, mock_container):
        """Test getting results for non-existent discovery job"""
        container, mock_use_case = mock_container
        
        mock_use_case.get_discovery_results.return_value = None
        
        response = client.get("/api/v2/discover/non_existent_job")
        
        assert response.status_code == 404
        data = response.json()
        assert "Discovery job not found" in data["detail"]
    
    def test_cancel_discovery_success(self, client, mock_container):
        """Test cancelling discovery job"""
        container, mock_use_case = mock_container
        
        mock_use_case.cancel_discovery.return_value = True
        
        response = client.delete("/api/v2/discover/discovery_123")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "cancelled successfully" in data["message"]
        assert data["job_id"] == "discovery_123"
    
    def test_cancel_discovery_not_found(self, client, mock_container):
        """Test cancelling non-existent discovery job"""
        container, mock_use_case = mock_container
        
        mock_use_case.cancel_discovery.return_value = False
        
        response = client.delete("/api/v2/discover/non_existent")
        
        assert response.status_code == 404
    
    def test_get_discovery_criteria_suggestions(self, client, mock_container):
        """Test getting discovery criteria suggestions"""
        container, mock_use_case = mock_container
        
        mock_suggestions = {
            "industries": ["Technology", "FinTech", "Healthcare", "E-commerce"],
            "business_models": ["B2B", "B2C", "B2B2C", "Marketplace"],
            "company_sizes": ["startup", "small", "medium", "large", "enterprise"],
            "tech_sophistication": ["low", "medium", "high", "cutting_edge"]
        }
        
        mock_use_case.get_criteria_suggestions.return_value = mock_suggestions
        
        response = client.get("/api/v2/discover/criteria/suggestions")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "industries" in data
        assert "business_models" in data
        assert len(data["industries"]) == 4
        assert "Technology" in data["industries"]
    
    def test_discovery_with_company_analysis(self, client, mock_container):
        """Test discovery that includes company analysis"""
        container, mock_use_case = mock_container
        
        mock_discovery_result = MagicMock()
        mock_discovery_result.job_id = "discovery_789"
        mock_discovery_result.status = "completed"
        mock_discovery_result.similar_companies = [
            {
                "name": "Similar Company",
                "similarity_score": 0.88,
                "analysis": {
                    "shared_characteristics": ["B2B SaaS", "AI-powered"],
                    "differentiators": ["Market focus", "Customer size"],
                    "competitive_insights": ["Pricing strategy", "Feature comparison"]
                }
            }
        ]
        mock_discovery_result.total_found = 1
        mock_discovery_result.created_at = datetime.now(timezone.utc)
        
        mock_use_case.execute.return_value = mock_discovery_result
        
        request_data = {
            "company_name": "Target Company",
            "include_analysis": True,
            "analysis_depth": "detailed"
        }
        
        response = client.post("/api/v2/discover", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        similar_company = data["similar_companies"][0]
        assert "analysis" in similar_company
        assert "shared_characteristics" in similar_company["analysis"]
        assert "differentiators" in similar_company["analysis"]
    
    def test_discovery_request_model_validation(self):
        """Test discovery request model validation"""
        # Valid request
        valid_request = DiscoveryRequest(
            company_name="Test Company",
            criteria={
                "industry": "Technology",
                "min_similarity": 0.7
            },
            limit=10
        )
        
        assert valid_request.company_name == "Test Company"
        assert valid_request.criteria["industry"] == "Technology"
        assert valid_request.limit == 10
        
        # Test default values
        basic_request = DiscoveryRequest(
            company_name="Test Company"
        )
        
        assert basic_request.limit == 20  # Default limit
        assert basic_request.include_analysis is False  # Default
    
    def test_discovery_response_model(self):
        """Test discovery response model"""
        response = DiscoveryResponse(
            job_id="discovery_123",
            status=JobStatus.COMPLETED,
            company_name="Test Company",
            similar_companies=[
                {
                    "name": "Similar Co",
                    "similarity_score": 0.85
                }
            ],
            total_found=1,
            created_at=datetime.now(timezone.utc)
        )
        
        assert response.job_id == "discovery_123"
        assert response.status == JobStatus.COMPLETED
        assert len(response.similar_companies) == 1
        assert response.total_found == 1
        
        # Test serialization
        data = response.dict()
        assert data["status"] == "completed"
        assert data["similar_companies"][0]["similarity_score"] == 0.85
    
    def test_discovery_endpoint_error_handling(self, client, mock_container):
        """Test error handling when discovery use case raises exception"""
        container, mock_use_case = mock_container
        
        mock_use_case.execute.side_effect = Exception("Discovery error")
        
        request_data = {
            "company_name": "Test Company"
        }
        
        response = client.post("/api/v2/discover", json=request_data)
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to start discovery" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_discovery_endpoint_metrics(self, client, mock_container):
        """Test that discovery endpoints record metrics"""
        with patch('src.api.routers.discovery.metrics') as mock_metrics:
            container, mock_use_case = mock_container
            
            mock_discovery_result = MagicMock()
            mock_discovery_result.job_id = "discovery_123"
            mock_discovery_result.created_at = datetime.now(timezone.utc)
            mock_use_case.execute.return_value = mock_discovery_result
            
            request_data = {"company_name": "Test Company"}
            response = client.post("/api/v2/discover", json=request_data)
            
            assert response.status_code == 200
            
            # Verify metrics were recorded
            mock_metrics.increment_counter.assert_called_with(
                "discovery_jobs_started",
                tags={
                    "include_analysis": "False",
                    "has_criteria": "False"
                }
            )
    
    def test_discovery_endpoint_logging(self, client, mock_container):
        """Test that discovery endpoints log appropriately"""
        with patch('src.api.routers.discovery.logger') as mock_logger:
            container, mock_use_case = mock_container
            
            mock_discovery_result = MagicMock()
            mock_discovery_result.job_id = "discovery_123"
            mock_discovery_result.created_at = datetime.now(timezone.utc)
            mock_use_case.execute.return_value = mock_discovery_result
            
            request_data = {"company_name": "Test Company"}
            response = client.post("/api/v2/discover", json=request_data)
            
            assert response.status_code == 200
            
            # Verify logging was called
            mock_logger.info.assert_called()
            
            # Check log content
            log_call = mock_logger.info.call_args
            assert "Discovery job started" in log_call[0][0]
    
    def test_get_popular_discovery_queries(self, client, mock_container):
        """Test getting popular discovery query patterns"""
        container, mock_use_case = mock_container
        
        mock_popular_queries = [
            {
                "query_pattern": "B2B SaaS companies in FinTech",
                "frequency": 45,
                "success_rate": 0.87
            },
            {
                "query_pattern": "AI-powered startups",
                "frequency": 38,
                "success_rate": 0.92
            }
        ]
        
        mock_use_case.get_popular_queries.return_value = mock_popular_queries
        
        response = client.get("/api/v2/discover/popular-queries")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["queries"]) == 2
        assert data["queries"][0]["frequency"] == 45
        assert data["queries"][1]["success_rate"] == 0.92
    
    def test_discovery_with_pagination(self, client, mock_container):
        """Test discovery with pagination parameters"""
        container, mock_use_case = mock_container
        
        mock_discovery_result = MagicMock()
        mock_discovery_result.job_id = "discovery_page"
        mock_discovery_result.status = "completed"
        mock_discovery_result.similar_companies = []
        mock_discovery_result.total_found = 0
        mock_discovery_result.has_more = False
        mock_discovery_result.page = 1
        mock_discovery_result.per_page = 5
        mock_discovery_result.created_at = datetime.now(timezone.utc)
        
        mock_use_case.execute.return_value = mock_discovery_result
        
        request_data = {
            "company_name": "Test Company",
            "limit": 5,
            "offset": 10
        }
        
        response = client.post("/api/v2/discover", json=request_data)
        
        assert response.status_code == 200
        
        # Verify pagination parameters were passed
        call_args = mock_use_case.execute.call_args
        assert call_args.kwargs["limit"] == 5
        assert call_args.kwargs["offset"] == 10