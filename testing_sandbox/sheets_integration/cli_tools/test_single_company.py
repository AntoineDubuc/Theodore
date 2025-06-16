#!/usr/bin/env python3
"""
Test processing a SINGLE company - SAFEST test possible
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from src.sheets_integration import GoogleSheetsServiceClient

# Constants
SERVICE_ACCOUNT_FILE = project_root / 'config' / 'credentials' / 'theodore-service-account.json'
TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'

def test_single_company():
    """Test processing exactly ONE company"""
    print("🧪 Single Company Processing Test (SAFEST TEST)")
    print("=" * 50)
    
    # Check service account file
    if not SERVICE_ACCOUNT_FILE.exists():
        print(f"❌ Service account key not found!")
        print(f"   Expected at: {SERVICE_ACCOUNT_FILE}")
        return 1
    
    try:
        # Initialize client
        print("📊 Initializing Google Sheets client...")
        client = GoogleSheetsServiceClient(SERVICE_ACCOUNT_FILE)
        
        # Validate access
        if not client.validate_sheet_access(TEST_SHEET_ID):
            print("❌ Cannot access spreadsheet")
            return 1
        
        # Read companies
        print("\n📋 Reading companies from sheet...")
        companies = client.read_companies_to_process(TEST_SHEET_ID)
        
        if not companies:
            print("❌ No companies found to process")
            return 1
        
        # Take ONLY the first company
        first_company = companies[0]
        print(f"\n🎯 Will process ONLY this company:")
        print(f"   Row {first_company['row_number']}: {first_company['name']}")
        print(f"   Website: {first_company.get('website', 'No website')}")
        
        response = input("\nProceed with processing this ONE company? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled")
            return 0
        
        # Process single company
        print("\n🚀 Processing single company...")
        
        # Update status to processing
        client.update_company_status(
            TEST_SHEET_ID,
            first_company['row_number'],
            'processing',
            '0%'
        )
        
        try:
            # Import pipeline here to avoid loading it unless we're actually processing
            from src.main_pipeline import pipeline
            
            # Process the company
            company_data = pipeline.process_company(
                company_name=first_company['name'],
                website_url=first_company.get('website'),
                job_id="single_test_001"
            )
            
            if company_data and company_data.name:
                # Update sheets with results
                client.update_company_results(
                    TEST_SHEET_ID,
                    first_company['row_number'],
                    company_data
                )
                
                # Mark as completed
                client.update_company_status(
                    TEST_SHEET_ID,
                    first_company['row_number'],
                    'completed',
                    '100%'
                )
                
                print(f"\n✅ Successfully processed: {first_company['name']}")
                print(f"   Industry: {company_data.industry}")
                print(f"   Stage: {company_data.company_stage}")
                print(f"   Tech Level: {company_data.tech_sophistication}")
            else:
                # Mark as failed
                client.update_company_status(
                    TEST_SHEET_ID,
                    first_company['row_number'],
                    'failed',
                    '0%',
                    'No data returned'
                )
                print(f"\n❌ Failed to process company")
                
        except Exception as e:
            # Mark as failed with error
            client.update_company_status(
                TEST_SHEET_ID,
                first_company['row_number'],
                'failed',
                '0%',
                f'Error: {str(e)[:200]}'
            )
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return 1
        
        print(f"\n📊 View results: https://docs.google.com/spreadsheets/d/{TEST_SHEET_ID}/edit")
        return 0
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    return test_single_company()

if __name__ == "__main__":
    sys.exit(main())