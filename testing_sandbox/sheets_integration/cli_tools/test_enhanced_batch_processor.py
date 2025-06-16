#!/usr/bin/env python3
"""
Test the enhanced batch processor with retry logic and adaptive timeouts
"""

import os
import sys
import logging
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from src.sheets_integration import GoogleSheetsServiceClient, create_enhanced_processor
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Constants
SERVICE_ACCOUNT_FILE = project_root / 'config' / 'credentials' / 'theodore-service-account.json'
TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_enhanced_processor():
    """Test the enhanced batch processor"""
    print("🚀 Testing Enhanced Batch Processor")
    print("=" * 50)
    print("\n✨ New Features:")
    print("  • Retry logic with exponential backoff")
    print("  • Adaptive timeouts (30s default, 60s for complex sites)")
    print("  • Smart error classification")
    print("  • Better error reporting")
    print("  • Parallel processing with proper error handling")
    print("\n" + "=" * 50)
    
    try:
        # Initialize sheets client
        sheets_client = GoogleSheetsServiceClient(SERVICE_ACCOUNT_FILE)
        
        # Initialize pipeline
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT', 'us-east-1'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        )
        
        # Create enhanced processor with custom configuration
        processor = create_enhanced_processor(
            sheets_client=sheets_client,
            pipeline=pipeline,
            concurrency=3,  # Process 3 companies at once
            max_companies=10,  # Process 10 companies total
            max_retries=2,  # Retry failed companies up to 2 times
            default_timeout=30,  # 30 second default timeout
            complex_timeout=60,  # 60 second timeout for complex sites
            max_timeout=90,  # Maximum 90 second timeout
            base_backoff=3.0,  # 3 second base backoff
            jitter=True  # Add random jitter to prevent thundering herd
        )
        
        # Process batch with parallel processing
        print("\n🔄 Starting enhanced batch processing...")
        print(f"   Configuration:")
        print(f"     • Concurrency: 3 companies in parallel")
        print(f"     • Max retries: 2 per company")
        print(f"     • Timeouts: 30s (default), 60s (complex), 90s (max)")
        print(f"     • Backoff: 3s base with jitter")
        print("-" * 50)
        
        start_time = time.time()
        results = processor.process_batch(TEST_SHEET_ID, use_parallel=True)
        duration = time.time() - start_time
        
        # Display results
        print("\n" + "=" * 50)
        print("📊 Processing Results:")
        print(f"   Total time: {duration:.1f} seconds")
        print(f"   Processed: {results['processed']} companies")
        print(f"   Failed: {results['failed']} companies")
        print(f"   Rate: {results['companies_per_minute']:.1f} companies/minute")
        
        # Display statistics
        stats = results.get('statistics', {})
        print(f"\n📈 Statistics:")
        print(f"   Retries attempted: {stats.get('retried', 0)}")
        print(f"   Timeout errors: {stats.get('timeouts', 0)}")
        print(f"   SSL errors: {stats.get('ssl_errors', 0)}")
        
        # Analyze individual results
        if 'results' in results:
            print(f"\n📋 Individual Results:")
            print("-" * 60)
            
            for result in results['results']:
                company = result.get('company_name', 'Unknown')
                if result['success']:
                    time_taken = result.get('processing_time', 0)
                    attempts = result.get('attempts', 1)
                    status = "✅"
                    if attempts > 1:
                        status = f"✅ (after {attempts} attempts)"
                    print(f"   {status} {company}: {time_taken:.1f}s")
                else:
                    error_type = result.get('error_type', 'unknown')
                    attempts = result.get('attempts', 1)
                    print(f"   ❌ {company}: {error_type} (tried {attempts} times)")
        
        # Check field coverage
        print("\n📊 Checking field coverage...")
        details = sheets_client.service.spreadsheets().values().get(
            spreadsheetId=TEST_SHEET_ID,
            range='Details!A1:BZ20'
        ).execute()
        
        if 'values' in details and len(details['values']) > 1:
            headers = details['values'][0]
            recent_rows = [row for row in details['values'][1:] if len(row) > 10][-10:]
            
            if recent_rows:
                coverages = []
                for row in recent_rows:
                    filled = sum(1 for v in row if v and str(v).strip())
                    coverage = filled / len(headers) * 100
                    coverages.append(coverage)
                
                avg_coverage = sum(coverages) / len(coverages)
                print(f"   Average field coverage: {avg_coverage:.1f}%")
                print(f"   Best: {max(coverages):.1f}%, Worst: {min(coverages):.1f}%")
        
        # Summary and recommendations
        print("\n💡 Summary:")
        success_rate = results['processed'] / (results['processed'] + results['failed']) * 100 if results['processed'] + results['failed'] > 0 else 0
        print(f"   Success rate: {success_rate:.1f}%")
        
        if success_rate < 50:
            print("\n📌 Recommendations:")
            if stats.get('timeouts', 0) > 2:
                print("   • Many timeouts detected - consider increasing timeout limits")
            if stats.get('ssl_errors', 0) > 2:
                print("   • SSL errors detected - may need proxy rotation")
            if stats.get('retried', 0) > 5:
                print("   • High retry count - websites may have anti-scraping measures")
        else:
            print("   ✨ Good success rate! The enhanced processor is working well.")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_processor()