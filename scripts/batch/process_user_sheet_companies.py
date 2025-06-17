#!/usr/bin/env python3
"""
Process companies from the user's Google Sheet
Read from 'Companies' tab, research them, and update 'Details' tab
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, 'src')

from src.sheets_integration import GoogleSheetsServiceClient
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Constants
SERVICE_ACCOUNT_FILE = Path('config/credentials/theodore-service-account.json')
TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'

def process_user_sheet():
    """Process companies from user's sheet and update Details tab"""
    print("🚀 Processing Companies from User's Google Sheet")
    print("=" * 60)
    print("Reading from 'Companies' tab, researching with enhanced extraction,")
    print("and updating 'Details' tab with complete results")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Initialize components
        print("🔧 Initializing Theodore pipeline...")
        sheets_client = GoogleSheetsServiceClient(SERVICE_ACCOUNT_FILE)
        
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT', 'us-east-1'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        )
        
        # Read companies from 'Companies' tab
        print("\\n📊 Reading companies from 'Companies' tab...")
        companies_data = sheets_client.service.spreadsheets().values().get(
            spreadsheetId=TEST_SHEET_ID,
            range="Companies!A2:B20"  # Skip header, get first ~18 companies
        ).execute()
        
        companies = []
        if 'values' in companies_data:
            for i, row in enumerate(companies_data['values'], 2):  # Row 2 = index 0
                if len(row) >= 2 and row[0] and row[1]:
                    companies.append({
                        'row': i,
                        'name': row[0].strip(),
                        'website': row[1].strip()
                    })
        
        print(f"   Found {len(companies)} companies to process")
        for i, company in enumerate(companies[:10], 1):  # Show first 10
            print(f"      {i:2}. {company['name']:20} -> {company['website']}")
        
        if len(companies) == 0:
            print("❌ No companies found in 'Companies' tab!")
            return
        
        # Process first 10 companies
        companies = companies[:10]
        print(f"\\n🔄 Processing first {len(companies)} companies...")
        
        results = []
        successful = 0
        failed = 0
        
        for i, company in enumerate(companies, 1):
            print(f"\\n{'='*50}")
            print(f"📦 [{i}/{len(companies)}] Processing: {company['name']}")
            print(f"   Website: {company['website']}")
            print(f"   Row: {company['row']}")
            
            process_start = time.time()
            
            try:
                # Process the company with enhanced extraction
                print("   🔄 Starting enhanced research...")
                result = pipeline.process_single_company(
                    company_name=company['name'],
                    website=company['website']
                )
                
                process_time = time.time() - process_start
                
                if result and result.scrape_status == 'success':
                    print(f"   ✅ Success in {process_time:.1f}s")
                    
                    # Show extracted data preview
                    products_count = len(result.products_services_offered or [])
                    print(f"   📦 Products/Services: {products_count} items")
                    if result.products_services_offered:
                        for j, product in enumerate(result.products_services_offered[:3], 1):
                            print(f"      {j}. {product}")
                        if products_count > 3:
                            print(f"      ... and {products_count-3} more")
                    
                    if result.value_proposition:
                        print(f"   💡 Value Prop: {result.value_proposition[:80]}...")
                    
                    if result.location:
                        print(f"   📍 Location: {result.location}")
                    
                    if result.founding_year:
                        print(f"   📅 Founded: {result.founding_year}")
                    
                    if result.employee_count_range:
                        print(f"   👥 Employees: {result.employee_count_range}")
                    
                    # Update the Details sheet with complete data
                    print("   📄 Updating Details sheet...")
                    try:
                        sheets_client.update_company_results(
                            TEST_SHEET_ID,
                            company['row'],
                            result
                        )
                        print("   ✅ Details sheet updated successfully")
                    except Exception as update_error:
                        print(f"   ⚠️  Details update failed: {update_error}")
                    
                    successful += 1
                    results.append({
                        'company': company['name'],
                        'status': 'success',
                        'process_time': process_time,
                        'products_count': products_count,
                        'has_value_prop': bool(result.value_proposition),
                        'has_location': bool(result.location),
                        'has_founding_year': bool(result.founding_year)
                    })
                    
                else:
                    error_msg = result.scrape_error if result else "No result returned"
                    print(f"   ❌ Failed: {error_msg}")
                    failed += 1
                    results.append({
                        'company': company['name'],
                        'status': 'failed',
                        'error': error_msg
                    })
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                failed += 1
                results.append({
                    'company': company['name'],
                    'status': 'error',
                    'error': str(e)
                })
            
            # Small delay between companies
            if i < len(companies):
                print("   💤 Waiting 2 seconds...")
                time.sleep(2)
        
        # Final summary
        total_time = time.time() - start_time
        print(f"\\n{'='*60}")
        print(f"📊 PROCESSING COMPLETE!")
        print(f"   Total time: {total_time:.1f} seconds")
        print(f"   ✅ Successful: {successful}/{len(companies)} ({successful/len(companies)*100:.1f}%)")
        print(f"   ❌ Failed: {failed}/{len(companies)} ({failed/len(companies)*100:.1f}%)")
        
        # Field extraction summary
        successful_results = [r for r in results if r.get('status') == 'success']
        if successful_results:
            products_count = sum(1 for r in successful_results if r.get('products_count', 0) > 0)
            value_prop_count = sum(1 for r in successful_results if r.get('has_value_prop'))
            location_count = sum(1 for r in successful_results if r.get('has_location'))
            founding_count = sum(1 for r in successful_results if r.get('has_founding_year'))
            
            print(f"\\n📈 Field Extraction Results (from {len(successful_results)} successful):")
            print(f"   Products/Services: {products_count}/{len(successful_results)} ({products_count/len(successful_results)*100:.0f}%)")
            print(f"   Value Proposition: {value_prop_count}/{len(successful_results)} ({value_prop_count/len(successful_results)*100:.0f}%)")
            print(f"   Location: {location_count}/{len(successful_results)} ({location_count/len(successful_results)*100:.0f}%)")
            print(f"   Founding Year: {founding_count}/{len(successful_results)} ({founding_count/len(successful_results)*100:.0f}%)")
        
        print(f"\\n🌐 Updated Google Sheet:")
        print(f"   {TEST_SHEET_ID}")
        print(f"   https://docs.google.com/spreadsheets/d/{TEST_SHEET_ID}/edit#gid=81910028")
        print(f"\\n✨ Check the 'Details' tab for complete extracted company data!")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    process_user_sheet()