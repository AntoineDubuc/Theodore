#!/usr/bin/env python3
"""
Debug Vungle.com Social Media Extraction Issue
==============================================

Investigate why vungle.com fails social media extraction despite having
visible social media links in the footer. Test various approaches to
handle consent popups and overlays.

Usage:
    python debug_vungle_extraction.py
"""

import sys
import os
import requests
from bs4 import BeautifulSoup
from typing import Dict, List
import time

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from test_social_media_extraction import SocialMediaExtractor

def test_basic_request():
    """Test basic HTTP request to vungle.com"""
    print("🔍 Testing Basic HTTP Request to vungle.com")
    print("-" * 50)
    
    url = "https://vungle.com"
    
    # Try different user agents
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
    ]
    
    for i, user_agent in enumerate(user_agents, 1):
        print(f"\n{i}. Testing with User Agent: {user_agent[:50]}...")
        
        try:
            response = requests.get(url, timeout=15, headers={
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response Size: {len(response.text):,} bytes")
            
            if response.status_code == 200:
                print(f"   ✅ Success! Content preview: {response.text[:100]}...")
                return response.text
            else:
                print(f"   ❌ Failed with status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
    
    return None

def analyze_html_structure(html_content: str):
    """Analyze the HTML structure for social media links and consent popups"""
    print("\n🔍 Analyzing HTML Structure")
    print("-" * 50)
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Look for consent popup elements
    consent_indicators = [
        'consent', 'cookie', 'privacy', 'gdpr', 'accept', 'popup', 'overlay',
        'modal', 'banner', 'notice', 'policy'
    ]
    
    print("🍪 Searching for consent popup elements...")
    consent_elements = []
    
    for indicator in consent_indicators:
        # Search in class names
        elements = soup.find_all(attrs={'class': lambda x: x and indicator in str(x).lower()})
        if elements:
            consent_elements.extend(elements)
        
        # Search in id attributes
        elements = soup.find_all(attrs={'id': lambda x: x and indicator in str(x).lower()})
        if elements:
            consent_elements.extend(elements)
    
    if consent_elements:
        print(f"   Found {len(consent_elements)} potential consent-related elements:")
        for elem in consent_elements[:5]:  # Show first 5
            attrs = elem.attrs
            tag_info = f"<{elem.name}"
            if 'class' in attrs:
                tag_info += f" class='{' '.join(attrs['class'])}'"
            if 'id' in attrs:
                tag_info += f" id='{attrs['id']}'"
            tag_info += ">"
            print(f"      {tag_info}")
    else:
        print("   No consent popup elements found")
    
    # Look for footer elements
    print("\n🦶 Searching for footer elements...")
    footer_elements = soup.find_all(['footer', 'div'], attrs={'class': lambda x: x and 'footer' in str(x).lower()})
    
    if footer_elements:
        print(f"   Found {len(footer_elements)} footer elements")
        for i, footer in enumerate(footer_elements):
            print(f"      Footer {i+1}: {footer.name} with classes: {footer.get('class', [])}")
    else:
        print("   No footer elements found")
    
    # Look for social media links manually
    print("\n🔗 Manual search for social media links...")
    social_domains = ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com', 'youtube.com', 'github.com', 'tiktok.com']
    
    all_links = soup.find_all('a', href=True)
    social_links_found = []
    
    for link in all_links:
        href = link['href']
        for domain in social_domains:
            if domain in href.lower():
                social_links_found.append({
                    'platform': domain.split('.')[0],
                    'url': href,
                    'text': link.get_text(strip=True)[:50],
                    'parent': link.parent.name if link.parent else None
                })
    
    if social_links_found:
        print(f"   ✅ Found {len(social_links_found)} social media links:")
        for link in social_links_found:
            print(f"      {link['platform']}: {link['url']} (text: '{link['text']}', parent: {link['parent']})")
    else:
        print("   ❌ No social media links found in manual search")
    
    return social_links_found

def test_extraction_with_consent_handling(html_content: str):
    """Test extraction with consent popup handling"""
    print("\n🛠️ Testing Extraction with Consent Handling")
    print("-" * 50)
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove consent popup elements before extraction
    consent_selectors = [
        '[class*="consent"]', '[class*="cookie"]', '[class*="privacy"]', 
        '[class*="gdpr"]', '[class*="popup"]', '[class*="overlay"]',
        '[class*="modal"]', '[class*="banner"]', '[class*="notice"]',
        '[id*="consent"]', '[id*="cookie"]', '[id*="privacy"]'
    ]
    
    removed_elements = 0
    for selector in consent_selectors:
        elements = soup.select(selector)
        for elem in elements:
            elem.decompose()
            removed_elements += 1
    
    print(f"   Removed {removed_elements} potential consent popup elements")
    
    # Test extraction on cleaned HTML
    cleaned_html = str(soup)
    extractor = SocialMediaExtractor()
    social_links = extractor.extract_social_media_links(cleaned_html)
    
    print(f"   🔍 Extraction after cleanup: {len(social_links)} links found")
    for platform, url in social_links.items():
        print(f"      {platform}: {url}")
    
    return social_links

def test_different_parsing_strategies(html_content: str):
    """Test different parsing strategies for social media extraction"""
    print("\n🎯 Testing Different Parsing Strategies")
    print("-" * 50)
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    strategies = [
        ("Footer-only extraction", lambda s: s.find_all(['footer'])),
        ("Bottom 20% of page", lambda s: s.find_all()[int(len(s.find_all()) * 0.8):]),
        ("All links extraction", lambda s: s.find_all('a', href=True)),
        ("Social-specific selectors", lambda s: s.select('[href*="facebook"], [href*="twitter"], [href*="linkedin"], [href*="instagram"], [href*="youtube"]'))
    ]
    
    for strategy_name, strategy_func in strategies:
        print(f"\n   Testing: {strategy_name}")
        
        try:
            elements = strategy_func(soup)
            social_links = []
            
            for elem in elements:
                if elem.name == 'a' and elem.get('href'):
                    href = elem['href']
                    for domain in ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com', 'youtube.com', 'github.com']:
                        if domain in href.lower():
                            platform = domain.split('.')[0]
                            social_links.append((platform, href))
                elif elem.name != 'a':
                    # Look for links within this element
                    links = elem.find_all('a', href=True)
                    for link in links:
                        href = link['href']
                        for domain in ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com', 'youtube.com', 'github.com']:
                            if domain in href.lower():
                                platform = domain.split('.')[0]
                                social_links.append((platform, href))
            
            # Remove duplicates
            unique_links = list(set(social_links))
            
            print(f"      Found {len(unique_links)} unique social media links:")
            for platform, url in unique_links:
                print(f"         {platform}: {url}")
                
        except Exception as e:
            print(f"      ❌ Strategy failed: {e}")

def test_javascript_rendered_content():
    """Test if the content requires JavaScript rendering"""
    print("\n🌐 Testing JavaScript Rendering Requirements")
    print("-" * 50)
    
    url = "https://vungle.com"
    
    print("   Testing if social media links are JavaScript-rendered...")
    
    # Check if we can use selenium for JavaScript rendering
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        print("   ✅ Selenium available - testing JavaScript rendering")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get rendered HTML
            rendered_html = driver.page_source
            print(f"   Rendered HTML size: {len(rendered_html):,} bytes")
            
            # Extract social media links from rendered content
            extractor = SocialMediaExtractor()
            social_links = extractor.extract_social_media_links(rendered_html)
            
            print(f"   🔍 Social links from rendered content: {len(social_links)}")
            for platform, url in social_links.items():
                print(f"      {platform}: {url}")
            
            return social_links
            
        finally:
            driver.quit()
            
    except ImportError:
        print("   ⚠️  Selenium not available - skipping JavaScript rendering test")
        print("   Install selenium and chromedriver to test JavaScript-rendered content")
        return {}
    except Exception as e:
        print(f"   ❌ JavaScript rendering test failed: {e}")
        return {}

def main():
    """Main debugging function"""
    print("🐛 Debugging Vungle.com Social Media Extraction")
    print("=" * 60)
    
    # Step 1: Test basic request
    html_content = test_basic_request()
    
    if not html_content:
        print("\n❌ Could not fetch HTML content - debugging cannot continue")
        return
    
    # Step 2: Analyze HTML structure
    manual_links = analyze_html_structure(html_content)
    
    # Step 3: Test extraction with consent handling
    cleaned_links = test_extraction_with_consent_handling(html_content)
    
    # Step 4: Test different parsing strategies
    test_different_parsing_strategies(html_content)
    
    # Step 5: Test JavaScript rendering
    js_links = test_javascript_rendered_content()
    
    # Summary
    print("\n📊 Debugging Summary")
    print("=" * 60)
    print(f"Manual search found: {len(manual_links)} links")
    print(f"After consent cleanup: {len(cleaned_links)} links")
    print(f"JavaScript rendered: {len(js_links)} links")
    
    if manual_links and not cleaned_links:
        print("\n💡 Recommendation: The issue is likely consent popup interference")
        print("   - Social media links exist in the HTML")
        print("   - Standard extraction fails due to popup overlays")
        print("   - Solution: Remove consent popups before extraction")
    
    if js_links and len(js_links) > len(cleaned_links):
        print("\n💡 Recommendation: JavaScript rendering improves extraction")
        print("   - More links found with JavaScript rendering")
        print("   - Consider using Selenium or similar for dynamic content")
    
    print("\n🔧 Suggested fixes:")
    print("1. Add consent popup removal to SocialMediaExtractor")
    print("2. Use JavaScript rendering for sites with dynamic content")
    print("3. Add retry mechanism with different user agents")
    print("4. Implement fallback extraction strategies")

if __name__ == "__main__":
    main()