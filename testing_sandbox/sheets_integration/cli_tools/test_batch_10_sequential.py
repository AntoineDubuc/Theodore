#!/usr/bin/env python3
"""
Test processing 10 companies sequentially to avoid SSL errors
"""

import os
import sys
import logging
import time
from pathlib import Path
from dotenv import load_dotenv
import json
import ssl
import certifi

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

# Configure SSL before importing Google APIs
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

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

def test_batch_processing():
    """Test processing 10 companies with better error handling"""
    print("🚀 Testing batch processing of 10 companies")
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
        
        # Initialize batch processor with sequential processing to avoid SSL issues
        batch_processor = BatchProcessorService(
            sheets_client=sheets_client,
            concurrency=2,  # Lower concurrency to avoid SSL issues
            max_companies_to_process=10,  # Process exactly 10 companies
            update_interval=1  # Update every second
        )
        
        # Set the pipeline
        batch_processor.pipeline = pipeline
        
        # Get initial status
        print("\n📊 Checking initial status...")
        companies = sheets_client.read_companies_to_process(TEST_SHEET_ID)
        
        # Find companies that haven't been processed yet
        unprocessed = [c for c in companies if c.get('status', '') not in ['completed', 'processing']]
        print(f"   Total companies in sheet: {len(companies)}")
        print(f"   Unprocessed companies: {len(unprocessed)}")
        
        # Show the companies we'll process
        print("\n📋 Companies to process:")
        for i, company in enumerate(unprocessed[:10], 1):
            print(f"   {i}. {company.get('name', 'Unknown')} - {company.get('website', 'No website')}")
        
        # Process companies
        print("\n🔄 Starting batch processing...")
        print(f"   Concurrency: 2 companies at a time (to avoid SSL issues)")
        print(f"   Total to process: 10 companies")
        print("-" * 50)
        
        # Process in smaller batches to handle errors better
        total_processed = 0
        total_failed = 0
        
        while total_processed + total_failed < 10:
            remaining = 10 - (total_processed + total_failed)
            batch_size = min(2, remaining)  # Process 2 at a time
            
            print(f"\n📦 Processing batch of {batch_size} companies...")
            
            # Temporarily set the limit for this batch
            batch_processor.max_companies_to_process = batch_size
            
            try:
                results = batch_processor.process_batch(TEST_SHEET_ID)
                total_processed += results.get('processed', 0)
                total_failed += results.get('failed', 0)
                
                print(f"   Batch result: {results.get('processed', 0)} processed, {results.get('failed', 0)} failed")
                
                # Small delay between batches to avoid rate limits
                if total_processed + total_failed < 10:
                    print("   Waiting 2 seconds before next batch...")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"   ❌ Batch error: {str(e)}")
                total_failed += batch_size
        
        duration = time.time() - start_time
        
        print("\n" + "=" * 50)
        print(f"✅ Batch processing completed in {duration:.1f} seconds!")
        print(f"   Total processed: {total_processed} companies")
        print(f"   Total failed: {total_failed} companies")
        print(f"   Average time: {duration/10:.1f} seconds per company")
        
        # Check the results in the sheet
        print("\n📋 Checking results in Details sheet...")
        details = sheets_client.service.spreadsheets().values().get(
            spreadsheetId=TEST_SHEET_ID,
            range='Details!A1:BZ15'  # Get headers + first 14 data rows
        ).execute()
        
        if 'values' in details and len(details['values']) > 1:
            headers = details['values'][0]
            
            # Analyze field coverage
            print("\n📊 Field Coverage Analysis:")
            print("-" * 60)
            
            coverage_stats = []
            
            for row_idx, row in enumerate(details['values'][1:], start=2):
                if len(row) > 10:  # Has substantial data
                    company_name = row[1] if len(row) > 1 else "Unknown"
                    
                    # Count filled fields
                    filled_fields = 0
                    important_fields_filled = 0
                    important_fields = ['industry', 'business_model', 'company_size', 
                                      'location', 'tech_stack', 'key_services', 
                                      'value_proposition', 'target_market']
                    
                    for col_idx, value in enumerate(row):
                        if col_idx < len(headers) and value and str(value).strip():
                            filled_fields += 1
                            if headers[col_idx].lower() in important_fields:
                                important_fields_filled += 1
                    
                    coverage = filled_fields / len(headers) * 100
                    coverage_stats.append(coverage)
                    
                    status = "✅" if coverage >= 40 else "⚠️" if coverage >= 20 else "❌"
                    print(f"   {status} Row {row_idx}: {company_name[:30]:30} | "
                          f"{coverage:5.1f}% ({filled_fields:2}/{len(headers)}) | "
                          f"Key fields: {important_fields_filled}/8")
            
            if coverage_stats:
                avg_coverage = sum(coverage_stats) / len(coverage_stats)
                good_coverage = sum(1 for c in coverage_stats if c >= 40)
                
                print("\n📈 Summary Statistics:")
                print(f"   Average field coverage: {avg_coverage:.1f}%")
                print(f"   Companies with good coverage (≥40%): {good_coverage}/{len(coverage_stats)}")
                print(f"   Processing rate: {10/duration*60:.1f} companies/hour")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.error("Batch processing error", exc_info=True)

if __name__ == "__main__":
    test_batch_processing()