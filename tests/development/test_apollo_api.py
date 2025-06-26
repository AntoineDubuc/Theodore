#!/usr/bin/env python3
"""
Apollo.io API Test Script
Tests organization search and job postings endpoints with sample companies
"""

import os
import json
import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

class ApolloAPITester:
    """Test Apollo.io API endpoints for Theodore integration"""
    
    def __init__(self, api_key: str):
        """Initialize with Apollo.io API key"""
        self.api_key = api_key
        self.base_url = "https://api.apollo.io/api/v1"
        self.headers = {
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "X-Api-Key": api_key
        }
        
        # Test companies to research
        self.test_companies = [
            {"name": "Stripe", "domain": "stripe.com"},
            {"name": "Shopify", "domain": "shopify.com"},
            {"name": "Slack", "domain": "slack.com"},
            {"name": "Notion", "domain": "notion.so"},
            {"name": "Figma", "domain": "figma.com"}
        ]
        
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "test_results": [],
            "summary": {},
            "errors": []
        }
    
    def search_organizations(self, company_name: str, domain: str = None) -> Optional[Dict]:
        """Test organization search API"""
        
        print(f"\n🔍 Searching for organization: {company_name}")
        
        # Build search payload
        payload = {
            "q_organization_name": company_name,
            "page": 1,
            "per_page": 10
        }
        
        if domain:
            payload["q_organization_domains"] = [domain]
        
        try:
            response = requests.post(
                f"{self.base_url}/mixed_companies/search",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                organizations = data.get("organizations", [])
                
                if organizations:
                    org = organizations[0]  # Get first match
                    print(f"   ✅ Found: {org.get('name')} (ID: {org.get('id')})")
                    print(f"   📍 Location: {org.get('city')}, {org.get('state')}, {org.get('country')}")
                    print(f"   🏢 Industry: {org.get('industry')}")
                    print(f"   👥 Employees: {org.get('estimated_num_employees')}")
                    print(f"   🌐 Website: {org.get('website_url')}")
                    
                    return {
                        "success": True,
                        "organization": org,
                        "total_results": data.get("pagination", {}).get("total_entries", 0)
                    }
                else:
                    print(f"   ❌ No organizations found for {company_name}")
                    return {"success": False, "error": "No organizations found"}
                    
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                print(f"   ❌ {error_msg}")
                return {"success": False, "error": error_msg}
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            return {"success": False, "error": error_msg}
    
    def get_job_postings(self, organization_id: str, company_name: str) -> Optional[Dict]:
        """Test job postings API for a specific organization"""
        
        print(f"\n💼 Getting job postings for: {company_name} (ID: {organization_id})")
        
        try:
            response = requests.get(
                f"{self.base_url}/organizations/{organization_id}/job_postings",
                headers=self.headers,
                timeout=30
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                job_postings = data.get("job_postings", [])
                
                print(f"   ✅ Found {len(job_postings)} job postings")
                
                if job_postings:
                    # Analyze job posting data
                    departments = {}
                    locations = {}
                    
                    for job in job_postings[:5]:  # Show first 5 jobs
                        title = job.get("title", "Unknown")
                        department = job.get("department", "Unknown")
                        location = job.get("location", "Unknown")
                        posted_date = job.get("posted_at", "Unknown")
                        
                        print(f"   📋 {title} | {department} | {location} | {posted_date}")
                        
                        # Count departments and locations
                        departments[department] = departments.get(department, 0) + 1
                        locations[location] = locations.get(location, 0) + 1
                    
                    print(f"   📊 Top Departments: {dict(sorted(departments.items(), key=lambda x: x[1], reverse=True)[:3])}")
                    print(f"   📍 Top Locations: {dict(sorted(locations.items(), key=lambda x: x[1], reverse=True)[:3])}")
                    
                    return {
                        "success": True,
                        "job_postings": job_postings,
                        "total_jobs": len(job_postings),
                        "departments": departments,
                        "locations": locations,
                        "growth_signal": len(job_postings) > 10  # Companies with 10+ jobs are likely growing
                    }
                else:
                    print(f"   ❌ No job postings found")
                    return {"success": True, "job_postings": [], "total_jobs": 0}
                    
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                print(f"   ❌ {error_msg}")
                return {"success": False, "error": error_msg}
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            return {"success": False, "error": error_msg}
    
    def test_company(self, company: Dict[str, str]) -> Dict[str, Any]:
        """Test both APIs for a single company"""
        
        company_name = company["name"]
        domain = company.get("domain")
        
        print(f"\n" + "="*60)
        print(f"🏢 TESTING: {company_name}")
        print(f"="*60)
        
        result = {
            "company_name": company_name,
            "domain": domain,
            "timestamp": datetime.utcnow().isoformat(),
            "organization_search": None,
            "job_postings": None,
            "apollo_intelligence": {}
        }
        
        # Step 1: Search for organization
        org_result = self.search_organizations(company_name, domain)
        result["organization_search"] = org_result
        
        if org_result and org_result.get("success"):
            org_data = org_result.get("organization", {})
            org_id = org_data.get("id")
            
            # Step 2: Get job postings if we found the organization
            if org_id:
                time.sleep(1)  # Rate limiting
                job_result = self.get_job_postings(org_id, company_name)
                result["job_postings"] = job_result
                
                # Step 3: Generate Apollo intelligence summary
                if job_result and job_result.get("success"):
                    result["apollo_intelligence"] = {
                        "company_found": True,
                        "employee_count": org_data.get("estimated_num_employees"),
                        "industry": org_data.get("industry"),
                        "location": f"{org_data.get('city')}, {org_data.get('state')}",
                        "website": org_data.get("website_url"),
                        "active_jobs": job_result.get("total_jobs", 0),
                        "growth_signal": job_result.get("growth_signal", False),
                        "top_departments": list(job_result.get("departments", {}).keys())[:3],
                        "hiring_locations": list(job_result.get("locations", {}).keys())[:3]
                    }
                else:
                    result["apollo_intelligence"] = {
                        "company_found": True,
                        "job_data_available": False
                    }
            else:
                result["apollo_intelligence"] = {
                    "company_found": False,
                    "error": "No organization ID found"
                }
        else:
            result["apollo_intelligence"] = {
                "company_found": False,
                "error": org_result.get("error", "Unknown error") if org_result else "No search result"
            }
        
        return result
    
    def run_full_test(self) -> Dict[str, Any]:
        """Run complete Apollo.io API test suite"""
        
        print("🚀 APOLLO.IO API TEST SUITE")
        print("="*60)
        print(f"Testing {len(self.test_companies)} companies")
        print(f"Timestamp: {self.results['timestamp']}")
        
        # Test each company
        for i, company in enumerate(self.test_companies, 1):
            print(f"\n[{i}/{len(self.test_companies)}] Testing {company['name']}...")
            
            try:
                result = self.test_company(company)
                self.results["test_results"].append(result)
                
                # Rate limiting between companies
                if i < len(self.test_companies):
                    print(f"\n⏱️  Waiting 2 seconds before next test...")
                    time.sleep(2)
                    
            except Exception as e:
                error = {
                    "company": company["name"],
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.results["errors"].append(error)
                print(f"   ❌ Unexpected error: {e}")
        
        # Generate summary
        self.generate_summary()
        
        return self.results
    
    def generate_summary(self):
        """Generate test summary and statistics"""
        
        total_tests = len(self.test_companies)
        successful_searches = 0
        companies_found = 0
        total_jobs = 0
        growing_companies = 0
        
        for result in self.results["test_results"]:
            # Organization search success
            if result.get("organization_search", {}).get("success"):
                successful_searches += 1
            
            # Company intelligence
            intel = result.get("apollo_intelligence", {})
            if intel.get("company_found"):
                companies_found += 1
                
                active_jobs = intel.get("active_jobs", 0)
                if active_jobs:
                    total_jobs += active_jobs
                    
                if intel.get("growth_signal"):
                    growing_companies += 1
        
        self.results["summary"] = {
            "total_companies_tested": total_tests,
            "successful_api_calls": successful_searches,
            "companies_found_in_apollo": companies_found,
            "companies_with_job_data": sum(1 for r in self.results["test_results"] 
                                         if r.get("job_postings", {}).get("success")),
            "total_job_postings_found": total_jobs,
            "companies_showing_growth": growing_companies,
            "api_success_rate": f"{(successful_searches/total_tests)*100:.1f}%",
            "data_coverage_rate": f"{(companies_found/total_tests)*100:.1f}%"
        }
    
    def save_results(self, filename: str = None):
        """Save test results to JSON file"""
        
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"apollo_api_test_results_{timestamp}.json"
        
        filepath = f"/Users/antoinedubuc/Desktop/AI_Goodies/Theodore/tests/development/{filename}"
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filepath}")
        return filepath
    
    def print_summary(self):
        """Print detailed test summary"""
        
        summary = self.results["summary"]
        
        print(f"\n" + "="*60)
        print("📊 APOLLO.IO API TEST SUMMARY")
        print("="*60)
        print(f"📈 API Success Rate: {summary['api_success_rate']}")
        print(f"🏢 Companies Found: {summary['companies_found_in_apollo']}/{summary['total_companies_tested']}")
        print(f"💼 Companies with Job Data: {summary['companies_with_job_data']}")
        print(f"📋 Total Job Postings: {summary['total_job_postings_found']}")
        print(f"🚀 Growing Companies: {summary['companies_showing_growth']}")
        print(f"📊 Data Coverage: {summary['data_coverage_rate']}")
        
        if self.results["errors"]:
            print(f"\n❌ Errors Encountered: {len(self.results['errors'])}")
            for error in self.results["errors"]:
                print(f"   • {error['company']}: {error['error']}")
        
        print(f"\n🎯 INTEGRATION RECOMMENDATION:")
        
        coverage_rate = float(summary['data_coverage_rate'].rstrip('%'))
        success_rate = float(summary['api_success_rate'].rstrip('%'))
        
        if coverage_rate >= 80 and success_rate >= 90:
            print("   ✅ EXCELLENT - Proceed with full Apollo.io integration")
        elif coverage_rate >= 60 and success_rate >= 80:
            print("   🟡 GOOD - Apollo.io integration recommended with monitoring")
        elif coverage_rate >= 40 and success_rate >= 70:
            print("   🟠 FAIR - Consider Apollo.io as supplementary data source")
        else:
            print("   🔴 POOR - Review API configuration and test with more companies")


def main():
    """Main test execution"""
    
    # Get Apollo.io API key from environment
    api_key = os.getenv('APOLLO_API_KEY')
    
    if not api_key:
        print("❌ Error: APOLLO_API_KEY environment variable not set")
        print("Please set your Apollo.io API key:")
        print("export APOLLO_API_KEY='your_api_key_here'")
        return
    
    print(f"🔑 Using API key: {api_key[:8]}...")
    
    # Initialize tester
    tester = ApolloAPITester(api_key)
    
    # Run full test suite
    try:
        results = tester.run_full_test()
        
        # Print summary
        tester.print_summary()
        
        # Save results
        tester.save_results()
        
        print(f"\n🎉 Apollo.io API testing completed successfully!")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")


if __name__ == "__main__":
    main()