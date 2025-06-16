#!/usr/bin/env python3
"""
Test batch processing with the fixed extraction that populates raw_content
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from src.sheets_integration import GoogleSheetsServiceClient, BatchProcessorService
from src.models import CompanyData, CompanyIntelligenceConfig
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
    """Test batch processing with fixed extraction"""
    print("🚀 Testing batch processing with fixed extraction")
    print("=" * 50)
    
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
        
        # Initialize batch processor with pipeline
        batch_processor = BatchProcessorService(
            sheets_client=sheets_client,
            concurrency=1,  # Process one at a time for testing
            max_companies_to_process=2  # Process only 2 companies
        )
        
        # Set the pipeline
        batch_processor.pipeline = pipeline
        
        # Process companies
        print("\n📊 Starting batch processing...")
        results = batch_processor.process_batch(TEST_SHEET_ID)
        
        print(f"\n✅ Batch processing completed!")
        print(f"   Processed: {results['processed']}")
        print(f"   Failed: {results['failed']}")
        if 'skipped' in results:
            print(f"   Skipped: {results['skipped']}")
        
        # Check the results in the sheet
        print("\n📋 Checking processed companies in Details sheet...")
        details = sheets_client.spreadsheet.values().get(
            spreadsheetId=TEST_SHEET_ID,
            range='Details!A:Z'
        ).execute()
        
        if 'values' in details and len(details['values']) > 1:
            headers = details['values'][0]
            for row_idx, row in enumerate(details['values'][1:], start=2):
                if len(row) > 10:  # Has substantial data
                    print(f"\n🏢 Company Row {row_idx}:")
                    filled_fields = 0
                    total_fields = 0
                    
                    for col_idx, value in enumerate(row):
                        if col_idx < len(headers):
                            field_name = headers[col_idx]
                            total_fields += 1
                            if value and value.strip():
                                filled_fields += 1
                                if len(value) > 100:
                                    print(f"   ✅ {field_name}: {value[:100]}...")
                                else:
                                    print(f"   ✅ {field_name}: {value}")
                    
                    print(f"\n   📈 Filled {filled_fields} out of {total_fields} fields ({filled_fields/total_fields*100:.1f}%)")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.error("Batch processing error", exc_info=True)

if __name__ == "__main__":
    test_batch_processing()