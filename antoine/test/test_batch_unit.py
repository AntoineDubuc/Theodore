#!/usr/bin/env python3
"""
Unit Tests for Antoine Batch Processor
=====================================

Tests core functionality of the batch processor including resource pooling,
concurrency control, and error handling.
"""

import sys
import os
import time
import unittest
import threading
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from antoine.batch.batch_processor import AntoineBatchProcessor, BatchProcessingResult
from src.models import CompanyData, CompanyIntelligenceConfig


class TestBatchProcessor(unittest.TestCase):
    """Test cases for AntoineBatchProcessor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = CompanyIntelligenceConfig()
        self.batch_processor = AntoineBatchProcessor(
            config=self.config,
            max_concurrent_companies=2,
            enable_resource_pooling=True
        )
    
    def tearDown(self):
        """Clean up after tests"""
        self.batch_processor.shutdown()
    
    def test_initialization(self):
        """Test batch processor initialization"""
        self.assertEqual(self.batch_processor.max_concurrent_companies, 2)
        self.assertTrue(self.batch_processor.enable_resource_pooling)
        self.assertEqual(self.batch_processor.semaphore._value, 2)
        self.assertIsNotNone(self.batch_processor.executor)
    
    def test_resource_pooling(self):
        """Test scraper pooling functionality"""
        # Get a scraper
        scraper1 = self.batch_processor._get_scraper()
        self.assertIsNotNone(scraper1)
        
        # Return it to pool
        self.batch_processor._return_scraper(scraper1)
        self.assertEqual(len(self.batch_processor.scraper_pool), 1)
        
        # Get it again - should be same instance
        scraper2 = self.batch_processor._get_scraper()
        self.assertIs(scraper1, scraper2)
        
        # Pool should be empty now
        self.assertEqual(len(self.batch_processor.scraper_pool), 0)
    
    def test_semaphore_limiting(self):
        """Test concurrent execution limiting"""
        concurrent_count = 0
        max_concurrent_seen = 0
        lock = threading.Lock()
        
        def mock_process(company_data, job_id):
            nonlocal concurrent_count, max_concurrent_seen
            
            with lock:
                concurrent_count += 1
                max_concurrent_seen = max(max_concurrent_seen, concurrent_count)
            
            time.sleep(0.1)  # Simulate processing
            
            with lock:
                concurrent_count -= 1
            
            # Return mock result
            company = CompanyData(
                name=company_data['name'],
                website=company_data['website']
            )
            company.scrape_status = "success"
            return company, None
        
        # Patch the process method
        self.batch_processor._process_single_company = mock_process
        
        # Process 5 companies with max 2 concurrent
        companies = [{"name": f"Company{i}", "website": f"https://example{i}.com"} for i in range(5)]
        result = self.batch_processor.process_batch(companies)
        
        # Verify concurrency was limited
        self.assertEqual(result.total_companies, 5)
        self.assertLessEqual(max_concurrent_seen, 2)
    
    def test_error_isolation(self):
        """Test that errors in one company don't affect others"""
        def mock_process(company_data, job_id):
            if company_data['name'] == "FailCompany":
                raise Exception("Simulated failure")
            
            company = CompanyData(
                name=company_data['name'],
                website=company_data['website']
            )
            company.scrape_status = "success"
            return company, None
        
        self.batch_processor._process_single_company = mock_process
        
        companies = [
            {"name": "GoodCompany1", "website": "https://good1.com"},
            {"name": "FailCompany", "website": "https://fail.com"},
            {"name": "GoodCompany2", "website": "https://good2.com"}
        ]
        
        result = self.batch_processor.process_batch(companies)
        
        # Should have 2 successful, 1 failed
        self.assertEqual(result.successful, 2)
        self.assertEqual(result.failed, 1)
        self.assertIn("FailCompany", result.errors)
    
    def test_batch_result_statistics(self):
        """Test batch result statistics calculation"""
        def mock_process(company_data, job_id):
            company = CompanyData(
                name=company_data['name'],
                website=company_data['website']
            )
            company.scrape_status = "success"
            company.pages_crawled = ["page1", "page2", "page3"]
            
            # Simulate processing time
            time.sleep(0.1)
            
            # Update stats
            self.batch_processor.stats['total_pages_crawled'] += 3
            
            return company, None
        
        self.batch_processor._process_single_company = mock_process
        
        companies = [{"name": f"Company{i}", "website": f"https://example{i}.com"} for i in range(3)]
        result = self.batch_processor.process_batch(companies)
        
        # Verify statistics
        self.assertEqual(result.successful, 3)
        self.assertEqual(result.resource_stats['total_pages_crawled'], 9)
        self.assertEqual(result.resource_stats['avg_pages_per_company'], 3.0)
        self.assertGreater(result.companies_per_minute, 0)
        self.assertGreater(result.resource_stats['parallel_efficiency'], 0)
    
    @patch('src.progress_logger.start_company_processing')
    @patch('src.progress_logger.complete_company_processing')
    def test_progress_tracking(self, mock_complete, mock_start):
        """Test progress tracking integration"""
        mock_start.return_value = "test_job_123"
        
        # Create a mock scraper
        mock_scraper = Mock()
        mock_company_result = CompanyData(name="TestCo", website="https://test.com")
        mock_company_result.scrape_status = "success"
        mock_scraper.scrape_company.return_value = mock_company_result
        
        # Patch scraper creation
        self.batch_processor._get_scraper = Mock(return_value=mock_scraper)
        self.batch_processor._return_scraper = Mock()
        
        # Process one company
        companies = [{"name": "TestCo", "website": "https://test.com"}]
        result = self.batch_processor.process_batch(companies)
        
        # Verify progress tracking was called
        mock_start.assert_called_once_with("TestCo")
        mock_complete.assert_called_once_with("test_job_123", "completed")
    
    def test_shutdown(self):
        """Test proper shutdown and cleanup"""
        # Add some scrapers to pool
        scraper1 = Mock()
        scraper2 = Mock()
        self.batch_processor.scraper_pool = [scraper1, scraper2]
        
        # Shutdown
        self.batch_processor.shutdown()
        
        # Verify cleanup
        self.assertEqual(len(self.batch_processor.scraper_pool), 0)
        self.assertTrue(self.batch_processor.executor._shutdown)


class TestBatchProcessingResult(unittest.TestCase):
    """Test cases for BatchProcessingResult dataclass"""
    
    def test_initialization(self):
        """Test result initialization"""
        result = BatchProcessingResult(total_companies=10)
        
        self.assertEqual(result.total_companies, 10)
        self.assertEqual(result.successful, 0)
        self.assertEqual(result.failed, 0)
        self.assertIsNotNone(result.start_time)
        self.assertIsNone(result.end_time)
        self.assertEqual(len(result.company_results), 0)
        self.assertEqual(len(result.errors), 0)
    
    def test_metrics_calculation(self):
        """Test metric calculations"""
        result = BatchProcessingResult(total_companies=5)
        result.successful = 4
        result.failed = 1
        result.total_duration = 60.0  # 1 minute
        
        # Calculate companies per minute
        result.companies_per_minute = (result.successful / result.total_duration) * 60
        
        self.assertEqual(result.companies_per_minute, 4.0)


if __name__ == '__main__':
    unittest.main()