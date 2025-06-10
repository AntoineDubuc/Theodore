#!/usr/bin/env python3
"""
Test the fixed job listings crawler for MSI
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, 'src')

from job_listings_crawler import JobListingsCrawler
from openai_client import SimpleOpenAIClient

def test_msi_job_listings():
    """Test job listings for MSI with the fixed crawler"""
    print("🧪 Testing MSI job listings with fixed crawler...")
    
    try:
        # Initialize OpenAI client
        openai_client = SimpleOpenAIClient()
        
        # Initialize job listings crawler
        crawler = JobListingsCrawler(openai_client=openai_client)
        
        # Test MSI
        print("🏢 Testing MSI job listings...")
        result = crawler.crawl_job_listings("MSI", "https://www.msi.com")
        
        print(f"\n✅ Result:")
        print(f"📋 Job Listings: {result.get('job_listings', 'Not available')}")
        print(f"🔍 Source: {result.get('source', 'Unknown')}")
        print(f"📊 Steps Completed: {result.get('steps_completed', 'Unknown')}")
        print(f"💭 Reason: {result.get('reason', 'N/A')}")
        
        if result.get('details'):
            details = result['details']
            print(f"\n📋 Detailed Information:")
            if details.get('career_page_url'):
                print(f"📄 Career Page: {details['career_page_url']}")
            if details.get('best_job_sites'):
                print(f"🔍 Best Job Sites: {', '.join(details['best_job_sites'])}")
            if details.get('typical_roles'):
                print(f"💼 Typical Roles: {', '.join(details['typical_roles'])}")
            if details.get('search_tips'):
                print(f"💡 Search Tips: {details['search_tips']}")
            if details.get('hiring_status'):
                print(f"✅ Hiring Status: {details['hiring_status']}")
        
        # Check if Google fallback was used
        if 'google_search' in result.get('source', ''):
            print(f"\n🌐 ✅ SUCCESS: Google search fallback was triggered!")
            print(f"📝 This means the job listings crawler is now working as intended.")
        else:
            print(f"\n⚠️ Google fallback was not used - investigating...")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_msi_job_listings()