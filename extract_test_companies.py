#!/usr/bin/env python3
"""
Extract first 10 companies from Google Sheet for testing
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

def clean_domain_to_company_name(domain):
    """Convert domain to a readable company name"""
    if not domain:
        return ""
    
    # Remove protocol if present
    domain = domain.replace('http://', '').replace('https://', '')
    
    # Remove www. if present
    if domain.startswith('www.'):
        domain = domain[4:]
    
    # Remove trailing slashes
    domain = domain.rstrip('/')
    
    # Split by dots and take the main part
    parts = domain.split('.')
    if len(parts) >= 2:
        # Take the part before the TLD
        main_part = parts[0]
        # Capitalize first letter
        return main_part.capitalize()
    
    return domain.capitalize()

def format_url(domain):
    """Format domain as proper URL"""
    if not domain:
        return ""
    
    # Remove protocol if present
    domain = domain.replace('http://', '').replace('https://', '')
    
    # Remove trailing slashes
    domain = domain.rstrip('/')
    
    # Add https:// if not present
    if not domain.startswith('https://'):
        domain = f"https://{domain}"
    
    return domain

def main():
    """Extract test companies from Google Sheet"""
    
    # Google Sheet ID
    spreadsheet_id = "1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk"
    
    # Service account credentials file
    service_account_file = Path("config/credentials/theodore-service-account.json")
    
    try:
        # Initialize the Google Sheets client
        logger.info("Initializing Google Sheets client...")
        sheets_client = GoogleSheetsServiceClient(service_account_file)
        
        # Read companies data
        logger.info("Reading companies from the 'Companies' sheet...")
        
        result = sheets_client.service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range="Companies!A:Z"
        ).execute()
        
        values = result.get('values', [])
        
        if not values or len(values) <= 1:
            logger.error("No company data found in the sheet")
            return
        
        # Extract first 10 companies for testing
        test_companies = []
        
        for row_num, row in enumerate(values[1:11], start=2):  # Take first 10 data rows
            if not row or not row[0]:  # Skip empty rows
                continue
            
            domain = row[0]  # First column contains the domain
            company_name = clean_domain_to_company_name(domain)
            website_url = format_url(domain)
            
            # Get status if available
            status = row[2] if len(row) > 2 else "unknown"
            
            company_info = {
                'name': company_name,
                'domain': domain,
                'website': website_url,
                'status': status,
                'row': row_num
            }
            
            test_companies.append(company_info)
        
        # Display results
        print("\n" + "="*80)
        print("FIRST 10 COMPANIES FOR TESTING")
        print("="*80)
        
        for i, company in enumerate(test_companies, 1):
            print(f"\n{i}. {company['name']}")
            print(f"   Domain: {company['domain']}")
            print(f"   Website: {company['website']}")
            print(f"   Status: {company['status']}")
            print(f"   Row: {company['row']}")
        
        # Generate test data for copy-paste
        print("\n" + "="*80)
        print("FORMATTED FOR TESTING (copy-paste friendly)")
        print("="*80)
        
        for i, company in enumerate(test_companies, 1):
            print(f"{i}. Name: {company['name']}")
            print(f"   URL: {company['website']}")
            print()
        
        # Generate a simple list
        print("="*80)
        print("SIMPLE LIST FORMAT")
        print("="*80)
        
        for i, company in enumerate(test_companies, 1):
            print(f"{i}. {company['name']} - {company['website']}")
        
        print(f"\nTotal companies available in sheet: {len(values)-1}")
        print(f"Test companies extracted: {len(test_companies)}")
        
    except Exception as e:
        logger.error(f"Error reading Google Sheet: {e}")
        return

if __name__ == "__main__":
    main()