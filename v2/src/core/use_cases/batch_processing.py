"""
Batch Processing Use Case for Theodore v2.

Provides comprehensive batch processing capabilities for company research
with job management, progress tracking, and intelligent concurrency control.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncIterator, Callable
from datetime import datetime, timezone

from ..domain.entities.batch_job import (
    BatchJob, BatchJobStatus, BatchJobType, BatchProgress, 
    BatchResultSummary, BatchInputSource, BatchOutputDestination
)
from ..use_cases.research_company import ResearchCompanyUseCase
from ..use_cases.discover_similar import DiscoverSimilarCompaniesUseCase
from ..use_cases.base import BaseUseCase

logger = logging.getLogger(__name__)


class BatchInputProcessor:
    """Processes various input sources for batch operations"""
    
    async def read_companies_from_csv(self, file_path: str) -> AsyncIterator[Dict[str, Any]]:
        """Read companies from CSV file with schema detection"""
        import aiofiles
        import csv
        from io import StringIO
        
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                content = await file.read()
                
            # Parse CSV content
            csv_reader = csv.DictReader(StringIO(content))
            
            for row in csv_reader:
                # Auto-detect company name and website columns
                company_data = self._normalize_company_row(row)
                if company_data:
                    yield company_data
                    
        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {e}")
            raise
    
    def _normalize_company_row(self, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize CSV row to extract company information"""
        # Common column name patterns
        name_columns = ['name', 'company', 'company_name', 'company name', 'business_name']
        website_columns = ['website', 'url', 'domain', 'web', 'site', 'homepage']
        
        company_name = None
        website = None
        
        # Find company name
        for col in name_columns:
            for key in row.keys():
                if key.lower().strip() == col:
                    company_name = row[key]
                    break
            if company_name:
                break
        
        # Find website
        for col in website_columns:
            for key in row.keys():
                if key.lower().strip() == col:
                    website = row[key]
                    break
            if website:
                break
        
        if not company_name:
            return None
        
        return {
            'company_name': company_name.strip(),
            'website': website.strip() if website else None,
            'original_row': row
        }


class BatchOutputProcessor:
    """Handles various output formats for batch results"""
    
    async def write_results_to_csv(
        self, 
        results: List[Dict[str, Any]], 
        file_path: str,
        include_metadata: bool = True
    ) -> None:
        """Write batch results to CSV file"""
        import aiofiles
        import csv
        from io import StringIO
        
        if not results:
            return
        
        # Determine CSV columns
        fieldnames = self._get_csv_fieldnames(results, include_metadata)
        
        # Write to string buffer first
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            flattened_row = self._flatten_result_for_csv(result, include_metadata)
            writer.writerow(flattened_row)
        
        # Write to file
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
            await file.write(output.getvalue())
    
    def _get_csv_fieldnames(self, results: List[Dict[str, Any]], include_metadata: bool) -> List[str]:
        """Determine CSV column names from results"""
        fieldnames = ['company_name', 'website', 'status']
        
        # Add company data fields
        if results and 'company_data' in results[0]:
            sample_data = results[0]['company_data']
            if sample_data:
                # Add key company fields
                company_fields = [
                    'industry', 'description', 'founding_year', 'employee_count',
                    'headquarters_location', 'business_model', 'value_proposition'
                ]
                fieldnames.extend(company_fields)
        
        if include_metadata:
            metadata_fields = [
                'processing_time', 'cost', 'confidence_score', 'data_quality_score', 'error_message'
            ]
            fieldnames.extend(metadata_fields)
        
        return fieldnames
    
    def _flatten_result_for_csv(self, result: Dict[str, Any], include_metadata: bool) -> Dict[str, Any]:
        """Flatten complex result structure for CSV output"""
        flattened = {
            'company_name': result.get('company_name', ''),
            'website': result.get('website', ''),
            'status': result.get('status', '')
        }
        
        # Add company data
        company_data = result.get('company_data')
        if company_data:
            flattened.update({
                'industry': getattr(company_data, 'industry', ''),
                'description': getattr(company_data, 'description', ''),
                'founding_year': getattr(company_data, 'founding_year', ''),
                'employee_count': getattr(company_data, 'employee_count', ''),
                'headquarters_location': getattr(company_data, 'headquarters_location', ''),
                'business_model': getattr(company_data, 'business_model', ''),
                'value_proposition': getattr(company_data, 'value_proposition', '')
            })
        
        if include_metadata:
            flattened.update({
                'processing_time': result.get('processing_time', ''),
                'cost': result.get('cost', ''),
                'confidence_score': result.get('confidence_score', ''),
                'data_quality_score': result.get('data_quality_score', ''),
                'error_message': result.get('error_message', '')
            })
        
        return flattened


class ConcurrencyController:
    """Controls concurrent execution with rate limiting and resource management"""
    
    def __init__(self, max_concurrent: int = 5, rate_limit_per_minute: int = 60):
        self.max_concurrent = max_concurrent
        self.rate_limit_per_minute = rate_limit_per_minute
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.request_times: List[float] = []
        
    async def acquire_slot(self) -> None:
        """Acquire a processing slot with rate limiting"""
        # Wait for semaphore
        await self.semaphore.acquire()
        
        # Apply rate limiting
        await self._enforce_rate_limit()
    
    def release_slot(self) -> None:
        """Release a processing slot"""
        self.semaphore.release()
    
    async def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting based on recent requests"""
        current_time = time.time()
        
        # Clean old request times (older than 1 minute)
        cutoff_time = current_time - 60
        self.request_times = [t for t in self.request_times if t > cutoff_time]
        
        # Check if we're hitting rate limit
        if len(self.request_times) >= self.rate_limit_per_minute:
            # Calculate delay needed
            oldest_request = min(self.request_times)
            delay = 60 - (current_time - oldest_request) + 1  # Add 1 second buffer
            if delay > 0:
                await asyncio.sleep(delay)
        
        # Record this request time
        self.request_times.append(current_time)


class BatchProcessingUseCase(BaseUseCase):
    """
    Main batch processing use case for Theodore v2.
    
    Provides comprehensive batch processing capabilities including:
    - Multi-format input/output support
    - Job persistence and resumption
    - Progress tracking and analytics
    - Intelligent concurrency control
    - Error handling and recovery
    """
    
    def __init__(
        self,
        research_use_case: ResearchCompanyUseCase,
        discovery_use_case: DiscoverSimilarCompaniesUseCase,
        progress_tracker=None
    ):
        super().__init__(progress_tracker)
        self.research_use_case = research_use_case
        self.discovery_use_case = discovery_use_case
        self.input_processor = BatchInputProcessor()
        self.output_processor = BatchOutputProcessor()
        self.active_jobs: Dict[str, BatchJob] = {}
    
    async def execute(self, request) -> None:
        """Execute method required by BaseUseCase (not used in batch processing)"""
        # This method is required by the abstract base class but not used
        # in batch processing as we have specific methods for different operations
        pass
        
    async def start_batch_research(
        self,
        input_source: BatchInputSource,
        output_destination: BatchOutputDestination,
        job_name: Optional[str] = None,
        **config_kwargs
    ) -> BatchJob:
        """Start a new batch research job"""
        
        # Count total companies first
        total_companies = await self._count_companies_in_source(input_source)
        
        # Create batch job
        job = BatchJob(
            job_name=job_name,
            job_type=BatchJobType.RESEARCH,
            input_source=input_source,
            output_destination=output_destination,
            progress=BatchProgress(total_companies=total_companies)
        )
        
        # Update configuration
        for key, value in config_kwargs.items():
            if hasattr(job.configuration, key):
                setattr(job.configuration, key, value)
        
        # Total companies already set during job creation
        
        # Store active job
        self.active_jobs[job.job_id] = job
        
        # Start processing
        asyncio.create_task(self._execute_batch_research(job))
        
        return job
    
    async def _count_companies_in_source(self, input_source: BatchInputSource) -> int:
        """Count total companies in input source"""
        count = 0
        
        if input_source.type.value == "csv_file":
            async for _ in self.input_processor.read_companies_from_csv(input_source.path):
                count += 1
        
        return count
    
    async def _execute_batch_research(self, job: BatchJob) -> None:
        """Execute batch research processing"""
        try:
            job.start_job()
            await self._emit_progress("batch_research", "started", 0, f"Starting batch job {job.job_id}")
            
            # Initialize concurrency controller
            concurrency_controller = ConcurrencyController(
                max_concurrent=job.configuration.max_concurrent,
                rate_limit_per_minute=job.configuration.rate_limit_per_minute
            )
            
            # Process companies
            results = []
            company_tasks = []
            
            # Read companies from input source
            if job.input_source.type.value == "csv_file":
                async for company_data in self.input_processor.read_companies_from_csv(job.input_source.path):
                    # Create processing task
                    task = asyncio.create_task(
                        self._process_single_company(
                            job, company_data, concurrency_controller
                        )
                    )
                    company_tasks.append(task)
                    
                    # Process in batches to avoid memory issues
                    if len(company_tasks) >= job.configuration.max_concurrent * 2:
                        batch_results = await asyncio.gather(*company_tasks, return_exceptions=True)
                        results.extend([r for r in batch_results if not isinstance(r, Exception)])
                        company_tasks = []
                        
                        # Create checkpoint if needed
                        if job.should_checkpoint():
                            await self._create_checkpoint(job)
            
            # Process remaining tasks
            if company_tasks:
                batch_results = await asyncio.gather(*company_tasks, return_exceptions=True)
                results.extend([r for r in batch_results if not isinstance(r, Exception)])
            
            # Save results
            await self._save_batch_results(job, results)
            
            # Complete job
            result_summary = self._create_result_summary(job, results)
            job.complete_job(result_summary)
            
            await self._emit_progress("batch_research", "completed", 100, f"Batch job {job.job_id} completed")
            
        except Exception as e:
            logger.error(f"Batch job {job.job_id} failed: {e}")
            job.fail_job(str(e))
            await self._emit_progress("batch_research", "failed", 0, f"Batch job {job.job_id} failed: {e}")
        
        finally:
            # Clean up active job
            if job.job_id in self.active_jobs:
                del self.active_jobs[job.job_id]
    
    async def _process_single_company(
        self,
        job: BatchJob,
        company_data: Dict[str, Any],
        concurrency_controller: ConcurrencyController
    ) -> Dict[str, Any]:
        """Process a single company within the batch"""
        
        company_name = company_data['company_name']
        start_time = time.time()
        
        try:
            # Acquire processing slot
            await concurrency_controller.acquire_slot()
            
            try:
                # Update current company in progress
                job.progress.current_company = company_name
                job.progress.processing_companies += 1
                
                # Perform research
                company_result = await self.research_use_case.execute(
                    company_name=company_name,
                    website=company_data.get('website'),
                    timeout=job.configuration.timeout_per_company
                )
                
                processing_time = time.time() - start_time
                
                # Record success
                job.add_processed_company(company_name, success=True)
                job.progress.processing_companies -= 1
                
                # Update performance metrics
                self._update_performance_metrics(job, processing_time)
                
                result = {
                    'company_name': company_name,
                    'website': company_data.get('website'),
                    'status': 'success',
                    'company_data': company_result.company_data,
                    'processing_time': processing_time,
                    'cost': getattr(company_result, 'cost', 0),
                    'confidence_score': getattr(company_result, 'confidence_score', 0),
                    'data_quality_score': getattr(company_result.company_data, 'data_quality_score', 0) if company_result.company_data else 0,
                    'original_row': company_data.get('original_row', {})
                }
                
                return result
                
            finally:
                concurrency_controller.release_slot()
                
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Record failure
            job.add_processed_company(company_name, success=False)
            job.add_error(company_name, type(e).__name__, str(e))
            job.progress.processing_companies -= 1
            
            logger.warning(f"Failed to process company {company_name}: {e}")
            
            result = {
                'company_name': company_name,
                'website': company_data.get('website'),
                'status': 'failed',
                'error_message': str(e),
                'processing_time': processing_time,
                'original_row': company_data.get('original_row', {})
            }
            
            return result
    
    def _update_performance_metrics(self, job: BatchJob, processing_time: float) -> None:
        """Update job performance metrics"""
        # Update average processing time
        total_processed = job.progress.completed_companies + job.progress.failed_companies
        if total_processed > 0:
            job.progress.average_processing_time = (
                (job.progress.average_processing_time * (total_processed - 1) + processing_time) / total_processed
            )
        
        # Update processing rate (companies per minute)
        if job.started_at:
            elapsed_minutes = (datetime.now(timezone.utc) - job.started_at).total_seconds() / 60
            if elapsed_minutes > 0:
                job.progress.processing_rate = total_processed / elapsed_minutes
    
    async def _create_checkpoint(self, job: BatchJob) -> None:
        """Create a checkpoint for job state"""
        checkpoint_data = job.create_checkpoint()
        # Here you would typically save to persistent storage
        logger.info(f"Created checkpoint for job {job.job_id} at {checkpoint_data['timestamp']}")
    
    async def _save_batch_results(self, job: BatchJob, results: List[Dict[str, Any]]) -> None:
        """Save batch processing results to output destination"""
        if job.output_destination.type.value == "csv_file":
            await self.output_processor.write_results_to_csv(
                results,
                job.output_destination.path,
                include_metadata=job.configuration.include_metadata
            )
        
        logger.info(f"Saved {len(results)} results for job {job.job_id}")
    
    def _create_result_summary(self, job: BatchJob, results: List[Dict[str, Any]]) -> BatchResultSummary:
        """Create comprehensive result summary"""
        successful_results = len([r for r in results if r.get('status') == 'success'])
        failed_results = len([r for r in results if r.get('status') == 'failed'])
        
        # Calculate performance metrics
        total_processing_time = job.execution_time or 0
        average_processing_time = job.progress.average_processing_time
        peak_processing_rate = job.progress.processing_rate
        
        # Calculate costs
        total_cost = sum(r.get('cost', 0) for r in results if r.get('cost'))
        cost_per_company = total_cost / len(results) if results else 0
        
        # Calculate quality scores
        quality_scores = [r.get('data_quality_score', 0) for r in results if r.get('data_quality_score')]
        data_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        completeness_score = successful_results / len(results) if results else 0
        
        # Error analysis
        error_categories = job.progress.errors_by_type.copy()
        most_common_errors = sorted(
            error_categories.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        return BatchResultSummary(
            total_processed=len(results),
            successful_results=successful_results,
            failed_results=failed_results,
            skipped_results=job.progress.skipped_companies,
            total_processing_time=total_processing_time,
            average_processing_time=average_processing_time,
            peak_processing_rate=peak_processing_rate,
            total_cost=total_cost,
            cost_per_company=cost_per_company,
            data_quality_score=data_quality_score,
            completeness_score=completeness_score,
            error_categories=error_categories,
            most_common_errors=[error[0] for error in most_common_errors]
        )
    
    async def get_job_status(self, job_id: str) -> Optional[BatchJob]:
        """Get current status of a batch job"""
        return self.active_jobs.get(job_id)
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a batch job"""
        job = self.active_jobs.get(job_id)
        if job and not job.is_terminal:
            job.cancel_job()
            return True
        return False
    
    async def pause_job(self, job_id: str) -> bool:
        """Pause a running batch job"""
        job = self.active_jobs.get(job_id)
        if job and job.status == BatchJobStatus.RUNNING:
            job.pause_job()
            return True
        return False
    
    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused batch job"""
        job = self.active_jobs.get(job_id)
        if job and job.can_resume:
            job.resume_job()
            # Restart processing
            asyncio.create_task(self._execute_batch_research(job))
            return True
        return False
    
    def list_active_jobs(self) -> List[BatchJob]:
        """List all currently active batch jobs"""
        return list(self.active_jobs.values())