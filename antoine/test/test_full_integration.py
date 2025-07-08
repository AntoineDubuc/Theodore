#!/usr/bin/env python3
"""
Full Integration Test
====================

Complete test that:
1. Reads companies from Google Sheets
2. Processes with antoine batch processor
3. Saves to Pinecone
4. Creates new tab in Google Sheets with results
"""

import sys
import os
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load env vars
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

from antoine.batch.batch_processor import AntoineBatchProcessor
from src.models import CompanyIntelligenceConfig
from src.sheets_integration.google_sheets_service_client import GoogleSheetsServiceClient
from src.main_pipeline import TheodoreIntelligencePipeline
from googleapiclient.errors import HttpError
from antoine.test.test_helpers import (
    get_all_company_headers,
    company_data_to_complete_row,
    get_field_coverage_report
)

# Constants
SERVICE_ACCOUNT_FILE = Path('config/credentials/theodore-service-account.json')
TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'


def create_results_tab(sheets_client, spreadsheet_id, tab_name):
    """Create a new tab for test results"""
    try:
        # Check if tab already exists
        spreadsheet = sheets_client.service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()
        
        existing_sheets = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]
        
        if tab_name in existing_sheets:
            print(f"   ⚠️  Tab '{tab_name}' already exists, will use existing tab")
            return True
            
        # Create new sheet
        request_body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': tab_name,
                        'gridProperties': {
                            'rowCount': 100,
                            'columnCount': 54  # Updated to accommodate all fields
                        }
                    }
                }
            }]
        }
        
        sheets_client.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=request_body
        ).execute()
        
        print(f"   ✅ Created new tab: {tab_name}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error creating tab: {e}")
        return False


def add_headers_to_tab(sheets_client, spreadsheet_id, tab_name):
    """Add headers to the results tab"""
    # Get ALL headers from the complete data columns (54 fields)
    headers = get_all_company_headers()
    
    try:
        # Write headers
        sheets_client.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{tab_name}!A1:BB1",  # Updated to include all columns up to BB
            valueInputOption='RAW',
            body={'values': [headers]}
        ).execute()
        
        # Format headers (bold, background color)
        requests = [{
            'repeatCell': {
                'range': {
                    'sheetId': get_sheet_id(sheets_client, spreadsheet_id, tab_name),
                    'startRowIndex': 0,
                    'endRowIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {
                            'red': 0.2,
                            'green': 0.3,
                            'blue': 0.5
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
        }]
        
        sheets_client.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        
        print(f"   ✅ Added {len(headers)} headers to {tab_name}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error adding headers: {e}")
        return False


def get_sheet_id(sheets_client, spreadsheet_id, sheet_name):
    """Get the sheet ID for a given sheet name"""
    spreadsheet = sheets_client.service.spreadsheets().get(
        spreadsheetId=spreadsheet_id
    ).execute()
    
    for sheet in spreadsheet['sheets']:
        if sheet['properties']['title'] == sheet_name:
            return sheet['properties']['sheetId']
    return None


def write_results_to_sheet(sheets_client, spreadsheet_id, tab_name, results, pinecone_results):
    """Write processing results to the sheet"""
    rows = []
    
    for i, company in enumerate(results.company_results):
        # Add Pinecone status to company data for the converter
        if not hasattr(company, 'pinecone_status'):
            company.pinecone_status = pinecone_results.get(company.name, 'Not attempted')
        
        # Use the helper function to convert all fields
        row = company_data_to_complete_row(company)
        rows.append(row)
    
    if rows:
        # Write all rows at once
        range_notation = f"{tab_name}!A2:BB{len(rows) + 1}"  # Updated to include all columns
        sheets_client.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_notation,
            valueInputOption='RAW',
            body={'values': rows}
        ).execute()
        
        print(f"   ✅ Wrote {len(rows)} results to {tab_name}")


def test_full_integration():
    """Run the full integration test"""
    
    print("=" * 80)
    print("ANTOINE BATCH - FULL INTEGRATION TEST")
    print("=" * 80)
    print("This test will:")
    print("1. Read companies from Google Sheets")
    print("2. Process with antoine batch processor")
    print("3. Save to Pinecone")
    print("4. Create new tab with results")
    print("=" * 80)
    
    # Step 1: Initialize components
    print("\n📋 Step 1: Initializing components...")
    
    # Sheets client
    print("   Initializing Google Sheets client...")
    sheets_client = GoogleSheetsServiceClient(SERVICE_ACCOUNT_FILE)
    
    # Validate access
    if not sheets_client.validate_sheet_access(TEST_SHEET_ID):
        print("   ❌ Cannot access spreadsheet")
        return False
    
    # Pipeline for Pinecone
    print("   Initializing Theodore pipeline...")
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment='gcp-starter',
        pinecone_index=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
    )
    
    # Batch processor
    print("   Initializing antoine batch processor...")
    batch_processor = AntoineBatchProcessor(
        config=config,
        bedrock_client=pipeline.bedrock_client,
        max_concurrent_companies=2  # Small for testing
    )
    
    # Step 2: Read companies from sheet
    print("\n📋 Step 2: Reading companies from Google Sheets...")
    
    # Manually select specific companies that are likely to work
    # Using simpler company websites
    test_companies = [
        {'name': 'Adtheorent', 'website': 'https://adtheorent.com'},
        {'name': 'Lotlinx', 'website': 'https://lotlinx.com'},
        {'name': 'Appodeal', 'website': 'https://appodeal.com'}
    ]
    
    companies = test_companies
    print(f"   Using {len(companies)} test companies:")
    for company in companies:
        print(f"      - {company['name']} ({company['website']})")
    
    # Step 3: Create new tab for results
    print("\n📋 Step 3: Creating results tab...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    tab_name = f"AntoineTest_{timestamp}"
    
    if not create_results_tab(sheets_client, TEST_SHEET_ID, tab_name):
        return False
    
    if not add_headers_to_tab(sheets_client, TEST_SHEET_ID, tab_name):
        return False
    
    # Step 4: Process companies with antoine
    print("\n📋 Step 4: Processing companies with antoine batch processor...")
    start_time = time.time()
    
    try:
        result = batch_processor.process_batch(companies, batch_name="integration_test")
        
        print(f"\n   ✅ Batch processing completed:")
        print(f"      - Total: {result.total_companies}")
        print(f"      - Successful: {result.successful}")
        print(f"      - Failed: {result.failed}")
        print(f"      - Duration: {result.total_duration:.1f}s")
        
    except Exception as e:
        print(f"   ❌ Batch processing failed: {e}")
        return False
    finally:
        batch_processor.shutdown()
    
    # Step 5: Save to Pinecone
    print("\n📋 Step 5: Saving results to Pinecone...")
    pinecone_results = {}
    
    for company in result.company_results:
        if company.scrape_status == "success" and company.company_description:
            try:
                print(f"   Saving {company.name} to Pinecone...")
                
                # Generate embedding
                embedding = pipeline.bedrock_client.get_embeddings(company.company_description)
                company.embedding = embedding
                
                # Save to Pinecone
                success = pipeline.pinecone_client.upsert_company(company)
                
                if success:
                    print(f"      ✅ Saved successfully")
                    pinecone_results[company.name] = "Saved"
                else:
                    print(f"      ❌ Failed to save")
                    pinecone_results[company.name] = "Failed"
                    
            except Exception as e:
                print(f"      ❌ Error: {e}")
                pinecone_results[company.name] = f"Error: {str(e)}"
        else:
            pinecone_results[company.name] = "Skipped (no data)"
    
    # Step 6: Write results to new tab
    print("\n📋 Step 6: Writing results to Google Sheets...")
    write_results_to_sheet(sheets_client, TEST_SHEET_ID, tab_name, result, pinecone_results)
    
    # Final summary
    total_time = time.time() - start_time
    print("\n" + "=" * 80)
    print("✅ FULL INTEGRATION TEST COMPLETE!")
    print(f"   Total time: {total_time:.1f}s")
    print(f"   Results saved to: https://docs.google.com/spreadsheets/d/{TEST_SHEET_ID}/edit#{tab_name}")
    print(f"   Pinecone saves: {sum(1 for v in pinecone_results.values() if v == 'Saved')}/{len(pinecone_results)}")
    
    return True


if __name__ == "__main__":
    success = test_full_integration()
    sys.exit(0 if success else 1)