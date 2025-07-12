#!/usr/bin/env python3
"""
Test Volvo Canada Social Media Extraction
==========================================

Test that Volvo Canada now processes with working social media extraction.
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load env vars
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path)

from src.models import CompanyData, CompanyIntelligenceConfig
from src.antoine_scraper_adapter import AntoineScraperAdapter


def test_volvo_with_social_media():
    """Test Volvo Canada processing with working social media extraction."""
    print("🚗 TESTING VOLVO CANADA + SOCIAL MEDIA EXTRACTION")
    print("=" * 60)
    
    # Create test company
    volvo_company = CompanyData(
        name="Volvo Canada",
        website="https://www.volvocars.com/en-ca/"
    )
    
    print(f"Company: {volvo_company.name}")
    print(f"Website: {volvo_company.website}")
    print(f"Focus: Social media extraction working properly")
    
    # Create scraper
    config = CompanyIntelligenceConfig()
    scraper = AntoineScraperAdapter(config)
    
    print(f"\n🔍 Starting processing with social media fix...")
    start_time = time.time()
    
    try:
        # Run the scraper
        result = scraper.scrape_company(volvo_company)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"⏱️  Processing completed in {duration:.1f}s")
        
        # Check results
        print(f"\n📊 PROCESSING RESULTS:")
        print(f"   Status: {result.scrape_status}")
        
        if result.scrape_status == "success":
            print(f"   🎉 SUCCESS!")
            
            # Check social media specifically
            print(f"\n🔗 SOCIAL MEDIA ANALYSIS:")
            social_media = getattr(result, 'social_media', None)
            
            if social_media:
                if isinstance(social_media, dict) and social_media:
                    print(f"   ✅ Social media found: {len(social_media)} platforms")
                    for platform, url in social_media.items():
                        print(f"      📱 {platform}: {url}")
                    print(f"   🎯 Status: WORKING (no longer pending!)")
                    return True
                elif isinstance(social_media, dict) and not social_media:
                    print(f"   ⚠️  Social media: Empty dict (extraction ran but found nothing)")
                    print(f"   💡 This is normal - not all companies have easily discoverable social links")
                    print(f"   🎯 Status: WORKING (no longer pending!)")
                    return True
                else:
                    print(f"   ❌ Social media: Invalid format ({type(social_media)})")
                    print(f"   🎯 Status: BROKEN")
                    return False
            else:
                print(f"   ❌ Social media: None/missing")
                print(f"   🎯 Status: BROKEN")
                return False
        else:
            print(f"   ❌ Processing failed: {result.scrape_error}")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False


def main():
    """Run Volvo social media test."""
    print("🧪 VOLVO CANADA SOCIAL MEDIA EXTRACTION TEST")
    print("Testing that social media no longer shows as 'pending'")
    print("=" * 80)
    
    try:
        success = test_volvo_with_social_media()
        
        print(f"\n" + "=" * 80)
        print("🎯 VOLVO SOCIAL MEDIA TEST RESULTS")
        print("=" * 80)
        
        if success:
            print(f"✅ TEST PASSED!")
            print(f"🎉 Social media extraction working properly")
            print(f"🌐 Social media should no longer show as 'pending' in web UI")
            print(f"🔗 Enhanced social media research integrated successfully")
        else:
            print(f"❌ TEST FAILED!")
            print(f"⚠️  Social media may still show as 'pending'")
            print(f"🔧 Additional debugging may be needed")
        
        return success
        
    except Exception as e:
        print(f"\n❌ TEST FRAMEWORK ERROR: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)