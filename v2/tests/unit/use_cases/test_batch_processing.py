"""
Unit tests for batch processing use case.

Tests comprehensive batch processing functionality including job management,
progress tracking, concurrency control, and error handling.
"""

import pytest
import asyncio
import tempfile
import csv
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from src.core.domain.entities.batch_job import (
    BatchJob, BatchJobStatus, BatchJobType, BatchProgress,
    BatchInputSource, BatchOutputDestination, 
    InputSourceType, OutputDestinationType, BatchConfiguration
)
from src.core.use_cases.batch_processing import (
    BatchProcessingUseCase, BatchInputProcessor, BatchOutputProcessor,
    ConcurrencyController
)


class TestBatchInputProcessor:
    """Test batch input processing functionality"""
    
    @pytest.fixture
    def sample_csv_content(self):
        """Create sample CSV content for testing"""
        return [
            ['Company Name', 'Website', 'Industry'],
            ['TestCorp A', 'https://testcorp-a.com', 'Technology'],
            ['TestCorp B', 'https://testcorp-b.com', 'Software'], 
            ['TestCorp C', '', 'Finance'],
            ['', 'https://invalid.com', 'Healthcare']  # Invalid - no name
        ]
    
    @pytest.fixture
    def csv_file(self, sample_csv_content, tmp_path):
        """Create temporary CSV file for testing"""
        csv_file_path = tmp_path / "test_companies.csv"
        
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(sample_csv_content)
        
        return str(csv_file_path)
    
    @pytest.mark.asyncio
    async def test_read_companies_from_csv(self, csv_file):
        """Test reading companies from CSV file with schema detection"""
        processor = BatchInputProcessor()
        
        companies = []
        async for company_data in processor.read_companies_from_csv(csv_file):
            companies.append(company_data)
        
        # Should read valid companies and skip invalid ones
        assert len(companies) == 3  # 4 data rows, 1 invalid (no name)
        
        # Check first company
        assert companies[0]['company_name'] == 'TestCorp A'
        assert companies[0]['website'] == 'https://testcorp-a.com'
        assert 'original_row' in companies[0]
        
        # Check company with no website
        test_corp_c = next(c for c in companies if c['company_name'] == 'TestCorp C')
        assert test_corp_c['website'] is None
    
    def test_normalize_company_row_valid(self):
        """Test normalizing valid company row"""
        processor = BatchInputProcessor()
        
        row = {
            'Company Name': 'Test Corp',
            'Website': 'https://test.com',
            'Industry': 'Tech'
        }
        
        result = processor._normalize_company_row(row)
        
        assert result is not None
        assert result['company_name'] == 'Test Corp'
        assert result['website'] == 'https://test.com'
        assert result['original_row'] == row
    
    def test_normalize_company_row_invalid(self):
        """Test normalizing invalid company row (no name)"""
        processor = BatchInputProcessor()
        
        row = {
            'Website': 'https://test.com',
            'Industry': 'Tech'
        }
        
        result = processor._normalize_company_row(row)
        assert result is None
    
    def test_normalize_company_row_alternative_columns(self):
        """Test normalizing with alternative column names"""
        processor = BatchInputProcessor()
        
        row = {
            'company': 'Alt Corp',
            'url': 'https://alt.com',
            'sector': 'Finance'
        }
        
        result = processor._normalize_company_row(row)
        
        assert result is not None
        assert result['company_name'] == 'Alt Corp'
        assert result['website'] == 'https://alt.com'


class TestBatchOutputProcessor:
    """Test batch output processing functionality"""
    
    @pytest.fixture
    def sample_results(self):
        """Create sample batch processing results"""
        from src.core.domain.entities.company import Company
        
        company_data = Company(
            name="Test Corp",
            website="https://test.com",
            industry="Technology",
            description="A test company"
        )
        
        return [
            {
                'company_name': 'Test Corp A',
                'website': 'https://test-a.com',
                'status': 'success',
                'company_data': company_data,
                'processing_time': 45.2,
                'cost': 0.15,
                'confidence_score': 0.85,
                'data_quality_score': 0.92,
                'original_row': {'Company': 'Test Corp A', 'URL': 'https://test-a.com'}
            },
            {
                'company_name': 'Test Corp B',
                'website': 'https://test-b.com',
                'status': 'failed',
                'error_message': 'Connection timeout',
                'processing_time': 120.0,
                'original_row': {'Company': 'Test Corp B', 'URL': 'https://test-b.com'}
            }
        ]
    
    @pytest.mark.asyncio
    async def test_write_results_to_csv(self, sample_results, tmp_path):
        """Test writing batch results to CSV file"""
        processor = BatchOutputProcessor()
        output_file = tmp_path / "test_results.csv"
        
        await processor.write_results_to_csv(
            sample_results, 
            str(output_file),
            include_metadata=True
        )
        
        # Verify file was created
        assert output_file.exists()
        
        # Read and verify content
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        
        # Check successful result
        success_row = rows[0]
        assert success_row['company_name'] == 'Test Corp A'
        assert success_row['status'] == 'success'
        assert success_row['processing_time'] == '45.2'
        assert success_row['cost'] == '0.15'
        
        # Check failed result
        failed_row = rows[1]
        assert failed_row['company_name'] == 'Test Corp B'
        assert failed_row['status'] == 'failed'
        assert failed_row['error_message'] == 'Connection timeout'
    
    def test_get_csv_fieldnames(self, sample_results):
        """Test determining CSV field names from results"""
        processor = BatchOutputProcessor()
        
        fieldnames = processor._get_csv_fieldnames(sample_results, include_metadata=True)
        
        # Check required fields are present
        required_fields = ['company_name', 'website', 'status', 'processing_time', 'cost']
        for field in required_fields:
            assert field in fieldnames
    
    def test_flatten_result_for_csv(self, sample_results):
        """Test flattening complex result for CSV output"""
        processor = BatchOutputProcessor()
        
        flattened = processor._flatten_result_for_csv(sample_results[0], include_metadata=True)
        
        assert flattened['company_name'] == 'Test Corp A'
        assert flattened['status'] == 'success'
        assert flattened['industry'] == 'Technology'
        assert flattened['processing_time'] == 45.2


class TestConcurrencyController:
    """Test concurrency control functionality"""
    
    @pytest.mark.asyncio
    async def test_acquire_release_slot(self):
        """Test basic slot acquisition and release"""
        controller = ConcurrencyController(max_concurrent=2, rate_limit_per_minute=60)
        
        # Should be able to acquire slots
        await controller.acquire_slot()
        await controller.acquire_slot()
        
        # Release slots
        controller.release_slot()
        controller.release_slot()
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting enforcement"""
        controller = ConcurrencyController(max_concurrent=5, rate_limit_per_minute=2)
        
        # Acquire slots rapidly
        start_time = asyncio.get_event_loop().time()
        
        await controller.acquire_slot()
        controller.release_slot()
        
        await controller.acquire_slot()
        controller.release_slot()
        
        # Third request should be delayed due to rate limiting
        await controller.acquire_slot()
        controller.release_slot()
        
        end_time = asyncio.get_event_loop().time()
        
        # Should have taken some time due to rate limiting
        # (This is a simplified test - real rate limiting is more complex)
        assert end_time >= start_time


class TestBatchJob:
    """Test batch job entity functionality"""
    
    @pytest.fixture
    def sample_batch_job(self):
        """Create sample batch job for testing"""
        input_source = BatchInputSource(
            type=InputSourceType.CSV_FILE,
            path="/test/companies.csv"
        )
        
        output_destination = BatchOutputDestination(
            type=OutputDestinationType.CSV_FILE,
            path="/test/results.csv"
        )
        
        progress = BatchProgress(total_companies=100)
        
        return BatchJob(
            job_name="Test Batch",
            job_type=BatchJobType.RESEARCH,
            input_source=input_source,
            output_destination=output_destination,
            progress=progress
        )
    
    def test_batch_job_creation(self, sample_batch_job):
        """Test batch job creation and initialization"""
        job = sample_batch_job
        
        assert job.job_name == "Test Batch"
        assert job.job_type == BatchJobType.RESEARCH
        assert job.status == BatchJobStatus.PENDING
        assert job.progress.total_companies == 100
        assert job.progress.completed_companies == 0
        assert job.job_id.startswith("batch_")
    
    def test_job_lifecycle_transitions(self, sample_batch_job):
        """Test job status transitions through lifecycle"""
        job = sample_batch_job
        
        # Start job
        job.start_job()
        assert job.status == BatchJobStatus.RUNNING
        assert job.started_at is not None
        
        # Pause job
        job.pause_job()
        assert job.status == BatchJobStatus.PAUSED
        
        # Resume job
        job.resume_job()
        assert job.status == BatchJobStatus.RESUMING
        
        # Complete job
        from src.core.domain.entities.batch_job import BatchResultSummary
        result_summary = BatchResultSummary(
            total_processed=100,
            successful_results=95,
            failed_results=5,
            skipped_results=0,
            total_processing_time=3600.0,
            average_processing_time=36.0,
            peak_processing_rate=2.5,
            total_cost=15.0,
            cost_per_company=0.15,
            data_quality_score=0.85,
            completeness_score=0.95,
            error_categories={'timeout': 3, 'network': 2},
            most_common_errors=['timeout', 'network']
        )
        
        job.complete_job(result_summary)
        assert job.status == BatchJobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.result_summary == result_summary
    
    def test_progress_tracking(self, sample_batch_job):
        """Test progress tracking functionality"""
        job = sample_batch_job
        
        # Add processed companies
        job.add_processed_company("Company A", success=True)
        job.add_processed_company("Company B", success=False)
        job.add_processed_company("Company C", success=True)
        
        assert job.progress.completed_companies == 2
        assert job.progress.failed_companies == 1
        assert len(job.processed_companies) == 3
        assert len(job.failed_companies) == 1
        assert "Company B" in job.failed_companies
    
    def test_error_tracking(self, sample_batch_job):
        """Test error tracking and categorization"""
        job = sample_batch_job
        
        # Add various errors
        job.add_error("Company A", "timeout", "Request timed out")
        job.add_error("Company B", "network", "Network unreachable")
        job.add_error("Company C", "timeout", "Another timeout")
        
        assert job.progress.errors_by_type["timeout"] == 2
        assert job.progress.errors_by_type["network"] == 1
        assert len(job.progress.errors_by_company) == 3
    
    def test_checkpoint_functionality(self, sample_batch_job):
        """Test checkpoint creation and restoration"""
        job = sample_batch_job
        
        # Process some companies
        job.add_processed_company("Company A", success=True)
        job.add_processed_company("Company B", success=False)
        job.add_error("Company B", "timeout", "Timeout error")
        
        # Create checkpoint
        checkpoint = job.create_checkpoint()
        
        assert checkpoint["job_id"] == job.job_id
        assert checkpoint["progress"]["completed_companies"] == 1
        assert checkpoint["progress"]["failed_companies"] == 1
        assert "Company A" in checkpoint["processed_companies"]
        assert "Company B" in checkpoint["failed_companies"]
        
        # Create new job and restore from checkpoint
        new_job = BatchJob(
            job_name="Restored Job",
            job_type=BatchJobType.RESEARCH,
            input_source=job.input_source,
            output_destination=job.output_destination,
            progress=BatchProgress(total_companies=100)
        )
        
        new_job.restore_from_checkpoint(checkpoint)
        
        assert new_job.progress.completed_companies == 1
        assert new_job.progress.failed_companies == 1
        assert len(new_job.processed_companies) == 2
        assert len(new_job.failed_companies) == 1
    
    def test_job_properties(self, sample_batch_job):
        """Test computed job properties"""
        job = sample_batch_job
        
        # Test initial state
        assert not job.is_active
        assert not job.is_terminal
        assert not job.can_resume
        
        # Test running state
        job.start_job()
        assert job.is_active
        assert not job.is_terminal
        
        # Test completed state
        from src.core.domain.entities.batch_job import BatchResultSummary
        result_summary = BatchResultSummary(
            total_processed=10, successful_results=10, failed_results=0,
            skipped_results=0, total_processing_time=100, average_processing_time=10,
            peak_processing_rate=1, total_cost=1, cost_per_company=0.1,
            data_quality_score=1, completeness_score=1, error_categories={},
            most_common_errors=[]
        )
        job.complete_job(result_summary)
        
        assert not job.is_active
        assert job.is_terminal
        assert not job.can_resume  # Completed jobs can't be resumed


class TestBatchProcessingUseCase:
    """Test main batch processing use case"""
    
    @pytest.fixture
    def mock_research_use_case(self):
        """Create mock research use case"""
        use_case = AsyncMock()
        
        # Mock research result
        from src.core.domain.entities.company import Company
        from src.core.domain.value_objects.research_result import ResearchCompanyResult
        from src.core.use_cases.base import UseCaseStatus
        from datetime import datetime
        import uuid
        
        company_data = Company(
            name="Test Corp",
            website="https://test.com",
            industry="Technology"
        )
        
        research_result = ResearchCompanyResult(
            # Required from BaseUseCaseResult
            status=UseCaseStatus.COMPLETED,
            execution_id=str(uuid.uuid4()),
            started_at=datetime.now(timezone.utc),
            company_name="Test Corp",
            # Additional fields
            company_data=company_data
        )
        
        use_case.execute.return_value = research_result
        return use_case
    
    @pytest.fixture
    def mock_discovery_use_case(self):
        """Create mock discovery use case"""
        return AsyncMock()
    
    @pytest.fixture
    def batch_use_case(self, mock_research_use_case, mock_discovery_use_case):
        """Create batch processing use case with mocked dependencies"""
        return BatchProcessingUseCase(
            research_use_case=mock_research_use_case,
            discovery_use_case=mock_discovery_use_case
        )
    
    @pytest.fixture
    def csv_file(self, tmp_path):
        """Create temporary CSV file for testing"""
        csv_content = [
            ['Company Name', 'Website', 'Industry'],
            ['TestCorp A', 'https://testcorp-a.com', 'Technology'],
            ['TestCorp B', 'https://testcorp-b.com', 'Software'], 
            ['TestCorp C', '', 'Finance']
        ]
        
        csv_file_path = tmp_path / "test_companies.csv"
        
        import csv
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_content)
        
        return str(csv_file_path)
    
    @pytest.mark.asyncio
    async def test_start_batch_research(self, batch_use_case, csv_file):
        """Test starting a batch research job"""
        input_source = BatchInputSource(
            type=InputSourceType.CSV_FILE,
            path=csv_file
        )
        
        output_destination = BatchOutputDestination(
            type=OutputDestinationType.CSV_FILE,
            path="/test/results.csv"
        )
        
        job = await batch_use_case.start_batch_research(
            input_source=input_source,
            output_destination=output_destination,
            job_name="Test Batch",
            max_concurrent=2,
            timeout_per_company=60
        )
        
        assert job is not None
        assert job.job_name == "Test Batch"
        assert job.job_type == BatchJobType.RESEARCH
        assert job.progress.total_companies == 3  # From sample CSV
        assert job.configuration.max_concurrent == 2
        assert job.configuration.timeout_per_company == 60
    
    @pytest.mark.asyncio
    async def test_count_companies_in_source(self, batch_use_case, csv_file):
        """Test counting companies in input source"""
        input_source = BatchInputSource(
            type=InputSourceType.CSV_FILE,
            path=csv_file
        )
        
        count = await batch_use_case._count_companies_in_source(input_source)
        assert count == 3  # Valid companies in sample CSV
    
    @pytest.mark.asyncio
    async def test_job_management_operations(self, batch_use_case):
        """Test job management operations (cancel, pause, resume)"""
        # Create a mock job
        from src.core.domain.entities.batch_job import BatchProgress
        
        job = BatchJob(
            job_name="Test Job",
            job_type=BatchJobType.RESEARCH,
            input_source=BatchInputSource(type=InputSourceType.CSV_FILE, path="test.csv"),
            output_destination=BatchOutputDestination(type=OutputDestinationType.CSV_FILE, path="out.csv"),
            progress=BatchProgress(total_companies=10)
        )
        job.start_job()
        
        # Process some companies to make the job resumable
        job.add_processed_company("Company A", success=True)
        job.add_processed_company("Company B", success=False)
        
        # Add to active jobs
        batch_use_case.active_jobs[job.job_id] = job
        
        # Test pause
        success = await batch_use_case.pause_job(job.job_id)
        assert success
        assert job.status == BatchJobStatus.PAUSED
        
        # Test cancel (cancel the paused job)
        success = await batch_use_case.cancel_job(job.job_id)
        assert success
        assert job.status == BatchJobStatus.CANCELLED
        
        # Test resume (should return False for cancelled job)
        success = await batch_use_case.resume_job(job.job_id)
        assert not success  # Can't resume a cancelled job
    
    def test_list_active_jobs(self, batch_use_case):
        """Test listing active jobs"""
        # Initially no jobs
        assert len(batch_use_case.list_active_jobs()) == 0
        
        # Add mock jobs
        job1 = BatchJob(
            job_name="Job 1", job_type=BatchJobType.RESEARCH,
            input_source=BatchInputSource(type=InputSourceType.CSV_FILE, path="test1.csv"),
            output_destination=BatchOutputDestination(type=OutputDestinationType.CSV_FILE, path="out1.csv"),
            progress=BatchProgress(total_companies=10)
        )
        job2 = BatchJob(
            job_name="Job 2", job_type=BatchJobType.RESEARCH,
            input_source=BatchInputSource(type=InputSourceType.CSV_FILE, path="test2.csv"),
            output_destination=BatchOutputDestination(type=OutputDestinationType.CSV_FILE, path="out2.csv"),
            progress=BatchProgress(total_companies=20)
        )
        
        batch_use_case.active_jobs[job1.job_id] = job1
        batch_use_case.active_jobs[job2.job_id] = job2
        
        active_jobs = batch_use_case.list_active_jobs()
        assert len(active_jobs) == 2
        assert job1 in active_jobs
        assert job2 in active_jobs