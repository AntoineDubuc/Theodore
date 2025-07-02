#!/usr/bin/env python3
"""
Test Full Scraper Flow - Debug where the actual failure occurs
"""

import asyncio
import sys
import os
sys.path.append(os.getcwd())

from src.intelligent_company_scraper import IntelligentCompanyScraper
from src.models import CompanyData, CompanyIntelligenceConfig
from dotenv import load_dotenv

load_dotenv()

async def test_full_scraper_flow():
    """Test the full scraper flow with debug output"""
    print(f"🔍 Testing full scraper flow")
    
    # Create test data
    company_data = CompanyData(
        name="KRK Music",
        website="https://www.krkmusic.com"
    )
    
    # Create scraper
    config = CompanyIntelligenceConfig()
    scraper = IntelligentCompanyScraper(config)
    
    try:
        print(f"🚀 Starting scraper...")
        result = await scraper.scrape_company_intelligent(company_data, job_id="test_debug")
        
        print(f"✅ Scraper completed!")
        print(f"📊 Results:")
        print(f"   Status: {result.scrape_status}")
        print(f"   Error: {result.scrape_error}")
        print(f"   Description: {result.company_description[:200] if result.company_description else 'None'}...")
        print(f"   Pages crawled: {len(result.pages_crawled) if result.pages_crawled else 0}")
        
    except Exception as e:
        print(f"❌ Scraper failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_scraper_flow())