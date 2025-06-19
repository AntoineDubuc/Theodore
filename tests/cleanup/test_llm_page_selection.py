#!/usr/bin/env python3
"""
Test LLM page selection specifically for FreeConvert about page
"""

import asyncio
import sys
import os
sys.path.append('src')

from intelligent_company_scraper import IntelligentCompanyScraper
from models import CompanyData, CompanyIntelligenceConfig

async def test_llm_page_selection():
    print("🧠 TESTING LLM Page Selection for FreeConvert...")
    
    config = CompanyIntelligenceConfig()
    scraper = IntelligentCompanyScraper(config)
    
    # Create mock link list that includes the about page
    test_links = [
        "https://www.freeconvert.com",
        "https://www.freeconvert.com/",
        "https://www.freeconvert.com/about",  # This should be selected!
        "https://www.freeconvert.com/pricing", 
        "https://www.freeconvert.com/mp4-to-mp3",
        "https://www.freeconvert.com/pdf-converter",
        "https://www.freeconvert.com/contact",  # If it exists
        "https://www.freeconvert.com/terms",
        "https://www.freeconvert.com/privacy",
    ]
    
    print(f"📋 Testing with {len(test_links)} sample links:")
    for i, link in enumerate(test_links, 1):
        print(f"  {i}. {link}")
    
    print("\n🤖 Testing LLM Page Selection...")
    
    try:
        selected_urls = await scraper._llm_select_promising_pages(
            test_links, "FreeConvert", "https://www.freeconvert.com"
        )
        
        print(f"\n✅ LLM Selection Result: {len(selected_urls)} pages selected")
        for i, url in enumerate(selected_urls, 1):
            print(f"  {i}. {url}")
        
        # Check if about page was selected
        about_selected = any("/about" in url for url in selected_urls)
        print(f"\n🎯 About page selected: {'✅ YES' if about_selected else '❌ NO'}")
        
        return selected_urls
        
    except Exception as e:
        print(f"\n❌ LLM Selection FAILED: {e}")
        import traceback
        traceback.print_exc()
        
        print(f"\n🔄 Testing Heuristic Selection...")
        heuristic_urls = scraper._heuristic_page_selection(test_links)
        
        print(f"\n📊 Heuristic Selection Result: {len(heuristic_urls)} pages selected")
        for i, url in enumerate(heuristic_urls, 1):
            print(f"  {i}. {url}")
            
        # Check if about page was selected
        about_selected = any("/about" in url for url in heuristic_urls)
        print(f"\n🎯 About page selected: {'✅ YES' if about_selected else '❌ NO'}")
        
        return heuristic_urls

if __name__ == "__main__":
    result = asyncio.run(test_llm_page_selection())