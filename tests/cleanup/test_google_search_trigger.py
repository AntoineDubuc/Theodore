#!/usr/bin/env python3
"""
Test Google search trigger with unknown company
"""

import requests
import json

def test_unknown_company():
    """Test discovery with company not in database"""
    
    print("🧪 Testing Google Search Trigger...")
    print("=" * 60)
    
    # Test with a company NOT in database
    test_company = "Acme Innovations Corp"
    
    url = "http://localhost:5002/api/discover"
    payload = {
        "company_name": test_company,
        "limit": 3  # Small limit to test Google search
    }
    
    print(f"🔍 Testing with unknown company: {test_company}")
    print(f"📋 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"\n📥 Response Status: {response.status_code}")
        
        data = response.json()
        
        if response.status_code == 200:
            print("\n✅ Success! Response data:")
            print(f"   Target Company: {data.get('target_company', 'N/A')}")
            print(f"   Total Found: {data.get('total_found', 0)}")
            print(f"   Sources Used: {data.get('sources_used', [])}")
            
            # Check if Google search was used
            if 'google' in data.get('sources_used', []):
                print("   🌐 GOOGLE SEARCH WAS TRIGGERED!")
            else:
                print("   ℹ️  Google search NOT triggered")
            
            results = data.get('results', [])
            print(f"\n📊 Found {len(results)} companies:")
            
            for i, company in enumerate(results, 1):
                print(f"\n   {i}. {company.get('company_name', 'Unknown')}")
                print(f"      Website: {company.get('website', 'N/A')}")
                print(f"      Sources: {', '.join(company.get('sources', []))}")
                print(f"      Method: {company.get('discovery_method', 'N/A')}")
                
                if 'google' in company.get('sources', []):
                    print(f"      🌐 FOUND VIA GOOGLE SEARCH!")
                    
        else:
            print(f"\n❌ Error: {data.get('error', 'Unknown error')}")
                
    except Exception as e:
        print(f"\n❌ Request failed: {e}")

def test_insufficient_results():
    """Test with company that returns few results to trigger Google"""
    
    print("\n\n🧪 Testing Google Search Enhancement...")
    print("=" * 60)
    
    # Test with high limit to trigger Google enhancement
    test_company = "Theodore AI"
    
    url = "http://localhost:5002/api/discover"
    payload = {
        "company_name": test_company,
        "limit": 10  # High limit should trigger Google if LLM returns < 10
    }
    
    print(f"🔍 Testing with high limit: {test_company}")
    print(f"📋 Requesting {payload['limit']} companies")
    
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        
        if response.status_code == 200:
            results = data.get('results', [])
            google_count = sum(1 for r in results if 'google' in r.get('sources', []))
            
            print(f"\n📊 Results:")
            print(f"   Total Found: {len(results)}")
            print(f"   From Google: {google_count}")
            print(f"   Sources: {data.get('sources_used', [])}")
            
            if google_count > 0:
                print(f"\n✅ SUCCESS! Google search enhanced results with {google_count} companies")
            
    except Exception as e:
        print(f"\n❌ Request failed: {e}")

if __name__ == "__main__":
    test_unknown_company()
    test_insufficient_results()