#!/usr/bin/env python3
"""
UI Simulation Test - Uses the exact same endpoint as the web UI
"""

import requests
import time
import json
from datetime import datetime

def test_single_company_ui_way(company_name: str):
    """Test using the exact same API call as the web UI Add Company button"""
    
    print(f"🔍 Testing {company_name} using UI simulation...")
    
    # Use the exact same payload format as the web UI
    payload = {
        "company_name": company_name,
        "website": f"https://{company_name}"
    }
    
    start_time = time.time()
    
    try:
        # Use the same endpoint as the web UI "Add Company" button
        print(f"📡 Calling /api/process-company...")
        response = requests.post(
            "http://localhost:5002/api/process-company",
            json=payload,
            timeout=180  # 3 minutes like the UI
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"📋 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Processing time: {processing_time:.1f}s")
            
            # Extract company data
            company_data = data.get('company', {})
            print(f"📊 Company data keys: {list(company_data.keys())}")
            
            # Key information
            print(f"🏢 Name: {company_data.get('name', 'Not extracted')}")
            print(f"🏭 Industry: {company_data.get('industry', 'Not extracted')}")
            print(f"💼 Business Model: {company_data.get('business_model', 'Not extracted')}")
            print(f"📄 Pages Crawled: {len(company_data.get('pages_crawled', []))}")
            
            # Calculate coverage
            key_fields = ['name', 'company_description', 'industry', 'business_model', 'company_size', 'target_market']
            populated = sum(1 for field in key_fields if company_data.get(field))
            coverage = (populated / len(key_fields)) * 100
            print(f"📈 Coverage: {coverage:.1f}% ({populated}/{len(key_fields)} fields)")
            
            return {
                "success": True,
                "company_name": company_name,
                "processing_time": processing_time,
                "coverage_percentage": coverage,
                "populated_fields": populated,
                "total_fields": len(key_fields),
                "extracted_data": {
                    "name": company_data.get('name'),
                    "industry": company_data.get('industry'),
                    "business_model": company_data.get('business_model'),
                    "company_description": company_data.get('company_description'),
                    "pages_crawled": len(company_data.get('pages_crawled', [])),
                    "ai_summary_length": len(company_data.get('ai_summary', '') or '')
                },
                "full_response": data
            }
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"🔍 Response: {response.text}")
            return {
                "success": False,
                "company_name": company_name,
                "error": f"HTTP {response.status_code}: {response.text}",
                "processing_time": processing_time
            }
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {
            "success": False,
            "company_name": company_name,
            "error": str(e),
            "processing_time": time.time() - start_time
        }

def main():
    """Test one company to see if the UI approach works"""
    
    print("🎯 UI Simulation Test")
    print("=" * 50)
    print("Testing the exact same API call as the web UI 'Add Company' button")
    
    # Check if app is running
    try:
        response = requests.get("http://localhost:5002/", timeout=5)
        print("✅ Theodore app is running")
    except:
        print("❌ Theodore app is not running")
        return
    
    # Test one company first
    test_company = "certara.com"
    result = test_single_company_ui_way(test_company)
    
    # Save result
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = f"docs/analysis/ui_simulation_test_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n📁 Result saved to: {output_file}")
    
    if result["success"]:
        print(f"\n🎉 SUCCESS! The UI approach works.")
        print(f"   Company: {result['extracted_data']['name']}")
        print(f"   Industry: {result['extracted_data']['industry']}")
        print(f"   Coverage: {result['coverage_percentage']}%")
        print(f"   Time: {result['processing_time']:.1f}s")
        print(f"\n💡 We can now run the full comparison using this approach!")
    else:
        print(f"\n🚨 FAILED: {result['error']}")

if __name__ == "__main__":
    main()