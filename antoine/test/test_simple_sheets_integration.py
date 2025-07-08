#!/usr/bin/env python3
"""
Simple Google Sheets Integration Test
=====================================

A focused test that:
1. Reads one company from Google Sheets
2. Processes it with antoine
3. Saves to Pinecone
4. Writes results to a new tab
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

from src.antoine_scraper_adapter import AntoineScraperAdapter
from src.models import CompanyData, CompanyIntelligenceConfig
from src.sheets_integration.google_sheets_service_client import GoogleSheetsServiceClient
from src.bedrock_client import BedrockClient
from src.pinecone_client import PineconeClient

# Constants
SERVICE_ACCOUNT_FILE = Path('config/credentials/theodore-service-account.json')
TEST_SHEET_ID = '1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk'


def test_simple_integration():
    """Run a simple integration test with one company"""
    
    print("=" * 80)
    print("SIMPLE GOOGLE SHEETS + ANTOINE + PINECONE TEST")
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
    
    # Step 2: Process one company
    print("\n📋 Step 2: Processing test company...")
    
    # Use a reliable test company
    test_company = CompanyData(
        name="Stripe",
        website="https://stripe.com"
    )
    
    print(f"   Testing with: {test_company.name} ({test_company.website})")
    
    start_time = time.time()
    result = scraper.scrape_company(test_company)
    process_time = time.time() - start_time
    
    print(f"\n   Processing completed in {process_time:.1f}s")
    print(f"   Status: {result.scrape_status}")
    
    if result.scrape_status == "success":
        # Count extracted fields
        field_count = sum(1 for attr in dir(result) 
                         if not attr.startswith('_') 
                         and getattr(result, attr) 
                         and getattr(result, attr) != "unknown")
        
        print(f"   Fields extracted: {field_count}")
        print(f"   Pages crawled: {len(result.pages_crawled or [])}")
        
        # Show some sample data
        if result.company_description:
            print(f"   Description: {result.company_description[:100]}...")
        if result.industry:
            print(f"   Industry: {result.industry}")
        if result.business_model:
            print(f"   Business Model: {result.business_model}")
    else:
        print(f"   Error: {result.scrape_error}")
        return False
    
    # Step 3: Save to Pinecone
    print("\n📋 Step 3: Saving to Pinecone...")
    
    pinecone_saved = False
    if result.company_description:
        try:
            # Generate embedding
            embedding = bedrock_client.get_embeddings(result.company_description)
            result.embedding = embedding
            
            # Save to Pinecone
            success = pinecone_client.upsert_company(result)
            
            if success:
                print("   ✅ Saved to Pinecone successfully")
                pinecone_saved = True
            else:
                print("   ❌ Failed to save to Pinecone")
                
        except Exception as e:
            print(f"   ❌ Pinecone error: {e}")
    
    # Step 4: Write to Google Sheets
    print("\n📋 Step 4: Writing results to Google Sheets...")
    
    # Create new tab
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    tab_name = f"SimpleTest_{timestamp}"
    
    try:
        # Create tab
        request_body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': tab_name,
                        'gridProperties': {
                            'rowCount': 10,
                            'columnCount': 20
                        }
                    }
                }
            }]
        }
        
        sheets_client.service.spreadsheets().batchUpdate(
            spreadsheetId=TEST_SHEET_ID,
            body=request_body
        ).execute()
        
        print(f"   ✅ Created new tab: {tab_name}")
        
        # Add headers
        headers = [
            'Company Name', 'Website', 'Status', 'Processing Time',
            'Industry', 'Business Model', 'Location', 'Company Size',
            'Description', 'Products/Services', 'Fields Extracted',
            'Pages Crawled', 'Pinecone Status', 'Timestamp'
        ]
        
        sheets_client.service.spreadsheets().values().update(
            spreadsheetId=TEST_SHEET_ID,
            range=f"{tab_name}!A1:N1",
            valueInputOption='RAW',
            body={'values': [headers]}
        ).execute()
        
        # Add data row
        data_row = [
            result.name,
            result.website,
            result.scrape_status,
            f"{process_time:.1f}s",
            result.industry or "unknown",
            result.business_model or "unknown",
            result.location or "unknown",
            result.company_size or "unknown",
            result.company_description[:200] + "..." if result.company_description else "",
            str(result.products_services_offered)[:200] if result.products_services_offered else "",
            field_count,
            len(result.pages_crawled or []),
            "Saved" if pinecone_saved else "Not saved",
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ]
        
        sheets_client.service.spreadsheets().values().update(
            spreadsheetId=TEST_SHEET_ID,
            range=f"{tab_name}!A2:N2",
            valueInputOption='RAW',
            body={'values': [data_row]}
        ).execute()
        
        print("   ✅ Results written to Google Sheets")
        
    except Exception as e:
        print(f"   ❌ Error writing to sheets: {e}")
        return False
    
    # Final summary
    print("\n" + "=" * 80)
    print("✅ SIMPLE INTEGRATION TEST COMPLETE!")
    print(f"   Company processed: {result.name}")
    print(f"   Processing time: {process_time:.1f}s")
    print(f"   Fields extracted: {field_count}")
    print(f"   Pinecone: {'Saved' if pinecone_saved else 'Not saved'}")
    print(f"   Results: https://docs.google.com/spreadsheets/d/{TEST_SHEET_ID}/edit#{tab_name}")
    
    return True


if __name__ == "__main__":
    success = test_simple_integration()
    sys.exit(0 if success else 1)