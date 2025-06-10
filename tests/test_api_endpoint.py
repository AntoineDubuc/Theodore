#!/usr/bin/env python3
"""
Test the actual API endpoint that the frontend calls
"""

import requests
import json

def test_api_endpoint():
    """Test the /api/discover endpoint directly"""
    print("🌐 Testing /api/discover endpoint for ASUS")
    print("=" * 50)
    
    try:
        # Test the actual API endpoint
        url = "http://localhost:5001/api/discover"
        data = {
            "company_name": "ASUS",
            "limit": 5
        }
        
        print(f"Making POST request to: {url}")
        print(f"With data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, json=data, timeout=30)
        
        print(f"\nResponse status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("✅ API request successful!")
            print(f"Response data: {json.dumps(response_data, indent=2)}")
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Response text: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to localhost:5001")
        print("Make sure the Flask app is running with: python3 app.py")
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 30 seconds")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_api_endpoint()