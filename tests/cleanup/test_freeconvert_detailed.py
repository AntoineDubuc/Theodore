#!/usr/bin/env python3
"""
Test FreeConvert.com scraping with detailed logging output
"""

import asyncio
import sys
import os
sys.path.append('src')

from intelligent_company_scraper import IntelligentCompanyScraper
from models import CompanyData, CompanyIntelligenceConfig
from bedrock_client import BedrockClient

async def test_freeconvert_detailed():
    print("🚀 TESTING FreeConvert.com with detailed logging...")
    
    # Initialize components
    config = CompanyIntelligenceConfig()
    try:
        bedrock_client = BedrockClient()
        print("✅ Bedrock client initialized")
    except Exception as e:
        print(f"❌ Bedrock client failed: {e}")
        bedrock_client = None
    
    scraper = IntelligentCompanyScraper(config, bedrock_client)
    
    company_data = CompanyData(
        name='FreeConvert', 
        website='https://www.freeconvert.com'
    )
    
    print("="*80)
    print("STARTING SCRAPING PROCESS")
    print("="*80)
    
    try:
        result = await scraper.scrape_company_intelligent(company_data)
        
        print("\n" + "="*80)
        print("SCRAPING RESULTS")
        print("="*80)
        print(f"Company: {result.name}")
        print(f"Website: {result.website}")
        print(f"Status: {result.scrape_status}")
        print(f"Pages crawled: {len(result.pages_crawled) if result.pages_crawled else 0}")
        print(f"Company description length: {len(result.company_description) if result.company_description else 0}")
        print(f"Raw content length: {len(result.raw_content) if result.raw_content else 0}")
        
        if result.company_description:
            print(f"\nGenerated Description ({len(result.company_description)} chars):")
            print("-" * 40)
            print(result.company_description)
            print("-" * 40)
        
        if result.pages_crawled:
            print(f"\nPages Crawled ({len(result.pages_crawled)}):")
            for i, url in enumerate(result.pages_crawled[:10], 1):
                print(f"  {i}. {url}")
            if len(result.pages_crawled) > 10:
                print(f"  ... and {len(result.pages_crawled) - 10} more")
        
        return result
        
    except Exception as e:
        print(f"\n❌ SCRAPING FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_freeconvert_detailed())
    if result:
        print(f"\n✅ Test completed successfully")
    else:
        print(f"\n❌ Test failed")