#!/usr/bin/env python3
"""
Test the URL validation fix to ensure it filters out invalid URLs properly
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.concurrent_intelligent_scraper import ConcurrentIntelligentScraperSync
from src.models import CompanyIntelligenceConfig

def test_url_validation():
    """Test URL validation logic"""
    
    print("🧪 Testing URL Validation Fix")
    print("=" * 50)
    
    # Create scraper instance
    config = CompanyIntelligenceConfig()
    scraper = ConcurrentIntelligentScraperSync(config)
    
    base_url = "https://trivalleyathletics.org"
    
    # Test URLs - mix of valid and invalid
    test_urls = [
        # ✅ Valid URLs that should pass
        ("https://trivalleyathletics.org/about", True, "Absolute HTTPS URL"),
        ("https://trivalleyathletics.org/contact", True, "Absolute HTTPS URL"),
        ("/coaches-contact-information/", True, "Absolute path (relative)"),
        ("teams/varsity/football", True, "Relative path"),
        ("https://example.com/page", True, "External HTTPS URL"),
        
        # ❌ Invalid URLs that should be filtered out
        ("internal", False, "Navigation text"),
        ("external", False, "Navigation text"),
        ("javascript:void(0)", False, "JavaScript URL"),
        ("mailto:test@example.com", False, "Email link"),
        ("tel:+1234567890", False, "Phone link"),
        ("#section", False, "Fragment only"),
        ("", False, "Empty string"),
        ("   ", False, "Whitespace only"),
        ("data:text/plain,hello", False, "Data URL"),
        ("about:", False, "Browser protocol"),
        ("chrome://settings", False, "Browser URL"),
        ("file:///local/path", False, "File URL"),
        ("invalid-url", False, "Invalid domain"),
        ("http://", False, "Incomplete URL"),
        ("https://", False, "Incomplete URL")
    ]
    
    print(f"Testing {len(test_urls)} URLs...")
    print()
    
    passed = 0
    failed = 0
    
    for url, expected_valid, description in test_urls:
        try:
            is_valid = scraper._is_valid_crawlable_url(url, base_url)
            
            if is_valid == expected_valid:
                status = "✅ PASS"
                passed += 1
            else:
                status = "❌ FAIL"
                failed += 1
                
            expected_str = "VALID" if expected_valid else "INVALID"
            actual_str = "VALID" if is_valid else "INVALID"
            
            print(f"{status} {url:<40} | Expected: {expected_str:<7} | Actual: {actual_str:<7} | {description}")
            
        except Exception as e:
            print(f"❌ ERROR {url:<40} | Exception: {e}")
            failed += 1
    
    print()
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ All URL validation tests passed!")
        return True
    else:
        print(f"❌ {failed} test(s) failed!")
        return False

def test_problematic_scotties_urls():
    """Test specifically the URLs that caused Scotties to fail"""
    
    print(f"\n🔍 Testing Problematic URLs (Scotties case)")
    print("-" * 50)
    
    config = CompanyIntelligenceConfig()
    scraper = ConcurrentIntelligentScraperSync(config)
    
    base_url = "https://trivalleyathletics.org"
    
    # The problematic URLs from Scotties logs
    problematic_urls = [
        "internal",
        "external", 
        "#",
        "/",
        "javascript:void(0)",
        ""
    ]
    
    print("Testing URLs that caused Scotties to fail:")
    
    valid_count = 0
    for url in problematic_urls:
        is_valid = scraper._is_valid_crawlable_url(url, base_url)
        status = "⚠️ VALID" if is_valid else "✅ FILTERED"
        print(f"   {status}: '{url}'")
        
        if is_valid:
            valid_count += 1
    
    if valid_count == 0:
        print(f"\n✅ SUCCESS: All problematic URLs are now properly filtered!")
        print(f"This should fix the Scotties '0 pages scraped' issue.")
    else:
        print(f"\n⚠️ WARNING: {valid_count} problematic URLs still pass validation")
    
    return valid_count == 0

if __name__ == "__main__":
    print("🚀 URL VALIDATION FIX TEST")
    print("=" * 60)
    
    success1 = test_url_validation()
    success2 = test_problematic_scotties_urls()
    
    if success1 and success2:
        print(f"\n✅ URL VALIDATION FIX VERIFIED!")
        print(f"The fix should resolve the Scotties '0 pages scraped' issue")
        print(f"while preserving all existing search functionality.")
    else:
        print(f"\n❌ URL VALIDATION FIX NEEDS ATTENTION")
        print(f"Some tests failed - please review the validation logic.")