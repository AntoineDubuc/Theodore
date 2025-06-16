#!/usr/bin/env python3
"""
Test Google Sheets Service Account authentication
No browser interaction required!
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from src.sheets_integration import GoogleSheetsServiceClient

# Constants
SERVICE_ACCOUNT_FILE = project_root / 'config' / 'credentials' / 'theodore-service-account.json'
TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'

def test_service_account():
    """Test service account authentication and basic operations"""
    print("🧪 Google Sheets Service Account Authentication Test")
    print("=" * 50)
    
    # Check if service account file exists
    if not SERVICE_ACCOUNT_FILE.exists():
        print(f"❌ Service account key file not found!")
        print(f"   Expected location: {SERVICE_ACCOUNT_FILE}")
        print("\n📋 Please follow these steps:")
        print("1. Complete the setup in SERVICE_ACCOUNT_SETUP.md")
        print("2. Download the service account key")
        print("3. Save it as: service_account_key.json")
        print("4. Place it in the credentials folder")
        return False
    
    print(f"✅ Found service account key file")
    
    try:
        # Initialize client
        print("\n🔐 Initializing Google Sheets client...")
        client = GoogleSheetsServiceClient(SERVICE_ACCOUNT_FILE)
        print("✅ Client initialized successfully")
        
        # Test sheet access
        print(f"\n📊 Testing access to spreadsheet...")
        if not client.validate_sheet_access(TEST_SHEET_ID):
            print("\n❌ Cannot access the spreadsheet!")
            print("Make sure you've shared the sheet with the service account email.")
            print("Check SERVICE_ACCOUNT_SETUP.md for instructions.")
            return False
        
        # Test reading data
        print("\n📖 Testing data reading...")
        companies = client.read_companies_to_process(TEST_SHEET_ID)
        
        if companies:
            print(f"✅ Successfully read {len(companies)} companies to process")
            print("\n📋 First 5 companies:")
            for i, company in enumerate(companies[:5]):
                print(f"   {i+1}. Row {company['row_number']}: {company['name']} - {company.get('website', 'No website')}")
        else:
            print("ℹ️  No companies found to process (or all are already processed)")
        
        # Test sheet setup
        print("\n🔧 Testing sheet structure setup...")
        if client.setup_dual_sheet_structure(TEST_SHEET_ID):
            print("✅ Sheet structure verified/updated successfully")
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Service account authentication is working.")
        print("\nYou can now run batch processing without any browser prompts!")
        print(f"\n📊 Sheet URL: https://docs.google.com/spreadsheets/d/{TEST_SHEET_ID}/edit")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def show_service_account_email():
    """Extract and display the service account email from the key file"""
    if SERVICE_ACCOUNT_FILE.exists():
        try:
            with open(SERVICE_ACCOUNT_FILE, 'r') as f:
                key_data = json.load(f)
                email = key_data.get('client_email', 'Not found')
                print(f"\n📧 Service Account Email: {email}")
                print("   (This is the email you need to share your sheet with)")
        except Exception as e:
            print(f"Could not read service account email: {e}")

def main():
    """Main function"""
    
    # Run the test
    success = test_service_account()
    
    # Show the service account email if available
    if SERVICE_ACCOUNT_FILE.exists():
        show_service_account_email()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())