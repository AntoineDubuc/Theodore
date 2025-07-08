"""
Antoine Batch Processor
======================

Batch processing implementation for the antoine 4-phase pipeline that enables
parallel processing of multiple companies with resource pooling and error handling.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add parent directory to path for imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.models import CompanyData, CompanyIntelligenceConfig
from src.antoine_scraper_adapter import AntoineScraperAdapter
from src.progress_logger import start_company_processing, log_processing_phase, complete_company_processing

logger = logging.getLogger(__name__)


@dataclass
class BatchProcessingResult:
    """Result from batch processing multiple companies"""
    total_companies: int = 0
    successful: int = 0
    failed: int = 0
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    total_duration: float = 0.0
    companies_per_minute: float = 0.0
    company_results: List[CompanyData] = field(default_factory=list)
    errors: Dict[str, str] = field(default_factory=dict)
    resource_stats: Dict[str, Any] = field(default_factory=dict)


class AntoineBatchProcessor:
    """
    Batch processor for antoine pipeline with parallel company processing.
    
    This processor enables:
    - Parallel processing of multiple companies
    - Resource pooling for efficiency  
    - Progress tracking and error handling
    - Adaptive timeout management
    """
    
    def __init__(
        self,
        config: CompanyIntelligenceConfig,
        bedrock_client=None,
        max_concurrent_companies: int = 3,
        enable_resource_pooling: bool = True,
        progress_callback=None
    ):
        """
        Initialize batch processor.
        
        Args:
            config: Company intelligence configuration
            bedrock_client: Optional bedrock client for embeddings
            max_concurrent_companies: Maximum companies to process in parallel
            enable_resource_pooling: Whether to enable resource pooling optimizations
            progress_callback: Optional callback function(processed_count, message, current_company)
        """
        self.config = config
        self.bedrock_client = bedrock_client
        self.max_concurrent_companies = max_concurrent_companies
        self.enable_resource_pooling = enable_resource_pooling
        self.progress_callback = progress_callback
        
        # Thread pool for parallel company processing
        self.executor = ThreadPoolExecutor(
            max_workers=max_concurrent_companies,
            thread_name_prefix="antoine_batch"
        )
        
        # Semaphore for controlling concurrency
        self.semaphore = threading.Semaphore(max_concurrent_companies)
        
        # Resource pools (if enabled)
        self.scraper_pool = []
        self.pool_lock = threading.Lock()
        
        # Statistics tracking
        self.stats = {
            'companies_processed': 0,
            'total_api_calls': 0,
            'total_pages_crawled': 0,
            'total_processing_time': 0.0
        }
        
        logger.info(f"Antoine batch processor initialized with {max_concurrent_companies} concurrent companies")
    
    def _get_scraper(self) -> AntoineScraperAdapter:
        """Get a scraper instance from pool or create new one"""
        if self.enable_resource_pooling and self.scraper_pool:
            with self.pool_lock:
                if self.scraper_pool:
                    return self.scraper_pool.pop()
        
        # Create new scraper
        return AntoineScraperAdapter(self.config, self.bedrock_client)
    
    def _return_scraper(self, scraper: AntoineScraperAdapter):
        """Return scraper to pool for reuse"""
        if self.enable_resource_pooling:
            with self.pool_lock:
                if len(self.scraper_pool) < self.max_concurrent_companies:
                    self.scraper_pool.append(scraper)
    
    def _process_single_company(
        self,
        company_data: Dict[str, str],
        batch_job_id: str
    ) -> Tuple[CompanyData, Optional[str]]:
        """
        Process a single company with error handling.
        
        Args:
            company_data: Dictionary with 'name' and 'website' keys
            batch_job_id: Batch job ID for tracking
            
        Returns:
            Tuple of (CompanyData result, error message if any)
        """
        company_name = company_data.get('name', 'Unknown')
        website = company_data.get('website', '')
        
        # Acquire semaphore
        with self.semaphore:
            logger.info(f"🏢 Processing {company_name} in batch")
            
            # Start progress tracking
            job_id = start_company_processing(company_name)
            
            # Get scraper from pool
            scraper = self._get_scraper()
            
            try:
                # Create CompanyData object
                company = CompanyData(name=company_name, website=website)
                
                # Process using antoine pipeline
                start_time = time.time()
                result = scraper.scrape_company(company, job_id=job_id)
                duration = time.time() - start_time
                
                # Update statistics
                self.stats['companies_processed'] += 1
                self.stats['total_processing_time'] += duration
                
                if result.scrape_status == "success":
                    self.stats['total_pages_crawled'] += len(result.pages_crawled or [])
                    logger.info(f"✅ {company_name} processed successfully in {duration:.1f}s")
                    complete_company_processing(job_id, "completed")
                    return result, None
                else:
                    error_msg = f"Scraping failed: {result.scrape_error}"
                    logger.warning(f"❌ {company_name} failed: {error_msg}")
                    complete_company_processing(job_id, "failed")
                    return result, error_msg
                    
            except Exception as e:
                error_msg = f"Exception: {str(e)}"
                logger.error(f"💥 Error processing {company_name}: {error_msg}")
                complete_company_processing(job_id, "failed")
                
                # Create failed result
                company = CompanyData(name=company_name, website=website)
                company.scrape_status = "failed"
                company.scrape_error = error_msg
                return company, error_msg
                
            finally:
                # Return scraper to pool
                self._return_scraper(scraper)
    
    def process_batch(
        self,
        companies: List[Dict[str, str]],
        batch_name: str = "batch"
    ) -> BatchProcessingResult:
        """
        Process a batch of companies in parallel.
        
        Args:
            companies: List of company dictionaries with 'name' and 'website' keys
            batch_name: Name for this batch (for tracking)
            
        Returns:
            BatchProcessingResult with processing statistics
        """
        logger.info(f"📦 Starting batch processing of {len(companies)} companies")
        
        # Initialize result
        result = BatchProcessingResult(total_companies=len(companies))
        batch_job_id = f"antoine_batch_{int(time.time())}"
        
        # Reset statistics
        self.stats = {
            'companies_processed': 0,
            'total_api_calls': 0,
            'total_pages_crawled': 0,
            'total_processing_time': 0.0
        }
        
        # Submit all companies to thread pool
        futures = {}
        for company in companies:
            future = self.executor.submit(
                self._process_single_company,
                company,
                batch_job_id
            )
            futures[future] = company
        
        # Process results as they complete
        processed_count = 0
        for future in as_completed(futures):
            company_info = futures[future]
            company_name = company_info.get('name', 'Unknown')
            
            try:
                company_result, error = future.result()
                result.company_results.append(company_result)
                
                if error:
                    result.failed += 1
                    result.errors[company_name] = error
                else:
                    result.successful += 1
                
                # Update progress
                processed_count += 1
                if self.progress_callback:
                    status_msg = "✅ Completed" if not error else f"❌ Failed: {error}"
                    self.progress_callback(
                        processed_count, 
                        f"{status_msg} {company_name} ({processed_count}/{result.total_companies})",
                        company_name
                    )
                    
            except Exception as e:
                logger.error(f"Failed to get result for {company_name}: {e}")
                result.failed += 1
                result.errors[company_name] = str(e)
                
                # Update progress for failures too
                processed_count += 1
                if self.progress_callback:
                    self.progress_callback(
                        processed_count,
                        f"❌ Failed {company_name}: {str(e)} ({processed_count}/{result.total_companies})",
                        company_name
                    )
        
        # Calculate final statistics
        result.end_time = datetime.utcnow()
        result.total_duration = (result.end_time - result.start_time).total_seconds()
        
        if result.total_duration > 0:
            result.companies_per_minute = (result.successful / result.total_duration) * 60
        
        result.resource_stats = {
            'total_pages_crawled': self.stats['total_pages_crawled'],
            'avg_pages_per_company': self.stats['total_pages_crawled'] / max(result.successful, 1),
            'avg_seconds_per_company': self.stats['total_processing_time'] / max(result.successful, 1),
            'parallel_efficiency': self.stats['total_processing_time'] / max(result.total_duration, 1)
        }
        
        logger.info(f"📊 Batch processing completed:")
        logger.info(f"   Total: {result.total_companies}")
        logger.info(f"   Successful: {result.successful}")
        logger.info(f"   Failed: {result.failed}")
        logger.info(f"   Duration: {result.total_duration:.1f}s")
        logger.info(f"   Throughput: {result.companies_per_minute:.1f} companies/minute")
        logger.info(f"   Parallel efficiency: {result.resource_stats['parallel_efficiency']:.1%}")
        
        return result
    
    def process_batch_async(
        self,
        companies: List[Dict[str, str]],
        batch_name: str = "batch"
    ) -> BatchProcessingResult:
        """
        Async wrapper for batch processing.
        
        This allows the batch processor to be used in async contexts.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run batch processing in executor to avoid blocking
            future = loop.run_in_executor(
                None,
                self.process_batch,
                companies,
                batch_name
            )
            return loop.run_until_complete(future)
        finally:
            loop.close()
    
    def shutdown(self):
        """Shutdown the batch processor and cleanup resources"""
        logger.info("Shutting down antoine batch processor")
        self.executor.shutdown(wait=True)
        
        # Clear resource pools
        with self.pool_lock:
            self.scraper_pool.clear()