#!/usr/bin/env python3
"""
Tests for Export Data Use Case
"""

import pytest
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, Mock

from src.core.use_cases.export_data import ExportData, ExportDataRequest, ExportDataResponse
from src.core.domain.models.export import (
    ExportFormat, ExportFilters, OutputConfig, ExportResult,
    Analytics, Visualization, VisualizationType
)
from src.core.domain.models.company import CompanyData


class TestExportData:
    """Test cases for ExportData use case"""
    
    @pytest.fixture
    def mock_export_engine(self):
        """Mock export engine"""
        engine = AsyncMock()
        engine.export.return_value = ExportResult(
            file_path=Path("/tmp/test_export.csv"),
            format=ExportFormat.CSV,
            record_count=10,
            file_size_bytes=1024,
            columns=['name', 'industry', 'location']
        )
        engine.validate_export_config.return_value = True
        engine.get_supported_formats.return_value = ['csv', 'json', 'excel']
        return engine
    
    @pytest.fixture
    def mock_analytics_engine(self):
        """Mock analytics engine"""
        engine = AsyncMock()
        engine.generate_analytics.return_value = Analytics(
            total_companies=10,
            industries_count=5,
            industry_distribution={'Technology': 5, 'Finance': 3, 'Healthcare': 2},
            size_distribution={'Small': 7, 'Medium': 3},
            location_distribution={'San Francisco': 4, 'New York': 3, 'Austin': 3}
        )
        return engine
    
    @pytest.fixture
    def mock_visualization_engine(self):
        """Mock visualization engine"""
        engine = AsyncMock()
        engine.create_visualizations.return_value = [
            Visualization(
                type=VisualizationType.CHARTS,
                title="Industry Distribution",
                data={'Technology': 5, 'Finance': 3},
                chart_type="pie"
            )
        ]
        return engine
    
    @pytest.fixture
    def sample_companies(self):
        """Sample company data"""
        return [
            CompanyData(
                name="TechCorp",
                industry="Technology",
                location="San Francisco",
                description="A tech company"
            ),
            CompanyData(
                name="FinanceInc",
                industry="Finance", 
                location="New York",
                description="A finance company"
            ),
            CompanyData(
                name="HealthCo",
                industry="Healthcare",
                location="Austin",
                description="A healthcare company"
            )
        ]
    
    @pytest.fixture
    def basic_export_request(self):
        """Basic export request"""
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            return ExportDataRequest(
                filters=ExportFilters(),
                output_config=OutputConfig(
                    format=ExportFormat.CSV,
                    file_path=Path(tmp.name)
                )
            )
    
    @pytest.mark.asyncio
    async def test_basic_export_success(self, mock_export_engine, basic_export_request):
        """Test basic export without analytics or visualizations"""
        
        # Arrange
        use_case = ExportData(export_engine=mock_export_engine)
        
        # Act
        response = await use_case.execute(basic_export_request)
        
        # Assert
        assert response.success is True
        assert response.file_path == Path("/tmp/test_export.csv")
        assert response.record_count == 10
        assert response.format == ExportFormat.CSV
        assert response.error_message is None
        
        # Verify export engine was called
        mock_export_engine.validate_export_config.assert_called_once()
        mock_export_engine.export.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_export_with_analytics(self, mock_export_engine, mock_analytics_engine, basic_export_request):
        """Test export with analytics generation"""
        
        # Arrange
        basic_export_request.include_analytics = True
        use_case = ExportData(
            export_engine=mock_export_engine,
            analytics_engine=mock_analytics_engine
        )
        
        # Act
        response = await use_case.execute(basic_export_request)
        
        # Assert
        assert response.success is True
        assert response.analytics is not None
        assert response.analytics.total_companies == 10
        assert response.analytics.industries_count == 5
        
        # Verify analytics engine was called
        mock_analytics_engine.generate_analytics.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_export_with_visualizations(self, mock_export_engine, mock_visualization_engine, basic_export_request):
        """Test export with visualization generation"""
        
        # Arrange
        basic_export_request.include_visualizations = True
        use_case = ExportData(
            export_engine=mock_export_engine,
            visualization_engine=mock_visualization_engine
        )
        
        # Act
        response = await use_case.execute(basic_export_request)
        
        # Assert
        assert response.success is True
        assert response.visualizations is not None
        assert len(response.visualizations) == 1
        assert response.visualizations[0].title == "Industry Distribution"
        
        # Verify visualization engine was called
        mock_visualization_engine.create_visualizations.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_export_with_all_features(self, mock_export_engine, mock_analytics_engine, 
                                          mock_visualization_engine, basic_export_request):
        """Test export with both analytics and visualizations"""
        
        # Arrange
        basic_export_request.include_analytics = True
        basic_export_request.include_visualizations = True
        use_case = ExportData(
            export_engine=mock_export_engine,
            analytics_engine=mock_analytics_engine,
            visualization_engine=mock_visualization_engine
        )
        
        # Act
        response = await use_case.execute(basic_export_request)
        
        # Assert
        assert response.success is True
        assert response.analytics is not None
        assert response.visualizations is not None
        assert len(response.visualizations) == 1
        
        # Verify both engines were called
        mock_analytics_engine.generate_analytics.assert_called_once()
        mock_visualization_engine.create_visualizations.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_export_invalid_config(self, mock_export_engine, basic_export_request):
        """Test export with invalid configuration"""
        
        # Arrange
        mock_export_engine.validate_export_config.return_value = False
        use_case = ExportData(export_engine=mock_export_engine)
        
        # Act
        response = await use_case.execute(basic_export_request)
        
        # Assert
        assert response.success is False
        assert "Invalid export configuration" in response.error_message
        
        # Verify export was not called
        mock_export_engine.export.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_export_engine_failure(self, mock_export_engine, basic_export_request):
        """Test handling of export engine failure"""
        
        # Arrange
        mock_export_engine.export.side_effect = Exception("Export failed")
        use_case = ExportData(export_engine=mock_export_engine)
        
        # Act
        response = await use_case.execute(basic_export_request)
        
        # Assert
        assert response.success is False
        assert "Export failed" in response.error_message
    
    @pytest.mark.asyncio
    async def test_analytics_engine_failure(self, mock_export_engine, mock_analytics_engine, basic_export_request):
        """Test handling of analytics engine failure"""
        
        # Arrange
        basic_export_request.include_analytics = True
        mock_analytics_engine.generate_analytics.side_effect = Exception("Analytics failed")
        use_case = ExportData(
            export_engine=mock_export_engine,
            analytics_engine=mock_analytics_engine
        )
        
        # Act
        response = await use_case.execute(basic_export_request)
        
        # Assert
        assert response.success is False
        assert "Analytics failed" in response.error_message
    
    @pytest.mark.asyncio
    async def test_visualization_engine_failure(self, mock_export_engine, mock_visualization_engine, basic_export_request):
        """Test handling of visualization engine failure"""
        
        # Arrange
        basic_export_request.include_visualizations = True
        mock_visualization_engine.create_visualizations.side_effect = Exception("Visualization failed")
        use_case = ExportData(
            export_engine=mock_export_engine,
            visualization_engine=mock_visualization_engine
        )
        
        # Act
        response = await use_case.execute(basic_export_request)
        
        # Assert
        assert response.success is False
        assert "Visualization failed" in response.error_message
    
    @pytest.mark.asyncio
    async def test_analytics_without_engine(self, mock_export_engine, basic_export_request):
        """Test requesting analytics without analytics engine"""
        
        # Arrange
        basic_export_request.include_analytics = True
        use_case = ExportData(export_engine=mock_export_engine)  # No analytics engine
        
        # Act
        response = await use_case.execute(basic_export_request)
        
        # Assert
        assert response.success is False
        assert "Analytics engine required" in response.error_message
    
    @pytest.mark.asyncio
    async def test_visualizations_without_engine(self, mock_export_engine, basic_export_request):
        """Test requesting visualizations without visualization engine"""
        
        # Arrange
        basic_export_request.include_visualizations = True
        use_case = ExportData(export_engine=mock_export_engine)  # No visualization engine
        
        # Act
        response = await use_case.execute(basic_export_request)
        
        # Assert
        assert response.success is False
        assert "Visualization engine required" in response.error_message
    
    @pytest.mark.asyncio
    async def test_filters_applied_tracking(self, mock_export_engine, basic_export_request):
        """Test tracking of applied filters"""
        
        # Arrange
        basic_export_request.filters.industries = ["Technology", "Finance"]
        basic_export_request.filters.min_employee_count = 10
        use_case = ExportData(export_engine=mock_export_engine)
        
        # Act
        response = await use_case.execute(basic_export_request)
        
        # Assert
        assert response.success is True
        assert "industry filter" in response.filters_applied
        assert "employee count filter" in response.filters_applied
    
    @pytest.mark.asyncio
    async def test_streaming_mode_detection(self, mock_export_engine, basic_export_request):
        """Test detection of streaming mode usage"""
        
        # Arrange
        mock_export_engine.export.return_value.streaming_used = True
        mock_export_engine.export.return_value.chunks_processed = 5
        use_case = ExportData(export_engine=mock_export_engine)
        
        # Act
        response = await use_case.execute(basic_export_request)
        
        # Assert
        assert response.success is True
        assert response.streaming_used is True
        assert response.chunks_processed == 5
    
    @pytest.mark.asyncio
    async def test_processing_time_tracking(self, mock_export_engine, basic_export_request):
        """Test processing time tracking"""
        
        # Arrange
        mock_export_engine.export.return_value.processing_time_seconds = 1.5
        use_case = ExportData(export_engine=mock_export_engine)
        
        # Act
        response = await use_case.execute(basic_export_request)
        
        # Assert
        assert response.success is True
        assert response.processing_time_seconds == 1.5
    
    @pytest.mark.asyncio
    async def test_file_size_tracking(self, mock_export_engine, basic_export_request):
        """Test file size tracking and formatting"""
        
        # Arrange
        mock_export_engine.export.return_value.file_size_bytes = 2048
        use_case = ExportData(export_engine=mock_export_engine)
        
        # Act
        response = await use_case.execute(basic_export_request)
        
        # Assert
        assert response.success is True
        assert response.file_size_bytes == 2048
        assert response.file_size_mb == 0.002  # 2048 bytes = ~0.002 MB


class TestExportDataRequest:
    """Test cases for ExportDataRequest model"""
    
    def test_request_validation(self):
        """Test request validation"""
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            request = ExportDataRequest(
                filters=ExportFilters(),
                output_config=OutputConfig(
                    format=ExportFormat.CSV,
                    file_path=Path(tmp.name)
                )
            )
            
            assert request.filters is not None
            assert request.output_config is not None
            assert request.include_analytics is False
            assert request.include_visualizations is False
    
    def test_request_with_all_options(self):
        """Test request with all options enabled"""
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            request = ExportDataRequest(
                filters=ExportFilters(
                    industries=["Technology"],
                    min_employee_count=10
                ),
                output_config=OutputConfig(
                    format=ExportFormat.JSON,
                    file_path=Path(tmp.name),
                    compress=True
                ),
                include_analytics=True,
                include_visualizations=True
            )
            
            assert request.include_analytics is True
            assert request.include_visualizations is True
            assert request.filters.industries == ["Technology"]
            assert request.output_config.compress is True


class TestExportDataResponse:
    """Test cases for ExportDataResponse model"""
    
    def test_successful_response(self):
        """Test successful response creation"""
        
        response = ExportDataResponse(
            success=True,
            file_path=Path("/tmp/export.csv"),
            format=ExportFormat.CSV,
            record_count=100,
            file_size_bytes=4096
        )
        
        assert response.success is True
        assert response.file_path == Path("/tmp/export.csv")
        assert response.format == ExportFormat.CSV
        assert response.record_count == 100
        assert response.file_size_bytes == 4096
        assert response.file_size_mb == 0.004  # 4096 bytes = 0.004 MB
        assert response.error_message is None
    
    def test_failed_response(self):
        """Test failed response creation"""
        
        response = ExportDataResponse(
            success=False,
            error_message="Export failed"
        )
        
        assert response.success is False
        assert response.error_message == "Export failed"
        assert response.file_path is None
        assert response.record_count == 0
    
    def test_response_with_analytics(self):
        """Test response with analytics"""
        
        analytics = Analytics(
            total_companies=50,
            industries_count=5,
            industry_distribution={'Tech': 30, 'Finance': 20},
            size_distribution={'Small': 35, 'Large': 15},
            location_distribution={'SF': 25, 'NYC': 25}
        )
        
        response = ExportDataResponse(
            success=True,
            file_path=Path("/tmp/export.json"),
            format=ExportFormat.JSON,
            record_count=50,
            file_size_bytes=8192,
            analytics=analytics
        )
        
        assert response.analytics is not None
        assert response.analytics.total_companies == 50
        assert response.analytics.industries_count == 5
    
    def test_response_with_visualizations(self):
        """Test response with visualizations"""
        
        visualizations = [
            Visualization(
                type=VisualizationType.CHARTS,
                title="Test Chart",
                data={'A': 1, 'B': 2}
            )
        ]
        
        response = ExportDataResponse(
            success=True,
            file_path=Path("/tmp/export.xlsx"),
            format=ExportFormat.EXCEL,
            record_count=25,
            file_size_bytes=16384,
            visualizations=visualizations
        )
        
        assert response.visualizations is not None
        assert len(response.visualizations) == 1
        assert response.visualizations[0].title == "Test Chart"
    
    def test_filters_applied_tracking(self):
        """Test filters applied tracking"""
        
        response = ExportDataResponse(
            success=True,
            file_path=Path("/tmp/export.csv"),
            format=ExportFormat.CSV,
            record_count=10,
            file_size_bytes=1024,
            filters_applied=["industry filter", "size filter"]
        )
        
        assert response.filters_applied == ["industry filter", "size filter"]
    
    def test_streaming_information(self):
        """Test streaming information tracking"""
        
        response = ExportDataResponse(
            success=True,
            file_path=Path("/tmp/export.parquet"),
            format=ExportFormat.PARQUET,
            record_count=10000,
            file_size_bytes=1048576,
            streaming_used=True,
            chunks_processed=10
        )
        
        assert response.streaming_used is True
        assert response.chunks_processed == 10