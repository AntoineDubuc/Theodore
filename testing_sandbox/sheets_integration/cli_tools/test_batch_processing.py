#!/usr/bin/env python3
"""
Test batch processing of companies from Google Sheets
This script tests the full pipeline integration
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

# Import from the old location for compatibility
sys.path.insert(0, str(Path(__file__).parent.parent))
from google_sheets_client import GoogleSheetsClient
from batch_processor import BatchProcessor

# Constants
CREDENTIALS_FILE = project_root / 'config' / 'credentials' / 'client_secret_1096944990043-5u1eohnobc583lvueqr2cvfvm9tcjc3p.apps.googleusercontent.com.json'
TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('batch_processing.log')
        ]
    )

def main():
    """Main test function"""
    print("🧪 Google Sheets Batch Processing Test")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize Google Sheets client
        print("📊 Initializing Google Sheets client...")
        sheets_client = GoogleSheetsClient(CREDENTIALS_FILE)
        
        # Validate access
        if not sheets_client.validate_sheet_access(TEST_SHEET_ID):
            print("❌ Cannot access test spreadsheet")
            return 1
        
        print("✅ Google Sheets client initialized")
        
        # Initialize batch processor
        print("\n🔧 Initializing batch processor...")
        processor = BatchProcessor(
            sheets_client=sheets_client,
            concurrency=3,  # Start with lower concurrency for testing
            update_interval=1,  # Update after every company for testing
            max_consecutive_errors=3
        )
        
        # Show companies to process
        print("\n📋 Reading companies to process...")
        companies = sheets_client.read_companies_to_process(TEST_SHEET_ID)
        
        if not companies:
            print("ℹ️  No companies to process. Add some companies to the sheet first!")
            print(f"   Sheet URL: https://docs.google.com/spreadsheets/d/{TEST_SHEET_ID}/edit")
            return 0
        
        print(f"📊 Found {len(companies)} companies to process:")
        for i, company in enumerate(companies[:5]):  # Show first 5
            print(f"   {i+1}. {company['name']} ({company.get('website', 'No website')})")
        
        if len(companies) > 5:
            print(f"   ... and {len(companies) - 5} more")
        
        # Confirm processing
        print(f"\n⚠️  About to process {len(companies)} companies with:")
        print(f"   - Concurrency: 3 companies at once")
        print(f"   - Updates: After every company")
        print(f"   - Stop after: 3 consecutive errors")
        
        response = input("\nProceed with batch processing? (y/n): ")
        if response.lower() != 'y':
            print("Batch processing cancelled")
            return 0
        
        # Start processing
        print("\n🚀 Starting batch processing...")
        print(f"📊 Monitor progress at: https://docs.google.com/spreadsheets/d/{TEST_SHEET_ID}/edit")
        print("=" * 50)
        
        results = processor.process_batch(TEST_SHEET_ID, job_id="test_batch_001")
        
        # Show results
        print("\n" + "=" * 50)
        print("📊 Batch Processing Complete!")
        print(f"   ✅ Processed: {results['processed']} companies")
        print(f"   ❌ Failed: {results['failed']} companies")
        print(f"   ⏱️  Duration: {results.get('duration_seconds', 0):.1f} seconds")
        print(f"   📈 Rate: {results.get('companies_per_minute', 0):.1f} companies/minute")
        
        if results['failed'] > 0:
            print(f"\n⚠️  {results['failed']} companies failed. Check the 'Error Notes' column in the sheet.")
        
        print(f"\n📊 View results: https://docs.google.com/spreadsheets/d/{TEST_SHEET_ID}/edit")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Batch processing interrupted by user")
        return 1
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        print(f"\n❌ Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())