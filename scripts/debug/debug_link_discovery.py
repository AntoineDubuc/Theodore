#!/usr/bin/env python3
"""
Debug link discovery to see if about page was found
"""

import asyncio
import sys
import os
sys.path.append('src')

from intelligent_company_scraper import IntelligentCompanyScraper
from models import CompanyData, CompanyIntelligenceConfig

async def debug_link_discovery():
    print("🔍 DEBUGGING Link Discovery for FreeConvert...")
    
    config = CompanyIntelligenceConfig()
    scraper = IntelligentCompanyScraper(config)
    
    print("="*60)
    print("PHASE 1: Link Discovery")
    print("="*60)
    
    try:
        # Test link discovery
        discovered_links = await scraper._discover_all_links("https://www.freeconvert.com")
        
        print(f"\n📊 DISCOVERY RESULTS:")
        print(f"Total links discovered: {len(discovered_links)}")
        
        # Check for key pages
        key_pages = ["/about", "/contact", "/team", "/careers", "/company"]
        found_pages = []
        
        for page in key_pages:
            matching_links = [link for link in discovered_links if page in link.lower()]
            if matching_links:
                found_pages.extend(matching_links)
                print(f"\n✅ Found {page} pages:")
                for link in matching_links[:3]:  # Show first 3
                    print(f"  - {link}")
                if len(matching_links) > 3:
                    print(f"  ... and {len(matching_links) - 3} more")
            else:
                print(f"\n❌ No {page} pages found")
        
        # Show sample of all discovered links
        print(f"\n📋 SAMPLE OF ALL DISCOVERED LINKS (first 20):")
        for i, link in enumerate(discovered_links[:20], 1):
            print(f"  {i:2d}. {link}")
        
        if len(discovered_links) > 20:
            print(f"  ... and {len(discovered_links) - 20} more")
            
        # Check if about page specifically exists
        about_links = [link for link in discovered_links if "/about" in link.lower()]
        print(f"\n🎯 ABOUT PAGE CHECK:")
        if about_links:
            print(f"✅ Found {len(about_links)} about-related links:")
            for link in about_links:
                print(f"  - {link}")
        else:
            print("❌ No about page found in discovered links!")
            
            # Manual check if about page exists but wasn't discovered
            print("\n🔍 Manual verification:")
            import aiohttp
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://www.freeconvert.com/about") as response:
                        if response.status == 200:
                            print("✅ https://www.freeconvert.com/about EXISTS but was NOT discovered!")
                            print("❌ This indicates a problem with our link discovery process")
                        else:
                            print(f"❌ https://www.freeconvert.com/about returns status {response.status}")
            except Exception as e:
                print(f"❌ Error checking about page: {e}")
        
        return discovered_links
        
    except Exception as e:
        print(f"\n❌ LINK DISCOVERY FAILED: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    result = asyncio.run(debug_link_discovery())