#!/usr/bin/env python3
"""
Format the Details sheet headers (separate script for just formatting)
"""

import os
import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def format_details_sheet(spreadsheet_id: str):
    """Apply formatting to the Details sheet headers"""
    
    # Authenticate
    service_account_path = Path(__file__).parent.parent / 'config' / 'credentials' / 'theodore-service-account.json'
    
    credentials = service_account.Credentials.from_service_account_file(
        str(service_account_path),
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    
    service = build('sheets', 'v4', credentials=credentials)
    
    # Get sheet ID for Details
    try:
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        
        sheet_id = None
        for sheet in spreadsheet.get('sheets', []):
            if sheet['properties']['title'] == 'Details':
                sheet_id = sheet['properties']['sheetId']
                break
        
        if sheet_id is None:
            logger.error("Details sheet not found!")
            return
            
        logger.info(f"Found Details sheet with ID: {sheet_id}")
        
        # Apply formatting
        requests = []
        
        # Format header row with dark background
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 0,
                    'endRowIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {
                            'red': 0.2,
                            'green': 0.2,
                            'blue': 0.2
                        },
                        'textFormat': {
                            'foregroundColor': {
                                'red': 1.0,
                                'green': 1.0,
                                'blue': 1.0
                            },
                            'bold': True
                        }
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat)'
            }
        })
        
        # Freeze header row and first two columns
        requests.append({
            'updateSheetProperties': {
                'properties': {
                    'sheetId': sheet_id,
                    'gridProperties': {
                        'frozenRowCount': 1,
                        'frozenColumnCount': 2
                    }
                },
                'fields': 'gridProperties.frozenRowCount,gridProperties.frozenColumnCount'
            }
        })
        
        # Auto-resize columns
        requests.append({
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': sheet_id,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': 71  # BS is column 71
                }
            }
        })
        
        # Apply all formatting
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        
        logger.info("✅ Successfully formatted Details sheet headers")
        
    except HttpError as error:
        logger.error(f"❌ Error: {error}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/format_details_sheet.py <spreadsheet_id>")
        sys.exit(1)
    
    format_details_sheet(sys.argv[1])