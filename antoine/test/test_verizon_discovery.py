#!/usr/bin/env python3
"""
Test Verizon discovery issue - why no paths are discovered
"""

import sys
import os
import requests

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Load env vars
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

from src.antoine_discovery import discover_all_paths_sync

def test_verizon_discovery():
    """Test Verizon website discovery"""
    
    print("=" * 80)
    print("VERIZON DISCOVERY TEST")
    print("=" * 80)
    
    # First, let's check if we can access Verizon's website
    test_url = "https://www.verizon.com"
    print(f"\n🌐 Testing URL: {test_url}")
    
    print("\n📍 STEP 1: Basic connectivity test")
    try:
        response = requests.get(test_url, timeout=10, allow_redirects=True)
        print(f"✅ Connected to Verizon")
        print(f"   - Status code: {response.status_code}")
        print(f"   - Final URL: {response.url}")
        print(f"   - Content length: {len(response.content)} bytes")
        
        if response.url != test_url:
            print(f"   ⚠️  Redirected from {test_url} to {response.url}")
            test_url = response.url
            
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    # Test robots.txt
    print("\n📍 STEP 2: Check robots.txt")
    try:
        robots_url = f"{test_url.rstrip('/')}/robots.txt"
        print(f"Checking: {robots_url}")
        robots_response = requests.get(robots_url, timeout=10)
        print(f"✅ Robots.txt status: {robots_response.status_code}")
        if robots_response.status_code == 200:
            print(f"   - Content length: {len(robots_response.content)} bytes")
            print("   - First 200 chars:")
            print(robots_response.text[:200])
    except Exception as e:
        print(f"❌ Robots.txt error: {e}")
    
    # Test sitemap
    print("\n📍 STEP 3: Check sitemap.xml")
    try:
        sitemap_url = f"{test_url.rstrip('/')}/sitemap.xml"
        print(f"Checking: {sitemap_url}")
        sitemap_response = requests.get(sitemap_url, timeout=10)
        print(f"✅ Sitemap.xml status: {sitemap_response.status_code}")
        if sitemap_response.status_code == 200:
            print(f"   - Content length: {len(sitemap_response.content)} bytes")
    except Exception as e:
        print(f"❌ Sitemap.xml error: {e}")
    
    # Now run the discovery
    print("\n📍 STEP 4: Run antoine discovery")
    try:
        discovery_result = discover_all_paths_sync(test_url, timeout_seconds=60)
        
        print(f"\n📊 Discovery Results:")
        print(f"✅ Discovery completed")
        print(f"   - Total paths found: {len(discovery_result.all_paths)}")
        print(f"   - Navigation paths: {len(discovery_result.navigation_paths)}")
        print(f"   - Content paths: {len(discovery_result.content_paths)}")
        print(f"   - Restricted paths: {len(discovery_result.restricted_paths)}")
        print(f"   - Errors: {len(discovery_result.errors)}")
        
        if discovery_result.errors:
            print("\n❌ Errors encountered:")
            for error in discovery_result.errors[:5]:
                print(f"   - {error}")
        
        if discovery_result.all_paths:
            print("\n📄 Sample paths discovered:")
            for i, path in enumerate(discovery_result.all_paths[:10]):
                print(f"   {i+1}. {path}")
        else:
            print("\n⚠️  No paths discovered!")
            
            # Check header/footer results
            print("\n🔍 Header/Footer extraction:")
            hf_results = discovery_result.header_footer_results
            if hf_results:
                print(f"   - Success: {hf_results.get('success', False)}")
                print(f"   - Error: {hf_results.get('error', 'None')}")
                print(f"   - Links found: {len(hf_results.get('links', []))}")
            
            # Check sitemap results
            print("\n🔍 Sitemap extraction:")
            print(f"   - Sitemap results: {len(discovery_result.sitemap_results)}")
            
            # Check robots results
            print("\n🔍 Robots.txt extraction:")
            robots_results = discovery_result.robots_results
            if robots_results:
                print(f"   - Success: {robots_results.get('success', False)}")
                print(f"   - Error: {robots_results.get('error', 'None')}")
                
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_verizon_discovery()