#!/usr/bin/env python3
"""
Simple test for Verizon - test crawling without all sitemaps
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Load env vars
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

from src.crawl_header_for_links import extract_header_footer_links

def test_verizon_simple():
    """Test just header/footer extraction from Verizon"""
    
    print("=" * 80)
    print("VERIZON SIMPLE CRAWL TEST")
    print("=" * 80)
    
    test_url = "https://www.verizon.com"
    
    print(f"\n🌐 Testing URL: {test_url}")
    print("\n📍 Extracting header/footer links only...")
    
    try:
        result = extract_header_footer_links(test_url)
        
        if result['success']:
            print(f"✅ Successfully extracted links")
            print(f"   - Total links found: {len(result['links'])}")
            
            print("\n📄 Links found:")
            for i, link in enumerate(result['links'][:20]):
                print(f"   {i+1}. {link}")
            
            if len(result['links']) > 20:
                print(f"   ... and {len(result['links']) - 20} more")
        else:
            print(f"❌ Failed to extract links: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Now let's test with a manual list of key pages
    print("\n\n📍 Testing with manual key pages...")
    key_pages = [
        "/",
        "/about",
        "/about/our-company",
        "/contact-us",
        "/careers",
        "/business",
        "/support",
        "/stores"
    ]
    
    print(f"Manual pages to test: {len(key_pages)}")
    for page in key_pages:
        print(f"  - {page}")

if __name__ == "__main__":
    test_verizon_simple()