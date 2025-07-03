#!/usr/bin/env python3
"""
Tests for Export Engine
"""

import pytest
import tempfile
import json
import csv
from pathlib import Path
from unittest.mock import patch, mock_open

from src.infrastructure.adapters.io.export_engine import (
    ExportEngine, CSVExporter, JSONExporter, ExcelExporter, PDFExporter,
    ParquetExporter, PowerBIExporter, TableauExporter, ExportError, UnsupportedFormatError
)
from src.core.domain.models.export import ExportFormat, OutputConfig, Visualization, VisualizationType
from src.core.domain.models.company import CompanyData


class TestExportEngine:
    """Test cases for ExportEngine"""
    
    @pytest.fixture
    def export_engine(self):
        """Export engine instance"""
        return ExportEngine()
    
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
            )
        ]
    
    @pytest.fixture
    def sample_visualizations(self):
        """Sample visualizations"""
        return [
            Visualization(
                type=VisualizationType.CHARTS,
                title="Industry Distribution",
                data={'Technology': 1, 'Finance': 1},
                chart_type="pie"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_csv_export_success(self, export_engine, sample_companies):
        """Test successful CSV export"""
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            config = OutputConfig(
                format=ExportFormat.CSV,
                file_path=Path(tmp.name)
            )
            
            result = await export_engine.export(sample_companies, config)
            
            assert result.format == ExportFormat.CSV
            assert result.record_count == 2
            assert result.file_size_bytes > 0
            assert len(result.columns) > 0
            assert Path(tmp.name).exists()
    
    @pytest.mark.asyncio
    async def test_json_export_success(self, export_engine, sample_companies, sample_visualizations):
        """Test successful JSON export with visualizations"""
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            config = OutputConfig(
                format=ExportFormat.JSON,
                file_path=Path(tmp.name)
            )
            
            result = await export_engine.export(sample_companies, config, sample_visualizations)
            
            assert result.format == ExportFormat.JSON
            assert result.record_count == 2
            assert result.file_size_bytes > 0
            
            # Verify JSON content
            with open(tmp.name, 'r') as f:
                data = json.load(f)
                assert 'companies' in data
                assert 'visualizations' in data
                assert len(data['companies']) == 2
                assert len(data['visualizations']) == 1
    
    @pytest.mark.asyncio
    async def test_unsupported_format_error(self, export_engine, sample_companies):
        """Test error handling for unsupported format"""
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            # Create a fake format that doesn't exist
            config = OutputConfig(
                format="FAKE_FORMAT",  # This will cause an error
                file_path=Path(tmp.name)
            )
            
            with pytest.raises(Exception):  # Should raise some kind of error
                await export_engine.export(sample_companies, config)
    
    @pytest.mark.asyncio
    async def test_validate_export_config_success(self, export_engine):
        """Test successful export configuration validation"""
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            config = OutputConfig(
                format=ExportFormat.CSV,
                file_path=Path(tmp.name)
            )
            
            is_valid = await export_engine.validate_export_config(config)
            assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_export_config_invalid_threshold(self, export_engine):
        """Test validation failure for invalid streaming threshold"""
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            config = OutputConfig(
                format=ExportFormat.CSV,
                file_path=Path(tmp.name),
                streaming_threshold=0  # Invalid threshold
            )
            
            is_valid = await export_engine.validate_export_config(config)
            assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_get_supported_formats(self, export_engine):
        """Test getting supported formats"""
        
        formats = await export_engine.get_supported_formats()
        
        assert isinstance(formats, list)
        assert len(formats) > 0
        assert 'csv' in formats
        assert 'json' in formats
    
    @pytest.mark.asyncio
    async def test_estimate_export_size(self, export_engine, sample_companies):
        """Test export size estimation"""
        
        config = OutputConfig(
            format=ExportFormat.JSON,
            file_path=Path("/tmp/test.json")
        )
        
        estimated_size = await export_engine.estimate_export_size(sample_companies, config)
        
        assert estimated_size > 0
        assert isinstance(estimated_size, int)
    
    @pytest.mark.asyncio
    async def test_estimate_export_size_with_compression(self, export_engine, sample_companies):
        """Test export size estimation with compression"""
        
        config = OutputConfig(
            format=ExportFormat.JSON,
            file_path=Path("/tmp/test.json"),
            compress=True
        )
        
        estimated_size = await export_engine.estimate_export_size(sample_companies, config)
        
        # Should be smaller due to compression factor
        config_no_compression = OutputConfig(
            format=ExportFormat.JSON,
            file_path=Path("/tmp/test.json"),
            compress=False
        )
        
        estimated_size_no_compression = await export_engine.estimate_export_size(
            sample_companies, config_no_compression
        )
        
        assert estimated_size < estimated_size_no_compression
    
    @pytest.mark.asyncio
    async def test_streaming_export(self, export_engine, sample_companies):
        """Test streaming export for large datasets"""
        
        # Create a large dataset to trigger streaming
        large_dataset = sample_companies * 100  # 200 companies
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            config = OutputConfig(
                format=ExportFormat.CSV,
                file_path=Path(tmp.name),
                stream_large_datasets=True,
                streaming_threshold=50,  # Low threshold to trigger streaming
                chunk_size=25
            )
            
            result = await export_engine.export(large_dataset, config)
            
            assert result.record_count == 200
            assert result.streaming_used is True
            assert result.chunks_processed > 0
    
    @pytest.mark.asyncio
    async def test_data_transformation_include_fields(self, export_engine, sample_companies):
        """Test data transformation with field inclusion"""
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            config = OutputConfig(
                format=ExportFormat.JSON,
                file_path=Path(tmp.name),
                include_fields=['name', 'industry']
            )
            
            result = await export_engine.export(sample_companies, config)
            
            # Verify only specified fields are included
            with open(tmp.name, 'r') as f:
                data = json.load(f)
                for company in data['companies']:
                    assert 'name' in company
                    assert 'industry' in company
                    assert 'location' not in company  # Should be excluded
    
    @pytest.mark.asyncio
    async def test_data_transformation_exclude_fields(self, export_engine, sample_companies):
        """Test data transformation with field exclusion"""
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            config = OutputConfig(
                format=ExportFormat.JSON,
                file_path=Path(tmp.name),
                exclude_fields=['description']
            )
            
            result = await export_engine.export(sample_companies, config)
            
            # Verify excluded fields are not present
            with open(tmp.name, 'r') as f:
                data = json.load(f)
                for company in data['companies']:
                    assert 'description' not in company
                    assert 'name' in company  # Should still be present


class TestCSVExporter:
    """Test cases for CSVExporter"""
    
    @pytest.fixture
    def csv_exporter(self):
        """CSV exporter instance"""
        return CSVExporter()
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for export"""
        return [
            {'name': 'Company A', 'industry': 'Tech', 'location': 'SF'},
            {'name': 'Company B', 'industry': 'Finance', 'location': 'NYC'}
        ]
    
    @pytest.mark.asyncio
    async def test_csv_export_basic(self, csv_exporter, sample_data):
        """Test basic CSV export"""
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            config = OutputConfig(
                format=ExportFormat.CSV,
                file_path=Path(tmp.name)
            )
            
            result = await csv_exporter.export(sample_data, config)
            
            assert result.format == ExportFormat.CSV
            assert result.record_count == 2
            assert result.columns == ['name', 'industry', 'location']
            
            # Verify CSV content
            with open(tmp.name, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]['name'] == 'Company A'
    
    @pytest.mark.asyncio
    async def test_csv_export_empty_data(self, csv_exporter):
        """Test CSV export with empty data"""
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            config = OutputConfig(
                format=ExportFormat.CSV,
                file_path=Path(tmp.name)
            )
            
            result = await csv_exporter.export([], config)
            
            assert result.record_count == 0
            assert result.columns == []
    
    @pytest.mark.asyncio
    async def test_csv_streaming_export(self, csv_exporter, sample_data):
        """Test CSV streaming export"""
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            config = OutputConfig(
                format=ExportFormat.CSV,
                file_path=Path(tmp.name)
            )
            
            # Initialize streaming
            context = await csv_exporter.initialize_streaming_export(config)
            
            # Export chunks
            await csv_exporter.export_chunk(sample_data[:1], context)
            await csv_exporter.export_chunk(sample_data[1:], context)
            
            # Finalize
            result = await csv_exporter.finalize_streaming_export(context)
            
            assert result.record_count == 2
            
            # Verify content
            with open(tmp.name, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2


class TestJSONExporter:
    """Test cases for JSONExporter"""
    
    @pytest.fixture
    def json_exporter(self):
        """JSON exporter instance"""
        return JSONExporter()
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for export"""
        return [
            {'name': 'Company A', 'industry': 'Tech'},
            {'name': 'Company B', 'industry': 'Finance'}
        ]
    
    @pytest.mark.asyncio
    async def test_json_export_basic(self, json_exporter, sample_data):
        """Test basic JSON export"""
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            config = OutputConfig(
                format=ExportFormat.JSON,
                file_path=Path(tmp.name)
            )
            
            result = await json_exporter.export(sample_data, config)
            
            assert result.format == ExportFormat.JSON
            assert result.record_count == 2
            
            # Verify JSON content
            with open(tmp.name, 'r') as f:
                data = json.load(f)
                assert 'companies' in data
                assert 'metadata' in data
                assert len(data['companies']) == 2
                assert data['metadata']['record_count'] == 2
    
    @pytest.mark.asyncio
    async def test_json_export_with_visualizations(self, json_exporter, sample_data):
        """Test JSON export with visualizations"""
        
        visualizations = [
            Visualization(
                type=VisualizationType.CHARTS,
                title="Test Chart",
                data={'A': 1, 'B': 2}
            )
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            config = OutputConfig(
                format=ExportFormat.JSON,
                file_path=Path(tmp.name)
            )
            
            result = await json_exporter.export(sample_data, config, visualizations)
            
            # Verify visualizations are included
            with open(tmp.name, 'r') as f:
                data = json.load(f)
                assert 'visualizations' in data
                assert len(data['visualizations']) == 1
                assert data['visualizations'][0]['title'] == "Test Chart"


class TestExcelExporter:
    """Test cases for ExcelExporter"""
    
    @pytest.fixture
    def excel_exporter(self):
        """Excel exporter instance"""
        return ExcelExporter()
    
    def test_is_available(self, excel_exporter):
        """Test availability check"""
        # This will depend on whether openpyxl is installed
        available = excel_exporter.is_available()
        assert isinstance(available, bool)
    
    def test_get_missing_dependencies(self, excel_exporter):
        """Test missing dependencies check"""
        deps = excel_exporter.get_missing_dependencies()
        assert isinstance(deps, list)
        
        # If openpyxl is not available, it should be in the list
        if not excel_exporter.is_available():
            assert 'openpyxl' in deps
    
    @pytest.mark.asyncio
    async def test_excel_export_basic(self, excel_exporter):
        """Test basic Excel export (only if openpyxl available)"""
        
        if not excel_exporter.is_available():
            pytest.skip("openpyxl not available")
        
        sample_data = [
            {'name': 'Company A', 'industry': 'Tech'},
            {'name': 'Company B', 'industry': 'Finance'}
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            config = OutputConfig(
                format=ExportFormat.EXCEL,
                file_path=Path(tmp.name)
            )
            
            result = await excel_exporter.export(sample_data, config)
            
            assert result.format == ExportFormat.EXCEL
            assert result.record_count == 2
            assert 'Companies' in result.sheets
            assert 'Summary' in result.sheets


class TestPDFExporter:
    """Test cases for PDFExporter"""
    
    @pytest.fixture
    def pdf_exporter(self):
        """PDF exporter instance"""
        return PDFExporter()
    
    def test_is_available(self, pdf_exporter):
        """Test availability check"""
        available = pdf_exporter.is_available()
        assert isinstance(available, bool)
    
    def test_get_missing_dependencies(self, pdf_exporter):
        """Test missing dependencies check"""
        deps = pdf_exporter.get_missing_dependencies()
        assert isinstance(deps, list)
        
        if not pdf_exporter.is_available():
            assert 'reportlab' in deps
    
    @pytest.mark.asyncio
    async def test_pdf_export_basic(self, pdf_exporter):
        """Test basic PDF export (only if reportlab available)"""
        
        if not pdf_exporter.is_available():
            pytest.skip("reportlab not available")
        
        sample_data = [
            {'name': 'Company A', 'industry': 'Tech', 'location': 'SF'},
            {'name': 'Company B', 'industry': 'Finance', 'location': 'NYC'}
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            config = OutputConfig(
                format=ExportFormat.PDF,
                file_path=Path(tmp.name)
            )
            
            result = await pdf_exporter.export(sample_data, config)
            
            assert result.format == ExportFormat.PDF
            assert result.record_count == 2
            assert result.file_size_bytes > 0


class TestParquetExporter:
    """Test cases for ParquetExporter"""
    
    @pytest.fixture
    def parquet_exporter(self):
        """Parquet exporter instance"""
        return ParquetExporter()
    
    def test_is_available(self, parquet_exporter):
        """Test availability check"""
        available = parquet_exporter.is_available()
        assert isinstance(available, bool)
    
    def test_get_missing_dependencies(self, parquet_exporter):
        """Test missing dependencies check"""
        deps = parquet_exporter.get_missing_dependencies()
        assert isinstance(deps, list)
        
        if not parquet_exporter.is_available():
            # Should include pandas and/or pyarrow
            assert any(dep in deps for dep in ['pandas', 'pyarrow'])
    
    @pytest.mark.asyncio
    async def test_parquet_export_basic(self, parquet_exporter):
        """Test basic Parquet export (only if dependencies available)"""
        
        if not parquet_exporter.is_available():
            pytest.skip("Parquet dependencies not available")
        
        sample_data = [
            {'name': 'Company A', 'industry': 'Tech'},
            {'name': 'Company B', 'industry': 'Finance'}
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as tmp:
            config = OutputConfig(
                format=ExportFormat.PARQUET,
                file_path=Path(tmp.name)
            )
            
            result = await parquet_exporter.export(sample_data, config)
            
            assert result.format == ExportFormat.PARQUET
            assert result.record_count == 2
            assert result.file_size_bytes > 0


class TestPowerBIExporter:
    """Test cases for PowerBIExporter"""
    
    @pytest.fixture
    def powerbi_exporter(self):
        """PowerBI exporter instance"""
        return PowerBIExporter()
    
    @pytest.mark.asyncio
    async def test_powerbi_export_fallback(self, powerbi_exporter):
        """Test PowerBI export fallback behavior"""
        
        sample_data = [
            {'name': 'Company A', 'industry': 'Tech'},
            {'name': 'Company B', 'industry': 'Finance'}
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            config = OutputConfig(
                format=ExportFormat.POWERBI,
                file_path=Path(tmp.name)
            )
            
            result = await powerbi_exporter.export(sample_data, config)
            
            # Should fall back to Excel or CSV format
            assert result.format == ExportFormat.POWERBI
            assert result.record_count == 2


class TestTableauExporter:
    """Test cases for TableauExporter"""
    
    @pytest.fixture
    def tableau_exporter(self):
        """Tableau exporter instance"""
        return TableauExporter()
    
    @pytest.mark.asyncio
    async def test_tableau_export_csv_fallback(self, tableau_exporter):
        """Test Tableau export CSV fallback"""
        
        sample_data = [
            {'name': 'Company A', 'industry': 'Tech'},
            {'name': 'Company B', 'industry': 'Finance'}
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            config = OutputConfig(
                format=ExportFormat.TABLEAU,
                file_path=Path(tmp.name)
            )
            
            result = await tableau_exporter.export(sample_data, config)
            
            # Should use CSV format internally
            assert result.format == ExportFormat.TABLEAU
            assert result.record_count == 2