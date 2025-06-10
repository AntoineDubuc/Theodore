#!/usr/bin/env python3
"""
Test the subprocess scraper approach in isolation
"""

import asyncio
import json
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from src.intelligent_company_scraper import IntelligentCompanyScraper
from src.models import CompanyData, CompanyIntelligenceConfig
from src.bedrock_client import BedrockClient

async def run_scraping():
    try:
        print("🔧 DEBUG: Starting subprocess scraper test...")
        
        # Initialize config and clients
        print("🔧 DEBUG: Initializing config...")
        config = CompanyIntelligenceConfig()
        
        print("🔧 DEBUG: Initializing Bedrock client...")
        bedrock_client = BedrockClient(config)
        
        # Create company data - test with a simpler site first
        print("🔧 DEBUG: Creating company data...")
        company_data = CompanyData(
            name="Anthropic",
            website="https://anthropic.com"
        )
        
        # Create scraper and run
        print("🔧 DEBUG: Creating scraper...")
        scraper = IntelligentCompanyScraper(config, bedrock_client)
        
        print("🔧 DEBUG: Starting scraping...")
        result = await scraper.scrape_company_intelligent(company_data, "test_job")
        
        print(f"🔧 DEBUG: Scraping completed with status: {result.scrape_status}")
        if result.scrape_error:
            print(f"🔧 DEBUG: Scrape error: {result.scrape_error}")
        
        # Return results as JSON
        result_dict = {
            "success": True,
            "name": result.name,
            "website": result.website,
            "scrape_status": result.scrape_status,
            "scrape_error": result.scrape_error,
            "company_description": result.company_description,
            "ai_summary": result.ai_summary,
            "industry": result.industry,
            "business_model": result.business_model,
            "target_market": result.target_market,
            "key_services": result.key_services or [],
            "company_size": result.company_size,
            "location": result.location,
            "tech_stack": result.tech_stack or [],
            "value_proposition": result.value_proposition,
            "pain_points": result.pain_points or [],
            "pages_crawled": result.pages_crawled or [],
            "crawl_duration": result.crawl_duration,
            "crawl_depth": result.crawl_depth
        }
        
        print(f"🔧 DEBUG: Final result dict created")
        print(f"🔧 DEBUG: Scrape status: {result_dict['scrape_status']}")
        print(f"🔧 DEBUG: Company description length: {len(str(result_dict['company_description'] or ''))}")
        
        return result_dict
        
    except Exception as e:
        print(f"🔧 DEBUG: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "scrape_status": "failed",
            "scrape_error": str(e)
        }

if __name__ == "__main__":
    result = asyncio.run(run_scraping())
    print("🔧 DEBUG: Final result:", json.dumps(result, indent=2))