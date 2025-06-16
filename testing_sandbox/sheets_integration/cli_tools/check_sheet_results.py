#!/usr/bin/env python3
"""
Check the results in the Google Sheet Details tab
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from src.sheets_integration import GoogleSheetsServiceClient

# Constants
SERVICE_ACCOUNT_FILE = project_root / 'config' / 'credentials' / 'theodore-service-account.json'
TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'

def check_sheet_results():
    """Check the results in the Details sheet"""
    print("📊 Checking Google Sheet Results")
    print("=" * 50)
    
    try:
        # Initialize sheets client
        sheets_client = GoogleSheetsServiceClient(SERVICE_ACCOUNT_FILE)
        
        # Get Details sheet data
        details = sheets_client.service.spreadsheets().values().get(
            spreadsheetId=TEST_SHEET_ID,
            range='Details!A:BZ'  # Extended range to get all fields
        ).execute()
        
        if 'values' in details and len(details['values']) > 1:
            headers = details['values'][0]
            print(f"📋 Found {len(headers)} fields in Details sheet\n")
            
            # Check each company row
            for row_idx, row in enumerate(details['values'][1:], start=2):
                if len(row) > 5:  # Has some data
                    company_name = row[0] if len(row) > 0 else "Unknown"
                    print(f"\n🏢 Row {row_idx}: {company_name}")
                    print("-" * 40)
                    
                    filled_fields = 0
                    total_fields = len(headers)
                    
                    # Sample important fields to display
                    important_fields = [
                        'name', 'industry', 'business_model', 'company_size', 
                        'location', 'employee_count_range', 'tech_stack',
                        'key_services', 'value_proposition', 'target_market',
                        'company_stage', 'tech_sophistication', 'partnerships',
                        'products_services_offered', 'company_description'
                    ]
                    
                    for col_idx, value in enumerate(row):
                        if col_idx < len(headers):
                            field_name = headers[col_idx]
                            if value and value.strip():
                                filled_fields += 1
                                
                                # Show important fields
                                if field_name.lower() in important_fields:
                                    if len(str(value)) > 100:
                                        print(f"   ✅ {field_name}: {str(value)[:100]}...")
                                    else:
                                        print(f"   ✅ {field_name}: {value}")
                    
                    print(f"\n   📈 Field Coverage: {filled_fields}/{total_fields} ({filled_fields/total_fields*100:.1f}%)")
                    
        else:
            print("❌ No data found in Details sheet")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_sheet_results()