#!/usr/bin/env python3
"""
Batch process companies from Google Sheets
Run from main Theodore directory to fix import paths
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.insert(0, 'src')

from src.sheets_integration import GoogleSheetsServiceClient
from src.models import CompanyIntelligenceConfig  
from src.main_pipeline import TheodoreIntelligencePipeline

# Constants
SERVICE_ACCOUNT_FILE = Path('config/credentials/theodore-service-account.json')
TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'

def batch_process_google_sheet():
    """Process companies from Google Sheets with working import paths"""
    print("🚀 BATCH PROCESSING GOOGLE SHEET COMPANIES")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Initialize sheets client
        print("📊 Initializing Google Sheets client...")
        sheets_client = GoogleSheetsServiceClient(SERVICE_ACCOUNT_FILE)
        
        # Initialize pipeline
        print("🔧 Initializing Theodore pipeline...")
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT', 'us-east-1'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        )
        
        # Get companies to process
        print("\n📋 Reading companies from Google Sheet...")
        companies = sheets_client.read_companies_to_process(TEST_SHEET_ID)
        
        if not companies:
            print("ℹ️  No companies to process")
            return
            
        # Limit to first 10 for this test
        companies = companies[:10]
        print(f"📊 Processing {len(companies)} companies:")
        for i, company in enumerate(companies, 1):
            print(f"   {i:2}. {company['name']:20} ({company.get('website', 'No website')})")
        
        print(f"\n🚀 Starting batch processing...")
        
        # Process companies one by one
        successful = 0
        failed = 0
        
        for i, company in enumerate(companies, 1):
            print(f"\n{'='*60}")
            print(f"📦 Processing {i}/{len(companies)}: {company['name']}")
            print(f"   Row: {company.get('row', 'Unknown')}")
            print(f"   Website: {company.get('website', 'No website')}")
            
            try:
                # Update status in sheet
                sheets_client.update_company_status(
                    TEST_SHEET_ID, 
                    company.get('row', i+1), 
                    'processing'
                )
                
                print("   🔄 Starting research...")
                
                # Process the company
                result = pipeline.process_single_company(
                    company['name'], 
                    company.get('website', '')
                )
                
                if result and result.scrape_status == 'success':
                    print(f"   ✅ Successfully processed {company['name']}")
                    print(f"   📊 Scrape status: {result.scrape_status}")
                    print(f"   📝 Products/Services: {len(result.products_services_offered or [])} items")
                    print(f"   🏢 Value Proposition: {bool(result.value_proposition)}")
                    print(f"   🎭 Company Culture: {bool(result.company_culture)}")
                    
                    # Update status in sheet
                    sheets_client.update_company_status(
                        TEST_SHEET_ID, 
                        company.get('row', i+1), 
                        'completed'
                    )
                    
                    # Update complete data in Details sheet
                    sheets_client.update_company_complete_data(
                        TEST_SHEET_ID,
                        company.get('row', i+1),
                        result
                    )
                    
                    successful += 1
                    
                else:
                    print(f"   ⚠️  Research failed or incomplete for {company['name']}")
                    sheets_client.update_company_status(
                        TEST_SHEET_ID, 
                        company.get('row', i+1), 
                        'failed'
                    )
                    failed += 1
                    
            except Exception as e:
                print(f"   ❌ Error processing {company['name']}: {e}")
                sheets_client.update_company_status(
                    TEST_SHEET_ID, 
                    company.get('row', i+1), 
                    'failed'
                )
                failed += 1
            
            # Wait between companies
            if i < len(companies):
                print("   💤 Waiting 2 seconds before next company...")
                time.sleep(2)
        
        # Final summary
        total_time = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"✅ BATCH PROCESSING COMPLETE!")
        print(f"   📊 Total time: {total_time:.1f} seconds")
        print(f"   ✅ Successful: {successful} companies")
        print(f"   ❌ Failed: {failed} companies")
        print(f"   📈 Success rate: {successful/(successful+failed)*100:.1f}%")
        print(f"   ⏱️  Average: {total_time/(successful+failed):.1f} seconds per company")
        print(f"\n🌐 Check your Google Sheet for updated data!")
        print(f"   Sheet: https://docs.google.com/spreadsheets/d/{TEST_SHEET_ID}/edit")
        
    except Exception as e:
        print(f"❌ Batch processing error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    batch_process_google_sheet()