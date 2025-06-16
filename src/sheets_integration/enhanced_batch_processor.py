"""
Enhanced batch processor with improved error handling, retry logic, and adaptive timeouts
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
from dataclasses import dataclass
from enum import Enum

from ..models import CompanyData
from ..main_pipeline import TheodoreIntelligencePipeline
from .google_sheets_service_client import GoogleSheetsServiceClient

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Classification of error types for smart retry logic"""
    TIMEOUT = "timeout"
    SSL_ERROR = "ssl_error"
    CONNECTION_ERROR = "connection_error"
    RATE_LIMIT = "rate_limit"
    PROTECTED_SITE = "protected_site"
    PARSING_ERROR = "parsing_error"
    UNKNOWN = "unknown"


@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_retries: int = 3
    base_backoff: float = 2.0
    max_backoff: float = 60.0
    jitter: bool = True
    retry_on: List[ErrorType] = None
    
    def __post_init__(self):
        if self.retry_on is None:
            self.retry_on = [
                ErrorType.TIMEOUT,
                ErrorType.SSL_ERROR,
                ErrorType.CONNECTION_ERROR,
                ErrorType.RATE_LIMIT
            ]


@dataclass
class TimeoutConfig:
    """Adaptive timeout configuration"""
    default: int = 30
    simple_sites: int = 20
    complex_sites: int = 60
    max_timeout: int = 120
    increase_factor: float = 1.5
    
    def get_timeout(self, attempt: int = 0, is_complex: bool = False) -> int:
        """Get timeout based on attempt number and site complexity"""
        if is_complex:
            base = self.complex_sites
        else:
            base = self.default
        
        # Increase timeout with each retry
        timeout = min(base * (self.increase_factor ** attempt), self.max_timeout)
        return int(timeout)


class EnhancedBatchProcessor:
    """Enhanced batch processor with retry logic and better error handling"""
    
    def __init__(
        self,
        sheets_client: GoogleSheetsServiceClient,
        pipeline: Optional[TheodoreIntelligencePipeline] = None,
        concurrency: int = 3,
        max_companies_to_process: Optional[int] = None,
        retry_config: Optional[RetryConfig] = None,
        timeout_config: Optional[TimeoutConfig] = None
    ):
        self.sheets_client = sheets_client
        self.pipeline = pipeline
        self.concurrency = concurrency
        self.max_companies_to_process = max_companies_to_process
        self.retry_config = retry_config or RetryConfig()
        self.timeout_config = timeout_config or TimeoutConfig()
        
        # Track processing statistics
        self.stats = {
            'processed': 0,
            'failed': 0,
            'retried': 0,
            'timeouts': 0,
            'ssl_errors': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Track site complexity for adaptive timeouts
        self.site_complexity = {}
        
    def classify_error(self, error: Exception) -> ErrorType:
        """Classify error type for smart retry logic"""
        error_str = str(error).lower()
        
        if 'timeout' in error_str or 'timed out' in error_str:
            return ErrorType.TIMEOUT
        elif 'ssl' in error_str or 'certificate' in error_str:
            return ErrorType.SSL_ERROR
        elif 'connection' in error_str or 'network' in error_str:
            return ErrorType.CONNECTION_ERROR
        elif '429' in error_str or 'rate limit' in error_str:
            return ErrorType.RATE_LIMIT
        elif '403' in error_str or 'forbidden' in error_str or 'cloudflare' in error_str:
            return ErrorType.PROTECTED_SITE
        elif 'parsing' in error_str or 'json' in error_str:
            return ErrorType.PARSING_ERROR
        else:
            return ErrorType.UNKNOWN
    
    def calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff with optional jitter"""
        backoff = min(
            self.retry_config.base_backoff ** attempt,
            self.retry_config.max_backoff
        )
        
        if self.retry_config.jitter:
            # Add random jitter to prevent thundering herd
            backoff *= (0.5 + random.random())
        
        return backoff
    
    def should_retry(self, error_type: ErrorType, attempt: int) -> bool:
        """Determine if error should be retried"""
        if attempt >= self.retry_config.max_retries:
            return False
        
        return error_type in self.retry_config.retry_on
    
    def process_company_with_retry(
        self,
        company_data: Dict[str, Any],
        row_number: int
    ) -> Dict[str, Any]:
        """Process a single company with retry logic"""
        company_name = company_data.get('name', 'Unknown')
        website = company_data.get('website', '')
        
        # Check if site is known to be complex
        is_complex = self.site_complexity.get(website, False)
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # Update status to processing
                self.sheets_client.update_company_status(
                    self.sheets_client.spreadsheet_id,
                    row_number,
                    'processing'
                )
                
                # Get timeout for this attempt
                timeout = self.timeout_config.get_timeout(attempt, is_complex)
                logger.info(f"Processing {company_name} (attempt {attempt + 1}, timeout: {timeout}s)")
                
                # Process with timeout
                start_time = time.time()
                
                # Temporarily set scraper timeout
                original_scrape_method = None
                if hasattr(self.pipeline, 'scraper') and hasattr(self.pipeline.scraper, 'scrape_company'):
                    # Wrap the scrape_company method to pass timeout
                    original_scrape_method = self.pipeline.scraper.scrape_company
                    
                    def scrape_with_timeout(company_data, job_id=None):
                        return original_scrape_method(company_data, job_id, timeout=timeout)
                    
                    self.pipeline.scraper.scrape_company = scrape_with_timeout
                
                try:
                    company_result = self.pipeline.process_single_company(
                        company_name=company_name,
                        website=website
                    )
                    
                    processing_time = time.time() - start_time
                    
                    # Update site complexity based on processing time
                    if processing_time > 40:
                        self.site_complexity[website] = True
                    
                    # Check if successful
                    if company_result.scrape_status == 'success':
                        # Update results in sheet
                        self.sheets_client.update_company_results(
                            self.sheets_client.spreadsheet_id,
                            row_number,
                            company_result
                        )
                        self.sheets_client.update_company_status(
                            self.sheets_client.spreadsheet_id,
                            row_number,
                            'completed'
                        )
                        
                        logger.info(f"✅ Successfully processed {company_name} in {processing_time:.1f}s")
                        return {
                            'success': True,
                            'company_name': company_name,
                            'processing_time': processing_time,
                            'attempts': attempt + 1
                        }
                    else:
                        raise Exception(f"Scraping failed: {company_result.scrape_error}")
                        
                finally:
                    # Restore original scraper method
                    if original_scrape_method and hasattr(self.pipeline, 'scraper'):
                        self.pipeline.scraper.scrape_company = original_scrape_method
                        
            except Exception as e:
                error_type = self.classify_error(e)
                logger.warning(f"Error processing {company_name}: {error_type.value} - {str(e)}")
                
                # Update statistics
                if error_type == ErrorType.TIMEOUT:
                    self.stats['timeouts'] += 1
                elif error_type == ErrorType.SSL_ERROR:
                    self.stats['ssl_errors'] += 1
                
                # Check if should retry
                if self.should_retry(error_type, attempt):
                    backoff = self.calculate_backoff(attempt)
                    logger.info(f"Retrying {company_name} after {backoff:.1f}s backoff")
                    self.stats['retried'] += 1
                    time.sleep(backoff)
                    continue
                else:
                    # Final failure
                    self.sheets_client.update_company_status(
                        self.sheets_client.spreadsheet_id,
                        row_number,
                        'failed',
                        error_message=f"{error_type.value}: {str(e)}"
                    )
                    return {
                        'success': False,
                        'company_name': company_name,
                        'error': str(e),
                        'error_type': error_type.value,
                        'attempts': attempt + 1
                    }
        
        # Should never reach here
        return {
            'success': False,
            'company_name': company_name,
            'error': 'Max retries exceeded',
            'attempts': self.retry_config.max_retries + 1
        }
    
    def process_batch(
        self,
        spreadsheet_id: str,
        use_parallel: bool = True
    ) -> Dict[str, Any]:
        """Process companies with enhanced error handling"""
        self.stats['start_time'] = time.time()
        
        try:
            # Set spreadsheet ID
            self.sheets_client.spreadsheet_id = spreadsheet_id
            
            # Initialize sheets if needed
            self.sheets_client.initialize_sheets(spreadsheet_id)
            
            # Get companies to process
            companies = self.sheets_client.read_companies_to_process(spreadsheet_id)
            
            # Filter and limit companies
            to_process = []
            for company in companies:
                if company.get('status', '').lower() not in ['completed', 'processing']:
                    to_process.append(company)
                    if self.max_companies_to_process and len(to_process) >= self.max_companies_to_process:
                        break
            
            logger.info(f"Found {len(to_process)} companies to process")
            
            if use_parallel and self.concurrency > 1:
                # Process in parallel with thread pool
                results = self._process_parallel(to_process)
            else:
                # Process sequentially
                results = self._process_sequential(to_process)
            
            # Calculate final statistics
            self.stats['end_time'] = time.time()
            duration = self.stats['end_time'] - self.stats['start_time']
            
            processed = sum(1 for r in results if r['success'])
            failed = sum(1 for r in results if not r['success'])
            
            self.stats['processed'] = processed
            self.stats['failed'] = failed
            
            companies_per_minute = (processed + failed) / duration * 60 if duration > 0 else 0
            
            summary = {
                'success': True,
                'processed': processed,
                'failed': failed,
                'total': len(results),
                'duration_seconds': duration,
                'companies_per_minute': companies_per_minute,
                'statistics': self.stats,
                'results': results
            }
            
            logger.info(f"Batch processing completed: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'statistics': self.stats
            }
    
    def _process_sequential(self, companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process companies sequentially"""
        results = []
        
        for i, company in enumerate(companies):
            row_number = company.get('row_number', i + 2)
            result = self.process_company_with_retry(company, row_number)
            results.append(result)
            
            # Log progress
            logger.info(f"Progress: {i + 1}/{len(companies)} completed")
            
            # Small delay between companies
            if i < len(companies) - 1:
                time.sleep(2)
        
        return results
    
    def _process_parallel(self, companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process companies in parallel with thread pool"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            # Submit all tasks
            future_to_company = {
                executor.submit(
                    self.process_company_with_retry,
                    company,
                    company.get('row_number', i + 2)
                ): company
                for i, company in enumerate(companies)
            }
            
            # Process completed tasks
            completed = 0
            for future in as_completed(future_to_company):
                company = future_to_company[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Unexpected error processing {company.get('name')}: {e}")
                    results.append({
                        'success': False,
                        'company_name': company.get('name', 'Unknown'),
                        'error': str(e),
                        'error_type': 'unexpected'
                    })
                
                completed += 1
                logger.info(f"Progress: {completed}/{len(companies)} completed")
        
        return results


def create_enhanced_processor(
    sheets_client: GoogleSheetsServiceClient,
    pipeline: TheodoreIntelligencePipeline,
    **kwargs
) -> EnhancedBatchProcessor:
    """Factory function to create enhanced processor with custom config"""
    
    # Create custom retry config
    retry_config = RetryConfig(
        max_retries=kwargs.get('max_retries', 3),
        base_backoff=kwargs.get('base_backoff', 2.0),
        max_backoff=kwargs.get('max_backoff', 60.0),
        jitter=kwargs.get('jitter', True)
    )
    
    # Create custom timeout config
    timeout_config = TimeoutConfig(
        default=kwargs.get('default_timeout', 30),
        simple_sites=kwargs.get('simple_timeout', 20),
        complex_sites=kwargs.get('complex_timeout', 60),
        max_timeout=kwargs.get('max_timeout', 120)
    )
    
    return EnhancedBatchProcessor(
        sheets_client=sheets_client,
        pipeline=pipeline,
        concurrency=kwargs.get('concurrency', 3),
        max_companies_to_process=kwargs.get('max_companies', None),
        retry_config=retry_config,
        timeout_config=timeout_config
    )