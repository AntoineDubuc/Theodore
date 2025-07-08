#!/usr/bin/env python3
"""
Quick Validation Test
====================

Quick test to validate the batch processing is actually working.
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load env vars
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

from antoine.batch.batch_processor import AntoineBatchProcessor
from src.models import CompanyIntelligenceConfig


def quick_test():
    """Quick test with 2 companies"""
    
    print("=" * 80)
    print("QUICK VALIDATION TEST")
    print("=" * 80)
    
    # Just 2 easy companies
    test_companies = [
        {"name": "Example", "website": "https://example.com"},
        {"name": "HTTPBin", "website": "https://httpbin.org"}
    ]
    
    print(f"\n📋 Testing with {len(test_companies)} simple companies")
    
    # Create batch processor
    config = CompanyIntelligenceConfig()
    batch_processor = AntoineBatchProcessor(
        config=config,
        max_concurrent_companies=2
    )
    
    print("\n🚀 Starting batch processing...")
    start_time = time.time()
    
    try:
        result = batch_processor.process_batch(test_companies)
        elapsed = time.time() - start_time
        
        print(f"\n✅ Completed in {elapsed:.1f}s")
        print(f"   Successful: {result.successful}/{result.total_companies}")
        
        # Check if it actually worked
        if result.successful > 0:
            print("\n✅ VALIDATION PASSED - Batch processing is working!")
            
            # Show some extracted data
            for company in result.company_results:
                if company.scrape_status == "success":
                    print(f"\n   {company.name}:")
                    print(f"   - Industry: {company.industry}")
                    print(f"   - Pages crawled: {len(company.pages_crawled or [])}")
                    if company.company_description:
                        print(f"   - Description: {company.company_description[:50]}...")
            
            return True
        else:
            print("\n❌ VALIDATION FAILED - No companies processed successfully")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        batch_processor.shutdown()


if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)