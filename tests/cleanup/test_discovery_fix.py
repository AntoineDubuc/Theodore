#!/usr/bin/env python3
"""
Test the fixed discovery functionality
"""

import requests
import json
import time

def test_discovery():
    """Test discovery API endpoint"""
    
    print("🧪 Testing Fixed Discovery Endpoint...")
    print("=" * 60)
    
    # Test with a company likely in database
    test_company = "walmart"
    
    url = "http://localhost:5002/api/discover"
    payload = {
        "company_name": test_company,
        "limit": 5
    }
    
    print(f"📤 Sending request to {url}")
    print(f"📋 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"\n📥 Response Status: {response.status_code}")
        
        data = response.json()
        
        if response.status_code == 200:
            print("\n✅ Success! Response data:")
            print(f"   Target Company: {data.get('target_company', 'N/A')}")
            print(f"   Total Found: {data.get('total_found', 0)}")
            print(f"   Discovery Method: {data.get('discovery_method', 'N/A')}")
            print(f"   Sources Used: {data.get('sources_used', [])}")
            
            results = data.get('results', [])
            print(f"\n📊 Found {len(results)} companies:")
            
            for i, company in enumerate(results, 1):
                print(f"\n   {i}. {company.get('company_name', 'Unknown')}")
                print(f"      Website: {company.get('website', 'N/A')}")
                print(f"      Similarity: {company.get('similarity_score', 0):.2f}")
                print(f"      Sources: {', '.join(company.get('sources', []))}")
                print(f"      Method: {company.get('discovery_method', 'N/A')}")
                
                # Check if from Google search
                if 'google' in company.get('sources', []):
                    print(f"      🌐 Found via Google search!")
            
            if data.get('error'):
                print(f"\n⚠️  Error: {data['error']}")
                
        else:
            print(f"\n❌ Error: {data.get('error', 'Unknown error')}")
            if data.get('suggestion'):
                print(f"💡 Suggestion: {data['suggestion']}")
                
    except Exception as e:
        print(f"\n❌ Request failed: {e}")

if __name__ == "__main__":
    test_discovery()