#!/usr/bin/env python3
"""
Debug why Connatix returns "No content could be extracted"
"""

import requests
from urllib.robotparser import RobotFileParser

def test_connatix_accessibility():
    """Test if we can access Connatix website"""
    
    url = "https://www.connatix.com"
    
    print(f"🔍 Testing accessibility of {url}")
    print("=" * 70)
    
    # Test 1: Check robots.txt
    print("\n1. Checking robots.txt...")
    try:
        robots_url = f"{url}/robots.txt"
        response = requests.get(robots_url, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Content preview:")
            print(response.text[:500])
            
            # Check if crawling is allowed
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            can_fetch = rp.can_fetch("*", url)
            print(f"\n   Can fetch homepage: {can_fetch}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Check homepage
    print("\n2. Checking homepage...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        print(f"   Content length: {len(response.text)} chars")
        
        if response.status_code == 200:
            # Check for JavaScript-heavy content
            if 'text/html' in response.headers.get('Content-Type', ''):
                # Look for signs of JavaScript rendering
                if '<noscript>' in response.text or 'window.NUXT' in response.text:
                    print("   ⚠️  Page appears to be JavaScript-rendered")
                else:
                    print("   ✅ Page appears to have static content")
                    
                # Check for meta tags
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for basic info
                title = soup.find('title')
                if title:
                    print(f"   Title: {title.text.strip()}")
                
                meta_desc = soup.find('meta', {'name': 'description'})
                if meta_desc:
                    print(f"   Description: {meta_desc.get('content', '')[:100]}...")
                    
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Check specific pages
    print("\n3. Checking key pages...")
    test_pages = ['/about', '/contact', '/team', '/company']
    
    for page in test_pages:
        try:
            page_url = f"{url}{page}"
            response = requests.get(page_url, headers=headers, timeout=5, allow_redirects=True)
            print(f"   {page}: Status {response.status_code}, {len(response.text)} chars")
        except Exception as e:
            print(f"   {page}: Error - {type(e).__name__}")
    
    print("\n💡 Recommendations:")
    print("   - If the site is JavaScript-rendered, we need browser automation")
    print("   - Check if Crawl4AI is configured for JavaScript rendering")
    print("   - May need to adjust scraping strategy for this site")

if __name__ == "__main__":
    test_connatix_accessibility()