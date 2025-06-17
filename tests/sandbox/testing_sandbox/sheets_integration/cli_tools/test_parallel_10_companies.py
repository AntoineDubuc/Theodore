#!/usr/bin/env python3
"""
Test processing 10 companies in parallel with the batch processor
"""

import os
import sys
import logging
import time
from pathlib import Path
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from src.sheets_integration import GoogleSheetsServiceClient, BatchProcessorService
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

def test_parallel_processing():
    """Test processing 10 companies in parallel"""
    print("🚀 Testing parallel processing of 10 companies")
    print("=" * 50)
    
    start_time = time.time()
    
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
        
        # Initialize batch processor with parallel processing
        batch_processor = BatchProcessorService(
            sheets_client=sheets_client,
            concurrency=5,  # Process 5 companies concurrently
            max_companies_to_process=10  # Process exactly 10 companies
        )
        
        # Set the pipeline
        batch_processor.pipeline = pipeline
        
        # Get initial status
        print("\n📊 Checking initial status...")
        companies = sheets_client.read_companies_to_process(TEST_SHEET_ID)
        print(f"   Total companies in sheet: {len(companies)}")
        
        # Process companies
        print("\n🔄 Starting parallel batch processing...")
        print(f"   Concurrency: 5 companies at a time")
        print(f"   Total to process: 10 companies")
        print("-" * 50)
        
        results = batch_processor.process_batch(TEST_SHEET_ID)
        
        duration = time.time() - start_time
        
        print("\n" + "=" * 50)
        print(f"✅ Batch processing completed in {duration:.1f} seconds!")
        print(f"   Processed: {results['processed']} companies")
        print(f"   Failed: {results['failed']} companies")
        print(f"   Rate: {results.get('companies_per_minute', 0):.1f} companies/minute")
        print(f"   Duration: {results.get('duration_seconds', 0):.1f} seconds")
        
        # Check the results in the sheet
        print("\n📋 Checking processed companies in Details sheet...")
        details = sheets_client.service.spreadsheets().values().get(
            spreadsheetId=TEST_SHEET_ID,
            range='Details!A:Z'
        ).execute()
        
        if 'values' in details and len(details['values']) > 1:
            headers = details['values'][0]
            
            # Count companies with good field coverage
            good_coverage_count = 0
            total_processed = 0
            
            for row_idx, row in enumerate(details['values'][1:11], start=2):  # Check first 10 data rows
                if len(row) > 10:  # Has substantial data
                    total_processed += 1
                    filled_fields = sum(1 for value in row if value and str(value).strip())
                    coverage = filled_fields / len(headers) * 100
                    
                    company_name = row[1] if len(row) > 1 else "Unknown"
                    status = "✅" if coverage >= 40 else "⚠️"
                    
                    print(f"   {status} Row {row_idx}: {company_name} - {coverage:.1f}% field coverage ({filled_fields}/{len(headers)})")
                    
                    if coverage >= 40:
                        good_coverage_count += 1
            
            print(f"\n📊 Summary:")
            print(f"   Total processed with data: {total_processed}")
            print(f"   Good field coverage (≥40%): {good_coverage_count}")
            print(f"   Average processing time: {duration/10:.1f} seconds per company")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.error("Parallel processing error", exc_info=True)

if __name__ == "__main__":
    test_parallel_processing()