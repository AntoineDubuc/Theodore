#!/usr/bin/env python3
"""
Test processing 10 companies one at a time with simple approach
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from src.sheets_integration import GoogleSheetsServiceClient
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Constants
SERVICE_ACCOUNT_FILE = project_root / 'config' / 'credentials' / 'theodore-service-account.json'
TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'

def process_companies_simple():
    """Process 10 companies using simple sequential approach"""
    print("🚀 Processing 10 companies sequentially")
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
        
        # Get companies to process
        print("\n📊 Reading companies from sheet...")
        companies = sheets_client.read_companies_to_process(TEST_SHEET_ID)
        
        # Find unprocessed companies
        to_process = []
        for idx, company in enumerate(companies):
            status = company.get('status', '').lower()
            if status not in ['completed', 'processing'] and company.get('name') and company.get('website'):
                to_process.append({
                    'row': company.get('row_number', idx + 2),
                    'name': company.get('name'),
                    'website': company.get('website')
                })
            if len(to_process) >= 10:
                break
        
        print(f"   Found {len(to_process)} companies to process")
        
        # Process each company
        processed_count = 0
        failed_count = 0
        
        for i, company in enumerate(to_process, 1):
            print(f"\n{'='*60}")
            print(f"📦 Processing {i}/10: {company['name']}")
            print(f"   Row: {company['row']}")
            print(f"   Website: {company['website']}")
            
            try:
                # Update status to processing
                sheets_client.update_company_status(TEST_SHEET_ID, company['row'], 'processing')
                
                # Process the company
                print("   🔄 Starting research...")
                company_data = pipeline.process_single_company(
                    company_name=company['name'],
                    website=company['website']
                )
                
                # Update results
                if company_data.scrape_status == 'success':
                    print(f"   ✅ Successfully processed {company['name']}")
                    sheets_client.update_company_results(TEST_SHEET_ID, company['row'], company_data)
                    sheets_client.update_company_status(TEST_SHEET_ID, company['row'], 'completed')
                    processed_count += 1
                else:
                    print(f"   ⚠️  Scraping failed: {company_data.scrape_error}")
                    sheets_client.update_company_status(TEST_SHEET_ID, company['row'], 'failed', 
                                                      error=company_data.scrape_error)
                    failed_count += 1
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                failed_count += 1
                try:
                    sheets_client.update_company_status(TEST_SHEET_ID, company['row'], 'failed', 
                                                      error=str(e))
                except:
                    pass
            
            # Small delay between companies
            if i < len(to_process):
                print("   💤 Waiting 2 seconds before next company...")
                time.sleep(2)
        
        # Final summary
        duration = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"✅ Processing completed!")
        print(f"   Total time: {duration:.1f} seconds")
        print(f"   Processed: {processed_count} companies")
        print(f"   Failed: {failed_count} companies")
        print(f"   Average: {duration/(processed_count + failed_count):.1f} seconds per company")
        print(f"   Rate: {(processed_count + failed_count)/duration*3600:.0f} companies/hour")
        
        # Check results
        print("\n📊 Checking field coverage in Details sheet...")
        details = sheets_client.service.spreadsheets().values().get(
            spreadsheetId=TEST_SHEET_ID,
            range='Details!A1:BZ20'
        ).execute()
        
        if 'values' in details and len(details['values']) > 1:
            headers = details['values'][0]
            print(f"   Found {len(headers)} fields")
            
            # Analyze recent results
            recent_rows = []
            for row in details['values'][1:]:
                if len(row) > 10:  # Has data
                    recent_rows.append(row)
            
            if recent_rows:
                coverages = []
                for row in recent_rows[-10:]:  # Last 10 rows
                    filled = sum(1 for v in row if v and str(v).strip())
                    coverage = filled / len(headers) * 100
                    coverages.append(coverage)
                
                avg_coverage = sum(coverages) / len(coverages)
                print(f"   Average field coverage (last {len(coverages)} companies): {avg_coverage:.1f}%")
                print(f"   Best coverage: {max(coverages):.1f}%")
                print(f"   Worst coverage: {min(coverages):.1f}%")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    process_companies_simple()