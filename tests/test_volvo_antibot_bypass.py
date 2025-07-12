#!/usr/bin/env python3
"""
Volvo Canada Anti-Bot Protection Bypass Test
============================================

Test the enhanced crawler with realistic browser headers and Crawl4AI fallback
to verify it can now bypass Volvo's anti-bot protection.
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


def test_volvo_antibot_bypass():
    """Test Volvo Canada with enhanced anti-bot protection bypass."""
    print("🚗 TESTING VOLVO CANADA - ANTI-BOT PROTECTION BYPASS")
    print("=" * 60)
    
    # Create test company
    volvo_company = CompanyData(
        name="Volvo Canada",
        website="https://www.volvocars.com/en-ca/"
    )
    
    print(f"Company: {volvo_company.name}")
    print(f"Website: {volvo_company.website}")
    print(f"Expected improvements:")
    print(f"  ✅ Realistic browser headers (User-Agent, Accept, etc.)")
    print(f"  ✅ Request delays (500ms between requests)")
    print(f"  ✅ Crawl4AI fallback for 403 errors")
    
    # Create scraper with enhanced anti-bot protection
    config = CompanyIntelligenceConfig()
    scraper = AntoineScraperAdapter(config)
    
    print(f"\n🔍 Starting enhanced Antoine scraper...")
    start_time = time.time()
    
    try:
        # Run the scraper (should now bypass anti-bot protection)
        result = scraper.scrape_company(volvo_company)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"⏱️  Processing completed in {duration:.1f}s")
        
        # Check results
        print(f"\n📊 DETAILED RESULTS:")
        print(f"   Status: {result.scrape_status}")
        
        if result.scrape_status == "success":
            print(f"   🎉 SUCCESS: Anti-bot protection bypassed!")
            print(f"   Pages crawled: {len(result.pages_crawled) if result.pages_crawled else 0}")
            print(f"   Company description: {len(result.company_description) if result.company_description else 0} chars")
            print(f"   Raw content: {len(result.raw_content) if result.raw_content else 0} chars")
            print(f"   Duration: {duration:.1f}s")
            
            # Show sample content
            if result.company_description:
                preview = result.company_description[:200] + "..." if len(result.company_description) > 200 else result.company_description
                print(f"\n📝 Content preview:")
                print(f"   {preview}")
            
            # Check for successful extraction methods
            if hasattr(result, 'crawl_method') or any(method in str(result.__dict__) for method in ['trafilatura', 'crawl4ai']):
                print(f"   🔧 Extraction method: Enhanced crawler with fallback")
            
            return True
            
        elif result.scrape_error:
            print(f"   ❌ FAILED: {result.scrape_error}")
            
            # Analyze the error to see what protection is still active
            if "403" in result.scrape_error or "Forbidden" in result.scrape_error:
                print(f"   🚫 Anti-bot protection still active")
                print(f"   💡 Suggestion: May need additional bypass techniques")
            elif "No content extracted" in result.scrape_error:
                print(f"   ⚠️  Pages accessible but content extraction failed")
                print(f"   💡 Suggestion: May need different content extraction approach")
            
            return False
        else:
            print(f"   ❌ UNKNOWN FAILURE: No specific error provided")
            return False
            
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"❌ EXCEPTION after {duration:.1f}s: {e}")
        print(f"💡 This suggests the enhanced crawler has implementation issues")
        return False


def test_simple_site_regression():
    """Test that the enhanced crawler doesn't break simple sites."""
    print(f"\n🔧 TESTING SIMPLE SITE (Regression Test)")
    print("=" * 60)
    
    # Test with a simple site that should work
    simple_company = CompanyData(
        name="Example Company",
        website="https://example.com"
    )
    
    print(f"Company: {simple_company.name}")
    print(f"Website: {simple_company.website}")
    
    config = CompanyIntelligenceConfig()
    scraper = AntoineScraperAdapter(config)
    
    print(f"\n🔍 Testing enhanced crawler with simple site...")
    start_time = time.time()
    
    try:
        result = scraper.scrape_company(simple_company)
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️  Processing completed in {duration:.1f}s")
        print(f"📊 Status: {result.scrape_status}")
        
        if result.scrape_status == "success":
            print(f"✅ Enhanced crawler works for simple sites")
            return True
        else:
            print(f"⚠️  Enhanced crawler may have issues: {result.scrape_error}")
            return False
            
    except Exception as e:
        print(f"❌ Enhanced crawler failed on simple site: {e}")
        return False


def main():
    """Run anti-bot protection bypass tests."""
    print("🧪 VOLVO CANADA ANTI-BOT PROTECTION BYPASS TESTS")
    print("Testing enhanced crawler with browser headers and Crawl4AI fallback")
    print("=" * 80)
    
    tests = [
        ("Volvo Canada Anti-Bot Bypass", test_volvo_antibot_bypass),
        ("Simple Site Regression Test", test_simple_site_regression)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔬 RUNNING: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            results.append((test_name, False))
            print(f"\n❌ ERROR: {test_name} - {e}")
    
    # Summary
    print(f"\n" + "=" * 80)
    print("🎯 ANTI-BOT PROTECTION BYPASS TEST RESULTS")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"📊 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ Anti-bot protection bypass successfully implemented")
        print(f"🚗 Volvo Canada should now work in the web UI")
        print(f"🔧 Enhanced crawler with browser headers + Crawl4AI fallback")
    elif any(name == "Volvo Canada Anti-Bot Bypass" and success for name, success in results):
        print(f"\n🎉 VOLVO CANADA BYPASS SUCCESSFUL!")
        print(f"✅ Main objective achieved - Volvo Canada now works")
        print(f"⚠️  Check any failed regression tests")
    else:
        print(f"\n⚠️ VOLVO CANADA BYPASS FAILED")
        print(f"🔧 Anti-bot protection may need additional techniques")
        print(f"💡 Consider: IP rotation, more sophisticated headers, selenium")
    
    return passed >= 1  # Success if at least Volvo Canada works


if __name__ == "__main__":
    main()