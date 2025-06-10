#!/usr/bin/env python3
"""
Test the scraping system with a real company to verify it works.
"""

import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append('src')

def test_real_company():
    """Test with a real company website"""
    
    print("🔍 Testing Theodore scraping with a real company...")
    
    try:
        from src.models import CompanyIntelligenceConfig, CompanyData
        from src.intelligent_company_scraper import IntelligentCompanyScraperSync
        from src.bedrock_client import BedrockClient
        
        config = CompanyIntelligenceConfig()
        bedrock_client = BedrockClient(config)
        scraper = IntelligentCompanyScraperSync(config, bedrock_client)
        
        # Test with a real company that definitely exists - Anthropic
        test_company = CompanyData(
            name="Anthropic",
            website="https://www.anthropic.com"
        )
        
        print(f"Testing scraping for: {test_company.name}")
        print(f"Website: {test_company.website}")
        
        # Test the scraping process
        result = scraper.scrape_company(test_company)
        
        print(f"Scrape status: {result.scrape_status}")
        if result.scrape_status == "success":
            print(f"Content length: {len(result.company_description or '')}")
            print(f"Pages crawled: {len(result.pages_crawled or [])}")
            print(f"Content preview: {(result.company_description or '')[:500]}...")
        else:
            print(f"Scrape error: {result.scrape_error}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_company()