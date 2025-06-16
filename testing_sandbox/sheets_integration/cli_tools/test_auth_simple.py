#!/usr/bin/env python3
"""
Simple authentication test that provides clear instructions
"""

import os
import sys
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

def main():
    print("🧪 Google Sheets Authentication Check")
    print("=" * 50)
    
    # Check credentials file
    if not CREDENTIALS_FILE.exists():
        print(f"❌ Credentials file not found: {CREDENTIALS_FILE}")
        return 1
    else:
        print(f"✅ Found credentials file")
    
    # Check for existing token
    if TOKEN_FILE.exists():
        print(f"✅ Found existing token file at: {TOKEN_FILE}")
        print("\nTrying to use existing authentication...")
        
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
            if creds and creds.valid:
                print("✅ Existing credentials are valid!")
                
                # Test API access
                service = build('sheets', 'v4', credentials=creds)
                test_sheet_id = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'
                
                spreadsheet = service.spreadsheets().get(
                    spreadsheetId=test_sheet_id
                ).execute()
                
                print(f"✅ Successfully accessed test spreadsheet: {spreadsheet['properties']['title']}")
                print("\n🎉 Authentication is working! You can proceed with batch processing.")
                return 0
                
            elif creds and creds.expired and creds.refresh_token:
                print("🔄 Token expired, attempting to refresh...")
                creds.refresh(Request())
                
                # Save refreshed token
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
                print("✅ Token refreshed successfully!")
                return 0
                
        except Exception as e:
            print(f"⚠️  Error with existing token: {e}")
    
    print("\n❌ No valid authentication found.")
    print("\n📋 To authenticate, you need to:")
    print("1. Run this command to start authentication:")
    print("   python3 cli_tools/test_auth.py")
    print("\n2. A browser window will open")
    print("3. Log in with the Google account that has access to the spreadsheet")
    print("4. Grant the requested permissions")
    print("5. The authentication will complete automatically")
    print("\n⚠️  Note: The browser authentication requires manual interaction")
    print("   If running on a remote server, use local authentication first")
    
    return 1

if __name__ == "__main__":
    sys.exit(main())