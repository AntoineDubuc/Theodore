#!/usr/bin/env python3
"""
Test the optimized Crawl4AI scraper with new caching, filtering, and dynamic model selection
"""

import asyncio
import logging
from src.models import CompanyData, CompanyIntelligenceConfig
from src.crawl4ai_scraper import Crawl4AICompanyScraper

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_optimized_scraper():
    """Test the optimized scraper with new features"""
    
    # Create config
    config = CompanyIntelligenceConfig(
        max_companies=1,
        max_content_length=10000
    )
    
    # Create test company
    test_company = CompanyData(
        name="Visterra",
        website="visterra.com",
        survey_response="Test response"
    )
    
    # Create scraper
    scraper = Crawl4AICompanyScraper(config)
    
    try:
        logger.info("Testing optimized Crawl4AI scraper with caching, filtering, and dynamic chunking...")
        
        # Test the comprehensive scraping
        result = await scraper.scrape_company_comprehensive(test_company)
        
        logger.info(f"Scraping completed!")
        logger.info(f"Status: {result.scrape_status}")
        logger.info(f"Pages crawled: {len(result.pages_crawled or [])}")
        logger.info(f"Company description: {result.company_description}")
        logger.info(f"Industry: {result.industry}")
        logger.info(f"Business model: {result.business_model}")
        logger.info(f"Target market: {result.target_market}")
        logger.info(f"Key services: {result.key_services}")
        logger.info(f"Leadership team: {result.leadership_team}")
        logger.info(f"Crawl duration: {result.crawl_duration:.2f}s")
        
        if result.scrape_status == "success":
            logger.info("✅ SUCCESS: Optimized scraper is working with new features!")
        else:
            logger.error(f"❌ FAILED: Scraping failed with error: {result.scrape_error}")
            
    except Exception as e:
        logger.error(f"❌ FAILED: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_optimized_scraper())