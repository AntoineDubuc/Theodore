#!/usr/bin/env python3
"""
Test research with a smaller company
"""

import requests
import json
import time

def test_simple_company():
    """Test researching a smaller, simpler company"""
    
    print("🧪 Testing Research for Smaller Company...")
    print("=" * 60)
    
    # Try a smaller tech company that should be easier to scrape
    url = "http://localhost:5002/api/research"
    payload = {
        "company": {
            "name": "Stripe",
            "website": "https://stripe.com"
        }
    }
    
    print(f"📤 Sending research request for Stripe")
    print(f"📋 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=60)  # 1 minute timeout
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
        else:
            print(f"\n❌ Research failed:")
            print(f"   Error: {data.get('error', 'Unknown error')}")
                
    except requests.exceptions.Timeout:
        print(f"\n❌ Request timed out after 60 seconds")
    except Exception as e:
        print(f"\n❌ Request failed: {e}")

if __name__ == "__main__":
    test_simple_company()