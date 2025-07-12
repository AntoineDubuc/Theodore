#!/usr/bin/env python3
"""
Volvo Canada Specific Debug Test
================================

Focus specifically on why Volvo Canada fails and how to fix it.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load env vars
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path)

from src.antoine_discovery import discover_all_paths_sync


def analyze_volvo_paths():
    """Analyze what paths are discovered for Volvo Canada"""
    print("🔍 Analyzing Volvo Canada path discovery")
    
    website = "https://www.volvocars.com/en-ca/"
    
    try:
        discovery_result = discover_all_paths_sync(website, timeout_seconds=30)
        
        print(f"📊 Discovery Results:")
        print(f"   Total paths: {len(discovery_result.all_paths)}")
        
        # Analyze path patterns
        locale_paths = []
        content_paths = []
        
        for path in discovery_result.all_paths:
            # Check if it's a locale path (2-5 chars, often country codes)
            if len(path) <= 6 and path.count('/') <= 1 and path != '/':
                locale_paths.append(path)
            else:
                content_paths.append(path)
        
        print(f"   Locale paths: {len(locale_paths)}")
        print(f"   Content paths: {len(content_paths)}")
        
        print(f"\n📋 Sample locale paths (likely rejected by Nova Pro):")
        for path in locale_paths[:20]:
            print(f"   {path}")
        
        print(f"\n📋 Sample content paths (might be valuable):")
        for path in content_paths[:20]:
            print(f"   {path}")
        
        # Test if we can find actual Volvo Canada content paths
        print(f"\n🔍 Looking for actual Volvo Canada content...")
        
        # Try the specific Canadian URL
        ca_website = "https://www.volvocars.com/en-ca"
        ca_discovery = discover_all_paths_sync(ca_website, timeout_seconds=30)
        
        print(f"📊 Canada-specific discovery:")
        print(f"   Total paths: {len(ca_discovery.all_paths)}")
        
        # Look for valuable Canadian content
        valuable_patterns = [
            '/about', '/company', '/contact', '/careers', '/dealers', 
            '/models', '/cars', '/vehicles', '/services', '/support',
            '/news', '/press', '/sustainability', '/safety'
        ]
        
        found_valuable = []
        for path in ca_discovery.all_paths:
            for pattern in valuable_patterns:
                if pattern in path.lower():
                    found_valuable.append(path)
                    break
        
        print(f"   Potentially valuable paths: {len(found_valuable)}")
        for path in found_valuable[:15]:
            print(f"   {path}")
        
        return ca_discovery.all_paths
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return []


def test_manual_volvo_paths():
    """Test with manually curated Volvo Canada paths"""
    print(f"\n🛠️ Testing with manually curated Volvo paths")
    
    # Paths that should exist on Volvo Canada site
    manual_paths = [
        "/en-ca",
        "/en-ca/about",
        "/en-ca/cars",
        "/en-ca/cars/xc90",
        "/en-ca/cars/xc60", 
        "/en-ca/cars/xc40",
        "/en-ca/sustainability",
        "/en-ca/safety",
        "/en-ca/dealers",
        "/en-ca/contact-us",
        "/en-ca/support",
        "/en-ca/news",
        "/en-ca/careers"
    ]
    
    website = "https://www.volvocars.com"
    
    print(f"🧪 Testing Nova Pro with {len(manual_paths)} curated paths")
    
    try:
        from src.antoine_selection import filter_valuable_links_sync
        
        result = filter_valuable_links_sync(
            manual_paths,
            website,
            min_confidence=0.4,
            timeout_seconds=60
        )
        
        print(f"📊 Results:")
        print(f"   Success: {result.success}")
        print(f"   Selected: {len(result.selected_paths)}")
        print(f"   Rejected: {len(result.rejected_paths)}")
        print(f"   Cost: ${result.cost_usd:.4f}")
        
        if result.selected_paths:
            print(f"\n✅ Selected paths:")
            for path in result.selected_paths:
                print(f"   {path}")
        
        if result.error:
            print(f"\n❌ Error: {result.error}")
        
        return len(result.selected_paths) > 0
        
    except Exception as e:
        print(f"❌ Manual test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_better_volvo_fallback():
    """Create a better fallback specifically for Volvo"""
    print(f"\n💡 Creating Volvo-specific fallback paths")
    
    # Volvo-specific paths based on their site structure
    volvo_fallback = [
        "/en-ca",
        "/en-ca/about",
        "/en-ca/about/volvo-cars",
        "/en-ca/cars", 
        "/en-ca/sustainability",
        "/en-ca/safety",
        "/en-ca/innovation",
        "/en-ca/dealers",
        "/en-ca/contact-us",
        "/en-ca/support",
        "/en-ca/news",
        "/en-ca/careers",
        "/en-ca/ownership",
        "/en-ca/shopping-tools"
    ]
    
    print(f"📋 Volvo-specific fallback paths ({len(volvo_fallback)}):")
    for path in volvo_fallback:
        print(f"   {path}")
    
    return volvo_fallback


def main():
    """Run Volvo-specific debugging"""
    print("🚗 VOLVO CANADA SPECIFIC DEBUG")
    print("="*50)
    
    # Step 1: Analyze current path discovery
    discovered_paths = analyze_volvo_paths()
    
    # Step 2: Test with manual paths
    manual_success = test_manual_volvo_paths()
    
    # Step 3: Create better fallback
    volvo_fallback = create_better_volvo_fallback()
    
    print(f"\n📊 SUMMARY:")
    print(f"   Discovered paths: {len(discovered_paths)}")
    print(f"   Manual test success: {manual_success}")
    print(f"   Fallback paths: {len(volvo_fallback)}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"   1. Filter out locale-only paths (like /ae, /ar, etc.)")
    print(f"   2. Use site-specific fallbacks for large international sites")
    print(f"   3. Add better path discovery for Canadian content")
    print(f"   4. Consider domain-specific path selection")


if __name__ == "__main__":
    main()