#!/usr/bin/env python3
"""
Test processing a SINGLE company - Automatic version (no prompts)
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from src.sheets_integration import GoogleSheetsServiceClient

# Constants
SERVICE_ACCOUNT_FILE = project_root / 'config' / 'credentials' / 'theodore-service-account.json'
TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'

def test_single_company():
    """Test processing exactly ONE company without prompts"""
    print("🧪 Single Company Processing Test (Automatic)")
    print("=" * 50)
    
    # Check service account file
    if not SERVICE_ACCOUNT_FILE.exists():
        print(f"❌ Service account key not found!")
        print(f"   Expected at: {SERVICE_ACCOUNT_FILE}")
        return 1
    
    try:
        # Initialize client
        print("📊 Initializing Google Sheets client...")
        client = GoogleSheetsServiceClient(SERVICE_ACCOUNT_FILE)
        
        # Validate access
        if not client.validate_sheet_access(TEST_SHEET_ID):
            print("❌ Cannot access spreadsheet")
            return 1
        
        # Read companies
        print("\n📋 Reading companies from sheet...")
        companies = client.read_companies_to_process(TEST_SHEET_ID)
        
        if not companies:
            print("❌ No companies found to process")
            return 1
        
        # Take ONLY the first company
        first_company = companies[0]
        print(f"\n🎯 Processing this company:")
        print(f"   Row {first_company['row_number']}: {first_company['name']}")
        print(f"   Website: {first_company.get('website', 'No website')}")
        
        print("\n⚠️  SKIPPING actual processing for safety")
        print("   To actually process, run test_single_company.py and confirm")
        
        # Just update status to show it works
        print("\n🔧 Testing status update...")
        client.update_company_status(
            TEST_SHEET_ID,
            first_company['row_number'],
            'pending',  # Keep as pending, don't actually process
            '',
            'Test run - not processed'
        )
        
        print("\n✅ Test completed successfully!")
        print(f"   Company: {first_company['name']}")
        print(f"   Row: {first_company['row_number']}")
        print(f"   Status update: Working")
        print(f"\n📊 View sheet: https://docs.google.com/spreadsheets/d/{TEST_SHEET_ID}/edit")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    return test_single_company()

if __name__ == "__main__":
    sys.exit(main())