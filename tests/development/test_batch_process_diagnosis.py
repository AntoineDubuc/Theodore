#!/usr/bin/env python3
"""
Diagnostic test to verify batch processing fixes are properly applied
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.sheets_integration.batch_processor_service import BatchProcessorService
from src.sheets_integration.google_sheets_service_client import GoogleSheetsServiceClient
from src.concurrent_intelligent_scraper import ConcurrentIntelligentScraperSync
from src.models import CompanyIntelligenceConfig

def test_batch_processor_configuration():
    """Test that batch processor is using updated concurrency settings"""
    
    print("🔧 BATCH PROCESSOR CONFIGURATION TEST")
    print("=" * 60)
    
    # Test 1: Verify batch processor uses 5 concurrent companies
    print("\n1️⃣ Testing Batch Processor Concurrency:")
    
    # Mock sheets client for testing
    class MockSheetsClient:
        pass
    
    mock_sheets = MockSheetsClient()
    processor = BatchProcessorService(sheets_client=mock_sheets)
    
    expected_concurrency = 5
    actual_concurrency = processor.concurrency
    
    if actual_concurrency == expected_concurrency:
        print(f"   ✅ Concurrency setting: {actual_concurrency} (CORRECT)")
    else:
        print(f"   ❌ Concurrency setting: {actual_concurrency} (Expected: {expected_concurrency})")
    
    # Test 2: Verify URL validation is available in scraper
    print("\n2️⃣ Testing URL Validation Availability:")
    
    config = CompanyIntelligenceConfig()
    scraper = ConcurrentIntelligentScraperSync(config)
    
    test_urls = [
        ("https://example.com/about", True, "Valid HTTPS URL"),
        ("internal", False, "Invalid navigation text"),
        ("external", False, "Invalid navigation text"),
        ("/contact", True, "Valid relative path")
    ]
    
    validation_works = True
    for url, expected, description in test_urls:
        try:
            result = scraper._is_valid_crawlable_url(url, "https://example.com")
            if result == expected:
                print(f"   ✅ {url:<20} → {result} ({description})")
            else:
                print(f"   ❌ {url:<20} → {result} (Expected: {expected})")
                validation_works = False
        except Exception as e:
            print(f"   ❌ {url:<20} → ERROR: {e}")
            validation_works = False
    
    # Test 3: Check which scraper the batch processor uses
    print("\n3️⃣ Testing Batch Processor Scraper Type:")
    
    pipeline = processor.pipeline
    scraper_type = type(pipeline.scraper).__name__
    expected_scraper = "ConcurrentIntelligentScraperSync"
    
    if scraper_type == expected_scraper:
        print(f"   ✅ Using scraper: {scraper_type} (CORRECT)")
    else:
        print(f"   ❌ Using scraper: {scraper_type} (Expected: {expected_scraper})")
    
    # Summary
    print("\n📊 DIAGNOSIS SUMMARY:")
    print("-" * 40)
    
    fixes_applied = (
        actual_concurrency == expected_concurrency and
        validation_works and 
        scraper_type == expected_scraper
    )
    
    if fixes_applied:
        print("✅ ALL FIXES PROPERLY APPLIED")
        print("   - Batch processor uses 5 concurrent companies")
        print("   - URL validation working correctly") 
        print("   - Using updated intelligent scraper")
        print("\nIf batch processing still fails, the issue is likely:")
        print("   1. Website bot detection/protection")
        print("   2. Network connectivity issues")
        print("   3. Rate limiting from target websites")
    else:
        print("❌ SOME FIXES NOT APPLIED")
        print("   Please check the batch processor configuration")
    
    return fixes_applied

def test_progress_tracking():
    """Test if progress tracking is working"""
    
    print("\n\n🔍 PROGRESS TRACKING TEST")
    print("=" * 60)
    
    from src.progress_logger import progress_logger
    
    # Test batch progress methods
    batch_methods = ['start_batch_job', 'update_batch_progress', 'complete_batch_job', 'get_batch_progress']
    
    print("Checking batch progress methods:")
    for method in batch_methods:
        if hasattr(progress_logger, method):
            print(f"   ✅ {method}")
        else:
            print(f"   ❌ {method} (MISSING)")
    
    # Test creating a mock batch job
    test_job_id = "test_batch_123"
    try:
        progress_logger.start_batch_job(test_job_id, 3)
        progress_logger.update_batch_progress(test_job_id, 1, "Testing...")
        
        # Check if we can retrieve it
        progress = progress_logger.get_batch_progress(test_job_id)
        if progress:
            print(f"   ✅ Mock batch job created and retrieved successfully")
            return True
        else:
            print(f"   ❌ Mock batch job created but could not retrieve")
            return False
    except Exception as e:
        print(f"   ❌ Error testing batch progress: {e}")
        return False

if __name__ == "__main__":
    print("🚀 BATCH PROCESSING DIAGNOSTIC")
    print("=" * 70)
    
    config_ok = test_batch_processor_configuration()
    progress_ok = test_progress_tracking()
    
    print(f"\n🎯 FINAL DIAGNOSIS:")
    print("=" * 70)
    
    if config_ok and progress_ok:
        print("✅ BATCH PROCESSING SYSTEM IS PROPERLY CONFIGURED")
        print("\nIf 'Failed to get progress updates' still occurs, investigate:")
        print("   • Network timeouts during scraping")
        print("   • Target websites with bot protection")
        print("   • Database connection issues")
        print("   • Specific company website accessibility")
    else:
        print("❌ BATCH PROCESSING SYSTEM NEEDS ATTENTION")
        if not config_ok:
            print("   • Batch processor configuration issues")
        if not progress_ok:
            print("   • Progress tracking system issues")