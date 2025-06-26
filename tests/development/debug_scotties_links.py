#!/usr/bin/env python3
"""
Debug what links were discovered for Scotties to understand why no pages were selected
"""

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def debug_scotties_links():
    """Debug link discovery for Scotties"""
    
    url = "https://trivalleyathletics.org"
    
    print(f"🔍 Debugging link discovery for: {url}")
    print("=" * 60)
    
    async with AsyncWebCrawler(
        headless=True,
        browser_type="chromium",
        verbose=True
    ) as crawler:
        
        config = CrawlerRunConfig(
            word_count_threshold=10,
            verbose=True
        )
        
        result = await crawler.arun(url=url, config=config)
        
        if result.success:
            print(f"✅ Successfully crawled: {url}")
            print(f"Content length: {len(result.cleaned_html):,} chars")
            
            # Extract links from the page
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(result.cleaned_html, 'html.parser')
            
            # Find all links
            links = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if href:
                    links.append(href)
            
            print(f"\n📄 Found {len(links)} total links:")
            
            # Categorize links
            internal_links = []
            external_links = []
            relative_links = []
            
            for link in links:
                if link.startswith('http'):
                    if 'trivalleyathletics.org' in link:
                        internal_links.append(link)
                    else:
                        external_links.append(link)
                else:
                    relative_links.append(link)
            
            print(f"   Internal (full URL): {len(internal_links)}")
            print(f"   External: {len(external_links)}")
            print(f"   Relative: {len(relative_links)}")
            
            # Show the actual links that would be used for heuristic selection
            all_useful_links = internal_links + [f"{url.rstrip('/')}/{link.lstrip('/')}" for link in relative_links if link not in ['#', '/']]
            
            print(f"\n🎯 Links that would be analyzed ({len(all_useful_links)}):")
            for i, link in enumerate(all_useful_links[:20], 1):
                print(f"   {i:2d}. {link}")
                
            if len(all_useful_links) > 20:
                print(f"   ... and {len(all_useful_links) - 20} more")
            
            # Test heuristic selection on these links
            print(f"\n🔍 Testing heuristic selection patterns:")
            priority_patterns = [
                ('contact', 10), ('about', 9), ('team', 8), ('careers', 7),
                ('leadership', 7), ('company', 6), ('services', 5), ('products', 5),
                ('history', 4), ('our-story', 4), ('management', 6)
            ]
            
            scored_urls = []
            for link in all_useful_links:
                score = 0
                link_lower = link.lower()
                for pattern, weight in priority_patterns:
                    if pattern in link_lower:
                        score += weight
                        print(f"   ✅ {link} matches '{pattern}' (score: {weight})")
                        
                if score > 0:
                    scored_urls.append((link, score))
            
            if scored_urls:
                scored_urls.sort(key=lambda x: x[1], reverse=True)
                print(f"\n📊 Heuristic selection results ({len(scored_urls)} pages):")
                for url, score in scored_urls[:10]:
                    print(f"   {score:2d}: {url}")
            else:
                print(f"\n❌ NO PAGES MATCHED HEURISTIC PATTERNS!")
                print(f"This explains why Scotties had 0 pages to scrape.")
                
                # Suggest what pages could be useful anyway
                print(f"\n💡 Pages that might still be useful:")
                for link in all_useful_links[:5]:
                    print(f"   • {link}")
                    
        else:
            print(f"❌ Failed to crawl: {url}")
            print(f"Error: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(debug_scotties_links())