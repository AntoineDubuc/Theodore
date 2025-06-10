#!/usr/bin/env python3
"""
Test the enhanced job listings crawler that tries common career URL patterns
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

def test_msi_enhanced_discovery():
    """Test MSI with the enhanced career URL discovery"""
    print("🧪 Testing MSI with enhanced career URL discovery...")
    
    try:
        # Initialize OpenAI client
        openai_client = SimpleOpenAIClient()
        
        # Initialize enhanced job listings crawler
        crawler = JobListingsCrawler(openai_client=openai_client)
        
        # Test the URL pattern discovery specifically
        print("🔍 Testing URL pattern discovery for MSI...")
        career_url = crawler._try_common_career_urls("MSI")
        
        if career_url:
            print(f"✅ SUCCESS: Found career URL: {career_url}")
            if "ca.msi.com/about/careers" in career_url:
                print(f"🎉 PERFECT: Discovered the exact URL you mentioned!")
            else:
                print(f"📝 Found different career URL than expected")
        else:
            print(f"❌ No career URL found via patterns")
        
        # Test full job listings crawl
        print(f"\n🏢 Testing full MSI job listings crawl...")
        result = crawler.crawl_job_listings("MSI", "https://www.msi.com")
        
        print(f"\n✅ Final Result:")
        print(f"📋 Job Listings: {result.get('job_listings', 'Not available')}")
        print(f"🔍 Source: {result.get('source', 'Unknown')}")
        print(f"📊 Steps Completed: {result.get('steps_completed', 'Unknown')}")
        print(f"💭 Reason: {result.get('reason', 'N/A')}")
        
        if result.get('details'):
            details = result['details']
            print(f"\n📋 Enhanced Details:")
            if details.get('career_page_url'):
                print(f"📄 Career Page: {details['career_page_url']}")
            if details.get('best_job_sites'):
                print(f"🔍 Best Job Sites: {', '.join(details['best_job_sites'])}")
            if details.get('search_tips'):
                print(f"💡 Search Tips: {details['search_tips']}")
            if details.get('hiring_status'):
                print(f"✅ Hiring Status: {details['hiring_status']}")
        
        # Check if we discovered a real career page
        if 'discovered_career_page' in result.get('source', ''):
            print(f"\n🌟 BREAKTHROUGH: Successfully discovered and crawled a real career page!")
            print(f"🎯 This is much better than just LLM knowledge fallback.")
        elif 'google_search' in result.get('source', ''):
            print(f"\n📝 Fell back to LLM knowledge - URL discovery didn't find accessible pages")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_msi_enhanced_discovery()