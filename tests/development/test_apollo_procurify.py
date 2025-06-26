#!/usr/bin/env python3
"""
Apollo.io API Test - Procurify Only
Simple test focusing on just Procurify to validate Apollo.io integration
"""

import os
import json
import requests
import time
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file
def load_env():
    """Load environment variables from .env file"""
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    os.environ[key] = value

# Load .env file
load_env()

def test_procurify_apollo():
    """Test Apollo.io APIs specifically for Procurify"""
    
    print("🔍 APOLLO.IO API TEST - PROCURIFY")
    print("="*50)
    
    # Get API key
    api_key = os.getenv('APOLLO_API_KEY')
    if not api_key:
        print("❌ Error: APOLLO_API_KEY environment variable not set")
        print("Please run: export APOLLO_API_KEY='your_api_key_here'")
        return
    
    print(f"🔑 Using API key: {api_key[:8]}...")
    
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "X-Api-Key": api_key
    }
    
    # Procurify test data
    company = {
        "name": "Procurify",
        "domain": "procurify.com"
    }
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "company": company,
        "organization_search": None,
        "job_postings": None,
        "summary": {}
    }
    
    print(f"\n🏢 Testing company: {company['name']}")
    print(f"🌐 Domain: {company['domain']}")
    
    # Step 1: Search for Procurify organization
    print(f"\n" + "="*40)
    print("STEP 1: Organization Search")
    print("="*40)
    
    search_payload = {
        "q_organization_name": company["name"],
        "q_organization_domains": [company["domain"]],
        "page": 1,
        "per_page": 5
    }
    
    try:
        print("🔍 Searching Apollo database...")
        response = requests.post(
            "https://api.apollo.io/api/v1/mixed_companies/search",
            headers=headers,
            json=search_payload,
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            organizations = data.get("organizations", [])
            
            if organizations:
                org = organizations[0]  # Get best match
                org_id = org.get("id")
                
                print(f"✅ Found Procurify!")
                print(f"   Organization ID: {org_id}")
                print(f"   Name: {org.get('name')}")
                print(f"   Industry: {org.get('industry')}")
                print(f"   Employees: {org.get('estimated_num_employees')}")
                print(f"   Location: {org.get('city')}, {org.get('state')}, {org.get('country')}")
                print(f"   Website: {org.get('website_url')}")
                print(f"   Founded: {org.get('founded_year')}")
                print(f"   Description: {org.get('short_description', 'N/A')[:100]}...")
                
                results["organization_search"] = {
                    "success": True,
                    "organization": org,
                    "total_results": data.get("pagination", {}).get("total_entries", 0)
                }
                
                # Step 2: Get job postings
                print(f"\n" + "="*40)
                print("STEP 2: Job Postings")
                print("="*40)
                
                print("⏱️  Waiting 2 seconds (rate limiting)...")
                time.sleep(2)
                
                print(f"💼 Getting job postings for Procurify...")
                job_response = requests.get(
                    f"https://api.apollo.io/api/v1/organizations/{org_id}/job_postings",
                    headers=headers,
                    timeout=30
                )
                
                print(f"Job Postings Response Status: {job_response.status_code}")
                
                if job_response.status_code == 200:
                    job_data = job_response.json()
                    job_postings = job_data.get("job_postings", [])
                    
                    print(f"✅ Found {len(job_postings)} job postings")
                    
                    if job_postings:
                        print(f"\n📋 Current Job Openings:")
                        
                        departments = {}
                        locations = {}
                        seniority_levels = {}
                        
                        for i, job in enumerate(job_postings, 1):
                            title = job.get("title", "Unknown")
                            department = job.get("department", "Unknown")
                            location = job.get("location", "Unknown") 
                            seniority = job.get("seniority_level", "Unknown")
                            posted_date = job.get("posted_at", "Unknown")
                            
                            print(f"   {i:2d}. {title}")
                            print(f"       Department: {department}")
                            print(f"       Location: {location}")
                            print(f"       Level: {seniority}")
                            print(f"       Posted: {posted_date}")
                            print()
                            
                            # Count statistics
                            departments[department] = departments.get(department, 0) + 1
                            locations[location] = locations.get(location, 0) + 1
                            seniority_levels[seniority] = seniority_levels.get(seniority, 0) + 1
                        
                        # Show hiring trends
                        print(f"📊 HIRING ANALYSIS:")
                        print(f"   Departments: {dict(sorted(departments.items(), key=lambda x: x[1], reverse=True))}")
                        print(f"   Locations: {dict(sorted(locations.items(), key=lambda x: x[1], reverse=True))}")
                        print(f"   Seniority: {dict(sorted(seniority_levels.items(), key=lambda x: x[1], reverse=True))}")
                        
                        # Growth signals
                        total_jobs = len(job_postings)
                        engineering_jobs = departments.get("Engineering", 0) + departments.get("Technology", 0)
                        remote_jobs = sum(1 for loc in locations.keys() if "remote" in loc.lower())
                        
                        print(f"\n🚀 GROWTH SIGNALS:")
                        print(f"   Total Active Jobs: {total_jobs}")
                        print(f"   Engineering/Tech Jobs: {engineering_jobs}")
                        print(f"   Remote Opportunities: {remote_jobs}")
                        print(f"   Growth Signal: {'🟢 HIGH' if total_jobs > 10 else '🟡 MODERATE' if total_jobs > 5 else '🔴 LOW'}")
                        
                        results["job_postings"] = {
                            "success": True,
                            "total_jobs": total_jobs,
                            "departments": departments,
                            "locations": locations,
                            "seniority_levels": seniority_levels,
                            "engineering_focus": engineering_jobs,
                            "remote_friendly": remote_jobs > 0,
                            "growth_signal": total_jobs > 10
                        }
                    else:
                        print("📋 No active job postings found")
                        results["job_postings"] = {
                            "success": True,
                            "total_jobs": 0,
                            "note": "No job postings available"
                        }
                        
                else:
                    error_msg = f"Job postings API error {job_response.status_code}: {job_response.text}"
                    print(f"❌ {error_msg}")
                    results["job_postings"] = {"success": False, "error": error_msg}
                    
            else:
                print("❌ Procurify not found in Apollo database")
                results["organization_search"] = {
                    "success": False,
                    "error": "Company not found"
                }
                
        else:
            error_msg = f"Organization search API error {response.status_code}: {response.text}"
            print(f"❌ {error_msg}")
            results["organization_search"] = {"success": False, "error": error_msg}
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        print(f"❌ {error_msg}")
        results["organization_search"] = {"success": False, "error": error_msg}
    
    # Generate summary
    print(f"\n" + "="*50)
    print("📊 PROCURIFY APOLLO.IO TEST SUMMARY")
    print("="*50)
    
    org_success = results.get("organization_search", {}).get("success", False)
    job_success = results.get("job_postings", {}).get("success", False)
    
    print(f"🔍 Organization Search: {'✅ SUCCESS' if org_success else '❌ FAILED'}")
    print(f"💼 Job Postings: {'✅ SUCCESS' if job_success else '❌ FAILED'}")
    
    if org_success:
        org_data = results["organization_search"]["organization"]
        print(f"📈 Employee Count: {org_data.get('estimated_num_employees', 'Unknown')}")
        print(f"🏢 Industry: {org_data.get('industry', 'Unknown')}")
        print(f"📍 Location: {org_data.get('city', 'Unknown')}, {org_data.get('country', 'Unknown')}")
        
        if job_success and results["job_postings"].get("total_jobs", 0) > 0:
            job_data = results["job_postings"]
            print(f"💼 Active Jobs: {job_data['total_jobs']}")
            print(f"🚀 Growth Signal: {'YES' if job_data.get('growth_signal') else 'NO'}")
            print(f"🏠 Remote Friendly: {'YES' if job_data.get('remote_friendly') else 'NO'}")
    
    # Save results
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"apollo_procurify_test_{timestamp}.json"
    filepath = f"tests/development/{filename}"
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filepath}")
    
    # Integration recommendation
    print(f"\n🎯 INTEGRATION RECOMMENDATION:")
    if org_success and job_success:
        print("   ✅ EXCELLENT - Apollo.io has good data coverage for Procurify")
        print("   🚀 Recommend proceeding with Theodore integration")
    elif org_success:
        print("   🟡 GOOD - Organization data available, limited job data")
        print("   📝 Consider Apollo.io for company profiles")
    else:
        print("   🔴 POOR - Limited data availability")
        print("   ❓ Test with more companies before integration decision")
    
    return results

if __name__ == "__main__":
    try:
        results = test_procurify_apollo()
        print(f"\n🎉 Procurify Apollo.io test completed!")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()