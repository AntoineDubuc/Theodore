#!/usr/bin/env python3
"""
Test Concurrent Scraper - Debug the concurrent scraper specifically
"""

import asyncio
import sys
import os
sys.path.append(os.getcwd())

from src.concurrent_intelligent_scraper import ConcurrentIntelligentScraper
from src.models import CompanyData, CompanyIntelligenceConfig
from dotenv import load_dotenv

load_dotenv()

async def test_concurrent_scraper():
    """Test the concurrent scraper that the main pipeline uses"""
    print(f"🔍 Testing ConcurrentIntelligentScraper (used by main pipeline)")
    
    # Create test data
    company_data = CompanyData(
        name="KRK Music",
        website="https://www.krkmusic.com"
    )
    
    # Create concurrent scraper (same as main pipeline)
    config = CompanyIntelligenceConfig()
    scraper = ConcurrentIntelligentScraper(config)
    
    try:
        print(f"🚀 Starting concurrent scraper...")
        result = await scraper.scrape_company_intelligent(company_data, job_id="test_concurrent")
        
        print(f"✅ Concurrent scraper completed!")
        print(f"📊 Results:")
        print(f"   Status: {result.scrape_status}")
        print(f"   Error: {result.scrape_error}")
        print(f"   Description: {result.company_description[:200] if result.company_description else 'None'}...")
        print(f"   Pages crawled: {len(result.pages_crawled) if result.pages_crawled else 0}")
        
    except Exception as e:
        print(f"❌ Concurrent scraper failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_concurrent_scraper())