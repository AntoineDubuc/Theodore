"""
Batch Processor for Google Sheets integration
Handles concurrent processing of companies from Google Sheets
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
import sys
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.main_pipeline import pipeline
from src.models import CompanyData
from google_sheets_client import GoogleSheetsClient

logger = logging.getLogger(__name__)

class BatchProcessor:
    """Handles batch processing of companies from Google Sheets"""
    
    def __init__(self, sheets_client: GoogleSheetsClient, 
                 concurrency: int = 10,
                 update_interval: int = 5,
                 max_consecutive_errors: int = 3):
        """
        Initialize batch processor
        
        Args:
            sheets_client: GoogleSheetsClient instance
            concurrency: Number of companies to process simultaneously
            update_interval: Update sheet every N companies
            max_consecutive_errors: Stop processing after N consecutive errors
        """
        self.sheets_client = sheets_client
        self.concurrency = concurrency
        self.update_interval = update_interval
        self.max_consecutive_errors = max_consecutive_errors
        self.consecutive_errors = 0
        self.processed_count = 0
        self.failed_count = 0
        self.start_time = None
    
    def process_batch(self, spreadsheet_id: str, job_id: str = None) -> Dict[str, Any]:
        """
        Process all pending companies in the spreadsheet
        
        Args:
            spreadsheet_id: Google Sheets ID
            job_id: Optional job ID for tracking
            
        Returns:
            Summary of processing results
        """
        self.start_time = time.time()
        logger.info(f"Starting batch processing for spreadsheet: {spreadsheet_id}")
        
        # Setup dual-sheet structure
        if not self.sheets_client.setup_dual_sheet_structure(spreadsheet_id):
            return {
                'success': False,
                'error': 'Failed to setup sheet structure',
                'processed': 0,
                'failed': 0
            }
        
        # Read companies to process
        companies = self.sheets_client.read_companies_to_process(spreadsheet_id)
        if not companies:
            logger.info("No companies to process")
            return {
                'success': True,
                'message': 'No companies to process',
                'processed': 0,
                'failed': 0
            }
        
        logger.info(f"Found {len(companies)} companies to process")
        
        # Process companies concurrently
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            # Submit all tasks
            future_to_company = {
                executor.submit(
                    self._process_single_company, 
                    company, 
                    spreadsheet_id,
                    job_id
                ): company 
                for company in companies
            }
            
            # Process completed tasks
            for future in as_completed(future_to_company):
                company = future_to_company[future]
                
                try:
                    result = future.result()
                    if result['success']:
                        self.consecutive_errors = 0  # Reset error counter
                        self.processed_count += 1
                    else:
                        self.failed_count += 1
                        self.consecutive_errors += 1
                        
                        # Check if we should stop
                        if self.consecutive_errors >= self.max_consecutive_errors:
                            logger.error(f"Stopping batch processing: {self.consecutive_errors} consecutive errors")
                            executor.shutdown(wait=False)
                            break
                    
                    # Update sheet periodically
                    if (self.processed_count + self.failed_count) % self.update_interval == 0:
                        self._log_progress()
                        
                except Exception as e:
                    logger.error(f"Error processing {company['name']}: {str(e)}")
                    self.failed_count += 1
                    self.consecutive_errors += 1
        
        # Final summary
        duration = time.time() - self.start_time
        summary = {
            'success': True,
            'processed': self.processed_count,
            'failed': self.failed_count,
            'total': len(companies),
            'duration_seconds': duration,
            'companies_per_minute': (self.processed_count / duration * 60) if duration > 0 else 0
        }
        
        logger.info(f"Batch processing completed: {summary}")
        return summary
    
    def _process_single_company(self, company: Dict[str, Any], 
                              spreadsheet_id: str, job_id: str = None) -> Dict[str, Any]:
        """
        Process a single company and update the sheet
        
        Args:
            company: Company data with row_number, name, website
            spreadsheet_id: Google Sheets ID
            job_id: Optional job ID for tracking
            
        Returns:
            Processing result
        """
        row_number = company['row_number']
        company_name = company['name']
        website = company.get('website', '')
        
        logger.info(f"Processing row {row_number}: {company_name}")
        
        try:
            # Update status to processing
            self.sheets_client.update_company_status(
                spreadsheet_id, 
                row_number, 
                'processing',
                '0%'
            )
            
            # Run Theodore research pipeline
            logger.info(f"Starting research for {company_name}...")
            company_data = pipeline.process_company(
                company_name=company_name,
                website_url=website if website else None,
                job_id=job_id
            )
            
            if company_data and company_data.name:
                # Update sheets with results
                self.sheets_client.update_company_results(
                    spreadsheet_id,
                    row_number,
                    company_data
                )
                
                # Update status to completed
                self.sheets_client.update_company_status(
                    spreadsheet_id,
                    row_number,
                    'completed',
                    '100%'
                )
                
                logger.info(f"✅ Successfully processed {company_name}")
                return {'success': True, 'company': company_name}
                
            else:
                # Mark as failed
                self.sheets_client.update_company_status(
                    spreadsheet_id,
                    row_number,
                    'failed',
                    '0%',
                    'No data returned from research pipeline'
                )
                
                logger.error(f"❌ Failed to process {company_name}: No data returned")
                return {'success': False, 'company': company_name, 'error': 'No data returned'}
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error processing {company_name}: {error_msg}")
            
            # Update sheet with error
            self.sheets_client.update_company_status(
                spreadsheet_id,
                row_number,
                'failed',
                '0%',
                f'Error: {error_msg[:200]}'  # Truncate long errors
            )
            
            return {'success': False, 'company': company_name, 'error': error_msg}
    
    def _log_progress(self):
        """Log current processing progress"""
        elapsed = time.time() - self.start_time
        rate = (self.processed_count / elapsed * 60) if elapsed > 0 else 0
        
        logger.info(
            f"📊 Progress: {self.processed_count} completed, "
            f"{self.failed_count} failed, "
            f"{rate:.1f} companies/minute"
        )

# Example usage function for testing
def test_batch_processor(spreadsheet_id: str):
    """Test the batch processor with a spreadsheet"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize clients
    credentials_file = project_root / 'config' / 'credentials' / 'client_secret_1096944990043-5u1eohnobc583lvueqr2cvfvm9tcjc3p.apps.googleusercontent.com.json'
    sheets_client = GoogleSheetsClient(credentials_file)
    
    # Initialize batch processor
    processor = BatchProcessor(
        sheets_client=sheets_client,
        concurrency=10,
        update_interval=5,
        max_consecutive_errors=3
    )
    
    # Process batch
    results = processor.process_batch(spreadsheet_id)
    
    print("\n📊 Batch Processing Results:")
    print(f"   Processed: {results['processed']} companies")
    print(f"   Failed: {results['failed']} companies")
    print(f"   Duration: {results.get('duration_seconds', 0):.1f} seconds")
    print(f"   Rate: {results.get('companies_per_minute', 0):.1f} companies/minute")
    
    return results

if __name__ == "__main__":
    # Test with the provided spreadsheet
    TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'
    test_batch_processor(TEST_SHEET_ID)