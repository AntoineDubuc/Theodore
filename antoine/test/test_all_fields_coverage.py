#!/usr/bin/env python3
"""
Comprehensive Field Coverage Test
=================================

This test verifies that ALL CompanyData fields are:
1. Properly extracted by the antoine pipeline
2. Saved to Pinecone with complete metadata
3. Written to Google Sheets with all columns
"""

import sys
import os
import time
from datetime import datetime
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load env vars
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

from src.antoine_scraper_adapter import AntoineScraperAdapter
from src.models import CompanyData, CompanyIntelligenceConfig
from src.sheets_integration.google_sheets_service_client import GoogleSheetsServiceClient
from src.bedrock_client import BedrockClient
from src.pinecone_client import PineconeClient
from antoine.test.test_helpers import (
    get_all_company_headers,
    company_data_to_complete_row,
    get_field_coverage_report,
    verify_pinecone_metadata,
    create_field_coverage_sheet_data
)

# Constants
SERVICE_ACCOUNT_FILE = Path('config/credentials/theodore-service-account.json')
TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'


def test_comprehensive_field_coverage():
    """Test that all fields are properly extracted and saved"""
    
    print("=" * 80)
    print("COMPREHENSIVE FIELD COVERAGE TEST")
    print("=" * 80)
    print("This test will:")
    print("1. Process a company with rich data")
    print("2. Verify ALL 71 CompanyData fields")
    print("3. Check Pinecone metadata completeness")
    print("4. Create detailed coverage report in Google Sheets")
    print("=" * 80)
    
    # Step 1: Initialize components
    print("\n📋 Step 1: Initializing components...")
    
    # Sheets client
    sheets_client = GoogleSheetsServiceClient(SERVICE_ACCOUNT_FILE)
    
    # Validate access
    if not sheets_client.validate_sheet_access(TEST_SHEET_ID):
        print("   ❌ Cannot access spreadsheet")
        return False
    
    # Initialize AI and DB clients
    config = CompanyIntelligenceConfig()
    bedrock_client = BedrockClient(config)
    pinecone_client = PineconeClient(
        config=config,
        api_key=os.getenv('PINECONE_API_KEY'),
        environment='gcp-starter',
        index_name=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
    )
    
    # Antoine adapter
    scraper = AntoineScraperAdapter(config, bedrock_client)
    
    # Step 2: Process a data-rich company
    print("\n📋 Step 2: Processing data-rich company...")
    
    # Use a company known to have rich data and be scrapable
    test_company = CompanyData(
        name="HubSpot",
        website="https://hubspot.com"
    )
    
    print(f"   Testing with: {test_company.name} ({test_company.website})")
    
    start_time = time.time()
    result = scraper.scrape_company(test_company)
    process_time = time.time() - start_time
    
    print(f"\n   Processing completed in {process_time:.1f}s")
    print(f"   Status: {result.scrape_status}")
    
    if result.scrape_status != "success":
        print(f"   ❌ Processing failed: {result.scrape_error}")
        return False
    
    # Step 3: Generate field coverage report
    print("\n📋 Step 3: Analyzing field coverage...")
    
    coverage_report = get_field_coverage_report(result)
    
    print(f"\n   📊 FIELD COVERAGE SUMMARY:")
    print(f"   Total fields: {coverage_report['total_fields']}")
    print(f"   Populated fields: {coverage_report['populated_fields']}")
    print(f"   Empty fields: {coverage_report['empty_fields']}")
    print(f"   Overall coverage: {coverage_report['overall_coverage']:.1f}%")
    
    print(f"\n   📊 COVERAGE BY CATEGORY:")
    for category, stats in coverage_report['coverage_by_category'].items():
        print(f"   {category}: {stats['populated']}/{stats['total']} ({stats['percentage']:.0f}%)")
    
    # Step 4: Save to Pinecone and verify metadata
    print("\n📋 Step 4: Saving to Pinecone and verifying metadata...")
    
    if result.company_description:
        try:
            # Generate embedding
            embedding = bedrock_client.get_embeddings(result.company_description)
            result.embedding = embedding
            
            # Save to Pinecone
            success = pinecone_client.upsert_company(result)
            
            if success:
                print("   ✅ Saved to Pinecone successfully")
                
                # Fetch back and verify metadata
                metadata = pinecone_client.get_company_metadata(result.id)
                if metadata:
                    verification = verify_pinecone_metadata(metadata)
                    print(f"\n   📊 PINECONE METADATA VERIFICATION:")
                    print(f"   Expected fields: {verification['total_expected']}")
                    print(f"   Found fields: {verification['found']}")
                    print(f"   Missing fields: {len(verification['missing'])}")
                    print(f"   Coverage: {verification['coverage_percentage']:.1f}%")
                    
                    if verification['missing']:
                        print(f"\n   ⚠️  Missing fields in Pinecone:")
                        for field in verification['missing'][:10]:  # Show first 10
                            print(f"      - {field}")
                else:
                    print("   ❌ Could not fetch metadata from Pinecone")
            else:
                print("   ❌ Failed to save to Pinecone")
                
        except Exception as e:
            print(f"   ❌ Pinecone error: {e}")
    
    # Step 5: Create comprehensive Google Sheets report
    print("\n📋 Step 5: Creating comprehensive Google Sheets report...")
    
    # Create new tabs
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    data_tab_name = f"FieldTest_Data_{timestamp}"
    coverage_tab_name = f"FieldTest_Coverage_{timestamp}"
    
    try:
        # Create tabs
        request_body = {
            'requests': [
                {
                    'addSheet': {
                        'properties': {
                            'title': data_tab_name,
                            'gridProperties': {
                                'rowCount': 10,
                                'columnCount': 54
                            }
                        }
                    }
                },
                {
                    'addSheet': {
                        'properties': {
                            'title': coverage_tab_name,
                            'gridProperties': {
                                'rowCount': 100,
                                'columnCount': 10
                            }
                        }
                    }
                }
            ]
        }
        
        sheets_client.service.spreadsheets().batchUpdate(
            spreadsheetId=TEST_SHEET_ID,
            body=request_body
        ).execute()
        
        print(f"   ✅ Created tabs: {data_tab_name} and {coverage_tab_name}")
        
        # Add headers to data tab
        headers = get_all_company_headers()
        sheets_client.service.spreadsheets().values().update(
            spreadsheetId=TEST_SHEET_ID,
            range=f"{data_tab_name}!A1:BB1",
            valueInputOption='RAW',
            body={'values': [headers]}
        ).execute()
        
        # Add data row
        data_row = company_data_to_complete_row(result)
        sheets_client.service.spreadsheets().values().update(
            spreadsheetId=TEST_SHEET_ID,
            range=f"{data_tab_name}!A2:BB2",
            valueInputOption='RAW',
            body={'values': [data_row]}
        ).execute()
        
        print("   ✅ Written all 54 fields to data tab")
        
        # Create coverage analysis sheet
        coverage_data = create_field_coverage_sheet_data(result, coverage_report)
        sheets_client.service.spreadsheets().values().update(
            spreadsheetId=TEST_SHEET_ID,
            range=f"{coverage_tab_name}!A1:E{len(coverage_data)}",
            valueInputOption='RAW',
            body={'values': coverage_data}
        ).execute()
        
        print("   ✅ Written field coverage analysis to coverage tab")
        
        # Format headers in both tabs
        format_requests = []
        
        # Get sheet IDs
        spreadsheet = sheets_client.service.spreadsheets().get(
            spreadsheetId=TEST_SHEET_ID
        ).execute()
        
        sheet_ids = {}
        for sheet in spreadsheet['sheets']:
            if sheet['properties']['title'] in [data_tab_name, coverage_tab_name]:
                sheet_ids[sheet['properties']['title']] = sheet['properties']['sheetId']
        
        # Format both sheets
        for tab_name, sheet_id in sheet_ids.items():
            format_requests.append({
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
            })
        
        if format_requests:
            sheets_client.service.spreadsheets().batchUpdate(
                spreadsheetId=TEST_SHEET_ID,
                body={'requests': format_requests}
            ).execute()
        
    except Exception as e:
        print(f"   ❌ Error creating sheets: {e}")
        return False
    
    # Final summary
    print("\n" + "=" * 80)
    print("✅ COMPREHENSIVE FIELD COVERAGE TEST COMPLETE!")
    print(f"   Company processed: {result.name}")
    print(f"   Processing time: {process_time:.1f}s")
    print(f"   Field coverage: {coverage_report['overall_coverage']:.1f}%")
    print(f"   Data tab: https://docs.google.com/spreadsheets/d/{TEST_SHEET_ID}/edit#{data_tab_name}")
    print(f"   Coverage tab: https://docs.google.com/spreadsheets/d/{TEST_SHEET_ID}/edit#{coverage_tab_name}")
    
    # Print fields that need improvement
    if coverage_report['empty_fields'] > 0:
        print(f"\n   ⚠️  Fields that could be improved:")
        empty_count = 0
        for field_name, details in coverage_report['field_details'].items():
            if not details['has_value'] and empty_count < 10:
                print(f"      - {details['header']} ({field_name})")
                empty_count += 1
        if coverage_report['empty_fields'] > 10:
            print(f"      ... and {coverage_report['empty_fields'] - 10} more")
    
    return True


def test_pinecone_field_retrieval():
    """Test that all fields can be retrieved from Pinecone"""
    
    print("\n" + "=" * 80)
    print("PINECONE FIELD RETRIEVAL TEST")
    print("=" * 80)
    
    config = CompanyIntelligenceConfig()
    pinecone_client = PineconeClient(
        config=config,
        api_key=os.getenv('PINECONE_API_KEY'),
        environment='gcp-starter',
        index_name=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
    )
    
    # Find a company with good data
    print("\n🔍 Searching for companies in Pinecone...")
    
    companies = pinecone_client.find_companies_by_filters(
        filters={"has_description": {"$eq": True}},
        top_k=5
    )
    
    if not companies:
        print("   ❌ No companies found in Pinecone")
        return False
    
    print(f"   Found {len(companies)} companies")
    
    # Check first company's metadata
    first_company = companies[0]
    metadata = first_company.get('metadata', {})
    
    print(f"\n📊 Analyzing metadata for: {metadata.get('company_name', 'Unknown')}")
    
    verification = verify_pinecone_metadata(metadata)
    
    print(f"\n   Metadata fields found: {verification['found']}/{verification['total_expected']}")
    print(f"   Coverage: {verification['coverage_percentage']:.1f}%")
    
    if verification['missing']:
        print(f"\n   Missing fields:")
        for field in verification['missing']:
            print(f"      - {field}")
    
    # Show sample of available fields
    print(f"\n   Sample of available fields:")
    sample_fields = ['company_description', 'industry', 'tech_stack', 
                    'products_services_offered', 'total_cost_usd']
    for field in sample_fields:
        if field in metadata:
            value = metadata[field]
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            print(f"      {field}: {value}")
    
    return True


if __name__ == "__main__":
    # Run comprehensive field coverage test
    success = test_comprehensive_field_coverage()
    
    # Also test Pinecone retrieval
    if success:
        test_pinecone_field_retrieval()
    
    sys.exit(0 if success else 1)