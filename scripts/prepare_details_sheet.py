#!/usr/bin/env python3
"""
Prepare Google Sheets 'Details' Tab with Headers
===============================================

This script sets up the 'Details' tab in Google Sheets with the correct headers
representing all CompanyData fields for the Antoine batch processing.

Usage:
    python scripts/prepare_details_sheet.py <spreadsheet_id>
    
Example:
    python scripts/prepare_details_sheet.py 1UEzGinv3IkR35F1UU6JdhiizNoLfaR1E0Vf4QXafbCw
"""

import os
import sys
from pathlib import Path
import logging
from typing import List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config.sheets_field_mapping import (
    get_complete_data_headers,
    SHEET_CONFIG,
    SHEET_FORMATTING,
    COMPLETE_DATA_COLUMNS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

class DetailsSheetPreparer:
    """Prepares the Details sheet with appropriate headers"""
    
    def __init__(self, spreadsheet_id: str):
        self.spreadsheet_id = spreadsheet_id
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate using service account"""
        # Try multiple possible locations for the service account file
        possible_paths = [
            Path(__file__).parent.parent / 'config' / 'credentials' / 'theodore-service-account.json',
            Path.home() / 'theodore-service-account.json',
            Path(__file__).parent.parent / 'theodore-service-account.json'
        ]
        
        service_account_path = None
        for path in possible_paths:
            if path.exists():
                service_account_path = path
                break
        
        if not service_account_path:
            raise FileNotFoundError(
                f"Service account key not found in any of these locations:\n" +
                "\n".join(f"  - {p}" for p in possible_paths) +
                "\nPlease ensure the service account JSON file is in place."
            )
        
        credentials = service_account.Credentials.from_service_account_file(
            str(service_account_path),
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        self.service = build('sheets', 'v4', credentials=credentials)
        logger.info("✅ Authenticated with Google Sheets API")
    
    def ensure_details_sheet_exists(self):
        """Ensure the Details sheet exists, create if necessary"""
        try:
            # Get all sheets
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheets = spreadsheet.get('sheets', [])
            sheet_names = [sheet['properties']['title'] for sheet in sheets]
            
            if 'Details' not in sheet_names:
                # Create Details sheet
                request = {
                    'addSheet': {
                        'properties': {
                            'title': 'Details',
                            'index': 1,  # Put it as second sheet
                            'gridProperties': {
                                'rowCount': 1000,
                                'columnCount': 100  # Enough for all our fields
                            }
                        }
                    }
                }
                
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={'requests': [request]}
                ).execute()
                
                logger.info("✅ Created 'Details' sheet")
            else:
                logger.info("✅ 'Details' sheet already exists")
                
            # Get sheet ID for Details
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            for sheet in spreadsheet.get('sheets', []):
                if sheet['properties']['title'] == 'Details':
                    return sheet['properties']['sheetId']
                    
        except HttpError as error:
            logger.error(f"❌ Error accessing spreadsheet: {error}")
            raise
    
    def prepare_headers(self, sheet_id: int):
        """Add headers to the Details sheet"""
        headers = get_complete_data_headers()
        
        # Log the headers being added
        logger.info(f"\n📋 Preparing to add {len(headers)} field headers to Details sheet:")
        
        # Display headers with their column positions
        for i, (col, info) in enumerate(sorted(COMPLETE_DATA_COLUMNS.items())):
            logger.info(f"   Column {col}: {info['header']} ({info['field']})")
        
        # Prepare the values
        values = [headers]  # Single row of headers
        
        # Update the sheet
        range_name = 'Details!A1:BS1'  # BS is column 71 (we have 71 fields)
        
        try:
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': values}
            ).execute()
            
            logger.info(f"\n✅ Successfully added {len(headers)} headers to Details sheet")
            
        except HttpError as error:
            logger.error(f"❌ Error updating headers: {error}")
            raise
    
    def format_headers(self, sheet_id: int):
        """Apply formatting to the header row"""
        requests = []
        
        # Format header row
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
        
        # Freeze header row
        requests.append({
            'updateSheetProperties': {
                'properties': {
                    'sheetId': sheet_id,
                    'gridProperties': {
                        'frozenRowCount': 1,
                        'frozenColumnCount': 2  # Freeze ID and Company Name
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
        
        try:
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
            logger.info("✅ Applied formatting to Details sheet headers")
            
        except HttpError as error:
            logger.error(f"❌ Error formatting headers: {error}")
            raise
    
    def run(self):
        """Main execution method"""
        logger.info(f"\n🚀 Preparing Details sheet for spreadsheet: {self.spreadsheet_id}")
        
        # Ensure Details sheet exists
        sheet_id = self.ensure_details_sheet_exists()
        
        # Add headers
        self.prepare_headers(sheet_id)
        
        # Format headers
        self.format_headers(sheet_id)
        
        logger.info("\n✨ Details sheet preparation complete!")
        logger.info("\n📝 Field Summary:")
        logger.info(f"   - Total fields configured: {len(COMPLETE_DATA_COLUMNS)}")
        logger.info("   - Categories covered:")
        logger.info("     • Core Identity (A-F)")
        logger.info("     • Technology Stack (G-I)")
        logger.info("     • Business Intelligence (J-P)")
        logger.info("     • Company Details (Q-AC)")
        logger.info("     • Similarity Metrics (AD-AM)")
        logger.info("     • Batch Research Intelligence (AN-AU)")
        logger.info("     • AI Analysis (AV-AX)")
        logger.info("     • System Metadata (AY-BB)")
        logger.info("     • SaaS Classification (BC-BH)")
        logger.info("     • Additional Fields (BI-BP)")
        logger.info("     • Token & Cost Tracking (BQ-BS)")
        
        logger.info("\n🎯 Next Steps:")
        logger.info("   1. Run batch processing to populate the Details sheet")
        logger.info("   2. The Companies sheet will link to Details for each company")
        logger.info("   3. All CompanyData fields will be captured in Details")


def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python scripts/prepare_details_sheet.py <spreadsheet_id>")
        print("\nExample:")
        print("  python scripts/prepare_details_sheet.py 1UEzGinv3IkR35F1UU6JdhiizNoLfaR1E0Vf4QXafbCw")
        sys.exit(1)
    
    spreadsheet_id = sys.argv[1]
    
    try:
        preparer = DetailsSheetPreparer(spreadsheet_id)
        preparer.run()
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()