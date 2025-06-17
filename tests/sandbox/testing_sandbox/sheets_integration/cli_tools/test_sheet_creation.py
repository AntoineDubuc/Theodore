#!/usr/bin/env python3
"""
Test Google Sheets dual-sheet creation
Tests creating and formatting the Progress Tracking and Complete Research Data sheets
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Import our field mapping
from config.sheets_field_mapping import (
    get_progress_sheet_headers,
    get_complete_data_headers,
    SHEET_CONFIG,
    SHEET_FORMATTING
)

# Constants
TOKEN_FILE = Path(__file__).parent.parent / 'credentials' / 'token.json'
TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'

def get_service():
    """Get authenticated Google Sheets service"""
    if not TOKEN_FILE.exists():
        print("❌ No authentication token found. Run test_auth.py first!")
        return None
    
    creds = Credentials.from_authorized_user_file(
        str(TOKEN_FILE), 
        ['https://www.googleapis.com/auth/spreadsheets']
    )
    
    return build('sheets', 'v4', credentials=creds)

def check_existing_sheets(service, spreadsheet_id):
    """Check what sheets already exist"""
    try:
        spreadsheet = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()
        
        existing_sheets = {}
        for sheet in spreadsheet['sheets']:
            sheet_title = sheet['properties']['title']
            sheet_id = sheet['properties']['sheetId']
            existing_sheets[sheet_title] = sheet_id
            
        return existing_sheets
        
    except HttpError as error:
        print(f"❌ Error checking sheets: {error}")
        return {}

def create_or_update_sheets(service, spreadsheet_id):
    """Create or update the dual-sheet structure"""
    
    # Check existing sheets
    existing_sheets = check_existing_sheets(service, spreadsheet_id)
    print(f"📋 Existing sheets: {list(existing_sheets.keys())}")
    
    requests = []
    
    # Progress Tracking Sheet
    progress_sheet_name = SHEET_CONFIG['progress_sheet_name']
    if progress_sheet_name not in existing_sheets:
        print(f"➕ Creating '{progress_sheet_name}' sheet...")
        requests.append({
            'addSheet': {
                'properties': {
                    'title': progress_sheet_name,
                    'gridProperties': {
                        'rowCount': 1000,
                        'columnCount': 12  # A-L columns
                    }
                }
            }
        })
    else:
        print(f"✅ '{progress_sheet_name}' sheet already exists")
    
    # Complete Research Data Sheet
    complete_sheet_name = SHEET_CONFIG['complete_data_sheet_name']
    if complete_sheet_name not in existing_sheets:
        print(f"➕ Creating '{complete_sheet_name}' sheet...")
        requests.append({
            'addSheet': {
                'properties': {
                    'title': complete_sheet_name,
                    'gridProperties': {
                        'rowCount': 1000,
                        'columnCount': 54  # A-BB columns (54 fields)
                    }
                }
            }
        })
    else:
        print(f"✅ '{complete_sheet_name}' sheet already exists")
    
    # Execute sheet creation if needed
    if requests:
        try:
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()
            print("✅ Sheets created successfully!")
        except HttpError as error:
            print(f"❌ Error creating sheets: {error}")
            return False
    
    return True

def add_headers(service, spreadsheet_id):
    """Add headers to both sheets"""
    
    # Progress sheet headers
    progress_headers = get_progress_sheet_headers()
    complete_headers = get_complete_data_headers()
    
    updates = []
    
    # Update Progress Tracking sheet headers
    updates.append({
        'range': f"{SHEET_CONFIG['progress_sheet_name']}!A1:L1",
        'values': [progress_headers]
    })
    
    # Update Complete Research Data sheet headers
    updates.append({
        'range': f"{SHEET_CONFIG['complete_data_sheet_name']}!A1:BB1",
        'values': [complete_headers]
    })
    
    try:
        print("📝 Adding headers to sheets...")
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                'valueInputOption': 'RAW',
                'data': updates
            }
        ).execute()
        print("✅ Headers added successfully!")
        return True
        
    except HttpError as error:
        print(f"❌ Error adding headers: {error}")
        return False

def format_sheets(service, spreadsheet_id):
    """Apply formatting to sheets"""
    
    # Get sheet IDs
    existing_sheets = check_existing_sheets(service, spreadsheet_id)
    
    progress_sheet_id = existing_sheets.get(SHEET_CONFIG['progress_sheet_name'])
    complete_sheet_id = existing_sheets.get(SHEET_CONFIG['complete_data_sheet_name'])
    
    if not progress_sheet_id or not complete_sheet_id:
        print("❌ Could not find sheet IDs for formatting")
        return False
    
    requests = []
    
    # Format headers (bold, dark background, white text)
    for sheet_id in [progress_sheet_id, complete_sheet_id]:
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': SHEET_FORMATTING['header_format']['background_color'],
                        'textFormat': {
                            'foregroundColor': SHEET_FORMATTING['header_format']['text_color'],
                            'bold': SHEET_FORMATTING['header_format']['bold']
                        }
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat)'
            }
        })
        
        # Freeze header row
        requests.append({
            'updateSheetProperties': {
                'properties': {
                    'sheetId': sheet_id,
                    'gridProperties': {
                        'frozenRowCount': SHEET_CONFIG['freeze_rows'],
                        'frozenColumnCount': SHEET_CONFIG['freeze_columns']
                    }
                },
                'fields': 'gridProperties.frozenRowCount,gridProperties.frozenColumnCount'
            }
        })
    
    # Auto-resize columns
    for sheet_id in [progress_sheet_id, complete_sheet_id]:
        requests.append({
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': sheet_id,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': 12 if sheet_id == progress_sheet_id else 54
                }
            }
        })
    
    try:
        print("🎨 Formatting sheets...")
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        print("✅ Formatting applied successfully!")
        return True
        
    except HttpError as error:
        print(f"❌ Error formatting sheets: {error}")
        return False

def add_sample_data(service, spreadsheet_id):
    """Add sample data to test the structure"""
    
    sample_companies = [
        ['Anthropic', 'https://anthropic.com'],
        ['OpenAI', 'https://openai.com'],
        ['Google DeepMind', 'https://deepmind.google.com']
    ]
    
    try:
        print("📊 Adding sample company data...")
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{SHEET_CONFIG['progress_sheet_name']}!A2:B4",
            valueInputOption='RAW',
            body={'values': sample_companies}
        ).execute()
        
        # Add status column for sample data
        status_data = [['pending'], ['pending'], ['pending']]
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{SHEET_CONFIG['progress_sheet_name']}!C2:C4",
            valueInputOption='RAW',
            body={'values': status_data}
        ).execute()
        
        print("✅ Sample data added successfully!")
        return True
        
    except HttpError as error:
        print(f"❌ Error adding sample data: {error}")
        return False

def main():
    """Main test function"""
    print("🧪 Google Sheets Dual-Sheet Creation Test")
    print("=" * 50)
    
    # Get authenticated service
    service = get_service()
    if not service:
        return 1
    
    print(f"📋 Working with spreadsheet: {TEST_SHEET_ID}")
    print()
    
    # Create or update sheets
    if not create_or_update_sheets(service, TEST_SHEET_ID):
        return 1
    
    # Add headers
    if not add_headers(service, TEST_SHEET_ID):
        return 1
    
    # Format sheets
    if not format_sheets(service, TEST_SHEET_ID):
        return 1
    
    # Add sample data
    if not add_sample_data(service, TEST_SHEET_ID):
        return 1
    
    print("\n✅ All tests passed! Dual-sheet structure is ready.")
    print(f"📊 View the spreadsheet: https://docs.google.com/spreadsheets/d/{TEST_SHEET_ID}/edit")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())