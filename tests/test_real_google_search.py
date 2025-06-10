#!/usr/bin/env python3
"""
Test the REAL Google search implementation for MSI job listings
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

def test_real_google_search():
    """Test REAL Google search for MSI careers"""
    print("🌐 Testing REAL Google search for MSI careers...")
    
    try:
        # Initialize OpenAI client
        openai_client = SimpleOpenAIClient()
        
        # Initialize job listings crawler with real Google search
        crawler = JobListingsCrawler(openai_client=openai_client)
        
        # Test Google search API directly
        print("🔍 Testing Google search APIs...")
        
        # Check available API keys
        google_api_key = os.getenv('GOOGLE_API_KEY')
        google_cx = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        serpapi_key = os.getenv('SERPAPI_KEY')
        
        print(f"📋 Available APIs:")
        print(f"   Google Custom Search: {'✅ Available' if google_api_key and google_cx else '❌ Not configured'}")
        print(f"   SerpAPI: {'✅ Available' if serpapi_key else '❌ Not configured'}")
        print(f"   Direct Search: ✅ Available (fallback)")
        
        # Test direct Google search for MSI
        print(f"\n🔍 Performing Google search for 'MSI careers'...")
        urls = crawler._google_search_api("MSI careers")
        
        if urls:
            print(f"✅ Google search found {len(urls)} results:")
            for i, url in enumerate(urls[:5], 1):
                print(f"   {i}. {url}")
                
                # Check if any look like career pages
                if crawler._is_likely_career_url(url):
                    print(f"      ✅ This looks like a career page!")
                    
                    # Check if it's the specific MSI careers page you mentioned
                    if "ca.msi.com/about/careers" in url:
                        print(f"      🎉 FOUND THE EXACT URL YOU MENTIONED!")
        else:
            print(f"❌ Google search returned no results")
        
        # Test full job listings discovery with real Google search
        print(f"\n🏢 Testing full MSI job listings discovery with REAL Google search...")
        result = crawler.crawl_job_listings("MSI", "https://www.msi.com")
        
        print(f"\n✅ Final Result:")
        print(f"📋 Job Listings: {result.get('job_listings', 'Not available')}")
        print(f"🔍 Source: {result.get('source', 'Unknown')}")
        
        if 'google_search' in result.get('source', ''):
            print(f"🌐 ✅ SUCCESS: REAL Google search was used!")
            if result.get('search_query'):
                print(f"📝 Search Query: {result['search_query']}")
        
        if result.get('career_page_url'):
            print(f"📄 Career Page Found: {result['career_page_url']}")
            
            # Check if we found the Canadian MSI careers page
            if "ca.msi.com/about/careers" in result['career_page_url']:
                print(f"🎯 PERFECT: Found the exact MSI careers page you mentioned!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_google_search()