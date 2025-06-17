"""
Google Sheets Client for Theodore batch processing
Handles all Google Sheets operations including authentication, reading, writing, and formatting
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
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

class GoogleSheetsClient:
    """Client for Google Sheets operations"""
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    def __init__(self, credentials_file: Path, token_file: Path = None):
        """
        Initialize Google Sheets client
        
        Args:
            credentials_file: Path to OAuth2 credentials JSON file
            token_file: Path to store/retrieve token (optional)
        """
        self.credentials_file = credentials_file
        self.token_file = token_file or Path(__file__).parent / 'credentials' / 'token.json'
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate and create Google Sheets service"""
        creds = None
        
        # Load existing token
        if self.token_file.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_file), self.SCOPES)
            logger.info("Loaded existing credentials from token file")
        
        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials...")
                creds.refresh(Request())
            else:
                logger.info("Creating new credentials via OAuth2 flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_file), 
                    self.SCOPES
                )
                creds = flow.run_local_server(
                    port=0,  # Use any available port
                    prompt='consent',
                    access_type='offline'
                )
            
            # Save credentials
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
                logger.info(f"Saved credentials to {self.token_file}")
        
        self.service = build('sheets', 'v4', credentials=creds)
        logger.info("Google Sheets service initialized successfully")
    
    def validate_sheet_access(self, spreadsheet_id: str) -> bool:
        """
        Validate that we have access to the spreadsheet
        
        Args:
            spreadsheet_id: Google Sheets ID
            
        Returns:
            True if accessible, False otherwise
        """
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            logger.info(f"Successfully accessed spreadsheet: {spreadsheet['properties']['title']}")
            return True
        except HttpError as error:
            logger.error(f"Cannot access spreadsheet: {error}")
            return False
    
    def setup_dual_sheet_structure(self, spreadsheet_id: str) -> bool:
        """
        Setup the dual-sheet structure with existing 'Companies' and 'Details' tabs
        
        Args:
            spreadsheet_id: Google Sheets ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check existing sheets
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            existing_sheets = {
                sheet['properties']['title']: sheet['properties']['sheetId']
                for sheet in spreadsheet['sheets']
            }
            
            logger.info(f"Found existing sheets: {list(existing_sheets.keys())}")
            
            # Check if we need to add headers to existing sheets
            needs_headers = self._check_and_add_headers_if_needed(spreadsheet_id, existing_sheets)
            
            # Format sheets if headers were added
            if needs_headers:
                self._format_sheets_by_name(spreadsheet_id, existing_sheets)
            
            return True
            
        except HttpError as error:
            logger.error(f"Error setting up dual-sheet structure: {error}")
            return False
    
    def _check_and_add_headers_if_needed(self, spreadsheet_id: str, existing_sheets: Dict[str, int]) -> bool:
        """
        Check if sheets have headers and add them if needed
        
        Returns:
            True if headers were added, False if already present
        """
        headers_added = False
        
        # Check Companies sheet
        if 'Companies' in existing_sheets:
            try:
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range='Companies!A1:L1'
                ).execute()
                
                values = result.get('values', [])
                if not values or not values[0]:  # No header found
                    logger.info("Adding headers to Companies sheet")
                    progress_headers = get_progress_sheet_headers()
                    self.service.spreadsheets().values().update(
                        spreadsheetId=spreadsheet_id,
                        range='Companies!A1:L1',
                        valueInputOption='RAW',
                        body={'values': [progress_headers]}
                    ).execute()
                    headers_added = True
                else:
                    logger.info("Companies sheet already has headers")
                    
            except HttpError as error:
                logger.error(f"Error checking Companies sheet: {error}")
        
        # Check Details sheet
        if 'Details' in existing_sheets:
            try:
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range='Details!A1:BB1'
                ).execute()
                
                values = result.get('values', [])
                if not values or not values[0]:  # No header found
                    logger.info("Adding headers to Details sheet")
                    complete_headers = get_complete_data_headers()
                    self.service.spreadsheets().values().update(
                        spreadsheetId=spreadsheet_id,
                        range='Details!A1:BB1',
                        valueInputOption='RAW',
                        body={'values': [complete_headers]}
                    ).execute()
                    headers_added = True
                else:
                    logger.info("Details sheet already has headers")
                    
            except HttpError as error:
                logger.error(f"Error checking Details sheet: {error}")
        
        return headers_added
    
    def _format_sheets_by_name(self, spreadsheet_id: str, sheet_ids: Dict[str, int]):
        """Apply formatting to sheets using their actual names"""
        requests = []
        
        # Format Companies sheet if it exists
        if 'Companies' in sheet_ids:
            sheet_id = sheet_ids['Companies']
            requests.extend(self._get_format_requests(sheet_id))
        
        # Format Details sheet if it exists
        if 'Details' in sheet_ids:
            sheet_id = sheet_ids['Details']
            requests.extend(self._get_format_requests(sheet_id))
        
        if requests:
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()
            logger.info("Formatting applied to sheets")
    
    def _get_format_requests(self, sheet_id: int) -> List[Dict]:
        """Get formatting requests for a sheet"""
        return [
            {
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
            },
            {
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
            }
        ]
    
    def _add_headers(self, spreadsheet_id: str):
        """Add headers to both sheets"""
        progress_headers = get_progress_sheet_headers()
        complete_headers = get_complete_data_headers()
        
        updates = [
            {
                'range': f"{SHEET_CONFIG['progress_sheet_name']}!A1:L1",
                'values': [progress_headers]
            },
            {
                'range': f"{SHEET_CONFIG['complete_data_sheet_name']}!A1:BB1",
                'values': [complete_headers]
            }
        ]
        
        self.service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                'valueInputOption': 'RAW',
                'data': updates
            }
        ).execute()
        logger.info("Headers added to sheets")
    
    def _format_sheets(self, spreadsheet_id: str):
        """Apply formatting to sheets"""
        # Get sheet IDs
        spreadsheet = self.service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()
        
        sheet_ids = {
            sheet['properties']['title']: sheet['properties']['sheetId']
            for sheet in spreadsheet['sheets']
        }
        
        progress_sheet_id = sheet_ids[SHEET_CONFIG['progress_sheet_name']]
        complete_sheet_id = sheet_ids[SHEET_CONFIG['complete_data_sheet_name']]
        
        requests = []
        
        # Format headers and freeze rows
        for sheet_id in [progress_sheet_id, complete_sheet_id]:
            # Header formatting
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
            
            # Freeze rows/columns
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
        
        self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        logger.info("Formatting applied to sheets")
    
    def read_companies_to_process(self, spreadsheet_id: str) -> List[Dict[str, Any]]:
        """
        Read companies from the Companies sheet
        
        Args:
            spreadsheet_id: Google Sheets ID
            
        Returns:
            List of companies with their row numbers and data
        """
        try:
            # Read all data from Companies sheet
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range="Companies!A:L"
            ).execute()
            
            values = result.get('values', [])
            if len(values) <= 1:  # Only header row or empty
                return []
            
            headers = values[0]
            companies = []
            
            # Find column indices
            name_idx = headers.index('Company Name') if 'Company Name' in headers else 0
            website_idx = headers.index('Website') if 'Website' in headers else 1
            status_idx = headers.index('Status') if 'Status' in headers else 2
            
            # Process each row
            for row_num, row in enumerate(values[1:], start=2):  # Start from row 2
                # Skip if no company name
                if not row or len(row) <= name_idx or not row[name_idx]:
                    continue
                
                company_data = {
                    'row_number': row_num,
                    'name': row[name_idx],
                    'website': row[website_idx] if len(row) > website_idx else '',
                    'status': row[status_idx] if len(row) > status_idx else 'pending'
                }
                
                # Only process pending companies
                if company_data['status'] in ['pending', 'failed', '']:
                    companies.append(company_data)
            
            logger.info(f"Found {len(companies)} companies to process")
            return companies
            
        except HttpError as error:
            logger.error(f"Error reading companies: {error}")
            return []
    
    def update_company_status(self, spreadsheet_id: str, row_number: int, 
                            status: str, progress: str = "", error_notes: str = ""):
        """
        Update company status in Companies sheet
        
        Args:
            spreadsheet_id: Google Sheets ID
            row_number: Row number to update (1-indexed)
            status: Status value (pending/processing/completed/failed)
            progress: Progress percentage
            error_notes: Error message if failed
        """
        try:
            updates = []
            
            # Status update
            updates.append({
                'range': f"Companies!C{row_number}",
                'values': [[status]]
            })
            
            # Progress update
            if progress:
                updates.append({
                    'range': f"Companies!D{row_number}",
                    'values': [[progress]]
                })
            
            # Error notes update
            if error_notes:
                updates.append({
                    'range': f"Companies!L{row_number}",
                    'values': [[error_notes]]
                })
            
            # Timestamp update
            if status in ['completed', 'failed']:
                updates.append({
                    'range': f"Companies!E{row_number}",
                    'values': [[datetime.now().strftime('%Y-%m-%d %H:%M:%S')]]
                })
            
            self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={
                    'valueInputOption': 'RAW',
                    'data': updates
                }
            ).execute()
            
            logger.info(f"Updated status for row {row_number}: {status}")
            
        except HttpError as error:
            logger.error(f"Error updating status: {error}")
    
    def update_company_results(self, spreadsheet_id: str, row_number: int, 
                             company_data: Any):
        """
        Update both Companies and Details sheets with results
        
        Args:
            spreadsheet_id: Google Sheets ID
            row_number: Row number to update
            company_data: CompanyData object with research results
        """
        try:
            # Convert data to rows
            progress_row = company_data_to_progress_row(company_data, row_number)
            complete_row = company_data_to_complete_row(company_data)
            
            updates = []
            
            # Update Companies sheet
            updates.append({
                'range': f"Companies!A{row_number}:L{row_number}",
                'values': [progress_row]
            })
            
            # Update Details sheet
            updates.append({
                'range': f"Details!A{row_number}:BB{row_number}",
                'values': [complete_row]
            })
            
            self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={
                    'valueInputOption': 'USER_ENTERED',  # Allows formulas
                    'data': updates
                }
            ).execute()
            
            logger.info(f"Updated research results for row {row_number}")
            
        except HttpError as error:
            logger.error(f"Error updating results: {error}")
    
    def batch_update_statuses(self, spreadsheet_id: str, 
                            status_updates: List[Tuple[int, str, str]]):
        """
        Batch update multiple company statuses at once
        
        Args:
            spreadsheet_id: Google Sheets ID
            status_updates: List of (row_number, status, progress) tuples
        """
        try:
            updates = []
            
            for row_number, status, progress in status_updates:
                updates.append({
                    'range': f"Companies!C{row_number}:D{row_number}",
                    'values': [[status, progress]]
                })
            
            if updates:
                self.service.spreadsheets().values().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={
                        'valueInputOption': 'RAW',
                        'data': updates
                    }
                ).execute()
                
                logger.info(f"Batch updated {len(updates)} status entries")
                
        except HttpError as error:
            logger.error(f"Error in batch status update: {error}")