#!/usr/bin/env python3
"""
Test direct scraping to debug extraction issues
"""

import asyncio
import logging
from src.models import CompanyData, CompanyIntelligenceConfig
from src.intelligent_company_scraper import IntelligentCompanyScraper
from src.bedrock_client import BedrockClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_direct_scraping():
    """Test the scraper directly"""
    
    test_companies = [
        {"name": "Stripe", "website": "https://stripe.com"},
        {"name": "Datadog", "website": "https://www.datadoghq.com"},
        {"name": "GitLab", "website": "https://about.gitlab.com"}
    ]
    
    config = CompanyIntelligenceConfig()
    bedrock_client = BedrockClient(config)
    scraper = IntelligentCompanyScraper(config, bedrock_client)
    
    for company_info in test_companies:
        print(f"\n{'='*70}")
        print(f"Testing: {company_info['name']} - {company_info['website']}")
        print(f"{'='*70}")
        
        company = CompanyData(
            name=company_info['name'],
            website=company_info['website']
        )
        
        try:
            # Test scraping
            result = await scraper.scrape_company_intelligent(company)
            
            print(f"\n📊 Scraping Results:")
            print(f"   Status: {result.scrape_status}")
            if result.scrape_status == "success":
                print(f"   Raw content length: {len(result.raw_content) if result.raw_content else 0} chars")
                print(f"   Pages crawled: {len(result.pages_crawled)}")
                print(f"   Industry: {result.industry}")
                print(f"   Company size: {result.company_size}")
                print(f"   Location: {result.location}")
                print(f"   Founded year: {result.founding_year}")
                print(f"   Employee count: {result.employee_count_range}")
                
                if result.raw_content and len(result.raw_content) > 100:
                    print(f"\n   Content preview:")
                    print(f"   {result.raw_content[:200]}...")
                    
                    # Test pattern extraction
                    from src.extraction_improvements import EnhancedFieldExtractor
                    extractor = EnhancedFieldExtractor()
                    
                    print(f"\n   Pattern extraction test:")
                    founding_year = extractor.extract_founding_year(result.raw_content)
                    location = extractor.extract_location(result.raw_content)
                    employee_count = extractor.extract_employee_count(result.raw_content)
                    
                    if founding_year:
                        print(f"   ✓ Found founding year: {founding_year}")
                    if location:
                        print(f"   ✓ Found location: {location}")
                    if employee_count:
                        print(f"   ✓ Found employee count: {employee_count}")
            else:
                print(f"   Error: {result.scrape_error}")
                
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_scraping())