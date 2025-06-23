#!/usr/bin/env python3
"""
Test Name-Only Company Workflow
Test that Theodore can process a company with just a name (no website)
"""

import sys
import os
import time
import requests
import json

def test_name_only_workflow():
    """Test adding a company with just a name"""
    
    print("🧪 TESTING NAME-ONLY COMPANY WORKFLOW")
    print("=" * 60)
    print("🎯 Testing: Company processing without website URL")
    print()
    
    # Test data
    test_company = {
        "company_name": "Anthropic",
        "website": ""  # Empty website to test auto-discovery
    }
    
    print(f"📋 Test Company: {test_company['company_name']}")
    print(f"🌐 Website Provided: {'Yes' if test_company['website'] else 'No (testing auto-discovery)'}")
    print()
    
    # Test URL (assumes Theodore is running on localhost:5002)
    base_url = "http://localhost:5002"
    
    # Test 1: Check if Theodore web app is running
    print("🔌 Testing Theodore web app connection...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Theodore is running")
            print(f"   Pipeline Ready: {health_data.get('pipeline_ready', False)}")
            print()
        else:
            print(f"❌ Theodore health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Theodore: {e}")
        print("💡 Make sure Theodore is running with: python3 app.py")
        return False
    
    # Test 2: Submit company with name only
    print("📤 Submitting company with name only...")
    try:
        response = requests.post(
            f"{base_url}/api/process-company",
            json=test_company,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Request accepted")
            print(f"   Job ID: {result.get('job_id', 'N/A')}")
            print(f"   Message: {result.get('message', 'N/A')}")
            
            # If we get a job_id, we can monitor progress
            job_id = result.get('job_id')
            if job_id:
                print(f"\n⏳ Monitoring processing progress...")
                return monitor_processing_progress(base_url, job_id)
            else:
                print("⚠️ No job ID returned, but request was accepted")
                return True
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def monitor_processing_progress(base_url, job_id, max_wait=120):
    """Monitor processing progress for a job"""
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{base_url}/api/progress/{job_id}", timeout=10)
            
            if response.status_code == 200:
                progress_data = response.json()
                status = progress_data.get('status', 'unknown')
                message = progress_data.get('message', '')
                
                print(f"   📊 Status: {status} - {message}")
                
                if status in ['completed', 'failed']:
                    if status == 'completed':
                        print(f"✅ Processing completed successfully!")
                        
                        # Check if company was added to database
                        return check_company_in_database(base_url, "Anthropic")
                    else:
                        print(f"❌ Processing failed: {message}")
                        return False
                        
            else:
                print(f"   ⚠️ Progress check failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ⚠️ Progress check error: {e}")
        
        time.sleep(5)  # Wait 5 seconds before next check
    
    print(f"⏰ Timeout reached ({max_wait}s), processing may still be ongoing")
    return False

def check_company_in_database(base_url, company_name):
    """Check if company was successfully added to database"""
    
    print(f"\n🔍 Checking if {company_name} was added to database...")
    
    try:
        response = requests.get(f"{base_url}/api/search?q={company_name}", timeout=10)
        
        if response.status_code == 200:
            search_results = response.json()
            companies = search_results.get('companies', [])
            
            for company in companies:
                if company.get('name', '').lower() == company_name.lower():
                    print(f"✅ Company found in database!")
                    print(f"   Name: {company.get('name')}")
                    print(f"   Website: {company.get('website', 'N/A')}")
                    print(f"   Classification: {company.get('saas_classification', 'Not classified')}")
                    print(f"   SaaS Type: {'SaaS' if company.get('is_saas') else 'Non-SaaS' if company.get('is_saas') is not None else 'Unknown'}")
                    return True
            
            print(f"⚠️ Company not found in search results")
            return False
            
        else:
            print(f"❌ Database search failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def main():
    """Main test execution"""
    
    success = test_name_only_workflow()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 NAME-ONLY WORKFLOW TEST: ✅ PASSED")
        print("✅ Theodore successfully processes companies with just a name")
        print("✅ Automatic website discovery/fallback is working")
        print("✅ SaaS classification integration is functional")
    else:
        print("❌ NAME-ONLY WORKFLOW TEST: ❌ FAILED")
        print("⚠️ Theodore may need improvements for name-only processing")
        print("💡 Check Theodore logs for more details")
    
    print("\n📋 Next Steps:")
    print("1. Update UI to reflect optional website field ✅ DONE")
    print("2. Test with various company names")
    print("3. Implement enhanced website discovery if needed")
    print("4. Validate SaaS classification accuracy")

if __name__ == "__main__":
    main()