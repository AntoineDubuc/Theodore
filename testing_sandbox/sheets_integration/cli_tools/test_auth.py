#!/usr/bin/env python3
"""
Test Google Sheets OAuth2 authentication
Tests the authentication flow and basic API access
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Constants
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_FILE = project_root / 'config' / 'credentials' / 'client_secret_1096944990043-5u1eohnobc583lvueqr2cvfvm9tcjc3p.apps.googleusercontent.com.json'
TOKEN_FILE = Path(__file__).parent.parent / 'credentials' / 'token.json'

def authenticate():
    """Authenticate and return Google Sheets service"""
    creds = None
    
    # Token file stores the user's access and refresh tokens
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            print(f"🔐 Starting OAuth2 flow...")
            print(f"📄 Using credentials file: {CREDENTIALS_FILE}")
            
            if not CREDENTIALS_FILE.exists():
                print(f"❌ Credentials file not found: {CREDENTIALS_FILE}")
                return None
                
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), 
                SCOPES
            )
            
            # Use local server for auth with default settings
            creds = flow.run_local_server(
                port=0,  # Use any available port
                prompt='consent',
                access_type='offline'
            )
            
        # Save the credentials for the next run
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            print(f"✅ Credentials saved to: {TOKEN_FILE}")
    
    return build('sheets', 'v4', credentials=creds)

def test_sheets_access(service):
    """Test basic Google Sheets API access"""
    test_sheet_id = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'
    
    try:
        # Test 1: Get spreadsheet metadata
        print("\n📊 Testing spreadsheet access...")
        spreadsheet = service.spreadsheets().get(
            spreadsheetId=test_sheet_id
        ).execute()
        
        print(f"✅ Successfully accessed spreadsheet: {spreadsheet['properties']['title']}")
        print(f"   Sheets: {[sheet['properties']['title'] for sheet in spreadsheet['sheets']]}")
        
        # Test 2: Read values from sheet
        print("\n📖 Testing read access...")
        result = service.spreadsheets().values().get(
            spreadsheetId=test_sheet_id,
            range='A1:B10'
        ).execute()
        
        values = result.get('values', [])
        if values:
            print(f"✅ Successfully read {len(values)} rows")
            for i, row in enumerate(values[:3]):  # Show first 3 rows
                print(f"   Row {i+1}: {row}")
        else:
            print("ℹ️  No data found in range A1:B10")
        
        # Test 3: Get sheet properties
        print("\n🔍 Sheet properties:")
        for sheet in spreadsheet['sheets']:
            props = sheet['properties']
            print(f"   - {props['title']}: {props['gridProperties']['rowCount']} rows x {props['gridProperties']['columnCount']} columns")
        
        return True
        
    except HttpError as error:
        print(f"❌ An error occurred: {error}")
        return False

def main():
    """Main test function"""
    print("🧪 Google Sheets Authentication Test")
    print("=" * 50)
    
    # Authenticate
    service = authenticate()
    if not service:
        print("❌ Authentication failed")
        return 1
    
    print("✅ Authentication successful!")
    
    # Test API access
    if test_sheets_access(service):
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())