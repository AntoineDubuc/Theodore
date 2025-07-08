#!/usr/bin/env python3
"""
Simple script to check the Google Sheet and list companies with names and websites
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.sheets_integration.google_sheets_service_client import GoogleSheetsServiceClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Check the Google Sheet and list companies"""
    
    # Google Sheet ID provided by user
    spreadsheet_id = "1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk"
    
    # Service account credentials file
    service_account_file = Path("config/credentials/theodore-service-account.json")
    
    if not service_account_file.exists():
        logger.error(f"Service account file not found: {service_account_file}")
        logger.error("Please ensure the service account JSON file is in the config/credentials/ directory")
        return
    
    try:
        # Initialize the Google Sheets client
        logger.info("Initializing Google Sheets client...")
        sheets_client = GoogleSheetsServiceClient(service_account_file)
        
        # Validate sheet access
        logger.info("Validating access to the Google Sheet...")
        if not sheets_client.validate_sheet_access(spreadsheet_id):
            logger.error("Cannot access the Google Sheet. Please check:")
            logger.error("1. The spreadsheet ID is correct")
            logger.error("2. The service account has been granted access to the sheet")
            logger.error("3. The sheet exists and is accessible")
            return
        
        # Try to read the 'Companies' sheet data
        logger.info("Reading companies from the 'Companies' sheet...")
        
        # Read all data from Companies sheet
        result = sheets_client.service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range="Companies!A:Z"  # Read all columns
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            logger.info("No data found in the Companies sheet.")
            return
        
        # Display header information
        headers = values[0] if values else []
        logger.info(f"Found {len(headers)} columns in the sheet:")
        for i, header in enumerate(headers):
            logger.info(f"  Column {i+1}: {header}")
        
        # Find companies with names and websites
        companies_found = []
        
        # Look for name and website columns
        name_columns = []
        website_columns = []
        
        for i, header in enumerate(headers):
            header_lower = header.lower()
            if any(keyword in header_lower for keyword in ['company', 'name', 'organization', 'org']):
                if 'name' in header_lower:
                    name_columns.append((i, header))
            elif any(keyword in header_lower for keyword in ['website', 'url', 'site', 'web']):
                website_columns.append((i, header))
        
        logger.info(f"\nFound potential name columns: {name_columns}")
        logger.info(f"Found potential website columns: {website_columns}")
        
        # Process companies
        if len(values) > 1:  # Skip header row
            logger.info(f"\nProcessing {len(values)-1} data rows...")
            
            for row_num, row in enumerate(values[1:], start=2):
                if not row:  # Skip empty rows
                    continue
                
                # Extract company info
                company_info = {
                    'row': row_num,
                    'raw_data': row
                }
                
                # Try to find name
                for name_col_idx, name_col_name in name_columns:
                    if len(row) > name_col_idx and row[name_col_idx]:
                        company_info['name'] = row[name_col_idx]
                        company_info['name_column'] = name_col_name
                        break
                
                # Try to find website
                for website_col_idx, website_col_name in website_columns:
                    if len(row) > website_col_idx and row[website_col_idx]:
                        company_info['website'] = row[website_col_idx]
                        company_info['website_column'] = website_col_name
                        break
                
                # Add to list if we found at least a name
                if 'name' in company_info and company_info['name']:
                    companies_found.append(company_info)
        
        # Display results
        logger.info(f"\n{'='*60}")
        logger.info(f"FOUND {len(companies_found)} COMPANIES WITH NAMES")
        logger.info(f"{'='*60}")
        
        for i, company in enumerate(companies_found[:10], 1):  # Show first 10
            logger.info(f"\n{i}. {company['name']}")
            if 'website' in company:
                logger.info(f"   Website: {company['website']}")
            else:
                logger.info(f"   Website: (not found)")
            logger.info(f"   Row: {company['row']}")
            
            # Show first few columns of raw data
            raw_preview = company['raw_data'][:5]  # First 5 columns
            logger.info(f"   Raw data preview: {raw_preview}")
        
        if len(companies_found) > 10:
            logger.info(f"\n... and {len(companies_found) - 10} more companies")
        
        logger.info(f"\n{'='*60}")
        logger.info("SUMMARY:")
        logger.info(f"Total companies found: {len(companies_found)}")
        logger.info(f"Companies with websites: {len([c for c in companies_found if 'website' in c])}")
        logger.info(f"Companies without websites: {len([c for c in companies_found if 'website' not in c])}")
        
    except Exception as e:
        logger.error(f"Error reading Google Sheet: {e}")
        logger.error("Please check:")
        logger.error("1. The service account has proper permissions")
        logger.error("2. The spreadsheet ID is correct")
        logger.error("3. The 'Companies' sheet exists")

if __name__ == "__main__":
    main()