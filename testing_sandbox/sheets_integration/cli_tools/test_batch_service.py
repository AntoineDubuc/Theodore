#!/usr/bin/env python3
"""
Test batch processing with Service Account authentication
No browser prompts - fully automated!
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from src.sheets_integration import GoogleSheetsServiceClient, BatchProcessorService

# Constants
SERVICE_ACCOUNT_FILE = project_root / 'config' / 'credentials' / 'theodore-service-account.json'
TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'

# TESTING LIMITS - VERY IMPORTANT!
MAX_COMPANIES_FOR_TESTING = 2  # Process only 2 companies max
TESTING_CONCURRENCY = 2  # Process 2 at a time

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('batch_processing_service.log')
        ]
    )

def main():
    """Main test function"""
    print("🧪 Google Sheets Batch Processing Test (Service Account)")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Check service account file
    if not SERVICE_ACCOUNT_FILE.exists():
        print(f"❌ Service account key not found!")
        print(f"   Expected at: {SERVICE_ACCOUNT_FILE}")
        print("\n📋 Setup Instructions:")
        print("1. Read SERVICE_ACCOUNT_SETUP.md")
        print("2. Create service account in Google Cloud Console")
        print("3. Download the JSON key")
        print("4. Save as service_account_key.json in credentials folder")
        print("5. Share your sheet with the service account email")
        return 1
    
    try:
        # Initialize Google Sheets client
        print("📊 Initializing Google Sheets client with service account...")
        sheets_client = GoogleSheetsServiceClient(SERVICE_ACCOUNT_FILE)
        
        # Validate access
        if not sheets_client.validate_sheet_access(TEST_SHEET_ID):
            print("❌ Cannot access test spreadsheet")
            print("Make sure you've shared the sheet with the service account email")
            return 1
        
        print("✅ Google Sheets client initialized (no browser needed!)")
        
        # Initialize batch processor
        print("\n🔧 Initializing batch processor...")
        print(f"⚠️  TESTING MODE: Limited to {MAX_COMPANIES_FOR_TESTING} companies MAX!")
        processor = BatchProcessorService(
            sheets_client=sheets_client,
            concurrency=TESTING_CONCURRENCY,  # Only 2 at a time for testing
            update_interval=1,  # Update after every company
            max_consecutive_errors=3,
            max_companies_to_process=MAX_COMPANIES_FOR_TESTING  # LIMIT FOR TESTING!
        )
        
        # Show companies to process
        print("\n📋 Reading companies to process...")
        companies = sheets_client.read_companies_to_process(TEST_SHEET_ID)
        
        if not companies:
            print("ℹ️  No companies to process. Add some companies to the sheet first!")
            print(f"   Sheet URL: https://docs.google.com/spreadsheets/d/{TEST_SHEET_ID}/edit")
            return 0
        
        # Show limited list for testing
        companies_to_show = min(len(companies), MAX_COMPANIES_FOR_TESTING)
        print(f"📊 Found {len(companies)} companies in sheet")
        print(f"⚠️  TESTING MODE: Will process ONLY {companies_to_show} companies!")
        
        for i, company in enumerate(companies[:companies_to_show]):
            print(f"   {i+1}. {company['name']} ({company.get('website', 'No website')})")
        
        if len(companies) > MAX_COMPANIES_FOR_TESTING:
            print(f"   ... {len(companies) - MAX_COMPANIES_FOR_TESTING} more companies will be SKIPPED for testing")
        
        # Confirm processing
        print(f"\n⚠️  TESTING MODE - About to process ONLY {companies_to_show} companies:")
        print(f"   - Concurrency: {TESTING_CONCURRENCY} companies at once")
        print(f"   - Max companies: {MAX_COMPANIES_FOR_TESTING} (TESTING LIMIT)")
        print(f"   - Updates: After every company")
        print(f"   - Stop after: 3 consecutive errors")
        print(f"   - No browser authentication needed!")
        
        response = input("\nProceed with batch processing? (y/n): ")
        if response.lower() != 'y':
            print("Batch processing cancelled")
            return 0
        
        # Start processing
        print("\n🚀 Starting batch processing...")
        print(f"📊 Monitor progress at: https://docs.google.com/spreadsheets/d/{TEST_SHEET_ID}/edit")
        print("=" * 50)
        
        results = processor.process_batch(TEST_SHEET_ID, job_id="test_batch_service_001")
        
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
        print("\n✨ No browser authentication was needed - fully automated!")
        
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