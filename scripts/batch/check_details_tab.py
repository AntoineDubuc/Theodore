#!/usr/bin/env python3
"""
Check the Details tab content
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, 'src')

from src.sheets_integration import GoogleSheetsServiceClient

# Constants
SERVICE_ACCOUNT_FILE = Path('config/credentials/theodore-service-account.json')
TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'

def check_details_tab():
    """Check the Details tab content"""
    print("🔍 Checking Details Tab Content")
    print("=" * 50)
    
    try:
        sheets_client = GoogleSheetsServiceClient(SERVICE_ACCOUNT_FILE)
        
        # Check Details tab
        print("\n📋 Checking Details tab...")
        data = sheets_client.service.spreadsheets().values().get(
            spreadsheetId=TEST_SHEET_ID,
            range="Details!A1:BZ20"
        ).execute()
        
        if 'values' in data and len(data['values']) > 0:
            headers = data['values'][0]
            print(f"   Found {len(headers)} columns in Details tab")
            
            # Find key columns
            products_col = None
            website_col = None
            status_col = None
            
            print(f"\n   Column headers:")
            for i, header in enumerate(headers):
                print(f"      {i+1:2}. {header}")
                if 'product' in header.lower() or 'service' in header.lower():
                    products_col = i
                if 'website' in header.lower():
                    website_col = i
                if 'status' in header.lower():
                    status_col = i
            
            # Check data rows
            data_rows = data['values'][1:] if len(data['values']) > 1 else []
            print(f"\n   Data rows: {len(data_rows)}")
            
            if data_rows:
                print(f"\n   Sample data (first 5 rows):")
                for i, row in enumerate(data_rows[:5], 2):
                    company_name = row[0] if len(row) > 0 else "N/A"
                    products = row[products_col] if products_col and len(row) > products_col else "EMPTY"
                    website = row[website_col] if website_col and len(row) > website_col else "N/A"
                    
                    filled_fields = sum(1 for cell in row if cell and str(cell).strip())
                    coverage = filled_fields / len(headers) * 100 if headers else 0
                    
                    print(f"      Row {i}: {company_name}")
                    print(f"              Products: {products}")
                    print(f"              Coverage: {coverage:.1f}% ({filled_fields}/{len(headers)} fields)")
                    print()
            else:
                print("   ❌ No data rows found in Details tab!")
                
        else:
            print("   ❌ Details tab is empty or doesn't exist!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_details_tab()