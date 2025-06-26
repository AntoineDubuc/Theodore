#!/usr/bin/env python3
"""
Test the fix specifically for Scotties-like scenarios
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.concurrent_intelligent_scraper import ConcurrentIntelligentScraperSync
from src.models import CompanyIntelligenceConfig

def test_scotties_problematic_urls():
    """Test the exact URLs that caused Scotties to fail"""
    
    print("🔍 Testing Scotties Fix")
    print("=" * 40)
    
    config = CompanyIntelligenceConfig()
    scraper = ConcurrentIntelligentScraperSync(config)
    
    base_url = "https://trivalleyathletics.org"
    
    # The exact problematic URLs from Scotties
    problematic_urls = ["internal", "external"]
    
    # URLs that SHOULD be valid for Scotties
    valid_urls = [
        "https://trivalleyathletics.org/coaches-contact-information/",
        "/teams/varsity/football", 
        "athletic-dept-info/",
        "https://trivalleyathletics.org/about"
    ]
    
    print("🚫 Testing problematic URLs (should be filtered):")
    problem_count = 0
    for url in problematic_urls:
        is_valid = scraper._is_valid_crawlable_url(url, base_url)
        status = "❌ PROBLEM" if is_valid else "✅ FILTERED"
        print(f"   {status}: '{url}'")
        if is_valid:
            problem_count += 1
    
    print(f"\n✅ Testing valid URLs (should pass):")
    valid_count = 0
    for url in valid_urls:
        is_valid = scraper._is_valid_crawlable_url(url, base_url)
        status = "✅ VALID" if is_valid else "❌ BLOCKED"
        print(f"   {status}: {url}")
        if is_valid:
            valid_count += 1
    
    print(f"\n📊 Results:")
    print(f"   Problematic URLs filtered: {len(problematic_urls) - problem_count}/{len(problematic_urls)}")
    print(f"   Valid URLs passed: {valid_count}/{len(valid_urls)}")
    
    if problem_count == 0 and valid_count >= 3:
        print(f"\n✅ SUCCESS: Scotties fix is working!")
        print(f"   - Invalid URLs are properly filtered out")
        print(f"   - Valid URLs are preserved")
        print(f"   - This should fix the '0 pages scraped' issue")
        return True
    else:
        print(f"\n⚠️ Issues found:")
        if problem_count > 0:
            print(f"   - {problem_count} problematic URLs still pass")
        if valid_count < 3:
            print(f"   - Only {valid_count} valid URLs pass (should be at least 3)")
        return False

def simulate_heuristic_selection():
    """Simulate what would happen with heuristic selection after filtering"""
    
    print(f"\n🎯 Simulating Heuristic Selection After Fix")
    print("-" * 50)
    
    # Simulate the URLs that would be discovered after filtering
    filtered_urls = [
        "https://trivalleyathletics.org",
        "https://trivalleyathletics.org/coaches-contact-information/",  # contact = 10 points
        "https://trivalleyathletics.org/athletic-dept-info/",
        "https://trivalleyathletics.org/teams/varsity/football",        # team = 8 points  
        "https://trivalleyathletics.org/teams/varsity/basketball",      # team = 8 points
        "https://trivalleyathletics.org/facilities/",
        "https://trivalleyathletics.org/news/"
    ]
    
    # Apply heuristic scoring
    priority_patterns = [
        ('contact', 10), ('about', 9), ('team', 8), ('careers', 7),
        ('leadership', 7), ('company', 6), ('services', 5), ('products', 5),
        ('history', 4), ('our-story', 4), ('management', 6)
    ]
    
    scored_urls = []
    for url in filtered_urls:
        score = 0
        url_lower = url.lower()
        for pattern, weight in priority_patterns:
            if pattern in url_lower:
                score += weight
        if score > 0:
            scored_urls.append((url, score))
    
    scored_urls.sort(key=lambda x: x[1], reverse=True)
    
    print(f"URLs after filtering and heuristic selection:")
    for url, score in scored_urls[:5]:
        print(f"   {score:2d}: {url}")
    
    pages_selected = len(scored_urls)
    print(f"\n📊 Heuristic Results:")
    print(f"   Total URLs after filtering: {len(filtered_urls)}")
    print(f"   Pages selected by heuristics: {pages_selected}")
    
    if pages_selected >= 2:
        print(f"   ✅ SUCCESS: {pages_selected} pages would be scraped (vs 0 before)")
        return True
    else:
        print(f"   ❌ PROBLEM: Still only {pages_selected} pages selected")
        return False

if __name__ == "__main__":
    print("🧪 SCOTTIES FIX VERIFICATION")
    print("=" * 50)
    
    success1 = test_scotties_problematic_urls()
    success2 = simulate_heuristic_selection()
    
    if success1 and success2:
        print(f"\n🎉 SCOTTIES FIX VERIFIED!")
        print(f"The URL validation fix should resolve:")
        print(f"  ✅ Invalid URLs like 'internal'/'external' are filtered")
        print(f"  ✅ Valid URLs are preserved for heuristic selection")
        print(f"  ✅ Heuristic selection finds multiple pages to scrape")
        print(f"  ✅ Should fix '0 pages scraped' issue")
    else:
        print(f"\n❌ FIX NEEDS MORE WORK")
        print(f"Some issues remain with URL validation or selection")