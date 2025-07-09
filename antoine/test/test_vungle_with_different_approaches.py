#!/usr/bin/env python3
"""
Test Multiple Approaches for Vungle.com Social Media Extraction
===============================================================

Test various approaches to handle vungle.com's blocking mechanisms.

Usage:
    python test_vungle_with_different_approaches.py
"""

import sys
import os
import requests
import time
from datetime import datetime

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from test_social_media_extraction import SocialMediaExtractor

def test_different_user_agents():
    """Test with different user agents to bypass bot detection"""
    
    print("🔍 Testing Different User Agents for Vungle.com")
    print("=" * 60)
    
    url = "https://vungle.com"
    
    # Various user agents to test
    user_agents = [
        {
            'name': 'Chrome Windows',
            'agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        },
        {
            'name': 'Firefox Windows',
            'agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
        },
        {
            'name': 'Safari macOS',
            'agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        },
        {
            'name': 'Edge Windows',
            'agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        },
        {
            'name': 'Chrome Android',
            'agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
        }
    ]
    
    extractor = SocialMediaExtractor()
    
    for i, ua_info in enumerate(user_agents, 1):
        print(f"\n{i}. Testing {ua_info['name']}...")
        
        try:
            headers = {
                'User-Agent': ua_info['agent'],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
            
            response = requests.get(url, timeout=15, headers=headers)
            
            print(f"   Status: {response.status_code}")
            print(f"   Content size: {len(response.text):,} bytes")
            
            if response.status_code == 200:
                print(f"   ✅ Success! Testing social media extraction...")
                
                start_time = datetime.now()
                social_links = extractor.extract_social_media_links(response.text)
                extraction_time = (datetime.now() - start_time).total_seconds()
                
                print(f"   🔗 Social links found: {len(social_links)} ({extraction_time:.2f}s)")
                
                if social_links:
                    for platform, link_url in social_links.items():
                        print(f"      📱 {platform}: {link_url}")
                    return True, social_links
                else:
                    print(f"      ⚠️  No social media links found")
            else:
                print(f"   ❌ Failed with status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
        except Exception as e:
            print(f"   ❌ Extraction failed: {e}")
        
        # Add delay between requests to be respectful
        time.sleep(2)
    
    return False, {}

def test_with_session_and_cookies():
    """Test with session management and cookies"""
    
    print(f"\n🍪 Testing with Session and Cookie Management")
    print("-" * 50)
    
    url = "https://vungle.com"
    
    try:
        # Use session for cookie persistence
        session = requests.Session()
        
        # Set realistic headers
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        })
        
        # First request - might get redirected or set cookies
        print("   Making initial request...")
        response = session.get(url, timeout=15, allow_redirects=True)
        
        print(f"   Status: {response.status_code}")
        print(f"   Final URL: {response.url}")
        print(f"   Content size: {len(response.text):,} bytes")
        print(f"   Cookies set: {len(session.cookies)}")
        
        if response.status_code == 200:
            print(f"   ✅ Success! Testing social media extraction...")
            
            extractor = SocialMediaExtractor()
            social_links = extractor.extract_social_media_links(response.text)
            
            print(f"   🔗 Social links found: {len(social_links)}")
            
            if social_links:
                for platform, link_url in social_links.items():
                    print(f"      📱 {platform}: {link_url}")
                return True, social_links
            else:
                print(f"      ⚠️  No social media links found")
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
    except Exception as e:
        print(f"   ❌ Extraction failed: {e}")
    
    return False, {}

def test_alternative_vungle_pages():
    """Test alternative Vungle pages that might be less protected"""
    
    print(f"\n🔍 Testing Alternative Vungle Pages")
    print("-" * 40)
    
    alternative_urls = [
        "https://vungle.com/about",
        "https://vungle.com/contact",
        "https://vungle.com/careers",
        "https://vungle.com/blog",
        "https://support.vungle.com",
        "https://liftoff.io",  # Parent company
    ]
    
    extractor = SocialMediaExtractor()
    
    for url in alternative_urls:
        print(f"\n   Testing: {url}")
        
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            print(f"      Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"      ✅ Success! Content size: {len(response.text):,} bytes")
                
                social_links = extractor.extract_social_media_links(response.text)
                
                if social_links:
                    print(f"      🔗 Social links found: {len(social_links)}")
                    for platform, link_url in social_links.items():
                        print(f"         📱 {platform}: {link_url}")
                    return True, social_links
                else:
                    print(f"      ⚠️  No social media links found")
            else:
                print(f"      ❌ Failed with status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"      ❌ Request failed: {e}")
        except Exception as e:
            print(f"      ❌ Extraction failed: {e}")
            
        time.sleep(1)  # Be respectful with requests
    
    return False, {}

def main():
    """Main testing function"""
    
    print("🔧 Vungle.com Social Media Extraction - Multiple Approaches")
    print("=" * 70)
    
    results = []
    
    # Test 1: Different user agents
    print("\n🎭 Test 1: Different User Agents")
    success1, links1 = test_different_user_agents()
    results.append(('User Agents', success1, links1))
    
    # Test 2: Session and cookies
    print("\n🍪 Test 2: Session and Cookie Management")
    success2, links2 = test_with_session_and_cookies()
    results.append(('Session Management', success2, links2))
    
    # Test 3: Alternative pages
    print("\n🔍 Test 3: Alternative Pages")
    success3, links3 = test_alternative_vungle_pages()
    results.append(('Alternative Pages', success3, links3))
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 70)
    
    successful_approaches = [name for name, success, _ in results if success]
    
    if successful_approaches:
        print(f"✅ Successful approaches: {', '.join(successful_approaches)}")
        
        # Show all unique social media links found
        all_links = {}
        for _, success, links in results:
            if success:
                all_links.update(links)
        
        if all_links:
            print(f"\n🔗 All social media links found:")
            for platform, url in all_links.items():
                print(f"   📱 {platform}: {url}")
            
            print(f"\n🎉 SUCCESS: Found {len(all_links)} social media links for Vungle/Liftoff")
            print(f"💡 Recommendation: Use successful approach in main extraction script")
        
    else:
        print(f"❌ All approaches failed")
        print(f"💡 Recommendations:")
        print(f"   1. Vungle.com has strong bot protection - consider manual verification")
        print(f"   2. Use JavaScript rendering (Selenium) for dynamic content")
        print(f"   3. Check if social media links are available through other sources")
    
    print(f"\n🔧 Next Steps:")
    if successful_approaches:
        print(f"   1. Update extract_top10_social_media.py with successful approach")
        print(f"   2. Test with other companies that showed HTTP 403 errors")
        print(f"   3. Update social media extraction report")
    else:
        print(f"   1. Consider using Selenium for JavaScript rendering")
        print(f"   2. Manual verification of social media links")
        print(f"   3. Mark vungle.com as requiring special handling")

if __name__ == "__main__":
    main()