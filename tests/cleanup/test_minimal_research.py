#!/usr/bin/env python3
"""
Test minimal research with a simple website
"""

import requests
import json
import time

def test_minimal():
    """Test with a minimal company"""
    
    print("🧪 Testing Minimal Research...")
    print("=" * 60)
    
    # Try with a very simple website
    url = "http://localhost:5002/api/research"
    payload = {
        "company": {
            "name": "Example",
            "website": "https://example.com"
        }
    }
    
    print(f"📤 Sending research request for Example.com")
    print(f"📋 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=30)  # 30 second timeout
        duration = time.time() - start_time
        
        print(f"\n📥 Response Status: {response.status_code}")
        print(f"⏱️  Duration: {duration:.1f} seconds")
        
        data = response.json()
        
        if response.status_code == 200 and data.get('success'):
            print("\n✅ Success! Research completed")
            company = data.get('company', {})
            print(f"   Company: {company.get('name', 'N/A')}")
            print(f"   Description Length: {len(company.get('company_description', ''))}")
        else:
            print(f"\n❌ Research failed:")
            print(f"   Error: {data.get('error', 'Unknown error')}")
                
    except requests.exceptions.Timeout:
        print(f"\n❌ Request timed out after 30 seconds")
    except Exception as e:
        print(f"\n❌ Request failed: {e}")

if __name__ == "__main__":
    test_minimal()