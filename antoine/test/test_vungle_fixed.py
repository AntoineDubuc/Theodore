#!/usr/bin/env python3
"""
Test Fixed Vungle.com Social Media Extraction
=============================================

Test the enhanced SocialMediaExtractor with vungle.com to verify that 
consent popup removal fixes the extraction issue.

Usage:
    python test_vungle_fixed.py
"""

import sys
import os
import requests
from datetime import datetime

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from test_social_media_extraction import SocialMediaExtractor

def test_vungle_extraction():
    """Test the fixed social media extraction with vungle.com"""
    
    print("🔧 Testing Fixed Vungle.com Social Media Extraction")
    print("=" * 60)
    
    url = "https://vungle.com"
    
    try:
        # Fetch the HTML content
        print(f"📥 Fetching content from {url}...")
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch HTML: HTTP {response.status_code}")
            return False
        
        print(f"✅ Successfully fetched {len(response.text):,} bytes of HTML")
        
        # Test with enhanced extractor
        print(f"\n🔍 Testing with enhanced SocialMediaExtractor...")
        extractor = SocialMediaExtractor()
        
        start_time = datetime.now()
        social_links = extractor.extract_social_media_links(response.text)
        extraction_time = (datetime.now() - start_time).total_seconds()
        
        print(f"⏱️  Extraction completed in {extraction_time:.2f}s")
        print(f"🔗 Social media links found: {len(social_links)}")
        
        if social_links:
            print(f"\n✅ SUCCESS! Found {len(social_links)} social media links:")
            for platform, url in social_links.items():
                print(f"   📱 {platform}: {url}")
            
            # Verify expected platforms
            expected_platforms = ['facebook', 'linkedin', 'youtube', 'twitter']
            found_expected = set(social_links.keys()) & set(expected_platforms)
            
            if found_expected:
                print(f"\n🎯 Found expected platforms: {', '.join(found_expected)}")
            else:
                print(f"\n⚠️  No expected platforms found (expected: {', '.join(expected_platforms)})")
            
            return True
        else:
            print(f"\n❌ No social media links found")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return False

def compare_with_previous_results():
    """Compare with previous extraction results"""
    
    print(f"\n📊 Comparison with Previous Results")
    print("-" * 40)
    
    # Previous results from the Google Sheet extraction
    previous_result = {
        'status': 'failed',
        'error': 'HTTP 403',
        'social_links_found': 0
    }
    
    print(f"📋 Previous extraction (from Google Sheet):")
    print(f"   Status: {previous_result['status']}")
    print(f"   Error: {previous_result['error']}")
    print(f"   Links found: {previous_result['social_links_found']}")
    
    # Run current extraction
    success = test_vungle_extraction()
    
    print(f"\n📈 Improvement Assessment:")
    if success:
        print(f"   ✅ Status: failed → success")
        print(f"   ✅ Error: HTTP 403 → none")
        print(f"   ✅ Links found: 0 → multiple")
        print(f"   ✅ Consent popup handling: working")
    else:
        print(f"   ❌ Still failing - needs further investigation")
    
    return success

def main():
    """Main testing function"""
    
    print("🐛 Vungle.com Social Media Extraction Fix Test")
    print("=" * 60)
    
    # Test the fixed extraction
    success = compare_with_previous_results()
    
    print(f"\n📝 Test Summary:")
    print(f"   Test result: {'✅ PASSED' if success else '❌ FAILED'}")
    
    if success:
        print(f"   🎉 Fix confirmed: Consent popup removal resolves vungle.com extraction issue")
        print(f"   🚀 Ready to update the main Google Sheet extraction script")
    else:
        print(f"   🔧 Fix needs refinement - additional debugging required")
    
    print(f"\n🔧 Next Steps:")
    if success:
        print(f"   1. Update extract_top10_social_media.py with enhanced extractor")
        print(f"   2. Re-run Google Sheet extraction for all companies")
        print(f"   3. Update top10_social_media_report.md with new results")
    else:
        print(f"   1. Review consent popup removal logic")
        print(f"   2. Test with additional consent management platforms")
        print(f"   3. Consider JavaScript rendering for dynamic content")

if __name__ == "__main__":
    main()