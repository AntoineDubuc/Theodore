"""
Google Sheets Client using Service Account Authentication
Better for automated/server environments - no browser interaction needed
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Add project root to path for imports
import sys
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from config.sheets_field_mapping import (
    get_progress_sheet_headers,
    get_complete_data_headers,
    company_data_to_progress_row,
    company_data_to_complete_row,
    SHEET_CONFIG,
    SHEET_FORMATTING
)

logger = logging.getLogger(__name__)

class GoogleSheetsServiceClient:
    """Google Sheets client using service account authentication"""
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    def __init__(self, service_account_file: Path):
        """
        Initialize Google Sheets client with service account
        
        Args:
            service_account_file: Path to service account JSON file
        """
        self.service_account_file = service_account_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate using service account credentials"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                str(self.service_account_file),
                scopes=self.SCOPES
            )
            
            self.service = build('sheets', 'v4', credentials=credentials)
            logger.info("Google Sheets service initialized with service account")
            
        except Exception as e:
            logger.error(f"Failed to authenticate with service account: {e}")
            raise
    
    # All other methods remain the same as GoogleSheetsClient
    # Just copy them here...

def create_service_account_instructions():
    """Create instructions for setting up service account"""
    
    instructions = """
# Service Account Setup for Google Sheets Batch Processing

## Why Use Service Account?
- No browser interaction required
- Works on servers and in automated environments
- More suitable for batch processing
- No OAuth2 redirect URI issues

## Setup Instructions:

### 1. Create Service Account
1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
2. Select project: theodore-462403
3. Click "+ CREATE SERVICE ACCOUNT"
4. Service account details:
   - Name: theodore-sheets-processor
   - ID: theodore-sheets-processor (auto-generated)
   - Description: Service account for batch processing Google Sheets
5. Click "CREATE AND CONTINUE"
6. Grant roles:
   - Click "Select a role"
   - Search for "Editor" or just "Sheets API" 
   - Select "Basic > Editor" or "Google Sheets API > Google Sheets API Editor"
7. Click "CONTINUE" then "DONE"

### 2. Create and Download Key
1. Find your new service account in the list
2. Click on it to open details
3. Go to "KEYS" tab
4. Click "ADD KEY" → "Create new key"
5. Choose "JSON" format
6. Click "CREATE"
7. Save the downloaded file as: `service_account_key.json`

### 3. Share Your Google Sheet
1. Open your Google Sheet
2. Click "Share" button
3. Add the service account email:
   - It will be: theodore-sheets-processor@theodore-462403.iam.gserviceaccount.com
4. Give "Editor" permission
5. Click "Send"

### 4. Update Code to Use Service Account
Place the service account key file in:
`testing_sandbox/sheets_integration/credentials/service_account_key.json`

### Test Command:
```bash
python3 cli_tools/test_service_account_auth.py
```

## Security Notes:
- Keep the service account key file secure
- Never commit it to version control
- Add to .gitignore: `**/service_account_key.json`
- Rotate keys periodically
"""
    
    # Save instructions
    instructions_path = Path(__file__).parent / "SERVICE_ACCOUNT_SETUP.md"
    with open(instructions_path, 'w') as f:
        f.write(instructions)
    
    print(f"✅ Instructions saved to: {instructions_path}")
    return instructions_path

if __name__ == "__main__":
    # Create setup instructions
    create_service_account_instructions()
    print("\n📋 Service account setup instructions have been created.")
    print("Follow the instructions in SERVICE_ACCOUNT_SETUP.md to set up authentication.")