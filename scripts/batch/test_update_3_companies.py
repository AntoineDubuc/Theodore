#!/usr/bin/env python3
"""
Test updating 3 companies to the Google Sheet - focused on Products/Services
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

def test_update_companies():
    """Test updating first 3 companies to Google Sheet"""
    print("🧪 Testing Google Sheet Updates - First 3 Companies")
    print("=" * 60)
    print("Focus: Verify Products/Services data gets written to column R")
    print("=" * 60)
    
    try:
        # Initialize components
        sheets_client = GoogleSheetsServiceClient(SERVICE_ACCOUNT_FILE)
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT', 'us-east-1'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        )
        
        # Test companies (first 3)
        test_companies = [
            {'row': 2, 'name': 'connatix.com', 'website': 'connatix.com'},
            {'row': 3, 'name': 'jelli.com', 'website': 'jelli.com'},
            {'row': 4, 'name': 'tritondigital.com', 'website': 'tritondigital.com'}
        ]
        
        for i, company in enumerate(test_companies, 1):
            print(f"\n{'='*40}")
            print(f"🔬 [{i}/3] Testing: {company['name']}")
            print(f"   Website: {company['website']}")
            print(f"   Target row: {company['row']}")
            
            try:
                # Process the company
                print("   🔄 Processing...")
                result = pipeline.process_single_company(
                    company_name=company['name'],
                    website=company['website']
                )
                
                if result and result.scrape_status == 'success':
                    # Show what we extracted
                    products_count = len(result.products_services_offered or [])
                    print(f"   ✅ Extracted {products_count} products/services:")
                    
                    if result.products_services_offered:
                        for j, product in enumerate(result.products_services_offered, 1):
                            print(f"      {j}. {product}")
                    
                    # Update Google Sheet
                    print("   📄 Updating Google Sheet...")
                    sheets_client.update_company_results(
                        TEST_SHEET_ID,
                        company['row'],
                        result
                    )
                    print("   ✅ Sheet updated successfully!")
                    
                    # Verify the update by reading back
                    print("   🔍 Verifying update...")
                    verify_data = sheets_client.service.spreadsheets().values().get(
                        spreadsheetId=TEST_SHEET_ID,
                        range=f"Details!R{company['row']}"  # Column R = Products/Services
                    ).execute()
                    
                    if 'values' in verify_data and verify_data['values']:
                        written_products = verify_data['values'][0][0] if verify_data['values'][0] else "EMPTY"
                        print(f"   ✅ Verified: Column R contains: {written_products[:100]}...")
                    else:
                        print("   ❌ Column R appears to be empty after update")
                    
                else:
                    print(f"   ❌ Processing failed: {result.scrape_error if result else 'No result'}")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()
            
            # Wait between companies
            if i < len(test_companies):
                print("   💤 Waiting 3 seconds...")
                time.sleep(3)
        
        print(f"\n🌐 Check your Google Sheet now:")
        print(f"   https://docs.google.com/spreadsheets/d/{TEST_SHEET_ID}/edit#gid=81910028")
        print(f"   Look at Column R (Products/Services Offered) for the first 3 companies")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_update_companies()