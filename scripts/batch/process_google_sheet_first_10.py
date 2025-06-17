#!/usr/bin/env python3
"""
Process first 10 companies from Google Sheets and update the Details tab
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import time

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.main_pipeline import TheodoreIntelligencePipeline
from src.models import CompanyIntelligenceConfig
from src.sheets_integration import GoogleSheetsServiceClient
from dotenv import load_dotenv

load_dotenv()

# Constants
SERVICE_ACCOUNT_FILE = Path('config/credentials/theodore-service-account.json')
TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'

def process_first_10_from_google_sheet():
    """Process first 10 companies from Google Sheet with enhanced extraction"""
    
    print("📊 Processing First 10 Companies from Google Sheet")
    print("=" * 70)
    print("Reading companies from Google Sheets and updating Details tab")
    print("=" * 70)
    
    try:
        # Initialize sheets client
        print("🔧 Initializing Google Sheets client...")
        sheets_client = GoogleSheetsServiceClient(SERVICE_ACCOUNT_FILE)
        
        # Initialize pipeline
        print("🔧 Initializing Theodore pipeline...")
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME')
        )
        
        # Get companies from sheet
        print("📋 Reading companies from Google Sheet...")
        companies = sheets_client.read_companies_to_process(TEST_SHEET_ID)
        
        if not companies:
            print("ℹ️  No companies found in sheet")
            return
        
        # Take only first 10
        companies = companies[:10]
        print(f"📊 Processing {len(companies)} companies:")
        for i, company in enumerate(companies, 1):
            print(f"   {i:2}. {company['name']:20} ({company.get('website', 'No website')})")
        
        print(f"\n🚀 Starting batch processing...")
        
        results = []
        successful = 0
        failed = 0
        
        for i, company in enumerate(companies, 1):
            print(f"\n📍 [{i}/{len(companies)}] Processing: {company['name']}")
            start_time = time.time()
            
            try:
                # Update status in sheet
                row_num = company.get('row', i+1)
                sheets_client.update_company_status(TEST_SHEET_ID, row_num, 'processing')
                
                # Process the company
                result = pipeline.process_single_company(
                    company['name'], 
                    company.get('website', '')
                )
                
                process_time = time.time() - start_time
                
                if result and result.scrape_status == 'success':
                    print(f"   ✅ Success in {process_time:.1f}s")
                    
                    # Show extracted data
                    if result.products_services_offered:
                        print(f"   📦 Products/Services: {len(result.products_services_offered)} items")
                        for product in result.products_services_offered[:3]:
                            print(f"      • {product}")
                    
                    if result.value_proposition:
                        print(f"   💡 Value Prop: {result.value_proposition[:60]}...")
                    
                    if result.company_culture:
                        print(f"   🎭 Culture: {result.company_culture[:60]}...")
                        
                    if result.location:
                        print(f"   📍 Location: {result.location}")
                        
                    if result.founding_year:
                        print(f"   📅 Founded: {result.founding_year}")
                    
                    # Update status to completed
                    sheets_client.update_company_status(TEST_SHEET_ID, row_num, 'completed')
                    
                    # Update complete data in Details sheet (if method exists)
                    try:
                        sheets_client.update_company_complete_data(TEST_SHEET_ID, row_num, result)
                        print(f"   📄 Updated Details sheet")
                    except AttributeError:
                        print(f"   ⚠️  Details sheet update method not available")
                    
                    successful += 1
                    
                    # Store results for summary
                    results.append({
                        'company': company['name'],
                        'status': 'success',
                        'process_time': f"{process_time:.1f}s",
                        'products_count': len(result.products_services_offered) if result.products_services_offered else 0,
                        'has_value_prop': bool(result.value_proposition),
                        'has_culture': bool(result.company_culture),
                        'has_location': bool(result.location),
                        'has_founding_year': bool(result.founding_year)
                    })
                    
                else:
                    print(f"   ❌ Failed: {result.scrape_error if result else 'No result returned'}")
                    sheets_client.update_company_status(TEST_SHEET_ID, row_num, 'failed')
                    failed += 1
                    
                    results.append({
                        'company': company['name'],
                        'status': 'failed',
                        'error': result.scrape_error if result else 'No result returned'
                    })
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                sheets_client.update_company_status(TEST_SHEET_ID, row_num, 'failed')
                failed += 1
                
                results.append({
                    'company': company['name'],
                    'status': 'error',
                    'error': str(e)
                })
            
            # Wait between companies
            if i < len(companies):
                print("   💤 Waiting 2 seconds...")
                time.sleep(2)
        
        # Final summary
        print(f"\n\n📊 BATCH PROCESSING SUMMARY")
        print("=" * 70)
        print(f"✅ Successful: {successful}/{len(companies)} ({successful/len(companies)*100:.1f}%)")
        print(f"❌ Failed: {failed}/{len(companies)} ({failed/len(companies)*100:.1f}%)")
        
        # Count extracted fields
        successful_results = [r for r in results if r.get('status') == 'success']
        if successful_results:
            products_count = sum(1 for r in successful_results if r.get('products_count', 0) > 0)
            value_prop_count = sum(1 for r in successful_results if r.get('has_value_prop'))
            culture_count = sum(1 for r in successful_results if r.get('has_culture'))
            location_count = sum(1 for r in successful_results if r.get('has_location'))
            founding_count = sum(1 for r in successful_results if r.get('has_founding_year'))
            
            print(f"\n📈 Field Extraction Results (from {len(successful_results)} successful):")
            print(f"   Products/Services: {products_count}/{len(successful_results)} ({products_count/len(successful_results)*100:.0f}%)")
            print(f"   Value Proposition: {value_prop_count}/{len(successful_results)} ({value_prop_count/len(successful_results)*100:.0f}%)")
            print(f"   Company Culture: {culture_count}/{len(successful_results)} ({culture_count/len(successful_results)*100:.0f}%)")
            print(f"   Location: {location_count}/{len(successful_results)} ({location_count/len(successful_results)*100:.0f}%)")
            print(f"   Founding Year: {founding_count}/{len(successful_results)} ({founding_count/len(successful_results)*100:.0f}%)")
        
        print(f"\n🌐 Google Sheet Updated!")
        print(f"   View results: https://docs.google.com/spreadsheets/d/{TEST_SHEET_ID}/edit")
        print(f"   Check Details tab for complete extracted data")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    process_first_10_from_google_sheet()