#!/usr/bin/env python3
"""
Process exactly ONE company - connatix.com
This will actually run the Theodore AI research pipeline
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from src.sheets_integration import GoogleSheetsServiceClient
from src.main_pipeline import TheodoreIntelligencePipeline
from src.models import CompanyIntelligenceConfig

# Constants
SERVICE_ACCOUNT_FILE = project_root / 'config' / 'credentials' / 'theodore-service-account.json'
TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_one_company():
    """Process exactly ONE company"""
    print("🚀 Processing ONE Company with Theodore AI")
    print("=" * 50)
    
    try:
        # Initialize Google Sheets client
        print("📊 Initializing Google Sheets client...")
        sheets_client = GoogleSheetsServiceClient(SERVICE_ACCOUNT_FILE)
        
        # Read companies
        companies = sheets_client.read_companies_to_process(TEST_SHEET_ID)
        if not companies:
            print("❌ No companies to process")
            return 1
        
        # Take first company
        company = companies[0]
        print(f"\n🎯 Processing: {company['name']}")
        print(f"   Row: {company['row_number']}")
        print(f"   Website: {company.get('website', 'No website')}")
        
        # Update status to processing
        print("\n📝 Updating status to 'processing'...")
        sheets_client.update_company_status(
            TEST_SHEET_ID,
            company['row_number'],
            'processing',
            '0%'
        )
        
        # Initialize Theodore pipeline
        print("\n🤖 Initializing Theodore AI pipeline...")
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT', 'us-east-1'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        )
        
        # Process the company
        print(f"\n🔬 Starting AI research for {company['name']}...")
        print("   This may take 1-2 minutes...")
        
        try:
            company_data = pipeline.process_single_company(
                company_name=company['name'],
                website=company.get('website', '')
            )
            
            if company_data and company_data.name:
                print(f"\n✅ Research completed successfully!")
                print(f"   Industry: {company_data.industry}")
                print(f"   Stage: {company_data.company_stage}")
                print(f"   Tech Level: {company_data.tech_sophistication}")
                print(f"   Summary: {company_data.ai_summary[:200]}..." if company_data.ai_summary else "")
                
                # Update sheets with results
                print("\n📊 Updating Google Sheets with results...")
                sheets_client.update_company_results(
                    TEST_SHEET_ID,
                    company['row_number'],
                    company_data
                )
                
                # Mark as completed
                sheets_client.update_company_status(
                    TEST_SHEET_ID,
                    company['row_number'],
                    'completed',
                    '100%'
                )
                
                print(f"\n🎉 SUCCESS! Company processed and sheet updated.")
                print(f"\n📊 View results: https://docs.google.com/spreadsheets/d/{TEST_SHEET_ID}/edit#gid=0&range=A{company['row_number']}")
                
            else:
                # Mark as failed
                sheets_client.update_company_status(
                    TEST_SHEET_ID,
                    company['row_number'],
                    'failed',
                    '0%',
                    'No data returned from research'
                )
                print(f"\n❌ Failed to get research data")
                
        except Exception as e:
            logger.error(f"Error processing company: {str(e)}", exc_info=True)
            # Mark as failed with error
            sheets_client.update_company_status(
                TEST_SHEET_ID,
                company['row_number'],
                'failed',
                '0%',
                f'Error: {str(e)[:200]}'
            )
            print(f"\n❌ Error during processing: {str(e)}")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return 1

def main():
    print("⚠️  This will process ONE real company using Theodore's AI")
    print("   Company: connatix.com")
    print("   Estimated time: 1-2 minutes")
    print("   AI API costs: Small amount")
    print()
    
    return process_one_company()

if __name__ == "__main__":
    sys.exit(main())