#!/usr/bin/env python3
"""
Test Phase 5 Social Media Integration
====================================

Test the integrated social media extraction as Phase 5 of the 
intelligent company scraper pipeline.

Usage:
    python test_phase5_integration.py
"""

import sys
import os
import asyncio
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Test imports
from src.models import CompanyData, CompanyIntelligenceConfig
from src.intelligent_company_scraper import IntelligentCompanyScraper

def test_phase5_integration():
    """Test Phase 5 social media extraction integration"""
    
    print("🧪 Testing Phase 5 Social Media Integration")
    print("=" * 60)
    
    # Test company known to have social media links
    test_company = CompanyData(
        name="Shopify",
        website="https://www.shopify.com"
    )
    
    print(f"🎯 Test Target: {test_company.name} ({test_company.website})")
    print(f"📋 Expected: Multiple social media links (Facebook, Twitter, LinkedIn, etc.)")
    
    # Configure intelligent scraper
    config = CompanyIntelligenceConfig(
        max_pages_to_crawl=10,  # Reduced for testing
        max_crawl_depth=2,
        max_content_per_page=5000,
        enable_ai_analysis=True
    )
    
    # Create scraper instance (no Bedrock needed for this test)
    scraper = IntelligentCompanyScraper(config, bedrock_client=None)
    
    print(f"\n🚀 Starting Intelligent Scraping with Phase 5...")
    start_time = datetime.now()
    
    try:
        # Run the full 5-phase pipeline
        result = asyncio.run(scraper.scrape_company_intelligent(test_company))
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n📊 Integration Test Results:")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Status: {result.scrape_status}")
        print(f"   Pages crawled: {len(result.pages_crawled) if result.pages_crawled else 0}")
        print(f"   Sales intelligence: {len(result.company_description) if result.company_description else 0} chars")
        print(f"   Social media links: {len(result.social_media) if result.social_media else 0}")
        
        if result.social_media:
            print(f"\n📱 Social Media Links Found:")
            for platform, url in result.social_media.items():
                print(f"   ✅ {platform}: {url}")
        else:
            print(f"\n⚠️  No social media links found")
        
        # Validation
        success_criteria = {
            "Scraping completed": result.scrape_status == "success",
            "Pages crawled": len(result.pages_crawled) > 0 if result.pages_crawled else False,
            "Social media field populated": hasattr(result, 'social_media'),
            "Social media links found": len(result.social_media) > 0 if result.social_media else False
        }
        
        print(f"\n✅ Validation Results:")
        all_passed = True
        for criterion, passed in success_criteria.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {status} {criterion}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print(f"\n🎉 Phase 5 Integration Test: ✅ PASSED")
            print(f"   Social media extraction successfully integrated!")
        else:
            print(f"\n❌ Phase 5 Integration Test: FAILED")
            print(f"   Some validation criteria not met")
        
        return all_passed, result
        
    except Exception as e:
        print(f"\n❌ Integration test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_social_media_researcher_standalone():
    """Test the SocialMediaResearcher module standalone"""
    
    print(f"\n🔬 Testing SocialMediaResearcher Standalone")
    print("-" * 50)
    
    from src.social_media_researcher import SocialMediaResearcher
    
    # Sample HTML content with social media links
    test_html = """
    <html>
        <body>
            <header>
                <a href="https://facebook.com/shopify">Facebook</a>
                <a href="https://twitter.com/shopify">Twitter</a>
            </header>
            <footer>
                <div class="social-links">
                    <a href="https://linkedin.com/company/shopify">LinkedIn</a>
                    <a href="https://instagram.com/shopify">Instagram</a>
                    <a href="https://youtube.com/user/shopify">YouTube</a>
                </div>
            </footer>
        </body>
    </html>
    """
    
    researcher = SocialMediaResearcher()
    social_links = researcher.extract_social_media_links(test_html)
    
    print(f"📄 Test HTML processed")
    print(f"🔗 Social media links found: {len(social_links)}")
    
    expected_platforms = {'facebook', 'twitter', 'linkedin', 'instagram', 'youtube'}
    found_platforms = set(social_links.keys())
    
    print(f"\n📋 Platform Detection:")
    print(f"   Expected: {expected_platforms}")
    print(f"   Found: {found_platforms}")
    print(f"   Match: {expected_platforms == found_platforms}")
    
    if social_links:
        print(f"\n📱 Extracted Links:")
        for platform, url in social_links.items():
            print(f"   {platform}: {url}")
    
    standalone_success = len(social_links) >= 4  # Expect at least 4 links
    
    print(f"\n{'✅ PASS' if standalone_success else '❌ FAIL'} Standalone SocialMediaResearcher test")
    
    return standalone_success

def main():
    """Run all integration tests"""
    
    print("🚀 Phase 5 Social Media Integration Test Suite")
    print("=" * 70)
    
    # Test 1: Standalone SocialMediaResearcher
    print("\n📋 Test 1: Standalone SocialMediaResearcher")
    standalone_success = test_social_media_researcher_standalone()
    
    # Test 2: Full Phase 5 Integration (only if standalone works)
    if standalone_success:
        print("\n📋 Test 2: Full Phase 5 Integration")
        integration_success, result = test_phase5_integration()
    else:
        print("\n⚠️  Skipping integration test due to standalone failure")
        integration_success = False
        result = None
    
    # Final Summary
    print(f"\n📊 Test Suite Summary")
    print("=" * 70)
    print(f"   Standalone Test: {'✅ PASSED' if standalone_success else '❌ FAILED'}")
    print(f"   Integration Test: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    
    overall_success = standalone_success and integration_success
    
    if overall_success:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"   Phase 5 social media extraction is ready for production")
        if result and result.social_media:
            print(f"   Found {len(result.social_media)} social media links in integration test")
    else:
        print(f"\n❌ SOME TESTS FAILED")
        print(f"   Review failures and fix issues before production deployment")
    
    print(f"\n🔧 Next Steps:")
    if overall_success:
        print(f"   1. Deploy Phase 5 integration to production")
        print(f"   2. Monitor social media extraction success rates")
        print(f"   3. Add social media data to UI displays")
    else:
        print(f"   1. Fix failing test components")
        print(f"   2. Re-run integration tests")
        print(f"   3. Validate with additional test companies")

if __name__ == "__main__":
    main()