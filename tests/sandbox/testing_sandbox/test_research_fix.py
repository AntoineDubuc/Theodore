#!/usr/bin/env python3
"""
Test script to verify the complete research flow fixes are working properly.
This will test a quick company that should succeed and a complex one that might timeout.
"""

import requests
import json
import time

def test_research_endpoint():
    """Test the research endpoint with comprehensive logging"""
    
    # Test 1: Quick success case
    print("=" * 60)
    print("🧪 TEST 1: Quick Research (Expected: Success)")
    print("=" * 60)
    
    test_payload = {
        "company": {
            "name": "Apple Inc",
            "website": "https://apple.com"
        }
    }
    
    print(f"📤 Sending request to http://localhost:5002/api/research")
    print(f"📤 Payload: {json.dumps(test_payload, indent=2)}")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            "http://localhost:5002/api/research",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minute timeout for this test
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"📥 Response received in {duration:.2f} seconds")
        print(f"📥 Status code: {response.status_code}")
        print(f"📥 Headers: {dict(response.headers)}")
        
        try:
            data = response.json()
            print(f"📥 Response data keys: {list(data.keys())}")
            
            if response.status_code == 200 and data.get("success"):
                print(f"✅ TEST 1 PASSED: Research completed successfully")
                print(f"✅ Company data keys: {list(data.get('company', {}).keys())}")
                print(f"✅ Research status: {data.get('company', {}).get('research_status')}")
                print(f"✅ Processing time: {data.get('processing_time', 'unknown')}s")
            else:
                print(f"❌ TEST 1 FAILED: {data.get('error', 'Unknown error')}")
                print(f"❌ Full response: {json.dumps(data, indent=2)}")
                
        except json.JSONDecodeError as e:
            print(f"❌ TEST 1 FAILED: Could not parse JSON response: {e}")
            print(f"❌ Raw response: {response.text[:500]}...")
            
    except requests.exceptions.Timeout:
        print(f"❌ TEST 1 FAILED: Request timed out after 2 minutes")
    except requests.exceptions.RequestException as e:
        print(f"❌ TEST 1 FAILED: Request error: {e}")
    
    print("\n")
    
    # Test 2: Progress tracking
    print("=" * 60)
    print("🧪 TEST 2: Progress Tracking")
    print("=" * 60)
    
    try:
        progress_response = requests.get("http://localhost:5002/api/progress/current")
        print(f"📥 Progress status: {progress_response.status_code}")
        
        if progress_response.ok:
            progress_data = progress_response.json()
            print(f"📥 Progress response: {json.dumps(progress_data, indent=2)}")
        else:
            print(f"❌ Progress request failed: {progress_response.text}")
            
    except Exception as e:
        print(f"❌ Progress test failed: {e}")
    
    print("\n" + "=" * 60)
    print("🧪 TESTS COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    print("🚀 Starting Theodore Research Flow Tests")
    print("🚀 Make sure the Flask app is running on http://localhost:5002")
    print("")
    
    # Check if server is running
    try:
        health_check = requests.get("http://localhost:5002/", timeout=5)
        print("✅ Server is running")
    except:
        print("❌ Server is not running. Please start the Flask app first.")
        exit(1)
    
    test_research_endpoint()