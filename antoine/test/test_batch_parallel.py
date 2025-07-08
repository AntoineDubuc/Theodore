#!/usr/bin/env python3
"""
Parallel Processing Validation Test
==================================

Test to validate and visualize parallel processing behavior of the antoine
batch processor, showing how companies are processed concurrently.
"""

import sys
import os
import time
import threading
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load env vars
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

from antoine.batch.batch_processor import AntoineBatchProcessor
from src.models import CompanyIntelligenceConfig


class ParallelMonitor:
    """Monitor to track parallel execution"""
    
    def __init__(self):
        self.events = []
        self.lock = threading.Lock()
        self.start_time = time.time()
    
    def log_event(self, company: str, phase: str, status: str):
        """Log an event with timestamp"""
        with self.lock:
            elapsed = time.time() - self.start_time
            self.events.append({
                'time': elapsed,
                'company': company,
                'phase': phase,
                'status': status,
                'timestamp': datetime.now()
            })
    
    def print_timeline(self):
        """Print execution timeline"""
        print("\n📊 EXECUTION TIMELINE:")
        print("Time | Company     | Phase      | Status")
        print("-" * 50)
        
        for event in sorted(self.events, key=lambda x: x['time']):
            print(f"{event['time']:5.1f}s | {event['company']:11s} | {event['phase']:10s} | {event['status']}")


# Global monitor instance
monitor = ParallelMonitor()


def monitored_scrape_company(original_method):
    """Wrapper to monitor scrape_company calls"""
    def wrapper(self, company, job_id=None):
        company_name = company.name
        
        # Log start
        monitor.log_event(company_name, "start", "🚀 Starting")
        
        # Log phases
        original_log_phase = None
        try:
            from src.progress_logger import log_processing_phase
            original_log_phase = log_processing_phase
            
            def monitored_log_phase(job_id, phase, message):
                monitor.log_event(company_name, phase, f"📍 {phase}")
                return original_log_phase(job_id, phase, message)
            
            # Monkey patch temporarily
            import src.progress_logger
            src.progress_logger.log_processing_phase = monitored_log_phase
            
            # Call original method
            result = original_method(self, company, job_id)
            
            # Log completion
            if result.scrape_status == "success":
                monitor.log_event(company_name, "complete", "✅ Success")
            else:
                monitor.log_event(company_name, "complete", "❌ Failed")
            
            return result
            
        finally:
            # Restore original
            if original_log_phase:
                import src.progress_logger
                src.progress_logger.log_processing_phase = original_log_phase
    
    return wrapper


def test_parallel_execution():
    """Test and visualize parallel execution"""
    
    print("=" * 80)
    print("ANTOINE BATCH PROCESSING - PARALLEL EXECUTION TEST")
    print("=" * 80)
    
    # Test companies with varying complexity
    test_companies = [
        {"name": "Small-Co", "website": "https://example.com"},      # Fast
        {"name": "Medium-Co", "website": "https://github.com"},       # Medium
        {"name": "Large-Co", "website": "https://www.microsoft.com"}, # Slow
        {"name": "Huge-Co", "website": "https://www.amazon.com"},     # Very slow
        {"name": "Quick-Co", "website": "https://httpbin.org"}       # Very fast
    ]
    
    print(f"\n📋 Test companies (ordered by expected complexity):")
    for i, company in enumerate(test_companies, 1):
        print(f"   {i}. {company['name']} - {company['website']}")
    
    # Test different concurrency levels
    for max_concurrent in [1, 2, 3]:
        print(f"\n{'='*60}")
        print(f"🔧 Testing with max_concurrent_companies = {max_concurrent}")
        print(f"{'='*60}")
        
        # Reset monitor
        monitor.events = []
        monitor.start_time = time.time()
        
        # Create batch processor
        batch_processor = AntoineBatchProcessor(
            config=CompanyIntelligenceConfig(),
            bedrock_client=None,
            max_concurrent_companies=max_concurrent,
            enable_resource_pooling=True
        )
        
        # Monkey patch the scraper method to add monitoring
        from src.antoine_scraper_adapter import AntoineScraperAdapter
        original_scrape = AntoineScraperAdapter.scrape_company
        AntoineScraperAdapter.scrape_company = monitored_scrape_company(original_scrape)
        
        try:
            # Process batch
            print(f"\n🚀 Starting batch with concurrency={max_concurrent}")
            start_time = time.time()
            
            result = batch_processor.process_batch(
                test_companies[:3],  # Only use first 3 for speed
                batch_name=f"parallel_test_{max_concurrent}"
            )
            
            elapsed = time.time() - start_time
            
            # Show results
            print(f"\n✅ Completed in {elapsed:.1f}s")
            print(f"   Successful: {result.successful}/{result.total_companies}")
            print(f"   Throughput: {result.companies_per_minute:.1f} companies/minute")
            
            # Show timeline
            monitor.print_timeline()
            
            # Analyze concurrency
            print(f"\n📈 CONCURRENCY ANALYSIS:")
            
            # Count overlapping executions
            active_companies = []
            max_active = 0
            
            for event in sorted(monitor.events, key=lambda x: x['time']):
                if event['status'].startswith('🚀'):
                    active_companies.append(event['company'])
                elif event['status'].startswith('✅') or event['status'].startswith('❌'):
                    if event['company'] in active_companies:
                        active_companies.remove(event['company'])
                
                max_active = max(max_active, len(active_companies))
            
            print(f"   Max concurrent executions: {max_active}")
            print(f"   Theoretical max: {max_concurrent}")
            print(f"   Concurrency utilization: {(max_active/max_concurrent)*100:.0f}%")
            
        finally:
            # Restore original method
            AntoineScraperAdapter.scrape_company = original_scrape
            
            # Cleanup
            batch_processor.shutdown()
        
        # Wait between tests
        if max_concurrent < 3:
            print(f"\n⏳ Waiting 2 seconds before next test...")
            time.sleep(2)
    
    print(f"\n🎉 Parallel execution test complete!")


if __name__ == "__main__":
    test_parallel_execution()