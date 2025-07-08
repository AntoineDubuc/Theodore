#!/usr/bin/env python3
"""
Test Rogers retrieval to debug why fields show as unknown
"""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Load env vars
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

from src.pinecone_client import PineconeClient
from src.models import CompanyIntelligenceConfig

def test_rogers_retrieval():
    """Test retrieving Rogers data from Pinecone"""
    
    print("=" * 80)
    print("ROGERS RETRIEVAL TEST")
    print("=" * 80)
    
    # Create config
    config = CompanyIntelligenceConfig()
    
    # Initialize Pinecone client
    client = PineconeClient(
        config=config,
        api_key=os.getenv('PINECONE_API_KEY'),
        environment='gcp-starter',  # Not used but required
        index_name=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
    )
    
    # Search for Rogers
    print("\n📍 Searching for Rogers Communications...")
    results = client.search_companies_by_text("Rogers Communications", top_k=5)
    
    if not results:
        print("❌ No Rogers companies found in database")
        return
    
    print(f"✅ Found {len(results)} Rogers-related companies")
    
    for i, result in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(f"ID: {result.get('id', 'N/A')}")
        print(f"Name: {result.get('company_name', 'N/A')}")
        print(f"Score: {result.get('score', 0):.3f}")
        
        # Check specific fields
        print("\n🔍 Field Analysis:")
        important_fields = [
            'company_description',
            'industry',
            'business_model',
            'location',
            'founding_year',
            'employee_count_range',
            'products_services_offered',
            'key_services',
            'competitive_advantages',
            'is_saas',
            'scrape_status'
        ]
        
        for field in important_fields:
            value = result.get(field, None)
            if value is None:
                print(f"  ❌ {field}: None")
            elif value == "" or value == "unknown":
                print(f"  ⚠️  {field}: '{value}' (empty/unknown)")
            else:
                # Truncate long values
                if isinstance(value, str) and len(value) > 50:
                    print(f"  ✅ {field}: {value[:50]}...")
                else:
                    print(f"  ✅ {field}: {value}")
        
        # Count total fields
        total_fields = len(result)
        non_empty_fields = sum(1 for v in result.values() if v and v != "unknown")
        print(f"\n📊 Field Summary:")
        print(f"  - Total fields: {total_fields}")
        print(f"  - Non-empty fields: {non_empty_fields}")
        print(f"  - Empty/unknown fields: {total_fields - non_empty_fields}")
        
        # Save full result for analysis
        if i == 0:  # Save first result
            with open('rogers_pinecone_data.json', 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n💾 Full data saved to: rogers_pinecone_data.json")

if __name__ == "__main__":
    test_rogers_retrieval()