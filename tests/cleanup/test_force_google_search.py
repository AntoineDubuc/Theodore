#!/usr/bin/env python3
"""
Force Google search by requesting many companies
"""

import requests
import json

def test_force_google():
    """Force Google search by requesting more than LLM returns"""
    
    print("🧪 Testing Forced Google Search...")
    print("=" * 60)
    
    # Request MORE companies than LLM typically returns (usually 5-10)
    test_company = "Small Startup Inc"
    
    url = "http://localhost:5002/api/discover"
    payload = {
        "company_name": test_company,
        "limit": 15  # High limit to force Google enhancement
    }
    
    print(f"🔍 Testing with company: {test_company}")
    print(f"📋 Requesting {payload['limit']} companies (more than LLM typically returns)")
    
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        
        if response.status_code == 200:
            results = data.get('results', [])
            sources = data.get('sources_used', [])
            
            print(f"\n📊 Results:")
            print(f"   Total Found: {len(results)}")
            print(f"   Sources Used: {sources}")
            
            # Count by source
            llm_count = sum(1 for r in results if 'llm' in r.get('sources', []))
            google_count = sum(1 for r in results if 'google' in r.get('sources', []))
            
            print(f"\n   From LLM: {llm_count}")
            print(f"   From Google: {google_count}")
            
            if 'google' in sources:
                print(f"\n✅ SUCCESS! Google search was triggered!")
                print(f"   Found {google_count} companies via Google search")
                
                # Show Google results
                print("\n🌐 Companies found via Google:")
                for i, company in enumerate(results):
                    if 'google' in company.get('sources', []):
                        print(f"   - {company.get('company_name')}: {company.get('website')}")
            else:
                print(f"\n❌ Google search was NOT triggered")
                print(f"   LLM returned enough results ({llm_count}) to satisfy limit")
                
    except Exception as e:
        print(f"\n❌ Request failed: {e}")

if __name__ == "__main__":
    test_force_google()