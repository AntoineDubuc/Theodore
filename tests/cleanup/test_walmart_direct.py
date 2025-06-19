#!/usr/bin/env python3
"""
Test Walmart research directly
"""

import requests
import json
import time

def test_walmart_research():
    """Test researching Walmart directly"""
    
    print("🧪 Testing Direct Walmart Research...")
    print("=" * 60)
    
    url = "http://localhost:5002/api/research"
    payload = {
        "company": {
            "name": "Walmart",
            "website": "https://walmart.com"
        }
    }
    
    print(f"📤 Sending research request for Walmart")
    print(f"📋 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=150)  # 2.5 minute timeout
        duration = time.time() - start_time
        
        print(f"\n📥 Response Status: {response.status_code}")
        print(f"⏱️  Duration: {duration:.1f} seconds")
        
        data = response.json()
        
        if response.status_code == 200 and data.get('success'):
            print("\n✅ Success! Research completed")
            company = data.get('company', {})
            print(f"   Company: {company.get('name', 'N/A')}")
            print(f"   Description Length: {len(company.get('company_description', ''))}")
            print(f"   Industry: {company.get('industry', 'N/A')}")
            print(f"   Business Model: {company.get('business_model', 'N/A')}")
            print(f"   Processing Time: {data.get('processing_time', 0):.1f}s")
        else:
            print(f"\n❌ Research failed:")
            print(f"   Error: {data.get('error', 'Unknown error')}")
            if data.get('details'):
                print(f"   Details: {data['details']}")
                
    except requests.exceptions.Timeout:
        print(f"\n❌ Request timed out after 150 seconds")
    except Exception as e:
        print(f"\n❌ Request failed: {e}")

if __name__ == "__main__":
    test_walmart_research()