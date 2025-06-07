#!/usr/bin/env python3
"""
Test script for the new Intelligent Company Scraper
Tests the full LLM-driven pipeline with a real company
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.intelligent_company_scraper import IntelligentCompanyScraper
from src.models import CompanyData, CompanyIntelligenceConfig
from src.bedrock_client import BedrockClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_intelligent_scraper():
    """
    Test the intelligent scraper with a real company
    """
    print("=" * 80)
    print("🧠 TESTING INTELLIGENT COMPANY SCRAPER")
    print("=" * 80)
    
    # Initialize configuration
    config = CompanyIntelligenceConfig()
    
    # Initialize Bedrock client as fallback
    try:
        bedrock_client = BedrockClient(config)
        print("✅ Bedrock client initialized")
    except Exception as e:
        print(f"⚠️  Bedrock client failed: {e}")
        bedrock_client = None
    
    # Initialize intelligent scraper
    scraper = IntelligentCompanyScraper(config, bedrock_client)
    
    # Test companies (choose companies with rich content)
    test_companies = [
        {
            "name": "Stripe",
            "website": "https://stripe.com",
            "description": "Financial technology company - should have rich sales intelligence"
        },
        {
            "name": "Notion",
            "website": "https://notion.so", 
            "description": "Productivity software - good for testing B2B sales content"
        },
        {
            "name": "Visterra Inc",
            "website": "https://visterra.com",
            "description": "Small company from your original test - good for comparison"
        }
    ]
    
    print(f"\n🎯 Testing with {len(test_companies)} companies...")
    
    for i, company_info in enumerate(test_companies, 1):
        print(f"\n{'='*60}")
        print(f"🏢 TEST {i}/{len(test_companies)}: {company_info['name']}")
        print(f"🌐 Website: {company_info['website']}")
        print(f"📝 Description: {company_info['description']}")
        print(f"{'='*60}")
        
        # Create company data object
        company_data = CompanyData(
            name=company_info['name'],
            website=company_info['website']
        )
        
        try:
            print(f"\n🚀 Starting intelligent scraping for {company_info['name']}...")
            
            # Run the intelligent scraper
            result = await scraper.scrape_company_intelligent(company_data)
            
            # Display results
            print(f"\n📊 RESULTS FOR {company_info['name']}:")
            print(f"Status: {result.scrape_status}")
            
            if result.scrape_status == "success":
                print(f"✅ Success! Processed {result.crawl_depth} pages in {result.crawl_duration:.2f}s")
                
                print(f"\n📄 SALES INTELLIGENCE SUMMARY:")
                print("-" * 50)
                print(result.company_description)
                print("-" * 50)
                
                print(f"\n🔗 PAGES CRAWLED ({len(result.pages_crawled)}):")
                for url in result.pages_crawled[:10]:  # Show first 10
                    print(f"  • {url}")
                if len(result.pages_crawled) > 10:
                    print(f"  ... and {len(result.pages_crawled) - 10} more pages")
                    
            else:
                print(f"❌ Failed: {result.scrape_error}")
                
        except Exception as e:
            print(f"💥 Error testing {company_info['name']}: {e}")
            logger.exception(f"Detailed error for {company_info['name']}")
        
        # Add delay between companies to avoid rate limiting
        if i < len(test_companies):
            print(f"\n⏳ Waiting 10 seconds before next company...")
            await asyncio.sleep(10)
    
    print(f"\n{'='*80}")
    print("🎉 INTELLIGENT SCRAPER TESTING COMPLETED")
    print("='*80")


async def test_single_phase():
    """
    Test individual phases of the scraper for debugging
    """
    print("=" * 80)
    print("🔧 TESTING INDIVIDUAL PHASES")
    print("=" * 80)
    
    config = CompanyIntelligenceConfig()
    
    try:
        bedrock_client = BedrockClient(config)
    except Exception as e:
        print(f"⚠️  Bedrock client failed: {e}")
        bedrock_client = None
    
    scraper = IntelligentCompanyScraper(config, bedrock_client)
    
    # Test with a simple company
    test_url = "https://visterra.com"
    company_name = "Visterra Inc"
    
    print(f"\n🔍 Phase 1: Testing link discovery for {test_url}")
    try:
        links = await scraper._discover_all_links(test_url)
        print(f"✅ Discovered {len(links)} links")
        print("Sample links:")
        for link in links[:10]:
            print(f"  • {link}")
    except Exception as e:
        print(f"❌ Link discovery failed: {e}")
        return
    
    print(f"\n🧠 Phase 2: Testing LLM page selection")
    try:
        selected = await scraper._llm_select_promising_pages(links, company_name, test_url)
        print(f"✅ LLM selected {len(selected)} promising pages")
        print("Selected pages:")
        for page in selected[:10]:
            print(f"  • {page}")
    except Exception as e:
        print(f"❌ Page selection failed: {e}")
        return
    
    print(f"\n📥 Phase 3: Testing parallel content extraction (first 5 pages)")
    try:
        content = await scraper._parallel_extract_content(selected[:5])
        print(f"✅ Extracted content from {len(content)} pages")
        for page_content in content:
            print(f"  • {page_content['url']}: {len(page_content['content'])} chars")
    except Exception as e:
        print(f"❌ Content extraction failed: {e}")
        return
    
    print(f"\n🤖 Phase 4: Testing LLM aggregation")
    try:
        intelligence = await scraper._llm_aggregate_sales_intelligence(content, company_name)
        print(f"✅ Generated sales intelligence:")
        print("-" * 50)
        print(intelligence)
        print("-" * 50)
    except Exception as e:
        print(f"❌ LLM aggregation failed: {e}")


def main():
    """
    Main test function
    """
    print("🧪 INTELLIGENT COMPANY SCRAPER TESTS")
    print("Choose test mode:")
    print("1. Full end-to-end test (recommended)")
    print("2. Individual phase testing (for debugging)")
    print("3. Quick single company test")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        asyncio.run(test_intelligent_scraper())
    elif choice == "2":
        asyncio.run(test_single_phase())
    elif choice == "3":
        async def quick_test():
            config = CompanyIntelligenceConfig()
            try:
                bedrock_client = BedrockClient(config)
            except:
                bedrock_client = None
            
            scraper = IntelligentCompanyScraper(config, bedrock_client)
            
            company_data = CompanyData(
                name="Visterra Inc",
                website="https://visterra.com"
            )
            
            result = await scraper.scrape_company_intelligent(company_data)
            
            print(f"\n📊 QUICK TEST RESULT:")
            print(f"Status: {result.scrape_status}")
            if result.scrape_status == "success":
                print(f"Sales Intelligence:\n{result.company_description}")
            else:
                print(f"Error: {result.scrape_error}")
        
        asyncio.run(quick_test())
    else:
        print("Invalid choice. Exiting.")


if __name__ == "__main__":
    main()