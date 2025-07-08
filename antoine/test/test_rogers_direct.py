#!/usr/bin/env python3
"""
Direct test of Rogers data in Pinecone
"""

import sys
import os
import json
from pinecone import Pinecone

# Load env vars
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

def test_rogers_direct():
    """Direct Pinecone test for Rogers"""
    
    print("=" * 80)
    print("DIRECT ROGERS PINECONE TEST")
    print("=" * 80)
    
    # Initialize Pinecone directly
    pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
    index = pc.Index(os.getenv('PINECONE_INDEX_NAME', 'theodore-companies'))
    
    # Query for Rogers
    print("\n📍 Querying for companies with 'Rogers' in name...")
    
    # Use a dummy vector for search
    import random
    dummy_vector = [random.random() for _ in range(1536)]
    
    results = index.query(
        vector=dummy_vector,
        top_k=100,
        include_metadata=True
    )
    
    print(f"\n📊 Total matches: {len(results.matches)}")
    
    rogers_results = []
    all_companies = []
    
    for match in results.matches:
        metadata = match.metadata
        if metadata and 'company_name' in metadata:
            name = metadata['company_name']
            all_companies.append(name)
            if 'Rogers' in name or 'rogers' in name.lower():
                rogers_results.append({
                    'id': match.id,
                    'score': match.score,
                    'metadata': metadata
                })
    
    print(f"Companies found: {', '.join(all_companies[:10])}{'...' if len(all_companies) > 10 else ''}")
    print(f"\n✅ Found {len(rogers_results)} Rogers companies")
    
    for i, result in enumerate(rogers_results):
        print(f"\n--- Rogers Result {i+1} ---")
        print(f"ID: {result['id']}")
        print(f"Name: {result['metadata'].get('company_name', 'N/A')}")
        
        # Analyze fields
        metadata = result['metadata']
        print("\n🔍 Key Fields:")
        
        fields_to_check = [
            'company_description',
            'industry', 
            'business_model',
            'location',
            'founding_year',
            'employee_count_range',
            'value_proposition',
            'products_services_offered',
            'key_services',
            'scrape_status',
            'is_saas'
        ]
        
        for field in fields_to_check:
            value = metadata.get(field)
            if value is None:
                print(f"  ❌ {field}: None")
            elif value == "" or value == "unknown":
                print(f"  ⚠️  {field}: empty/unknown")
            elif isinstance(value, str) and len(value) > 60:
                print(f"  ✅ {field}: {value[:60]}...")
            else:
                print(f"  ✅ {field}: {value}")
        
        # Save first Rogers result
        if i == 0:
            with open('rogers_direct_pinecone.json', 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"\n💾 Saved to: rogers_direct_pinecone.json")

if __name__ == "__main__":
    test_rogers_direct()