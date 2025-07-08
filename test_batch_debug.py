#!/usr/bin/env python3
"""
Debug script to test batch processing and see what's happening with progress tracking
"""

import requests
import time
import json

# Configuration
BASE_URL = "http://localhost:5002"
SHEET_ID = "1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk"  # Your Google Sheet ID

def test_batch_processing():
    """Test batch processing with debug output"""
    
    print("🔍 Testing batch processing debug...")
    
    # Start batch processing
    payload = {
        "sheet_id": SHEET_ID,
        "batch_size": 2,  # Small batch for testing
        "start_row": 2,
        "max_concurrent": 1  # Sequential for easier debugging
    }
    
    print(f"\n📋 Starting batch with payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/api/batch/process", json=payload)
    
    if not response.ok:
        print(f"❌ Failed to start batch: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    data = response.json()
    print(f"\n✅ Batch started: {json.dumps(data, indent=2)}")
    
    job_id = data.get('job_id')
    if not job_id:
        print("❌ No job_id returned")
        return
    
    # Poll for progress
    print(f"\n📊 Polling progress for job {job_id}...")
    
    for i in range(120):  # Poll for up to 2 minutes
        progress_response = requests.get(f"{BASE_URL}/api/batch/progress/{job_id}")
        
        if progress_response.ok:
            progress = progress_response.json()
            
            print(f"\n[{i+1}] Progress update:")
            print(f"  Status: {progress.get('status')}")
            print(f"  Processed: {progress.get('processed', 0)}/{progress.get('total_companies', 0)}")
            print(f"  Successful: {progress.get('successful', 0)}")
            print(f"  Failed: {progress.get('failed', 0)}")
            print(f"  Current: {progress.get('current_company', 'N/A')}")
            print(f"  Message: {progress.get('current_message', 'N/A')}")
            
            if progress.get('status') == 'completed':
                print("\n✅ Batch processing completed!")
                
                # Print results
                results = progress.get('results', {})
                print(f"\n📊 Final Results:")
                print(f"  Total companies: {progress.get('total_companies', 0)}")
                print(f"  Successful: {len(results.get('successful', []))}")
                print(f"  Failed: {len(results.get('failed', []))}")
                print(f"  Total cost: ${results.get('total_cost_usd', 0):.4f}")
                print(f"  Total tokens: {results.get('total_input_tokens', 0)} + {results.get('total_output_tokens', 0)}")
                
                # Print individual company results
                print(f"\n📋 Company Results:")
                for company in results.get('successful', []):
                    print(f"  ✅ {company.get('name')} - Row {company.get('row')}")
                    print(f"     Cost: ${company.get('cost_usd', 0):.4f}")
                    print(f"     Tokens: {company.get('tokens', {}).get('input', 0)} + {company.get('tokens', {}).get('output', 0)}")
                    print(f"     Pinecone: {'Yes' if company.get('pinecone_saved') else 'No'}")
                
                for company in results.get('failed', []):
                    print(f"  ❌ {company.get('name')} - Row {company.get('row')}")
                    print(f"     Error: {company.get('error', 'Unknown')}")
                
                break
                
        else:
            print(f"\n[{i+1}] Failed to get progress: {progress_response.status_code}")
        
        time.sleep(2)  # Wait 2 seconds before next poll
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    test_batch_processing()