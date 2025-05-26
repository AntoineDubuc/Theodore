#!/usr/bin/env python3
"""
Full Crawl4AI extraction with all 18 configured pages
Shows the complete enhanced extraction capabilities
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from dotenv import load_dotenv

from src.models import CompanyData, CompanyIntelligenceConfig
from src.enhanced_crawl4ai_scraper import EnhancedCrawl4AICompanyScraper

# Reduce logging noise
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

async def full_crawl4ai_extraction():
    """Run full extraction with all 18 configured pages"""
    
    load_dotenv()
    
    print("🚀 FULL CRAWL4AI EXTRACTION - ALL 18 PAGES")
    print("=" * 60)
    
    # Create config and company
    config = CompanyIntelligenceConfig()
    company = CompanyData(
        name="Visterra Inc",
        website="https://visterrainc.com"
    )
    
    # Create enhanced scraper (NO override - use all 18 pages)
    scraper = EnhancedCrawl4AICompanyScraper(config)
    
    print(f"📄 Configured for {len(scraper.page_configs)} pages:")
    print("-" * 40)
    
    # Show all configured pages
    for i, page_config in enumerate(scraper.page_configs, 1):
        page_url = f"https://visterrainc.com{page_config['path']}" if page_config['path'] else "https://visterrainc.com"
        print(f"  {i:2d}. {page_config['type']:10s} | {page_config['priority']:6s} | {page_url}")
    
    print(f"\n⏱️ Starting comprehensive extraction...")
    start_time = time.time()
    
    # Run the full extraction
    result = await scraper.scrape_company_comprehensive(company)
    
    duration = time.time() - start_time
    
    print(f"\n📊 FULL EXTRACTION RESULTS:")
    print("=" * 60)
    print(f"✅ Status: {result.scrape_status}")
    print(f"📄 Pages Crawled: {len(result.pages_crawled)} out of {len(scraper.page_configs)} configured")
    print(f"⏱️ Total Duration: {duration:.1f} seconds")
    print(f"📈 Success Rate: {len(result.pages_crawled)/len(scraper.page_configs)*100:.1f}%")
    
    if result.pages_crawled:
        print(f"\n🌐 SUCCESSFULLY CRAWLED PAGES:")
        print("-" * 50)
        
        # Group by page type
        pages_by_type = {"general": [], "leadership": [], "product": [], "news": []}
        
        for url in result.pages_crawled:
            # Determine page type based on URL
            if any(x in url for x in ["/team", "/leadership", "/management", "/executives"]):
                pages_by_type["leadership"].append(url)
            elif any(x in url for x in ["/services", "/products", "/solutions", "/platform", "/partners"]):
                pages_by_type["product"].append(url)
            elif any(x in url for x in ["/news", "/press", "/blog"]):
                pages_by_type["news"].append(url)
            else:
                pages_by_type["general"].append(url)
        
        for page_type, urls in pages_by_type.items():
            if urls:
                print(f"\n  {page_type.upper()} INTELLIGENCE ({len(urls)} pages):")
                for i, url in enumerate(urls, 1):
                    print(f"    {i}. {url}")
    
    # Show pages that were configured but not crawled
    configured_urls = set()
    for page_config in scraper.page_configs:
        page_url = f"https://visterrainc.com{page_config['path']}" if page_config['path'] else "https://visterrainc.com"
        configured_urls.add(page_url)
    
    crawled_urls = set(result.pages_crawled)
    missed_urls = configured_urls - crawled_urls
    
    if missed_urls:
        print(f"\n⚠️ PAGES NOT FOUND/CRAWLED ({len(missed_urls)}):")
        print("-" * 50)
        for i, url in enumerate(sorted(missed_urls), 1):
            print(f"  {i}. {url}")
    
    print(f"\n🎯 ENHANCED INTELLIGENCE EXTRACTED:")
    print("-" * 50)
    print(f"Company: {result.name}")
    print(f"Industry: {result.industry}")
    print(f"Business Model: {result.business_model}")
    print(f"Target Market: {result.target_market}")
    print(f"Location: {result.location}")
    print(f"Leadership Team: {len(result.leadership_team) if result.leadership_team else 0} executives")
    print(f"Key Services: {len(result.key_services) if result.key_services else 0} services")
    print(f"Tech Stack: {len(result.tech_stack) if result.tech_stack else 0} technologies")
    
    # Save comprehensive results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"full_crawl4ai_results_{timestamp}.json"
    
    results_data = {
        "extraction_metadata": {
            "company": result.name,
            "website": result.website,
            "configured_pages": len(scraper.page_configs),
            "crawled_pages": len(result.pages_crawled),
            "success_rate": len(result.pages_crawled)/len(scraper.page_configs)*100,
            "duration_seconds": duration,
            "extraction_timestamp": datetime.now().isoformat()
        },
        "company_intelligence": {
            "name": result.name,
            "industry": result.industry,
            "business_model": result.business_model,
            "company_description": result.company_description,
            "target_market": result.target_market,
            "location": result.location,
            "employee_count_range": result.employee_count_range,
            "leadership_team": result.leadership_team,
            "key_services": result.key_services,
            "tech_stack": result.tech_stack,
            "contact_info": result.contact_info
        },
        "crawl_details": {
            "pages_crawled": result.pages_crawled,
            "crawl_depth": result.crawl_depth,
            "crawl_duration": result.crawl_duration,
            "scrape_status": result.scrape_status,
            "scrape_error": result.scrape_error
        }
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Full results saved to: {results_file}")
    print(f"\n" + "=" * 60)
    print("✅ Full Crawl4AI extraction completed!")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(full_crawl4ai_extraction())