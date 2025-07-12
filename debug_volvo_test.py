#!/usr/bin/env python3
"""
Debug Volvo Canada Processing Issue
==================================

Test script to debug the specific Volvo Canada processing failure
and identify the root cause of the 500 error.
"""

import sys
import requests
import json
import time

def test_volvo_canada():
    """Test Volvo Canada processing to identify the issue"""
    
    print("🔍 Testing Volvo Canada Processing")
    print("=" * 50)
    
    # Test data
    company_data = {
        "company_name": "Volvo Canada",
        "website": "https://www.volvo.ca"
    }
    
    print(f"🏢 Company: {company_data['company_name']}")
    print(f"🌐 Website: {company_data['website']}")
    
    try:
        # Send request to process company
        print("\n📤 Sending processing request...")
        response = requests.post(
            "http://localhost:5002/api/process-company",
            json=company_data,
            timeout=60
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success Response:")
            print(json.dumps(result, indent=2))
            
            # Check if we got a job_id to monitor progress
            if 'job_id' in result:
                job_id = result['job_id']
                print(f"\n📊 Monitoring progress for job: {job_id}")
                
                # Monitor progress for a few seconds
                for i in range(10):
                    try:
                        progress_response = requests.get(f"http://localhost:5002/api/progress/current")
                        if progress_response.status_code == 200:
                            progress = progress_response.json()
                            print(f"⏱️  Progress check {i+1}: {progress.get('message', 'No progress')}")
                            
                            if progress.get('status') == 'no_active_job':
                                print("ℹ️  Job completed or failed")
                                break
                                
                        time.sleep(2)
                    except Exception as e:
                        print(f"⚠️  Progress check failed: {e}")
                        break
            
        elif response.status_code == 500:
            print(f"❌ Server Error (500):")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(f"Raw error response: {response.text}")
                
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out after 60 seconds")
    except requests.exceptions.ConnectionError:
        print("🔌 Connection error - is the server running?")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

def test_simple_website():
    """Test with a simple website to see if the issue is Volvo-specific"""
    
    print("\n🔍 Testing Simple Website for Comparison")
    print("=" * 50)
    
    # Test with a simpler website
    company_data = {
        "company_name": "Stripe",
        "website": "https://stripe.com"
    }
    
    print(f"🏢 Company: {company_data['company_name']}")
    print(f"🌐 Website: {company_data['website']}")
    
    try:
        print("\n📤 Sending processing request...")
        response = requests.post(
            "http://localhost:5002/api/process-company",
            json=company_data,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Simple website processing successful")
            print(f"Job ID: {result.get('job_id', 'No job ID')}")
        else:
            print(f"❌ Simple website also failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Simple website test failed: {e}")

if __name__ == "__main__":
    print("🐛 Volvo Canada Debug Test")
    print("=" * 70)
    
    # Test Volvo Canada
    test_volvo_canada()
    
    # Test simple website for comparison
    test_simple_website()
    
    print("\n✅ Debug test completed!")