#!/usr/bin/env python3
"""
Output raw Crawl4AI extraction data to file for analysis
Shows exactly what our enhanced scraper extracts
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

async def extract_and_output_raw_data():
    """Extract raw data and output to files"""
    
    load_dotenv()
    
    print("🚀 EXTRACTING RAW CRAWL4AI DATA")
    print("=" * 50)
    
    # Create config and company
    config = CompanyIntelligenceConfig()
    company = CompanyData(
        name="Visterra Inc",
        website="https://visterrainc.com"
    )
    
    # Create enhanced scraper with focused pages
    scraper = EnhancedCrawl4AICompanyScraper(config)
    
    # Focus on key pages for demo
    scraper.page_configs = [
        {"path": "", "type": "general", "priority": "high"},
        {"path": "/about-us", "type": "general", "priority": "high"},
        {"path": "/leadership", "type": "leadership", "priority": "high"},
        {"path": "/services", "type": "product", "priority": "high"},
        {"path": "/contact", "type": "general", "priority": "high"}
    ]
    
    print(f"Extracting from {len(scraper.page_configs)} key pages...")
    
    # Extract comprehensive intelligence with detailed tracking
    extractions_by_type = {
        "general": [],
        "leadership": [],
        "product": [],
        "news": []
    }
    
    start_time = time.time()
    
    try:
        from crawl4ai import AsyncWebCrawler
        
        async with AsyncWebCrawler(headless=True, verbose=False) as crawler:
            
            for i, page_config in enumerate(scraper.page_configs, 1):
                page_url = f"https://visterrainc.com{page_config['path']}"
                page_type = page_config['type']
                
                print(f"  {i}. Extracting {page_type} data from {page_url}")
                
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
                            extractions_by_type[page_type].append({
                                'page_url': page_url,
                                'page_path': page_config["path"],
                                'page_type': page_type,
                                'content_length': len(result.markdown),
                                'extraction_timestamp': datetime.now().isoformat(),
                                'intelligence': intelligence_data
                            })
                            print(f"     ✅ Extracted {len(str(intelligence_data))} chars of intelligence")
                        else:
                            print(f"     ⚠️ No intelligence extracted")
                    else:
                        print(f"     ❌ Failed to crawl page")
                
                except Exception as e:
                    print(f"     ❌ Error: {e}")
                
                # Rate limiting
                await asyncio.sleep(1)
        
        duration = time.time() - start_time
        print(f"\n⏱️ Extraction completed in {duration:.1f} seconds")
        
        # Output raw data to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"crawl4ai_raw_data_{timestamp}.json"
        
        output_data = {
            "extraction_metadata": {
                "company": company.name,
                "website": company.website,
                "extraction_timestamp": datetime.now().isoformat(),
                "duration_seconds": duration,
                "pages_processed": len([item for sublist in extractions_by_type.values() for item in sublist])
            },
            "raw_extractions": extractions_by_type
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Raw data saved to: {output_file}")
        
        # Also create a human-readable summary
        summary_file = f"crawl4ai_summary_{timestamp}.txt"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("CRAWL4AI EXTRACTION SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Company: {company.name}\n")
            f.write(f"Website: {company.website}\n")
            f.write(f"Extraction Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {duration:.1f} seconds\n\n")
            
            total_extractions = 0
            for page_type, extractions in extractions_by_type.items():
                if extractions:
                    f.write(f"{page_type.upper()} INTELLIGENCE EXTRACTIONS:\n")
                    f.write("-" * 40 + "\n")
                    
                    for extraction in extractions:
                        total_extractions += 1
                        f.write(f"\nPage: {extraction['page_url']}\n")
                        f.write(f"Content Length: {extraction['content_length']:,} chars\n")
                        f.write(f"Intelligence Data:\n")
                        
                        # Pretty print the intelligence data
                        intelligence = extraction['intelligence']
                        if isinstance(intelligence, dict):
                            for key, value in intelligence.items():
                                if key != '_extraction_metadata':
                                    f.write(f"  {key}: {json.dumps(value, indent=4)}\n")
                        else:
                            f.write(f"  {intelligence}\n")
                        
                        f.write("\n" + "="*60 + "\n")
                    
                    f.write("\n\n")
            
            f.write(f"TOTAL EXTRACTIONS: {total_extractions}\n")
        
        print(f"📄 Human-readable summary saved to: {summary_file}")
        
        # Show quick summary
        print(f"\n📊 EXTRACTION SUMMARY:")
        print("-" * 30)
        for page_type, extractions in extractions_by_type.items():
            if extractions:
                print(f"  {page_type.title()}: {len(extractions)} pages extracted")
        
        total_extractions = sum(len(extractions) for extractions in extractions_by_type.values())
        print(f"  Total: {total_extractions} successful extractions")
        
        return output_file, summary_file
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return None, None

if __name__ == "__main__":
    output_file, summary_file = asyncio.run(extract_and_output_raw_data())
    
    if output_file:
        print(f"\n✅ Raw Crawl4AI data available in:")
        print(f"   📄 {output_file} (JSON format)")
        print(f"   📄 {summary_file} (Human-readable)")
    else:
        print(f"\n❌ Extraction failed")