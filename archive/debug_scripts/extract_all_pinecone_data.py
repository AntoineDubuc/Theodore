#!/usr/bin/env python3
"""
Extract ALL data that will be stored in Pinecone
Comprehensive extraction showing complete dataset for storage
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from dotenv import load_dotenv

from src.models import CompanyData, CompanyIntelligenceConfig
from src.enhanced_crawl4ai_scraper import EnhancedCrawl4AICompanyScraper
from src.pinecone_client import PineconeClient

# Reduce logging noise but show progress
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def discover_all_pages(base_url: str, crawler):
    """Discover additional pages by crawling sitemap and common paths"""
    
    discovered_pages = []
    
    # Common page patterns to try
    additional_paths = [
        "/sitemap.xml", "/sitemap", "/robots.txt",
        "/company", "/mission", "/vision", "/values",
        "/technology", "/platform", "/research",
        "/clinical-trials", "/pipeline", "/programs",
        "/investors", "/investor-relations", "/financials",
        "/press-releases", "/media", "/resources",
        "/publications", "/white-papers", "/case-studies",
        "/partners", "/partnerships", "/alliances",
        "/careers", "/jobs", "/opportunities",
        "/support", "/help", "/faq",
        "/legal", "/privacy", "/terms",
        "/our-approach", "/our-research", "/our-vision"
    ]
    
    logger.info(f"🔍 Discovering additional pages beyond the 18 configured...")
    
    for path in additional_paths:
        try:
            page_url = f"{base_url}{path}"
            result = await crawler.arun(url=page_url, timeout=10)
            
            if result.success and result.markdown and len(result.markdown) > 100:
                # Determine page type based on content
                content_lower = result.markdown.lower()
                if any(word in content_lower for word in ['ceo', 'president', 'director', 'officer', 'team', 'leadership', 'management']):
                    page_type = "leadership"
                elif any(word in content_lower for word in ['product', 'service', 'solution', 'platform', 'offering']):
                    page_type = "product"
                elif any(word in content_lower for word in ['news', 'press', 'announcement', 'release']):
                    page_type = "news"
                else:
                    page_type = "general"
                
                discovered_pages.append({
                    "path": path,
                    "type": page_type,
                    "priority": "discovered",
                    "url": page_url,
                    "content_length": len(result.markdown)
                })
                
                logger.info(f"  ✅ Found: {page_url} ({page_type}, {len(result.markdown)} chars)")
            
        except Exception as e:
            # Silently skip failed discoveries
            pass
        
        # Small delay between discovery attempts
        await asyncio.sleep(0.5)
    
    logger.info(f"🔍 Discovered {len(discovered_pages)} additional pages")
    return discovered_pages

async def extract_complete_pinecone_dataset():
    """Extract complete dataset that will be stored in Pinecone"""
    
    load_dotenv()
    
    print("🚀 EXTRACTING COMPLETE PINECONE DATASET")
    print("=" * 70)
    
    # Create config and company
    config = CompanyIntelligenceConfig()
    company = CompanyData(
        name="Visterra Inc",
        website="https://visterrainc.com"
    )
    
    # Create enhanced scraper
    scraper = EnhancedCrawl4AICompanyScraper(config)
    base_url = "https://visterrainc.com"
    
    print(f"🏢 Company: {company.name}")
    print(f"🌐 Website: {company.website}")
    print(f"📄 Configured Pages: {len(scraper.page_configs)}")
    
    start_time = time.time()
    
    # First, discover additional pages
    try:
        from crawl4ai import AsyncWebCrawler
        
        async with AsyncWebCrawler(headless=True, verbose=False) as crawler:
            
            # Discover additional pages
            discovered_pages = await discover_all_pages(base_url, crawler)
            
            # Combine configured pages with discovered pages
            all_page_configs = scraper.page_configs.copy()
            for discovered in discovered_pages:
                all_page_configs.append(discovered)
            
            print(f"📄 Total Pages to Process: {len(all_page_configs)} ({len(scraper.page_configs)} configured + {len(discovered_pages)} discovered)")
            
            # Track extractions
            all_extractions = []
            successful_crawls = 0
            failed_crawls = 0
            
            print(f"\n⏱️ Starting comprehensive extraction...")
            
            for i, page_config in enumerate(all_page_configs, 1):
                page_url = page_config.get('url', f"{base_url}{page_config['path']}")
                page_type = page_config['type']
                priority = page_config['priority']
                
                print(f"  {i:2d}/{len(all_page_configs)} | {page_type:10s} | {priority:10s} | {page_url}")
                
                try:
                    # Crawl the page
                    result = await crawler.arun(url=page_url, timeout=30)
                    
                    if result.success and result.markdown:
                        # Extract intelligence with specialized prompt
                        intelligence_data = await scraper.extract_with_specialized_prompt(
                            result.markdown, 
                            page_url, 
                            page_type
                        )
                        
                        if intelligence_data:
                            extraction_record = {
                                'page_number': i,
                                'page_url': page_url,
                                'page_path': page_config.get('path', ''),
                                'page_type': page_type,
                                'priority': priority,
                                'content_length': len(result.markdown),
                                'html_length': len(result.html) if result.html else 0,
                                'extraction_timestamp': datetime.now().isoformat(),
                                'intelligence': intelligence_data,
                                'raw_content_sample': result.markdown[:500] + "..." if len(result.markdown) > 500 else result.markdown
                            }
                            
                            all_extractions.append(extraction_record)
                            successful_crawls += 1
                            print(f"       ✅ Extracted {len(str(intelligence_data))} chars")
                        else:
                            failed_crawls += 1
                            print(f"       ⚠️ No intelligence extracted")
                    else:
                        failed_crawls += 1
                        print(f"       ❌ Failed to crawl")
                
                except Exception as e:
                    failed_crawls += 1
                    print(f"       ❌ Error: {str(e)[:50]}")
                
                # Rate limiting
                if i % 5 == 0:  # Longer pause every 5 pages
                    await asyncio.sleep(3)
                else:
                    await asyncio.sleep(1)
        
        duration = time.time() - start_time
        
        print(f"\n📊 EXTRACTION COMPLETED:")
        print("=" * 70)
        print(f"⏱️ Duration: {duration:.1f} seconds")
        print(f"✅ Successful: {successful_crawls}")
        print(f"❌ Failed: {failed_crawls}")
        print(f"📊 Success Rate: {successful_crawls/(successful_crawls+failed_crawls)*100:.1f}%")
        
        # Now process the data through the enhanced scraper to get final company data
        print(f"\n🔄 Processing through enhanced scraper...")
        
        # Simulate the full processing by creating a mock extraction structure
        extractions_by_type = {
            "general": [],
            "leadership": [],
            "product": [],
            "news": []
        }
        
        for extraction in all_extractions:
            page_type = extraction['page_type']
            if page_type in extractions_by_type:
                extractions_by_type[page_type].append(extraction)
        
        # Merge intelligence
        comprehensive_intelligence = scraper._merge_specialized_intelligence(extractions_by_type)
        
        # Apply to company data
        scraper._apply_comprehensive_intelligence(company, comprehensive_intelligence)
        
        # Update metadata
        company.pages_crawled = [ext['page_url'] for ext in all_extractions]
        company.crawl_depth = len(all_extractions)
        company.crawl_duration = duration
        company.scrape_status = "success"
        
        # Now show what goes into Pinecone
        print(f"\n📦 PINECONE STORAGE DATA:")
        print("=" * 70)
        
        # Create Pinecone client to show storage format
        pinecone_client = PineconeClient(config)
        
        # Prepare metadata (what actually goes into Pinecone)
        pinecone_metadata = pinecone_client._prepare_pinecone_metadata(company)
        
        print(f"🏷️ PINECONE METADATA (stored with vector):")
        print("-" * 50)
        for key, value in pinecone_metadata.items():
            print(f"  {key}: {value}")
        
        # Prepare complete metadata (stored separately)
        complete_metadata = pinecone_client._prepare_complete_metadata(company)
        
        print(f"\n📋 COMPLETE METADATA (stored separately):")
        print("-" * 50)
        for key, value in complete_metadata.items():
            if isinstance(value, list):
                print(f"  {key}: {len(value)} items")
                if value:
                    for i, item in enumerate(value[:3], 1):  # Show first 3 items
                        print(f"    {i}. {item}")
                    if len(value) > 3:
                        print(f"    ... and {len(value)-3} more")
            elif isinstance(value, dict):
                print(f"  {key}: {len(value)} fields")
                for subkey, subvalue in list(value.items())[:3]:  # Show first 3 fields
                    print(f"    {subkey}: {subvalue}")
                if len(value) > 3:
                    print(f"    ... and {len(value)-3} more fields")
            else:
                print(f"  {key}: {value}")
        
        # Save comprehensive dataset
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dataset_file = f"complete_pinecone_dataset_{timestamp}.json"
        
        complete_dataset = {
            "extraction_metadata": {
                "company": company.name,
                "website": company.website,
                "total_pages_attempted": len(all_page_configs),
                "successful_extractions": successful_crawls,
                "failed_extractions": failed_crawls,
                "success_rate": successful_crawls/(successful_crawls+failed_crawls)*100,
                "duration_seconds": duration,
                "extraction_timestamp": datetime.now().isoformat()
            },
            "pinecone_storage_data": {
                "vector_metadata": pinecone_metadata,
                "complete_metadata": complete_metadata,
                "company_description_for_embedding": company.company_description or "Biotechnology company"
            },
            "raw_extractions": all_extractions,
            "processed_company_data": {
                "name": company.name,
                "website": company.website,
                "industry": company.industry,
                "business_model": company.business_model,
                "company_description": company.company_description,
                "target_market": company.target_market,
                "location": company.location,
                "employee_count_range": company.employee_count_range,
                "leadership_team": company.leadership_team,
                "key_services": company.key_services,
                "tech_stack": company.tech_stack,
                "contact_info": company.contact_info,
                "pages_crawled": company.pages_crawled,
                "crawl_duration": company.crawl_duration,
                "scrape_status": company.scrape_status
            }
        }
        
        with open(dataset_file, 'w', encoding='utf-8') as f:
            json.dump(complete_dataset, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Complete dataset saved to: {dataset_file}")
        
        # Summary statistics
        print(f"\n📊 FINAL DATASET SUMMARY:")
        print("-" * 50)
        print(f"  Company: {company.name}")
        print(f"  Industry: {company.industry}")
        print(f"  Leadership Team: {len(company.leadership_team) if company.leadership_team else 0} executives")
        print(f"  Key Services: {len(company.key_services) if company.key_services else 0} services")
        print(f"  Tech Stack: {len(company.tech_stack) if company.tech_stack else 0} technologies")
        print(f"  Pages Processed: {len(company.pages_crawled)} pages")
        print(f"  Total Content: {sum(ext['content_length'] for ext in all_extractions):,} characters")
        
        return dataset_file
        
    except Exception as e:
        logger.error(f"❌ Extraction failed: {e}")
        return None

if __name__ == "__main__":
    dataset_file = asyncio.run(extract_complete_pinecone_dataset())
    
    if dataset_file:
        print(f"\n✅ COMPLETE PINECONE DATASET EXTRACTED!")
        print(f"📄 All data available in: {dataset_file}")
        print(f"\nThis file contains:")
        print(f"  • Raw extractions from all discovered pages")
        print(f"  • Processed company intelligence")
        print(f"  • Exact Pinecone storage format")
        print(f"  • Complete metadata structure")
    else:
        print(f"\n❌ Extraction failed")