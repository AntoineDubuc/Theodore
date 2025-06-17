#!/usr/bin/env python3
"""
Debug crawling data for all companies to see what pages were actually crawled.
"""

import os
import sys
from typing import Dict, Any

sys.path.append('.')
from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Load environment
load_dotenv()

def debug_all_companies_crawling():
    """Debug what pages were crawled for all companies"""
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    # Get all companies
    companies = pipeline.pinecone_client.find_companies_by_filters({}, top_k=15)
    
    print("=" * 80)
    print("ALL COMPANIES CRAWLING DEBUG")
    print("=" * 80)
    
    for i, company in enumerate(companies, 1):
        metadata = company.get('metadata', {})
        company_name = metadata.get('company_name', f'Company_{i}')
        website = metadata.get('website', 'No website')
        
        pages_crawled = metadata.get('pages_crawled', [])
        crawl_depth = metadata.get('crawl_depth', 0)
        scrape_status = metadata.get('scrape_status', 'unknown')
        scrape_error = metadata.get('scrape_error', '')
        
        print(f"\n{i}. {company_name}")
        print(f"   Website: {website}")
        print(f"   Scrape Status: {scrape_status}")
        
        if scrape_error:
            print(f"   ❌ Error: {scrape_error}")
        
        if pages_crawled:
            print(f"   ✅ Pages Crawled ({len(pages_crawled)}):")
            for j, page in enumerate(pages_crawled[:5], 1):  # Show first 5
                print(f"     {j}. {page}")
            if len(pages_crawled) > 5:
                print(f"     ... and {len(pages_crawled) - 5} more")
                
            # Check for leadership-related pages
            leadership_pages = [url for url in pages_crawled if any(keyword in url.lower() for keyword in ['leadership', 'team', 'about', 'management', 'executives'])]
            if leadership_pages:
                print(f"   🎯 Leadership-related pages:")
                for page in leadership_pages:
                    print(f"     - {page}")
            else:
                print(f"   ❌ No leadership-related pages found")
        else:
            print(f"   ❌ No pages crawled (crawl_depth: {crawl_depth})")
        
        # Check if we have any leadership data despite missing pages_crawled
        leadership_team = metadata.get('leadership_team', '')
        if leadership_team and leadership_team.strip():
            print(f"   🎯 Leadership data found: {leadership_team[:100]}...")
    
    print(f"\n" + "=" * 80)
    print("SUMMARY:")
    
    companies_with_pages = sum(1 for company in companies if company.get('metadata', {}).get('pages_crawled'))
    companies_with_leadership = sum(1 for company in companies if company.get('metadata', {}).get('leadership_team'))
    
    print(f"• Total companies: {len(companies)}")
    print(f"• Companies with crawled pages data: {companies_with_pages}")
    print(f"• Companies with leadership data: {companies_with_leadership}")
    
    if companies_with_pages == 0:
        print(f"\n🔴 CRITICAL ISSUE: No companies have pages_crawled data!")
        print(f"This suggests either:")
        print(f"  1. The scraping system isn't storing crawled page URLs")
        print(f"  2. The data model isn't preserving pages_crawled field")
        print(f"  3. Companies were processed with a different system")
        
    print("=" * 80)

if __name__ == "__main__":
    debug_all_companies_crawling()