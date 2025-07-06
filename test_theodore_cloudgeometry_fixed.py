#!/usr/bin/env python3
"""
Test Theodore's intelligent scraper with CloudGeometry (now fixed)
"""

import asyncio
from src.models import CompanyData, CompanyIntelligenceConfig
from src.intelligent_company_scraper import IntelligentCompanyScraper

async def test_theodore_cloudgeometry():
    """Test Theodore's scraper with CloudGeometry"""
    print("="*60)
    print("TESTING THEODORE'S FIXED INTELLIGENT SCRAPER")
    print("="*60)
    
    # Create test company data
    company = CompanyData(
        name="CloudGeometry",
        website="https://cloudgeometry.com"
    )
    
    # Create config
    config = CompanyIntelligenceConfig()
    
    # Create scraper (without bedrock client for this test)
    scraper = IntelligentCompanyScraper(config)
    
    print(f"🔍 Testing CloudGeometry with Theodore's intelligent scraper...")
    print(f"Company: {company.name}")
    print(f"Website: {company.website}")
    
    try:
        # Run the full intelligent scraping pipeline
        result = await scraper.scrape_company_intelligent(company)
        
        print(f"\n📊 SCRAPING RESULTS:")
        print(f"   Status: {result.scrape_status}")
        print(f"   Pages crawled: {len(result.pages_crawled) if result.pages_crawled else 0}")
        print(f"   Crawl duration: {result.crawl_duration:.2f}s" if result.crawl_duration else "Unknown")
        print(f"   Description length: {len(result.company_description) if result.company_description else 0}")
        
        if result.scrape_status == "success":
            print(f"\n🎉 SUCCESS! Theodore's scraper now works with CloudGeometry!")
            
            if result.pages_crawled:
                print(f"\n📄 PAGES CRAWLED:")
                for i, url in enumerate(result.pages_crawled, 1):
                    print(f"   {i}. {url}")
            
            if result.company_description:
                print(f"\n📝 DESCRIPTION PREVIEW (first 500 chars):")
                print(f"{result.company_description[:500]}...")
                
        else:
            print(f"\n❌ FAILURE: {result.scrape_error}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_theodore_cloudgeometry())