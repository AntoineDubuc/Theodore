#!/usr/bin/env python3
"""
Check what tabs exist in the Google Sheet
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

def check_sheet_tabs():
    """Check what tabs exist in the Google Sheet"""
    print("🔍 Checking Google Sheet Tabs")
    print("=" * 50)
    
    try:
        sheets_client = GoogleSheetsServiceClient(SERVICE_ACCOUNT_FILE)
        
        # Get spreadsheet metadata
        spreadsheet = sheets_client.service.spreadsheets().get(
            spreadsheetId=TEST_SHEET_ID
        ).execute()
        
        sheets = spreadsheet.get('sheets', [])
        print(f"\nFound {len(sheets)} tabs:")
        
        for i, sheet in enumerate(sheets):
            properties = sheet.get('properties', {})
            title = properties.get('title', f'Sheet {i+1}')
            sheet_id = properties.get('sheetId')
            print(f"   {i+1}. '{title}' (ID: {sheet_id})")
        
        # Check first tab content
        if sheets:
            first_tab = sheets[0]['properties']['title']
            print(f"\n📊 Checking first tab '{first_tab}' content...")
            
            data = sheets_client.service.spreadsheets().values().get(
                spreadsheetId=TEST_SHEET_ID,
                range=f"'{first_tab}'!A1:Z10"
            ).execute()
            
            if 'values' in data:
                print(f"   Found {len(data['values'])} rows")
                
                # Show headers
                if len(data['values']) > 0:
                    headers = data['values'][0]
                    print(f"   Headers ({len(headers)} columns):")
                    for j, header in enumerate(headers[:10]):  # First 10 headers
                        print(f"      {j+1:2}. {header}")
                    if len(headers) > 10:
                        print(f"      ... and {len(headers)-10} more columns")
                
                # Show first few data rows
                print(f"\n   First few companies:")
                for i, row in enumerate(data['values'][1:6], 2):
                    if len(row) > 0:
                        company_name = row[0] if len(row) > 0 else "N/A"
                        website = row[1] if len(row) > 1 else "N/A"
                        print(f"      Row {i}: {company_name} | {website}")
        
        print(f"\n🌐 Sheet URL: https://docs.google.com/spreadsheets/d/{TEST_SHEET_ID}/edit")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_sheet_tabs()