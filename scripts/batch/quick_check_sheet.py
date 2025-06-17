#!/usr/bin/env python3
"""
Quick check of Google Sheet content
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

def check_sheet():
    """Check what's in the Google Sheet"""
    print("🔍 Checking Google Sheet Content")
    print("=" * 50)
    
    try:
        sheets_client = GoogleSheetsServiceClient(SERVICE_ACCOUNT_FILE)
        
        # Check Progress tab
        print("\n📊 Checking Progress tab...")
        progress_data = sheets_client.service.spreadsheets().values().get(
            spreadsheetId=TEST_SHEET_ID,
            range='Progress!A1:Z20'
        ).execute()
        
        if 'values' in progress_data:
            print(f"   Found {len(progress_data['values'])} rows")
            if len(progress_data['values']) > 1:
                headers = progress_data['values'][0]
                print(f"   Headers: {headers[:5]}...")
                
                # Show first few company rows
                for i, row in enumerate(progress_data['values'][1:6], 1):
                    if len(row) > 0:
                        company_name = row[0] if len(row) > 0 else "N/A"
                        status = row[2] if len(row) > 2 else "N/A"
                        print(f"   Row {i+1}: {company_name} - Status: {status}")
        
        # Check Details tab
        print("\n📋 Checking Details tab...")
        details_data = sheets_client.service.spreadsheets().values().get(
            spreadsheetId=TEST_SHEET_ID,
            range='Details!A1:Z5'
        ).execute()
        
        if 'values' in details_data:
            print(f"   Found {len(details_data['values'])} rows")
            if len(details_data['values']) > 1:
                headers = details_data['values'][0]
                print(f"   Headers: {headers[:10]}...")
                
                # Check for Products/Services column
                products_col = None
                for i, header in enumerate(headers):
                    if 'product' in header.lower() or 'service' in header.lower():
                        products_col = i
                        print(f"   Found Products/Services column at index {i}: '{header}'")
                        break
                
                if products_col is None:
                    print("   ❌ No Products/Services column found!")
                
                # Show first few data rows
                for i, row in enumerate(details_data['values'][1:4], 1):
                    if len(row) > 0:
                        company_name = row[0] if len(row) > 0 else "N/A"
                        products = row[products_col] if products_col and len(row) > products_col else "N/A"
                        print(f"   Row {i+1}: {company_name} - Products: {products}")
        
        print(f"\n🌐 Sheet URL: https://docs.google.com/spreadsheets/d/{TEST_SHEET_ID}/edit")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_sheet()