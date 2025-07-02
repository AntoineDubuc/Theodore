# TICKET-022: Batch Processing System Implementation

## Overview
Implement a comprehensive batch processing system for Theodore v2 that enables efficient processing of multiple companies from CSV files and Google Sheets, with advanced features like progress tracking, failure recovery, configurable concurrency, and intelligent job management.

## Problem Statement
Enterprise users need to process large datasets of companies efficiently while maintaining the same high-quality research as single company operations. Current challenges include:
- No mechanism for processing multiple companies systematically
- Lack of progress tracking and failure recovery for long-running operations
- No optimization for concurrent AI operations with rate limiting
- Missing support for common business data formats (CSV, Google Sheets)
- No job persistence or resume capability for interrupted operations
- Difficulty managing large datasets with proper resource utilization
- No incremental result saving for partial completions

Without robust batch processing, Theodore v2 cannot handle enterprise-scale company research requirements effectively.

## Acceptance Criteria
- [ ] Implement comprehensive BatchProcessor using ResearchCompany use case
- [ ] Support CSV input/output with flexible schema detection
- [ ] Support Google Sheets integration with authentication handling
- [ ] Implement job persistence with resume-on-failure capability
- [ ] Provide real-time progress tracking for entire batch with granular metrics
- [ ] Support configurable concurrency with intelligent rate limiting
- [ ] Ensure identical data quality between single and batch processing
- [ ] Implement incremental result saving with checkpointing
- [ ] Support batch job queuing and scheduling
- [ ] Provide comprehensive error handling and reporting
- [ ] Support multiple output formats (CSV, JSON, Excel, Google Sheets)
- [ ] Implement batch job status monitoring and management
- [ ] Support filtering and preprocessing of input data
- [ ] Provide cost estimation for large batches before execution
- [ ] Support partial batch execution with company selection
- [ ] Implement intelligent retry mechanisms for failed companies
- [ ] Support batch result analysis and summary reporting

## Technical Details

### Batch Processing Architecture
The batch processing system integrates with Theodore's core architecture while adding scalability features:

```
Batch Processing Layer
├── Job Management System (Persistence & Resume)
├── Concurrency Controller (Rate Limiting & Resource Management)
├── Progress Tracking Engine (Real-time Updates & Metrics)
├── Input/Output Adapters (CSV, Google Sheets, Excel)
├── Error Handling & Recovery (Retry Logic & Failure Analysis)
└── Result Aggregation (Summary Reports & Analytics)
```

### CLI Integration
Comprehensive batch commands with flexible options:

```bash
theodore batch [COMMAND] [OPTIONS]

Commands:
  research         Process companies for research intelligence
  discover         Batch discovery operations for competitive analysis
  status           Check status of running or completed batch jobs
  resume           Resume a previously interrupted batch job
  cancel           Cancel a running batch job
  list-jobs        List all batch jobs with status
  clean            Clean up completed or failed batch jobs
  export           Export batch results in different formats

# Research Batch Command
theodore batch research [OPTIONS] INPUT_FILE

Options:
  --output, -o PATH                      Output file path [default: results.csv]
  --format [csv|json|excel|sheets]       Output format [default: csv]
  --concurrency INTEGER                  Max concurrent operations [default: 5]
  --timeout INTEGER                      Timeout per company (seconds) [default: 120]
  --resume-job JOB_ID                   Resume specific job
  --checkpoint-interval INTEGER          Save progress every N companies [default: 10]
  --filter-column TEXT                   Column to filter companies
  --filter-value TEXT                    Value to match for filtering
  --cost-estimate                        Show cost estimate before processing
  --dry-run                             Validate input without processing
  --verbose, -v                         Enable verbose logging
  --config-override TEXT               Override configuration (key=value)
  --sheet-range TEXT                    Google Sheets range (A1:Z100)
  --include-columns TEXT                Additional columns to preserve
  --exclude-failed                      Skip companies that previously failed
  --max-retries INTEGER                 Max retry attempts per company [default: 2]
  --priority [low|medium|high]          Job priority for queuing [default: medium]
  --job-name TEXT                       Custom name for the batch job
  --notification-email TEXT             Email for job completion notification
  --help                                Show this message and exit

Examples:
  theodore batch research companies.csv --output results.json --format json
  theodore batch research sheet_id --format sheets --sheet-range A2:C100
  theodore batch research companies.csv --concurrency 10 --cost-estimate
  theodore batch resume job_abc123
  theodore batch status --all
```

### Advanced Batch Job Management
Comprehensive job lifecycle management with persistence:

```python
@dataclass
class BatchJob:
    job_id: str
    job_name: Optional[str]
    job_type: BatchJobType  # RESEARCH, DISCOVER
    status: BatchJobStatus  # PENDING, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED
    input_source: BatchInputSource  # CSV_FILE, GOOGLE_SHEETS, MANUAL_LIST
    output_destination: BatchOutputDestination
    progress: BatchProgress
    configuration: BatchConfiguration
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    error_summary: Optional[str]
    result_summary: Optional[BatchResultSummary]

class BatchProgress:
    total_companies: int
    completed_companies: int
    failed_companies: int
    skipped_companies: int
    current_company: Optional[str]
    estimated_completion: Optional[datetime]
    processing_rate: float  # companies per minute
    cost_accumulated: float
    errors_by_type: Dict[str, int]
    last_checkpoint: datetime
```

### Intelligent Concurrency Management
Advanced concurrency control with rate limiting and resource optimization:

```python
class ConcurrencyController:
    def __init__(
        self,
        max_concurrent: int,
        rate_limits: Dict[str, RateLimit],
        resource_monitor: ResourceMonitor
    ):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.rate_limiters = self._initialize_rate_limiters(rate_limits)
        self.resource_monitor = resource_monitor
        self.adaptive_scaling = AdaptiveScalingController()
    
    async def acquire_slot(self, operation_type: str) -> AsyncContextManager:
        """Acquire processing slot with rate limiting and resource checks"""
        # Wait for semaphore availability
        await self.semaphore.acquire()
        
        # Check rate limits for specific operation type
        await self.rate_limiters[operation_type].acquire()
        
        # Monitor system resources and adjust if needed
        if self.resource_monitor.should_throttle():
            await self.adaptive_scaling.apply_throttling()
        
        return AsyncConcurrencySlot(self.semaphore, self.rate_limiters[operation_type])

class AdaptiveScalingController:
    """Automatically adjusts concurrency based on system performance"""
    
    async def apply_throttling(self):
        """Reduce processing speed based on system load"""
        if self.cpu_usage > 0.8:
            await asyncio.sleep(2)  # CPU throttling
        if self.memory_usage > 0.85:
            await asyncio.sleep(1)  # Memory pressure relief
        if self.api_error_rate > 0.1:
            await asyncio.sleep(5)  # API error rate reduction
```

### Comprehensive Input/Output System
Multi-format support with intelligent schema detection:

```python
class BatchInputAdapter:
    """Unified interface for all input sources"""
    
    async def read_companies(self, source: BatchInputSource) -> AsyncIterator[CompanyInput]:
        if source.type == InputType.CSV:
            async for company in self.csv_reader.read_companies(source.path):
                yield company
        elif source.type == InputType.GOOGLE_SHEETS:
            async for company in self.sheets_reader.read_companies(source.sheet_id, source.range):
                yield company
        elif source.type == InputType.EXCEL:
            async for company in self.excel_reader.read_companies(source.path):
                yield company

class CSVInputReader:
    """Advanced CSV processing with schema detection"""
    
    async def read_companies(self, file_path: str) -> AsyncIterator[CompanyInput]:
        schema = await self.detect_schema(file_path)
        
        async with aiofiles.open(file_path, 'r') as file:
            async for row in AsyncDictReader(file):
                company_input = self.transform_row(row, schema)
                if self.validate_company_input(company_input):
                    yield company_input
                else:
                    self.log_validation_error(row, company_input)
    
    async def detect_schema(self, file_path: str) -> CSVSchema:
        """Intelligently detect column mappings"""
        # Analyze first few rows to detect:
        # - Company name column (name, company, company_name, etc.)
        # - Website column (website, url, domain, etc.)
        # - Additional metadata columns
        pass

class GoogleSheetsInputReader:
    """Google Sheets integration with authentication handling"""
    
    async def read_companies(self, sheet_id: str, range_spec: str) -> AsyncIterator[CompanyInput]:
        credentials = await self.auth_manager.get_credentials()
        service = await self.sheets_service.create_service(credentials)
        
        data = await service.values().get(
            spreadsheetId=sheet_id,
            range=range_spec
        ).execute()
        
        headers = data['values'][0]
        schema = self.detect_schema_from_headers(headers)
        
        for row in data['values'][1:]:
            company_input = self.transform_row_with_schema(row, headers, schema)
            yield company_input
```

### Advanced Progress Tracking with Analytics
Real-time progress monitoring with performance analytics:

```python
class BatchProgressTracker:
    """Advanced progress tracking with analytics and predictions"""
    
    def __init__(self, job_id: str, total_companies: int):
        self.job_id = job_id
        self.total_companies = total_companies
        self.progress_history: List[ProgressSnapshot] = []
        self.performance_analyzer = PerformanceAnalyzer()
        self.cost_tracker = CostTracker()
        
    async def update_progress(
        self,
        completed: int,
        failed: int,
        current_company: str,
        processing_time: float,
        cost_incurred: float
    ):
        snapshot = ProgressSnapshot(
            timestamp=datetime.utcnow(),
            completed=completed,
            failed=failed,
            processing_time=processing_time,
            cost=cost_incurred
        )
        
        self.progress_history.append(snapshot)
        
        # Calculate analytics
        analytics = await self.performance_analyzer.analyze(self.progress_history)
        
        # Update live display
        await self.update_live_display(snapshot, analytics)
        
        # Save checkpoint if needed
        if completed % self.checkpoint_interval == 0:
            await self.save_checkpoint()
    
    async def get_eta_prediction(self) -> Optional[datetime]:
        """Predict completion time based on processing history"""
        if len(self.progress_history) < 3:
            return None
            
        recent_rate = self.calculate_recent_processing_rate()
        remaining_companies = self.total_companies - self.get_completed_count()
        
        if recent_rate > 0:
            estimated_seconds = remaining_companies / recent_rate
            return datetime.utcnow() + timedelta(seconds=estimated_seconds)
        
        return None

class PerformanceAnalyzer:
    """Analyzes batch processing performance and provides insights"""
    
    async def analyze(self, progress_history: List[ProgressSnapshot]) -> PerformanceAnalytics:
        return PerformanceAnalytics(
            average_processing_time=self.calculate_average_time(progress_history),
            processing_rate_trend=self.calculate_rate_trend(progress_history),
            error_rate=self.calculate_error_rate(progress_history),
            cost_efficiency=self.calculate_cost_efficiency(progress_history),
            bottleneck_analysis=await self.identify_bottlenecks(progress_history),
            recommendations=self.generate_recommendations(progress_history)
        )
```

### Intelligent Failure Recovery System
Comprehensive error handling with automatic retry and recovery:

```python
class FailureRecoveryManager:
    """Manages failure recovery and retry logic for batch processing"""
    
    def __init__(self, max_retries: int = 3, backoff_strategy: BackoffStrategy = ExponentialBackoff()):
        self.max_retries = max_retries
        self.backoff_strategy = backoff_strategy
        self.failure_analyzer = FailureAnalyzer()
        
    async def handle_company_failure(
        self,
        company: CompanyInput,
        error: Exception,
        attempt: int
    ) -> FailureAction:
        """Determine appropriate action for company processing failure"""
        
        failure_classification = await self.failure_analyzer.classify_error(error)
        
        if failure_classification.is_retryable and attempt < self.max_retries:
            delay = self.backoff_strategy.calculate_delay(attempt)
            return FailureAction.RETRY_AFTER_DELAY(delay)
        elif failure_classification.is_skippable:
            return FailureAction.SKIP_WITH_LOG
        else:
            return FailureAction.FAIL_BATCH_JOB
    
    async def generate_failure_report(self, batch_job: BatchJob) -> FailureReport:
        """Generate comprehensive failure analysis report"""
        failed_companies = await self.get_failed_companies(batch_job.job_id)
        
        return FailureReport(
            total_failures=len(failed_companies),
            failure_breakdown=self.categorize_failures(failed_companies),
            retry_recommendations=self.suggest_retry_strategies(failed_companies),
            system_issues=await self.identify_system_issues(failed_companies),
            suggested_fixes=self.generate_fix_suggestions(failed_companies)
        )

class FailureAnalyzer:
    """Analyzes failures to determine retry strategies"""
    
    async def classify_error(self, error: Exception) -> FailureClassification:
        if isinstance(error, (TimeoutError, ConnectionError)):
            return FailureClassification(is_retryable=True, category="network")
        elif isinstance(error, RateLimitError):
            return FailureClassification(is_retryable=True, category="rate_limit", suggested_delay=60)
        elif isinstance(error, AuthenticationError):
            return FailureClassification(is_retryable=False, category="auth", requires_intervention=True)
        elif isinstance(error, ValidationError):
            return FailureClassification(is_retryable=False, category="data", is_skippable=True)
        else:
            return FailureClassification(is_retryable=True, category="unknown", max_retries=1)
```

### Comprehensive Result Management
Advanced result processing with aggregation and analysis:

```python
class BatchResultManager:
    """Manages batch results with aggregation and export capabilities"""
    
    async def aggregate_results(self, job_id: str) -> BatchResultSummary:
        """Create comprehensive summary of batch processing results"""
        individual_results = await self.load_individual_results(job_id)
        
        return BatchResultSummary(
            total_processed=len(individual_results),
            successful_extractions=self.count_successful_results(individual_results),
            data_quality_metrics=await self.analyze_data_quality(individual_results),
            industry_distribution=self.analyze_industry_distribution(individual_results),
            company_size_distribution=self.analyze_size_distribution(individual_results),
            geographic_distribution=self.analyze_geographic_distribution(individual_results),
            business_model_insights=self.analyze_business_models(individual_results),
            competitive_clusters=await self.identify_competitive_clusters(individual_results),
            market_insights=await self.generate_market_insights(individual_results)
        )
    
    async def export_results(
        self,
        job_id: str,
        format: OutputFormat,
        destination: str,
        include_analytics: bool = True
    ) -> ExportResult:
        """Export batch results in specified format with optional analytics"""
        
        results = await self.load_results(job_id)
        
        if format == OutputFormat.CSV:
            return await self.csv_exporter.export(results, destination, include_analytics)
        elif format == OutputFormat.EXCEL:
            return await self.excel_exporter.export_with_sheets(results, destination, include_analytics)
        elif format == OutputFormat.GOOGLE_SHEETS:
            return await self.sheets_exporter.export_to_sheet(results, destination, include_analytics)
        elif format == OutputFormat.JSON:
            return await self.json_exporter.export_structured(results, destination, include_analytics)

class DataQualityAnalyzer:
    """Analyzes data quality across batch results"""
    
    async def analyze_data_quality(self, results: List[CompanyResult]) -> DataQualityMetrics:
        return DataQualityMetrics(
            completeness_score=self.calculate_completeness(results),
            accuracy_indicators=self.assess_accuracy(results),
            consistency_score=self.measure_consistency(results),
            field_coverage=self.analyze_field_coverage(results),
            anomaly_detection=await self.detect_anomalies(results),
            quality_recommendations=self.generate_quality_recommendations(results)
        )
```

## Implementation Structure

### File Organization
```
v2/src/core/use_cases/batch/
├── __init__.py                           # Batch processing exports
├── batch_processor.py                   # Main BatchProcessor use case (1,200 lines)
├── job_manager.py                       # Batch job lifecycle management (800 lines)
├── concurrency_controller.py            # Advanced concurrency and rate limiting (600 lines)
├── progress_tracker.py                  # Real-time progress tracking (500 lines)
├── failure_recovery.py                  # Failure handling and retry logic (700 lines)
├── result_manager.py                    # Result aggregation and analysis (900 lines)
└── performance_analyzer.py              # Performance analytics and optimization (400 lines)

v2/src/infrastructure/adapters/io/
├── __init__.py                          # IO adapter exports
├── csv_handler.py                       # Advanced CSV processing (600 lines)
├── excel_handler.py                     # Excel file processing (400 lines)
├── sheets_handler.py                    # Google Sheets integration (700 lines)
├── batch_input_adapter.py               # Unified input interface (300 lines)
├── batch_output_adapter.py              # Unified output interface (400 lines)
└── schema_detector.py                   # Intelligent schema detection (350 lines)

v2/src/infrastructure/persistence/batch/
├── __init__.py                          # Batch persistence exports
├── job_repository.py                    # Job persistence interface (200 lines)
├── sqlite_job_repository.py             # SQLite job storage implementation (500 lines)
├── checkpoint_manager.py                # Checkpoint and resume logic (400 lines)
└── batch_database.py                    # Database schema and migrations (300 lines)

v2/src/cli/commands/
├── batch.py                             # Main batch CLI command (1,000 lines)
├── batch_research.py                    # Batch research subcommand (400 lines)
├── batch_discover.py                    # Batch discovery subcommand (300 lines)
├── batch_status.py                      # Job status management (250 lines)
└── batch_utils.py                       # CLI utilities and helpers (200 lines)

v2/tests/unit/batch/
├── test_batch_processor.py              # BatchProcessor unit tests (800 lines)
├── test_job_manager.py                  # Job management tests (600 lines)
├── test_concurrency_controller.py       # Concurrency tests (500 lines)
├── test_progress_tracker.py             # Progress tracking tests (400 lines)
├── test_failure_recovery.py             # Failure recovery tests (600 lines)
├── test_result_manager.py               # Result management tests (500 lines)
└── test_io_adapters.py                  # IO adapter tests (700 lines)

v2/tests/integration/batch/
├── test_batch_research.py               # End-to-end batch research tests (500 lines)
├── test_batch_csv_processing.py         # CSV processing integration tests (400 lines)
├── test_batch_sheets_integration.py     # Google Sheets integration tests (350 lines)
├── test_batch_resume_functionality.py   # Resume functionality tests (300 lines)
└── test_batch_performance.py            # Performance and load tests (400 lines)

v2/tests/fixtures/batch/
├── test_companies_small.csv             # 5 companies for quick testing
├── test_companies_medium.csv            # 50 companies for load testing
├── test_companies_with_errors.csv       # Companies with various error conditions
├── test_companies_schema_variants.csv   # Different CSV schema formats
└── batch_test_config.yml                # Batch testing configuration
```

## Dependency Integration

**Core Use Cases (TICKET-010, TICKET-011):**
- BatchProcessor orchestrates ResearchCompany and DiscoverSimilar use cases
- Maintains identical data quality and processing logic
- Proper dependency injection for all use case dependencies

**Progress Tracking (TICKET-004):**
- Integrates with established progress tracking infrastructure
- Extends progress tracking for batch-specific metrics
- Real-time updates through progress tracking port

**Configuration System (TICKET-003):**
- Batch-specific configuration with environment overrides
- Concurrency limits and rate limiting configuration
- Input/output format preferences and defaults

**Dependency Injection (TICKET-019):**
- All batch components properly registered in DI container
- Factory patterns for batch job creation
- Singleton patterns for shared resources like database connections

## Comprehensive Testing Strategy

### Unit Testing Approach
```python
# Comprehensive test coverage for all batch components
class TestBatchProcessor:
    async def test_single_company_processing_identical_to_direct():
        """Ensure batch processing of one company matches direct processing"""
        pass
    
    async def test_concurrent_processing_maintains_data_quality():
        """Verify concurrent processing doesn't compromise data quality"""
        pass
    
    async def test_failure_recovery_mechanisms():
        """Test all failure scenarios and recovery strategies"""
        pass
    
    async def test_progress_tracking_accuracy():
        """Verify progress tracking accuracy under various conditions"""
        pass

class TestJobManager:
    async def test_job_persistence_and_resume():
        """Test job persistence and resume functionality"""
        pass
    
    async def test_job_status_transitions():
        """Verify proper job status lifecycle management"""
        pass
    
    async def test_concurrent_job_execution():
        """Test multiple simultaneous batch jobs"""
        pass

class TestConcurrencyController:
    async def test_rate_limiting_enforcement():
        """Verify rate limits are properly enforced"""
        pass
    
    async def test_adaptive_scaling_behavior():
        """Test automatic scaling based on system load"""
        pass
    
    async def test_resource_monitoring_integration():
        """Verify resource monitoring and throttling"""
        pass
```

### Integration Testing Scenarios
```python
class TestBatchIntegration:
    async def test_end_to_end_csv_processing():
        """Process complete CSV file from input to output"""
        # 1. Load test CSV with 20 companies
        # 2. Process with batch system
        # 3. Verify all companies processed correctly
        # 4. Compare results with individual processing
        pass
    
    async def test_google_sheets_integration():
        """Test complete Google Sheets workflow"""
        # 1. Connect to test Google Sheet
        # 2. Process companies from sheet
        # 3. Write results back to output sheet
        # 4. Verify data integrity and formatting
        pass
    
    async def test_failure_and_resume_workflow():
        """Test failure scenarios and resume functionality"""
        # 1. Start batch job with 30 companies
        # 2. Simulate failure after 15 companies
        # 3. Resume job and verify proper continuation
        # 4. Ensure no duplicate processing
        pass
    
    async def test_performance_under_load():
        """Test system performance with larger datasets"""
        # 1. Process 100+ companies concurrently
        # 2. Monitor resource usage and performance
        # 3. Verify system stability and data quality
        # 4. Test memory usage and cleanup
        pass
```

## Cost Estimation and Optimization

### Intelligent Cost Prediction
```python
class BatchCostEstimator:
    """Provides accurate cost estimates for batch processing operations"""
    
    async def estimate_batch_cost(
        self,
        companies: List[CompanyInput],
        processing_options: BatchConfiguration
    ) -> CostEstimate:
        """Calculate comprehensive cost estimate including all AI operations"""
        
        base_cost_per_company = await self.calculate_base_cost()
        
        # Factor in processing complexity
        complexity_multiplier = self.assess_complexity_multiplier(companies)
        
        # Account for retry costs based on historical data
        retry_factor = await self.estimate_retry_factor(companies)
        
        # Calculate search tool costs
        search_costs = await self.estimate_search_costs(companies, processing_options)
        
        total_estimated_cost = (
            len(companies) * base_cost_per_company * complexity_multiplier * retry_factor
        ) + search_costs
        
        return CostEstimate(
            total_estimated_cost=total_estimated_cost,
            cost_per_company=total_estimated_cost / len(companies),
            confidence_level=self.calculate_confidence_level(companies),
            cost_breakdown=self.generate_cost_breakdown(companies, processing_options),
            optimization_suggestions=self.suggest_cost_optimizations(companies, processing_options)
        )
```

## Udemy Tutorial: Theodore v2 Batch Processing System Implementation

**Tutorial Duration: 75 minutes**
**Skill Level: Advanced**
**Prerequisites: Completion of TICKET-020 (CLI Research Command) and TICKET-019 (Dependency Injection)**

### Introduction and Overview (8 minutes)

Welcome to the comprehensive Theodore v2 Batch Processing System implementation tutorial. In this advanced session, we'll build a production-grade batch processing system that can handle hundreds or thousands of companies efficiently while maintaining the same high-quality research results as our individual company processing.

Batch processing is critical for enterprise use cases where users need to analyze entire market segments, competitive landscapes, or investment portfolios. Our system will demonstrate sophisticated software engineering patterns including concurrent processing, intelligent failure recovery, job persistence, and real-time progress tracking.

By the end of this tutorial, you'll have implemented a complete batch processing solution that showcases advanced concepts like adaptive scaling, comprehensive error handling, multi-format data integration, and enterprise-ready job management. This system represents the pinnacle of scalable AI-powered business intelligence processing.

The batch processing system we're building goes far beyond simple iteration. We're implementing intelligent concurrency control, failure recovery mechanisms, progress analytics, cost optimization, and multi-format input/output support. This is enterprise-grade software engineering that handles the complexities of real-world batch operations.

### Core Architecture and Design Patterns (12 minutes)

Let's start by understanding the sophisticated architecture that makes our batch processing system both scalable and maintainable. We're implementing several advanced design patterns that work together to create a robust enterprise solution.

The core architecture follows a layered approach with clear separation of concerns. At the top level, we have the CLI interface that provides user-friendly batch commands. Below that, we have the batch orchestration layer that manages job lifecycle, concurrency, and progress tracking. The processing layer leverages our existing use cases while adding batch-specific optimizations. Finally, we have the persistence layer that ensures job durability and resume capabilities.

One of the most important aspects of our design is maintaining identical processing logic between single and batch operations. We achieve this by using the same ResearchCompany and DiscoverSimilar use cases that we've already implemented. The batch processor acts as an orchestrator, not a reimplementation. This ensures data quality consistency and reduces code duplication.

Our concurrency model is particularly sophisticated. We're implementing adaptive scaling that automatically adjusts processing speed based on system load and API response times. This prevents overwhelming external services while maximizing throughput. We use semaphores for hard limits, rate limiters for API compliance, and resource monitors for system health.

The job persistence system ensures that long-running batch operations can survive system restarts and failures. We store job state, progress information, and intermediate results in a way that allows seamless resume operations. This is critical for enterprise environments where batch jobs might run for hours or days.

Error handling in batch processing requires a completely different approach than single operations. We implement classification-based error handling where different types of errors trigger different recovery strategies. Some errors warrant immediate retries, others suggest skipping the problematic company, and some indicate systemic issues that require human intervention.

### BatchProcessor Core Implementation (15 minutes)

Now let's implement the heart of our batch processing system - the BatchProcessor use case. This component orchestrates the entire batch operation while maintaining clean architecture principles and proper dependency injection.

```python
# v2/src/core/use_cases/batch/batch_processor.py

from typing import List, AsyncIterator, Optional, Dict, Any
import asyncio
from datetime import datetime, timedelta
import uuid
from dataclasses import dataclass

from ...entities.company import Company
from ...entities.batch import BatchJob, BatchConfiguration, BatchProgress, BatchResult
from ..research_company import ResearchCompany
from ..discover_similar import DiscoverSimilar
from ...ports.progress_tracking import ProgressTrackingPort
from .job_manager import BatchJobManager
from .concurrency_controller import ConcurrencyController
from .progress_tracker import BatchProgressTracker
from .failure_recovery import FailureRecoveryManager
from .result_manager import BatchResultManager

class BatchProcessor:
    """
    Core batch processing orchestrator that manages the complete lifecycle
    of batch company research operations with advanced features like
    intelligent concurrency, failure recovery, and progress analytics.
    """
    
    def __init__(
        self,
        research_company_use_case: ResearchCompany,
        discover_similar_use_case: DiscoverSimilar,
        job_manager: BatchJobManager,
        concurrency_controller: ConcurrencyController,
        progress_tracker: BatchProgressTracker,
        failure_recovery: FailureRecoveryManager,
        result_manager: BatchResultManager,
        progress_port: ProgressTrackingPort
    ):
        self.research_company = research_company_use_case
        self.discover_similar = discover_similar_use_case
        self.job_manager = job_manager
        self.concurrency_controller = concurrency_controller
        self.progress_tracker = progress_tracker
        self.failure_recovery = failure_recovery
        self.result_manager = result_manager
        self.progress_port = progress_port
    
    async def start_research_batch(
        self,
        companies: List[CompanyInput],
        configuration: BatchConfiguration,
        job_name: Optional[str] = None
    ) -> BatchJob:
        """
        Start a new batch research operation with comprehensive job management.
        Returns immediately with job information for monitoring and control.
        """
        
        # Create and persist batch job
        job = await self.job_manager.create_job(
            job_type=BatchJobType.RESEARCH,
            companies=companies,
            configuration=configuration,
            job_name=job_name or f"Research Batch {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        # Initialize progress tracking
        await self.progress_tracker.initialize_job(job.job_id, len(companies))
        
        # Start background processing
        asyncio.create_task(self._process_research_batch(job))
        
        return job
    
    async def _process_research_batch(self, job: BatchJob) -> None:
        """
        Internal method that handles the complete batch processing workflow
        with comprehensive error handling and progress tracking.
        """
        
        try:
            await self.job_manager.update_job_status(job.job_id, BatchJobStatus.RUNNING)
            
            # Initialize batch-specific resources
            async with self.concurrency_controller.create_batch_context(job.configuration.concurrency) as context:
                
                # Process companies with intelligent concurrency
                processed_count = 0
                failed_count = 0
                
                async for result in self._process_companies_concurrently(job, context):
                    if result.success:
                        processed_count += 1
                        await self.result_manager.store_result(job.job_id, result)
                    else:
                        failed_count += 1
                        recovery_action = await self.failure_recovery.handle_failure(
                            job.job_id, result.company, result.error, result.attempt_number
                        )
                        
                        if recovery_action.should_retry:
                            # Queue for retry with backoff
                            await self._schedule_retry(job, result.company, recovery_action.delay)
                        else:
                            await self.result_manager.store_failure(job.job_id, result)
                    
                    # Update progress and save checkpoint
                    await self.progress_tracker.update_progress(
                        job.job_id,
                        processed_count,
                        failed_count,
                        result.company.name,
                        result.processing_time,
                        result.cost_incurred
                    )
                    
                    # Periodic checkpoint saving
                    if (processed_count + failed_count) % job.configuration.checkpoint_interval == 0:
                        await self.job_manager.save_checkpoint(job.job_id)
            
            # Finalize batch job
            await self._finalize_batch_job(job.job_id, processed_count, failed_count)
            
        except Exception as e:
            await self.job_manager.update_job_status(job.job_id, BatchJobStatus.FAILED, str(e))
            await self.progress_port.report_error(job.job_id, f"Batch processing failed: {str(e)}")
            raise
    
    async def _process_companies_concurrently(
        self, 
        job: BatchJob, 
        context: ConcurrencyContext
    ) -> AsyncIterator[CompanyProcessingResult]:
        """
        Process companies with intelligent concurrency management and adaptive scaling.
        This is where the sophisticated concurrency logic manages multiple AI operations
        while respecting rate limits and system resources.
        """
        
        # Create processing tasks with semaphore-controlled concurrency
        processing_tasks = []
        
        for company in job.companies:
            # Check if company was already processed (resume scenario)
            if await self.result_manager.is_company_processed(job.job_id, company.name):
                continue
            
            # Acquire processing slot with rate limiting
            task = asyncio.create_task(
                self._process_single_company_with_concurrency(job, company, context)
            )
            processing_tasks.append(task)
            
            # Implement batch size limits to prevent memory issues
            if len(processing_tasks) >= job.configuration.batch_size:
                # Process current batch and yield results
                completed_results = await asyncio.gather(*processing_tasks, return_exceptions=True)
                
                for result in completed_results:
                    if isinstance(result, Exception):
                        # Handle task-level exceptions
                        yield CompanyProcessingResult.create_error_result(company, result)
                    else:
                        yield result
                
                processing_tasks.clear()
        
        # Process remaining tasks
        if processing_tasks:
            completed_results = await asyncio.gather(*processing_tasks, return_exceptions=True)
            for result in completed_results:
                if not isinstance(result, Exception):
                    yield result
    
    async def _process_single_company_with_concurrency(
        self,
        job: BatchJob,
        company: CompanyInput,
        context: ConcurrencyContext
    ) -> CompanyProcessingResult:
        """
        Process a single company within the concurrency-controlled environment.
        This method integrates our existing research use case with batch-specific
        error handling and progress tracking.
        """
        
        start_time = datetime.utcnow()
        attempt_number = await self.failure_recovery.get_attempt_number(job.job_id, company.name)
        
        try:
            # Acquire concurrency slot with rate limiting
            async with context.acquire_processing_slot("research") as slot:
                
                # Use existing research use case - maintains identical processing logic
                research_result = await self.research_company.execute(
                    company_name=company.name,
                    website=company.website,
                    config_overrides=job.configuration.research_config_overrides
                )
                
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                cost_incurred = await self._calculate_operation_cost(research_result)
                
                return CompanyProcessingResult(
                    company=company,
                    result=research_result,
                    success=True,
                    processing_time=processing_time,
                    cost_incurred=cost_incurred,
                    attempt_number=attempt_number
                )
                
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return CompanyProcessingResult(
                company=company,
                error=e,
                success=False,
                processing_time=processing_time,
                cost_incurred=0.0,
                attempt_number=attempt_number
            )
```

This implementation demonstrates several critical concepts. First, we maintain clean separation between batch orchestration and core business logic by delegating to existing use cases. Second, we implement sophisticated concurrency management that adapts to system conditions. Third, we handle failures gracefully with classification and retry logic.

The key insight here is that batch processing isn't just about running operations in parallel. It's about intelligent resource management, comprehensive error handling, and maintaining data consistency across potentially thousands of operations. Our implementation ensures that each company receives the same high-quality processing as individual operations while optimizing for throughput and reliability.

### Intelligent Concurrency and Rate Limiting (12 minutes)

Now let's implement the sophisticated concurrency management system that makes our batch processing both fast and reliable. This is one of the most complex parts of the system because it needs to balance multiple competing concerns: API rate limits, system resources, and processing speed.

```python
# v2/src/core/use_cases/batch/concurrency_controller.py

import asyncio
from typing import Dict, Optional, AsyncContextManager
from datetime import datetime, timedelta
import time
from dataclasses import dataclass
from contextlib import asynccontextmanager

from ...entities.batch import BatchConfiguration
from ...ports.monitoring import ResourceMonitorPort

@dataclass
class RateLimit:
    requests_per_minute: int
    requests_per_hour: int
    burst_allowance: int = 10

class AdaptiveRateLimiter:
    """
    Intelligent rate limiter that adapts to API response patterns and error rates.
    Goes beyond simple token bucket to implement predictive rate limiting.
    """
    
    def __init__(self, rate_limit: RateLimit):
        self.rate_limit = rate_limit
        self.request_history: List[datetime] = []
        self.error_history: List[datetime] = []
        self.adaptive_delay = 0.0
        self.success_rate_threshold = 0.95
        
    async def acquire(self) -> None:
        """
        Acquire permission to make a request with intelligent adaptive delays.
        This method implements sophisticated logic to prevent API abuse while
        maximizing throughput based on observed performance patterns.
        """
        
        current_time = datetime.utcnow()
        
        # Clean old request history (older than 1 hour)
        cutoff_time = current_time - timedelta(hours=1)
        self.request_history = [req_time for req_time in self.request_history if req_time > cutoff_time]
        self.error_history = [err_time for err_time in self.error_history if err_time > cutoff_time]
        
        # Check hourly limit
        if len(self.request_history) >= self.rate_limit.requests_per_hour:
            sleep_time = self._calculate_hourly_reset_time()
            await asyncio.sleep(sleep_time)
        
        # Check per-minute limit with burst handling
        minute_cutoff = current_time - timedelta(minutes=1)
        recent_requests = [req for req in self.request_history if req > minute_cutoff]
        
        if len(recent_requests) >= self.rate_limit.requests_per_minute:
            # Calculate adaptive delay based on success rate
            base_delay = 60.0 / self.rate_limit.requests_per_minute
            success_rate = self._calculate_recent_success_rate()
            
            if success_rate < self.success_rate_threshold:
                # Increase delay when seeing errors
                self.adaptive_delay = min(self.adaptive_delay * 1.5, base_delay * 3)
            else:
                # Gradually reduce delay when operations are successful
                self.adaptive_delay = max(self.adaptive_delay * 0.9, base_delay)
            
            await asyncio.sleep(self.adaptive_delay)
        
        # Record this request
        self.request_history.append(current_time)
    
    async def record_error(self) -> None:
        """Record an API error for adaptive rate limiting calculations"""
        self.error_history.append(datetime.utcnow())
        
        # Implement immediate backoff for consecutive errors
        recent_errors = [err for err in self.error_history if err > datetime.utcnow() - timedelta(minutes=5)]
        if len(recent_errors) >= 3:
            # Exponential backoff for consecutive errors
            backoff_time = min(2 ** len(recent_errors), 60)
            await asyncio.sleep(backoff_time)

class ConcurrencyController:
    """
    Advanced concurrency management with adaptive scaling and resource monitoring.
    This is the brain of our batch processing system that ensures optimal
    performance while preventing system overload and API abuse.
    """
    
    def __init__(
        self,
        resource_monitor: ResourceMonitorPort,
        api_rate_limits: Dict[str, RateLimit]
    ):
        self.resource_monitor = resource_monitor
        self.rate_limiters = {
            service: AdaptiveRateLimiter(limit) 
            for service, limit in api_rate_limits.items()
        }
        self.active_semaphores: Dict[str, asyncio.Semaphore] = {}
        self.performance_history: List[PerformanceSnapshot] = []
        
    @asynccontextmanager
    async def create_batch_context(self, max_concurrency: int) -> AsyncContextManager['ConcurrencyContext']:
        """
        Create a batch processing context with intelligent concurrency management.
        This context manages the entire lifecycle of concurrent operations
        with adaptive scaling based on system performance.
        """
        
        # Initialize semaphore for this batch
        semaphore = asyncio.Semaphore(max_concurrency)
        context = ConcurrencyContext(
            semaphore=semaphore,
            rate_limiters=self.rate_limiters,
            resource_monitor=self.resource_monitor,
            performance_tracker=self
        )
        
        # Start performance monitoring
        monitoring_task = asyncio.create_task(self._monitor_performance(context))
        
        try:
            yield context
        finally:
            # Clean up monitoring
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_performance(self, context: 'ConcurrencyContext') -> None:
        """
        Continuously monitor system performance and adjust concurrency accordingly.
        This implements adaptive scaling that responds to system load and API performance.
        """
        
        while True:
            try:
                # Collect performance metrics
                cpu_usage = await self.resource_monitor.get_cpu_usage()
                memory_usage = await self.resource_monitor.get_memory_usage()
                api_response_time = await self._measure_api_response_time()
                error_rate = await self._calculate_current_error_rate()
                
                # Create performance snapshot
                snapshot = PerformanceSnapshot(
                    timestamp=datetime.utcnow(),
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    api_response_time=api_response_time,
                    error_rate=error_rate,
                    active_operations=context.get_active_operation_count()
                )
                
                self.performance_history.append(snapshot)
                
                # Implement adaptive scaling logic
                if cpu_usage > 0.85 or memory_usage > 0.90:
                    # System under stress - reduce concurrency
                    await context.reduce_concurrency(factor=0.8)
                elif error_rate > 0.1:
                    # High API error rate - back off aggressively
                    await context.reduce_concurrency(factor=0.6)
                elif api_response_time > 10.0:
                    # Slow API responses - reduce load
                    await context.reduce_concurrency(factor=0.7)
                elif self._performance_is_stable():
                    # System performing well - gradually increase concurrency
                    await context.increase_concurrency(factor=1.1, max_limit=50)
                
                # Clean old performance history
                cutoff_time = datetime.utcnow() - timedelta(minutes=30)
                self.performance_history = [
                    snapshot for snapshot in self.performance_history 
                    if snapshot.timestamp > cutoff_time
                ]
                
                await asyncio.sleep(5)  # Monitor every 5 seconds
                
            except Exception as e:
                # Performance monitoring should never crash the batch
                print(f"Performance monitoring error: {e}")
                await asyncio.sleep(10)

class ConcurrencyContext:
    """
    Context manager for individual batch operations that provides access to
    concurrency control and performance monitoring within the batch scope.
    """
    
    def __init__(
        self,
        semaphore: asyncio.Semaphore,
        rate_limiters: Dict[str, AdaptiveRateLimiter],
        resource_monitor: ResourceMonitorPort,
        performance_tracker: ConcurrencyController
    ):
        self.semaphore = semaphore
        self.rate_limiters = rate_limiters
        self.resource_monitor = resource_monitor
        self.performance_tracker = performance_tracker
        self.active_operations = 0
        self.operation_lock = asyncio.Lock()
        
    @asynccontextmanager
    async def acquire_processing_slot(self, operation_type: str) -> AsyncContextManager['ProcessingSlot']:
        """
        Acquire a processing slot with full concurrency and rate limiting controls.
        This is where all the sophisticated concurrency management comes together
        to ensure optimal performance without overwhelming external services.
        """
        
        # Wait for semaphore availability
        await self.semaphore.acquire()
        
        try:
            # Check system resources before proceeding
            if await self._should_throttle_for_resources():
                await asyncio.sleep(2)  # Brief resource relief
            
            # Apply rate limiting for specific operation type
            if operation_type in self.rate_limiters:
                await self.rate_limiters[operation_type].acquire()
            
            # Track active operation
            async with self.operation_lock:
                self.active_operations += 1
            
            slot = ProcessingSlot(
                operation_type=operation_type,
                rate_limiter=self.rate_limiters.get(operation_type),
                context=self
            )
            
            yield slot
            
        finally:
            # Always release semaphore and update counters
            async with self.operation_lock:
                self.active_operations -= 1
            self.semaphore.release()
    
    async def _should_throttle_for_resources(self) -> bool:
        """Check if we should throttle based on current system resources"""
        cpu_usage = await self.resource_monitor.get_cpu_usage()
        memory_usage = await self.resource_monitor.get_memory_usage()
        
        return cpu_usage > 0.8 or memory_usage > 0.85

@dataclass
class ProcessingSlot:
    """
    Represents an acquired processing slot with associated rate limiting and monitoring.
    This class encapsulates all the context needed for a single concurrent operation.
    """
    operation_type: str
    rate_limiter: Optional[AdaptiveRateLimiter]
    context: ConcurrencyContext
    start_time: datetime = datetime.utcnow()
    
    async def record_success(self):
        """Record successful operation for performance tracking"""
        if self.rate_limiter:
            # Success helps reduce adaptive delays
            pass
    
    async def record_error(self, error: Exception):
        """Record operation error for adaptive rate limiting"""
        if self.rate_limiter:
            await self.rate_limiter.record_error()
```

This concurrency management system represents enterprise-grade software engineering. We're not just limiting concurrent operations - we're implementing intelligent adaptive behavior that responds to real-world conditions. The system learns from API response patterns, adjusts to system load, and prevents cascading failures through sophisticated backoff strategies.

The key insight is that effective batch processing requires understanding the entire system ecosystem. Our concurrency controller monitors CPU usage, memory consumption, API response times, and error rates to make intelligent decisions about processing speed. This ensures reliable operation even under varying system conditions.

### Advanced Progress Tracking and Job Management (10 minutes)

Progress tracking in batch processing is significantly more complex than single operations because we need to provide meaningful insights across potentially thousands of individual operations while predicting completion times and identifying performance trends.

```python
# v2/src/core/use_cases/batch/progress_tracker.py

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics
from collections import deque

@dataclass
class ProgressSnapshot:
    timestamp: datetime
    completed: int
    failed: int
    processing_time: float
    cost: float
    current_operation: str

@dataclass
class PerformanceAnalytics:
    average_processing_time: float
    processing_rate_trend: float  # companies per minute
    error_rate: float
    cost_efficiency: float  # cost per successful result
    bottleneck_analysis: Dict[str, Any]
    eta_prediction: Optional[datetime]
    confidence_level: float

class BatchProgressTracker:
    """
    Advanced progress tracking with predictive analytics and performance insights.
    This system provides real-time visibility into batch operations with
    intelligent prediction algorithms and comprehensive performance analysis.
    """
    
    def __init__(self, checkpoint_interval: int = 10):
        self.checkpoint_interval = checkpoint_interval
        self.job_progress: Dict[str, JobProgressState] = {}
        self.performance_analyzer = PerformanceAnalyzer()
        
    async def initialize_job(self, job_id: str, total_companies: int) -> None:
        """Initialize progress tracking for a new batch job"""
        
        self.job_progress[job_id] = JobProgressState(
            job_id=job_id,
            total_companies=total_companies,
            start_time=datetime.utcnow(),
            progress_history=deque(maxlen=1000),  # Keep last 1000 snapshots
            performance_metrics=PerformanceMetrics()
        )
    
    async def update_progress(
        self,
        job_id: str,
        completed: int,
        failed: int,
        current_company: str,
        processing_time: float,
        cost_incurred: float
    ) -> ProgressUpdate:
        """
        Update progress with comprehensive analytics and prediction updates.
        This method not only tracks progress but also analyzes performance
        trends and provides intelligent predictions about completion.
        """
        
        job_state = self.job_progress.get(job_id)
        if not job_state:
            raise ValueError(f"Job {job_id} not initialized for progress tracking")
        
        # Create progress snapshot
        snapshot = ProgressSnapshot(
            timestamp=datetime.utcnow(),
            completed=completed,
            failed=failed,
            processing_time=processing_time,
            cost=cost_incurred,
            current_operation=current_company
        )
        
        job_state.progress_history.append(snapshot)
        
        # Update cumulative metrics
        job_state.total_completed = completed
        job_state.total_failed = failed
        job_state.total_cost += cost_incurred
        job_state.last_update = datetime.utcnow()
        
        # Calculate advanced analytics
        analytics = await self.performance_analyzer.analyze_progress(job_state)
        
        # Generate progress update with predictions
        progress_update = ProgressUpdate(
            job_id=job_id,
            completion_percentage=self._calculate_completion_percentage(job_state),
            companies_remaining=job_state.total_companies - completed - failed,
            eta_prediction=analytics.eta_prediction,
            current_processing_rate=analytics.processing_rate_trend,
            cost_projection=self._project_total_cost(job_state, analytics),
            performance_insights=analytics,
            should_checkpoint=self._should_create_checkpoint(job_state)
        )
        
        # Update job state with latest analytics
        job_state.latest_analytics = analytics
        
        return progress_update
    
    async def get_detailed_status(self, job_id: str) -> DetailedJobStatus:
        """
        Get comprehensive job status with advanced analytics and insights.
        This provides everything needed for detailed progress monitoring
        and performance analysis.
        """
        
        job_state = self.job_progress.get(job_id)
        if not job_state:
            raise ValueError(f"Job {job_id} not found")
        
        analytics = job_state.latest_analytics or await self.performance_analyzer.analyze_progress(job_state)
        
        return DetailedJobStatus(
            job_id=job_id,
            total_companies=job_state.total_companies,
            completed=job_state.total_completed,
            failed=job_state.total_failed,
            in_progress=job_state.total_companies - job_state.total_completed - job_state.total_failed,
            start_time=job_state.start_time,
            elapsed_time=datetime.utcnow() - job_state.start_time,
            estimated_completion=analytics.eta_prediction,
            current_rate=analytics.processing_rate_trend,
            average_processing_time=analytics.average_processing_time,
            error_rate=analytics.error_rate,
            cost_per_company=analytics.cost_efficiency,
            total_cost_incurred=job_state.total_cost,
            projected_total_cost=self._project_total_cost(job_state, analytics),
            performance_trends=self._analyze_performance_trends(job_state),
            bottleneck_analysis=analytics.bottleneck_analysis,
            recommendations=self._generate_recommendations(job_state, analytics)
        )

class PerformanceAnalyzer:
    """
    Sophisticated performance analysis engine that provides insights into
    batch processing efficiency and identifies optimization opportunities.
    """
    
    async def analyze_progress(self, job_state: JobProgressState) -> PerformanceAnalytics:
        """
        Perform comprehensive analysis of job progress to identify trends,
        predict completion times, and detect performance issues.
        """
        
        if len(job_state.progress_history) < 3:
            # Not enough data for meaningful analysis
            return PerformanceAnalytics.create_initial_analytics()
        
        recent_snapshots = list(job_state.progress_history)[-50:]  # Last 50 updates
        
        # Calculate processing rate trend
        processing_rate = self._calculate_processing_rate_trend(recent_snapshots)
        
        # Analyze processing time patterns
        avg_processing_time = self._calculate_average_processing_time(recent_snapshots)
        
        # Calculate error rate
        error_rate = self._calculate_error_rate(recent_snapshots)
        
        # Analyze cost efficiency
        cost_efficiency = self._calculate_cost_efficiency(recent_snapshots)
        
        # Predict completion time
        eta_prediction = await self._predict_completion_time(job_state, processing_rate)
        
        # Identify bottlenecks
        bottleneck_analysis = await self._analyze_bottlenecks(recent_snapshots)
        
        # Calculate confidence in predictions
        confidence_level = self._calculate_prediction_confidence(recent_snapshots)
        
        return PerformanceAnalytics(
            average_processing_time=avg_processing_time,
            processing_rate_trend=processing_rate,
            error_rate=error_rate,
            cost_efficiency=cost_efficiency,
            bottleneck_analysis=bottleneck_analysis,
            eta_prediction=eta_prediction,
            confidence_level=confidence_level
        )
    
    def _calculate_processing_rate_trend(self, snapshots: List[ProgressSnapshot]) -> float:
        """
        Calculate the current processing rate with trend analysis.
        Uses weighted moving average to emphasize recent performance.
        """
        
        if len(snapshots) < 2:
            return 0.0
        
        # Calculate rates between consecutive snapshots
        rates = []
        for i in range(1, len(snapshots)):
            prev_snapshot = snapshots[i-1]
            curr_snapshot = snapshots[i]
            
            time_diff = (curr_snapshot.timestamp - prev_snapshot.timestamp).total_seconds() / 60.0
            if time_diff > 0:
                companies_processed = (curr_snapshot.completed + curr_snapshot.failed) - \
                                    (prev_snapshot.completed + prev_snapshot.failed)
                rate = companies_processed / time_diff
                rates.append(rate)
        
        if not rates:
            return 0.0
        
        # Use weighted moving average with more weight on recent data
        weights = [i / len(rates) for i in range(1, len(rates) + 1)]
        weighted_average = sum(rate * weight for rate, weight in zip(rates, weights)) / sum(weights)
        
        return weighted_average
    
    async def _predict_completion_time(
        self,
        job_state: JobProgressState,
        current_rate: float
    ) -> Optional[datetime]:
        """
        Predict job completion time using multiple algorithms and return
        the most reliable prediction based on current performance trends.
        """
        
        if current_rate <= 0:
            return None
        
        remaining_companies = (
            job_state.total_companies - 
            job_state.total_completed - 
            job_state.total_failed
        )
        
        if remaining_companies <= 0:
            return datetime.utcnow()  # Job should be complete
        
        # Linear prediction based on current rate
        linear_eta = datetime.utcnow() + timedelta(minutes=remaining_companies / current_rate)
        
        # Adjust for historical variance and trends
        if len(job_state.progress_history) > 10:
            # Account for rate variance
            rate_variance = self._calculate_rate_variance(job_state.progress_history)
            variance_buffer = timedelta(minutes=remaining_companies * rate_variance / current_rate)
            
            # Add confidence buffer based on prediction reliability
            confidence_factor = 1.2 if rate_variance > 0.3 else 1.1
            adjusted_eta = linear_eta + variance_buffer * confidence_factor
            
            return adjusted_eta
        
        return linear_eta
```

This progress tracking system demonstrates sophisticated real-time analytics that goes far beyond simple completion percentages. We're implementing predictive algorithms that learn from processing patterns to provide accurate completion estimates. The system identifies performance trends, detects bottlenecks, and provides actionable insights for optimization.

The key insight is that effective progress tracking in batch processing requires understanding not just what's happening now, but predicting what will happen next. Our analytics engine uses weighted moving averages, variance analysis, and trend detection to provide intelligent predictions that help users plan their work effectively.

### Failure Recovery and Result Management (10 minutes)

Our final implementation segment covers the sophisticated failure recovery system that ensures batch operations can handle real-world challenges gracefully while maintaining data integrity and providing comprehensive result analysis.

```python
# v2/src/core/use_cases/batch/failure_recovery.py

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import asyncio

class FailureCategory(Enum):
    NETWORK_ERROR = "network"
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION = "auth"
    VALIDATION = "validation"
    TIMEOUT = "timeout"
    RESOURCE_EXHAUSTION = "resource"
    UNKNOWN = "unknown"

class RecoveryAction(Enum):
    RETRY_IMMEDIATELY = "retry_now"
    RETRY_WITH_DELAY = "retry_delay"
    RETRY_WITH_BACKOFF = "retry_backoff"
    SKIP_COMPANY = "skip"
    PAUSE_BATCH = "pause"
    FAIL_BATCH = "fail"

@dataclass
class FailureClassification:
    category: FailureCategory
    is_retryable: bool
    max_retries: int
    suggested_delay: float
    recovery_action: RecoveryAction
    confidence: float

class FailureRecoveryManager:
    """
    Intelligent failure recovery system that classifies errors and implements
    sophisticated retry strategies to maximize batch completion rates while
    preventing system abuse and cascading failures.
    """
    
    def __init__(self, max_global_retries: int = 3):
        self.max_global_retries = max_global_retries
        self.failure_classifier = FailureClassifier()
        self.retry_tracker = RetryTracker()
        self.circuit_breaker = CircuitBreaker()
        
    async def handle_failure(
        self,
        job_id: str,
        company: CompanyInput,
        error: Exception,
        attempt_number: int
    ) -> RecoveryStrategy:
        """
        Analyze failure and determine optimal recovery strategy.
        This method implements sophisticated failure analysis that considers
        error patterns, system state, and historical success rates.
        """
        
        # Classify the failure
        classification = await self.failure_classifier.classify_error(error, company, attempt_number)
        
        # Check circuit breaker status
        if await self.circuit_breaker.should_trip(job_id, classification):
            return RecoveryStrategy(
                action=RecoveryAction.PAUSE_BATCH,
                delay=300,  # 5 minute pause
                reason="Circuit breaker triggered due to high failure rate"
            )
        
        # Determine retry strategy based on classification
        if classification.recovery_action == RecoveryAction.RETRY_WITH_BACKOFF:
            delay = self._calculate_exponential_backoff(attempt_number, classification.suggested_delay)
            return RecoveryStrategy(
                action=RecoveryAction.RETRY_WITH_DELAY,
                delay=delay,
                max_additional_retries=classification.max_retries - attempt_number
            )
        
        elif classification.recovery_action == RecoveryAction.RETRY_WITH_DELAY:
            return RecoveryStrategy(
                action=RecoveryAction.RETRY_WITH_DELAY,
                delay=classification.suggested_delay,
                max_additional_retries=classification.max_retries - attempt_number
            )
        
        elif classification.recovery_action == RecoveryAction.SKIP_COMPANY:
            await self.retry_tracker.mark_company_failed(job_id, company.name, classification.category)
            return RecoveryStrategy(
                action=RecoveryAction.SKIP_COMPANY,
                reason=f"Unrecoverable error: {classification.category.value}"
            )
        
        else:
            return RecoveryStrategy(
                action=classification.recovery_action,
                reason=f"Failure classification: {classification.category.value}"
            )
    
    async def analyze_batch_health(self, job_id: str) -> BatchHealthAnalysis:
        """
        Analyze overall batch health and provide recommendations for optimization.
        This comprehensive analysis helps identify systemic issues and suggests
        improvements for better batch performance.
        """
        
        failure_stats = await self.retry_tracker.get_failure_statistics(job_id)
        circuit_status = await self.circuit_breaker.get_status(job_id)
        
        # Analyze failure patterns
        failure_trends = self._analyze_failure_trends(failure_stats)
        
        # Generate health score (0-100)
        health_score = self._calculate_health_score(failure_stats, circuit_status)
        
        # Generate recommendations
        recommendations = self._generate_health_recommendations(failure_stats, failure_trends)
        
        return BatchHealthAnalysis(
            health_score=health_score,
            failure_rate=failure_stats.overall_failure_rate,
            most_common_failures=failure_stats.failure_breakdown,
            failure_trends=failure_trends,
            circuit_breaker_status=circuit_status,
            recommendations=recommendations,
            suggested_optimizations=self._suggest_optimizations(failure_stats)
        )

class FailureClassifier:
    """
    Sophisticated error classification system that uses pattern matching
    and machine learning-inspired techniques to categorize failures and
    suggest optimal recovery strategies.
    """
    
    def __init__(self):
        self.classification_patterns = self._initialize_classification_patterns()
        self.learning_history = {}
        
    async def classify_error(
        self,
        error: Exception,
        company: CompanyInput,
        attempt_number: int
    ) -> FailureClassification:
        """
        Classify an error and determine the optimal recovery strategy.
        Uses pattern matching, error analysis, and historical data to
        make intelligent decisions about how to handle each failure.
        """
        
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Network-related errors
        if any(keyword in error_message for keyword in ['connection', 'timeout', 'network', 'dns']):
            return FailureClassification(
                category=FailureCategory.NETWORK_ERROR,
                is_retryable=True,
                max_retries=3,
                suggested_delay=min(5.0 * attempt_number, 30.0),  # Progressive delay
                recovery_action=RecoveryAction.RETRY_WITH_BACKOFF,
                confidence=0.9
            )
        
        # Rate limiting errors
        elif any(keyword in error_message for keyword in ['rate limit', '429', 'too many requests']):
            return FailureClassification(
                category=FailureCategory.RATE_LIMIT,
                is_retryable=True,
                max_retries=5,
                suggested_delay=60.0 + (attempt_number * 30.0),  # Longer delays for rate limits
                recovery_action=RecoveryAction.RETRY_WITH_DELAY,
                confidence=0.95
            )
        
        # Authentication errors
        elif any(keyword in error_message for keyword in ['auth', 'unauthorized', '401', 'forbidden', '403']):
            return FailureClassification(
                category=FailureCategory.AUTHENTICATION,
                is_retryable=False,
                max_retries=0,
                suggested_delay=0.0,
                recovery_action=RecoveryAction.PAUSE_BATCH,  # Requires human intervention
                confidence=0.98
            )
        
        # Validation errors (bad company data)
        elif any(keyword in error_message for keyword in ['validation', 'invalid', 'malformed']):
            return FailureClassification(
                category=FailureCategory.VALIDATION,
                is_retryable=False,
                max_retries=0,
                suggested_delay=0.0,
                recovery_action=RecoveryAction.SKIP_COMPANY,  # Skip bad data
                confidence=0.85
            )
        
        # Timeout errors
        elif 'timeout' in error_message:
            return FailureClassification(
                category=FailureCategory.TIMEOUT,
                is_retryable=True,
                max_retries=2,
                suggested_delay=10.0 * attempt_number,
                recovery_action=RecoveryAction.RETRY_WITH_BACKOFF,
                confidence=0.8
            )
        
        # Unknown errors - conservative approach
        else:
            return FailureClassification(
                category=FailureCategory.UNKNOWN,
                is_retryable=True,
                max_retries=1,  # Conservative retry count
                suggested_delay=15.0,
                recovery_action=RecoveryAction.RETRY_WITH_DELAY,
                confidence=0.6
            )

class CircuitBreaker:
    """
    Circuit breaker pattern implementation for batch processing that prevents
    cascading failures and provides automatic recovery mechanisms.
    """
    
    def __init__(
        self,
        failure_threshold: int = 10,
        recovery_timeout: int = 300,  # 5 minutes
        minimum_operations: int = 20
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.minimum_operations = minimum_operations
        self.circuit_states: Dict[str, CircuitState] = {}
    
    async def should_trip(self, job_id: str, classification: FailureClassification) -> bool:
        """
        Determine if the circuit breaker should trip based on current failure patterns.
        This prevents batch jobs from continuing when systemic issues are detected.
        """
        
        if job_id not in self.circuit_states:
            self.circuit_states[job_id] = CircuitState()
        
        state = self.circuit_states[job_id]
        state.total_operations += 1
        
        # Record failure if applicable
        if not classification.is_retryable or classification.category == FailureCategory.AUTHENTICATION:
            state.failure_count += 1
            state.last_failure_time = datetime.utcnow()
        
        # Check if we should trip the circuit
        if (state.total_operations >= self.minimum_operations and
            state.failure_count >= self.failure_threshold):
            
            failure_rate = state.failure_count / state.total_operations
            if failure_rate > 0.5:  # 50% failure rate threshold
                state.circuit_open = True
                state.circuit_opened_time = datetime.utcnow()
                return True
        
        # Check if circuit should be reset
        if (state.circuit_open and 
            datetime.utcnow() - state.circuit_opened_time > timedelta(seconds=self.recovery_timeout)):
            
            # Reset circuit for testing
            state.circuit_open = False
            state.failure_count = 0
            state.total_operations = 0
        
        return state.circuit_open

# Result Management Implementation
class BatchResultManager:
    """
    Comprehensive result management system that aggregates individual results,
    performs quality analysis, and generates actionable insights from batch operations.
    """
    
    async def aggregate_batch_results(self, job_id: str) -> ComprehensiveBatchResults:
        """
        Aggregate all individual results into a comprehensive batch analysis.
        This method creates business intelligence insights from the processed data.
        """
        
        individual_results = await self.load_all_results(job_id)
        
        # Perform comprehensive analysis
        industry_analysis = await self._analyze_industry_distribution(individual_results)
        size_analysis = await self._analyze_company_sizes(individual_results)
        geographic_analysis = await self._analyze_geographic_distribution(individual_results)
        business_model_analysis = await self._analyze_business_models(individual_results)
        competitive_clusters = await self._identify_competitive_clusters(individual_results)
        
        # Calculate data quality metrics
        quality_metrics = await self._calculate_data_quality_metrics(individual_results)
        
        # Generate market insights
        market_insights = await self._generate_market_insights(individual_results)
        
        return ComprehensiveBatchResults(
            total_companies_processed=len(individual_results),
            successful_extractions=len([r for r in individual_results if r.success]),
            data_quality_score=quality_metrics.overall_score,
            industry_insights=industry_analysis,
            size_distribution=size_analysis,
            geographic_insights=geographic_analysis,
            business_model_patterns=business_model_analysis,
            competitive_landscape=competitive_clusters,
            market_opportunities=market_insights,
            processing_statistics=await self._calculate_processing_statistics(individual_results),
            recommendations=await self._generate_batch_recommendations(individual_results)
        )
```

This comprehensive implementation demonstrates enterprise-grade failure handling that goes far beyond simple retry logic. We're implementing intelligent error classification, circuit breaker patterns, and sophisticated result analysis that provides actionable business insights.

The key insight is that batch processing systems must be resilient to real-world conditions. Our failure recovery system learns from error patterns, prevents cascading failures, and ensures that temporary issues don't derail entire batch operations. The result management system transforms raw processing results into valuable business intelligence that users can act upon.

### Conclusion and Next Steps (8 minutes)

We've now implemented a comprehensive batch processing system that represents the pinnacle of enterprise-grade software engineering. This system demonstrates advanced concepts including intelligent concurrency management, predictive analytics, sophisticated failure recovery, and comprehensive result analysis.

The batch processing system we've built goes far beyond simple iteration over a list of companies. We've implemented adaptive scaling that responds to system conditions, predictive progress tracking that provides accurate completion estimates, and intelligent failure recovery that maximizes success rates while preventing system abuse.

Key architectural achievements include maintaining identical processing logic between single and batch operations through proper use case orchestration, implementing sophisticated concurrency control with rate limiting and resource monitoring, and providing comprehensive job management with persistence and resume capabilities.

Our failure recovery system demonstrates production-ready error handling with classification-based retry strategies, circuit breaker patterns for preventing cascading failures, and comprehensive analytics that provide insights into batch performance and optimization opportunities.

The result management system transforms individual company results into valuable business intelligence, providing industry analysis, competitive clustering, and market insights that users can act upon. This demonstrates how technical systems can create business value beyond their core functionality.

This implementation showcases advanced software engineering patterns including hexagonal architecture, dependency injection, sophisticated error handling, real-time analytics, and enterprise-grade job management. The system is designed to handle real-world challenges while maintaining high performance and reliability.

Looking ahead, this batch processing foundation enables additional advanced features like distributed processing across multiple machines, integration with workflow orchestration systems, and advanced machine learning-based optimization. The clean architecture and comprehensive error handling provide a solid foundation for scaling to handle massive datasets efficiently.

The Theodore v2 batch processing system represents a complete enterprise solution that can handle thousands of companies while maintaining the same high-quality research as individual operations. This level of sophistication is what separates professional software systems from simple scripts.

## Estimated Time: 8-9 hours

## Dependencies
- TICKET-010 (Research Company Use Case) - Core business logic for processing individual companies
- TICKET-019 (Dependency Injection Container) - Required for proper component wiring and lifecycle management
- TICKET-003 (Configuration System) - Needed for batch operation configuration and concurrency settings
- TICKET-004 (Progress Tracking Port) - Essential for real-time progress reporting during batch operations
- TICKET-026 (Observability System) - Required for batch job monitoring, metrics collection, and performance analytics

## Files to Create/Modify

### Core Implementation
- `v2/src/core/use_cases/batch_processing.py` - Main batch processing use case
- `v2/src/core/use_cases/batch/job_manager.py` - Job lifecycle and persistence management
- `v2/src/core/use_cases/batch/progress_tracker.py` - Advanced progress tracking and analytics
- `v2/src/core/use_cases/batch/failure_recovery.py` - Intelligent failure handling and retry logic
- `v2/src/core/use_cases/batch/result_aggregator.py` - Result analysis and business intelligence

### Domain Models
- `v2/src/core/domain/entities/batch_job.py` - Batch job entity with state management
- `v2/src/core/domain/entities/job_progress.py` - Progress tracking domain model
- `v2/src/core/domain/value_objects/batch_config.py` - Batch configuration value objects
- `v2/src/core/domain/value_objects/job_result.py` - Job result aggregation models

### Infrastructure Adapters
- `v2/src/infrastructure/adapters/io/csv_handler.py` - CSV input/output processing
- `v2/src/infrastructure/adapters/io/sheets_handler.py` - Google Sheets integration
- `v2/src/infrastructure/adapters/storage/job_persistence.py` - Job state persistence
- `v2/src/infrastructure/adapters/queue/batch_queue.py` - Batch job queue management

### CLI Integration
- `v2/src/cli/commands/batch.py` - Batch processing CLI commands
- `v2/src/cli/utils/batch_helpers.py` - CLI utility functions for batch operations

### Configuration & Testing
- `v2/config/batch_settings.yaml` - Default batch processing configuration
- `v2/tests/unit/use_cases/test_batch_processing.py` - Unit tests
- `v2/tests/integration/test_batch_workflows.py` - Integration tests
- `v2/tests/performance/test_batch_performance.py` - Performance and scalability tests