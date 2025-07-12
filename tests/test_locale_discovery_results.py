#!/usr/bin/env python3
"""
Locale Discovery Results Test
=============================

Comprehensive test to validate locale-specific discovery performance and quality
before implementing changes to production /antoine code.

This script provides concrete data on:
1. Locale detection accuracy
2. Discovery performance improvements  
3. Path quality comparisons
4. Nova Pro acceptance rates
5. Compatibility with existing sites

Run this script to get proof-of-concept results before approving production changes.
"""

import sys
import os
import time
import re
from typing import Optional, Dict, List
from urllib.parse import urlparse

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load env vars
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(env_path)

from src.antoine_discovery import discover_all_paths_sync
from src.antoine_selection import filter_valuable_links_sync


def extract_locale_from_url(url: str) -> Optional[str]:
    """
    Extract locale identifier from URL.
    
    Args:
        url: URL to analyze
        
    Returns:
        Locale string (e.g., 'en-ca', 'fr-fr') or None if no locale found
    """
    if not url:
        return None
    
    # Parse URL to get path
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    # Common locale patterns to look for
    locale_patterns = [
        # Standard locale codes (language-country)
        r'/([a-z]{2}-[a-z]{2})/',           # /en-ca/, /fr-fr/
        r'/([a-z]{2}-[a-z]{2})$',          # /en-ca
        r'/([a-z]{2}_[a-z]{2})/',          # /en_ca/
        r'/([a-z]{2}_[a-z]{2})$',          # /en_ca
        
        # Language only
        r'/([a-z]{2})/',                   # /en/, /fr/
        r'/([a-z]{2})$',                   # /en, /fr
        
        # Extended locale codes  
        r'/([a-z]{2}-[a-z]{3})/',          # /en-usa/
        r'/([a-z]{3}-[a-z]{2})/',          # /eng-ca/
    ]
    
    # Check each pattern
    for pattern in locale_patterns:
        match = re.search(pattern, path)
        if match:
            locale = match.group(1)
            
            # Validate it looks like a real locale
            if len(locale) >= 2 and not locale.isdigit():
                # Normalize underscores to hyphens
                return locale.replace('_', '-')
    
    return None


class LocaleDiscoveryTester:
    """Test locale-specific discovery performance and quality."""
    
    def __init__(self):
        self.test_results = {
            'locale_detection': {},
            'performance_comparison': {},
            'path_quality': {},
            'nova_acceptance': {},
            'compatibility': {}
        }
    
    def test_locale_detection_accuracy(self):
        """Test locale extraction from various URL patterns."""
        print("🔍 TESTING LOCALE DETECTION ACCURACY")
        print("=" * 60)
        
        test_cases = [
            # International automotive sites
            ("https://www.volvocars.com/en-ca/", "en-ca"),
            ("https://www.bmw.com/en-us/", "en-us"),
            ("https://www.mercedes-benz.com/fr-fr/", "fr-fr"),
            ("https://www.toyota.com/en-gb/", "en-gb"),
            
            # No locale sites
            ("https://stripe.com", None),
            ("https://linear.app", None),
            ("https://github.com", None),
            
            # Various locale patterns
            ("https://example.com/fr/about", "fr"),
            ("https://site.com/de-de/", "de-de"),
            ("https://company.com/en_us/", "en-us"),
            ("https://brand.com/pt-br/contact", "pt-br"),
            
            # Edge cases
            ("https://api.com/v1/", None),
            ("https://docs.com/2024/", None),
            ("https://subdomain.example.com/en-ca/", "en-ca"),
        ]
        
        correct = 0
        total = len(test_cases)
        
        for url, expected in test_cases:
            detected = extract_locale_from_url(url)
            is_correct = detected == expected
            
            status = "✅" if is_correct else "❌"
            print(f"{status} {url:45} → Expected: {str(expected):8} | Detected: {str(detected):8}")
            
            if is_correct:
                correct += 1
        
        accuracy = (correct / total) * 100
        print(f"\n📊 LOCALE DETECTION ACCURACY: {correct}/{total} ({accuracy:.1f}%)")
        
        self.test_results['locale_detection'] = {
            'accuracy_percent': accuracy,
            'correct': correct,
            'total': total,
            'test_cases': test_cases
        }
        
        return accuracy >= 90  # 90%+ accuracy required
    
    def test_volvo_discovery_performance(self):
        """Compare Volvo Canada discovery: global vs locale-filtered."""
        print(f"\n🚗 TESTING VOLVO CANADA DISCOVERY PERFORMANCE")
        print("=" * 60)
        
        volvo_url = "https://www.volvocars.com/en-ca/"
        detected_locale = extract_locale_from_url(volvo_url)
        
        print(f"URL: {volvo_url}")
        print(f"Detected locale: {detected_locale}")
        
        # Test 1: Current approach (no locale filter)
        print(f"\n🌍 Test 1: Global Discovery (Current Approach)")
        print("-" * 40)
        
        start_time = time.time()
        try:
            global_result = discover_all_paths_sync(volvo_url, timeout_seconds=30)
            global_time = time.time() - start_time
            global_success = True
            global_paths = len(global_result.all_paths) if global_result.all_paths else 0
            
            print(f"⏱️  Time: {global_time:.1f}s")
            print(f"✅ Success: {global_success}")
            print(f"📊 Paths found: {global_paths}")
            
        except Exception as e:
            global_time = time.time() - start_time
            global_success = False
            global_paths = 0
            
            print(f"⏱️  Time: {global_time:.1f}s (timeout)")
            print(f"❌ Success: {global_success}")
            print(f"📊 Paths found: {global_paths}")
            print(f"🚫 Error: {str(e)[:100]}...")
        
        # Test 2: Proposed approach (with locale filter)
        print(f"\n🇨🇦 Test 2: Locale Discovery (Proposed Approach)")
        print("-" * 40)
        
        start_time = time.time()
        try:
            locale_result = discover_all_paths_sync(
                volvo_url, 
                locale_filter=detected_locale,
                timeout_seconds=30
            )
            locale_time = time.time() - start_time
            locale_success = True
            locale_paths = len(locale_result.all_paths) if locale_result.all_paths else 0
            
            print(f"⏱️  Time: {locale_time:.1f}s")
            print(f"✅ Success: {locale_success}")
            print(f"📊 Paths found: {locale_paths}")
            
            # Show sample paths
            if locale_result.all_paths:
                print(f"\n📋 Sample paths:")
                for i, path in enumerate(locale_result.all_paths[:10]):
                    print(f"   {i+1:2d}. {path}")
                if len(locale_result.all_paths) > 10:
                    print(f"   ... and {len(locale_result.all_paths) - 10} more")
            
        except Exception as e:
            locale_time = time.time() - start_time
            locale_success = False
            locale_paths = 0
            
            print(f"⏱️  Time: {locale_time:.1f}s")
            print(f"❌ Success: {locale_success}")
            print(f"📊 Paths found: {locale_paths}")
            print(f"🚫 Error: {str(e)[:100]}...")
        
        # Performance comparison
        print(f"\n📈 PERFORMANCE COMPARISON")
        print("-" * 40)
        
        if global_time > 0:
            speed_improvement = global_time / locale_time if locale_time > 0 else float('inf')
        else:
            speed_improvement = 0
        
        success_improvement = locale_success and not global_success
        path_improvement = locale_paths - global_paths
        
        print(f"⚡ Speed improvement: {speed_improvement:.1f}x faster")
        print(f"✅ Success improvement: {success_improvement}")
        print(f"📊 Path count improvement: +{path_improvement} paths")
        
        # Store results
        self.test_results['performance_comparison'] = {
            'global_time': global_time,
            'locale_time': locale_time,
            'global_success': global_success,
            'locale_success': locale_success,
            'global_paths': global_paths,
            'locale_paths': locale_paths,
            'speed_improvement': speed_improvement,
            'success_improvement': success_improvement,
            'path_improvement': path_improvement
        }
        
        return locale_success and locale_paths > global_paths
    
    def test_path_quality_analysis(self):
        """Analyze quality of discovered paths."""
        print(f"\n📋 TESTING PATH QUALITY ANALYSIS")
        print("=" * 60)
        
        # Use a simpler international site for this test
        test_url = "https://www.bmw.com/en-us/"
        detected_locale = extract_locale_from_url(test_url)
        
        print(f"URL: {test_url}")
        print(f"Detected locale: {detected_locale}")
        
        try:
            # Test with locale filter
            result = discover_all_paths_sync(
                test_url,
                locale_filter=detected_locale,
                timeout_seconds=20
            )
            
            if not result.all_paths:
                print("❌ No paths discovered")
                return False
            
            print(f"✅ Discovered {len(result.all_paths)} paths")
            
            # Analyze path relevance
            relevant_patterns = [
                '/about', '/contact', '/careers', '/company', '/news',
                '/vehicles', '/cars', '/models', '/services', '/dealers'
            ]
            
            relevant_paths = []
            irrelevant_paths = []
            locale_paths = []
            
            for path in result.all_paths:
                path_lower = path.lower()
                
                # Check if contains locale
                if detected_locale and detected_locale in path_lower:
                    locale_paths.append(path)
                
                # Check relevance
                if any(pattern in path_lower for pattern in relevant_patterns):
                    relevant_paths.append(path)
                else:
                    irrelevant_paths.append(path)
            
            print(f"\n📊 PATH QUALITY ANALYSIS:")
            print(f"   🎯 Relevant paths: {len(relevant_paths)} ({len(relevant_paths)/len(result.all_paths)*100:.1f}%)")
            print(f"   🌍 Locale-specific paths: {len(locale_paths)} ({len(locale_paths)/len(result.all_paths)*100:.1f}%)")
            print(f"   🗂️  Total paths: {len(result.all_paths)}")
            
            print(f"\n📋 Sample relevant paths:")
            for i, path in enumerate(relevant_paths[:8]):
                print(f"   {i+1:2d}. {path}")
            
            self.test_results['path_quality'] = {
                'total_paths': len(result.all_paths),
                'relevant_paths': len(relevant_paths),
                'locale_paths': len(locale_paths),
                'relevance_percent': len(relevant_paths)/len(result.all_paths)*100,
                'locale_percent': len(locale_paths)/len(result.all_paths)*100
            }
            
            return len(relevant_paths) > 0
            
        except Exception as e:
            print(f"❌ Path quality test failed: {e}")
            return False
    
    def test_nova_pro_acceptance(self):
        """Test Nova Pro acceptance rate with different path sets."""
        print(f"\n🤖 TESTING NOVA PRO ACCEPTANCE RATES")
        print("=" * 60)
        
        # Test with a set of manually curated paths
        test_website = "https://www.volvocars.com"
        
        # Test set 1: Generic corporate paths (what fallback currently uses)
        generic_paths = [
            "/", "/about", "/about-us", "/company", "/contact", 
            "/careers", "/products", "/services", "/news"
        ]
        
        # Test set 2: Locale-specific paths (what locale discovery would find)
        locale_paths = [
            "/en-ca", "/en-ca/about", "/en-ca/cars", "/en-ca/contact-us",
            "/en-ca/dealers", "/en-ca/sustainability", "/en-ca/safety", "/en-ca/careers"
        ]
        
        print(f"Testing Nova Pro with {len(generic_paths)} generic paths...")
        
        try:
            generic_result = filter_valuable_links_sync(
                generic_paths,
                test_website,
                min_confidence=0.4,
                timeout_seconds=30
            )
            
            generic_selected = len(generic_result.selected_paths) if generic_result.success else 0
            generic_acceptance = (generic_selected / len(generic_paths)) * 100
            
            print(f"✅ Generic paths - Selected: {generic_selected}/{len(generic_paths)} ({generic_acceptance:.1f}%)")
            
        except Exception as e:
            print(f"❌ Generic path test failed: {e}")
            generic_selected = 0
            generic_acceptance = 0
        
        print(f"\nTesting Nova Pro with {len(locale_paths)} locale-specific paths...")
        
        try:
            locale_result = filter_valuable_links_sync(
                locale_paths,
                test_website,
                min_confidence=0.4,
                timeout_seconds=30
            )
            
            locale_selected = len(locale_result.selected_paths) if locale_result.success else 0
            locale_acceptance = (locale_selected / len(locale_paths)) * 100
            
            print(f"✅ Locale paths - Selected: {locale_selected}/{len(locale_paths)} ({locale_acceptance:.1f}%)")
            
            if locale_result.selected_paths:
                print(f"\n📋 Selected locale paths:")
                for i, path in enumerate(locale_result.selected_paths):
                    print(f"   {i+1:2d}. {path}")
            
        except Exception as e:
            print(f"❌ Locale path test failed: {e}")
            locale_selected = 0
            locale_acceptance = 0
        
        print(f"\n📊 NOVA PRO ACCEPTANCE COMPARISON:")
        print(f"   🔢 Generic paths: {generic_acceptance:.1f}% acceptance")
        print(f"   🇨🇦 Locale paths: {locale_acceptance:.1f}% acceptance")
        
        improvement = locale_acceptance - generic_acceptance
        print(f"   📈 Improvement: +{improvement:.1f} percentage points")
        
        self.test_results['nova_acceptance'] = {
            'generic_acceptance': generic_acceptance,
            'locale_acceptance': locale_acceptance,
            'improvement': improvement,
            'generic_selected': generic_selected,
            'locale_selected': locale_selected
        }
        
        return locale_acceptance >= generic_acceptance
    
    def test_compatibility_with_existing_sites(self):
        """Test that locale detection doesn't break existing non-international sites."""
        print(f"\n🔧 TESTING COMPATIBILITY WITH EXISTING SITES")
        print("=" * 60)
        
        # Sites that should NOT have locale detection
        non_locale_sites = [
            "https://stripe.com",
            "https://linear.app", 
            "https://github.com"
        ]
        
        compatibility_results = []
        
        for site in non_locale_sites:
            print(f"\nTesting: {site}")
            
            # Check locale detection
            detected_locale = extract_locale_from_url(site)
            locale_correct = detected_locale is None
            
            print(f"   Locale detected: {detected_locale} (should be None)")
            print(f"   ✅ Correct: {locale_correct}")
            
            # Test discovery still works
            try:
                start_time = time.time()
                result = discover_all_paths_sync(site, timeout_seconds=15)
                discovery_time = time.time() - start_time
                
                paths_found = len(result.all_paths) if result.all_paths else 0
                discovery_success = paths_found > 0
                
                print(f"   Discovery: {discovery_success} ({paths_found} paths in {discovery_time:.1f}s)")
                
                compatibility_results.append({
                    'site': site,
                    'locale_correct': locale_correct,
                    'discovery_success': discovery_success,
                    'paths_found': paths_found,
                    'discovery_time': discovery_time
                })
                
            except Exception as e:
                print(f"   ❌ Discovery failed: {str(e)[:50]}...")
                compatibility_results.append({
                    'site': site,
                    'locale_correct': locale_correct,
                    'discovery_success': False,
                    'paths_found': 0,
                    'discovery_time': 0
                })
        
        # Summary
        locale_accuracy = sum(1 for r in compatibility_results if r['locale_correct'])
        discovery_success = sum(1 for r in compatibility_results if r['discovery_success'])
        
        print(f"\n📊 COMPATIBILITY RESULTS:")
        print(f"   🎯 Locale detection accuracy: {locale_accuracy}/{len(non_locale_sites)}")
        print(f"   ✅ Discovery success: {discovery_success}/{len(non_locale_sites)}")
        
        self.test_results['compatibility'] = {
            'sites_tested': len(non_locale_sites),
            'locale_accuracy': locale_accuracy,
            'discovery_success': discovery_success,
            'results': compatibility_results
        }
        
        return locale_accuracy == len(non_locale_sites) and discovery_success >= len(non_locale_sites) * 0.8
    
    def run_all_tests(self):
        """Run complete test suite and provide summary results."""
        print("🧪 LOCALE DISCOVERY TEST SUITE")
        print("=" * 80)
        print("Testing locale-specific discovery before production implementation")
        print("=" * 80)
        
        # Run all tests
        tests = [
            ("Locale Detection Accuracy", self.test_locale_detection_accuracy),
            ("Volvo Performance Comparison", self.test_volvo_discovery_performance),
            ("Path Quality Analysis", self.test_path_quality_analysis),
            ("Nova Pro Acceptance Rates", self.test_nova_pro_acceptance),
            ("Compatibility Testing", self.test_compatibility_with_existing_sites)
        ]
        
        test_results = []
        
        for test_name, test_func in tests:
            print(f"\n" + "🔬" + " " * 10 + f"RUNNING: {test_name}")
            try:
                success = test_func()
                test_results.append((test_name, success))
                status = "✅ PASSED" if success else "❌ FAILED"
                print(f"\n{status}: {test_name}")
            except Exception as e:
                test_results.append((test_name, False))
                print(f"\n❌ ERROR: {test_name} - {e}")
        
        # Final summary
        self.print_final_summary(test_results)
        
        return all(result for _, result in test_results)
    
    def print_final_summary(self, test_results):
        """Print comprehensive test results summary."""
        print(f"\n" + "=" * 80)
        print("🎯 FINAL TEST RESULTS SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        print(f"📊 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        print()
        
        for test_name, success in test_results:
            status = "✅" if success else "❌"
            print(f"{status} {test_name}")
        
        print(f"\n📈 KEY PERFORMANCE METRICS:")
        
        # Locale detection
        locale_data = self.test_results.get('locale_detection', {})
        if locale_data:
            print(f"   🎯 Locale Detection: {locale_data.get('accuracy_percent', 0):.1f}% accuracy")
        
        # Performance improvement
        perf_data = self.test_results.get('performance_comparison', {})
        if perf_data:
            speed_imp = perf_data.get('speed_improvement', 0)
            path_imp = perf_data.get('path_improvement', 0)
            print(f"   ⚡ Volvo Canada: {speed_imp:.1f}x faster, +{path_imp} paths discovered")
        
        # Path quality
        quality_data = self.test_results.get('path_quality', {})
        if quality_data:
            relevance = quality_data.get('relevance_percent', 0)
            print(f"   📋 Path Quality: {relevance:.1f}% relevance rate")
        
        # Nova Pro acceptance
        nova_data = self.test_results.get('nova_acceptance', {})
        if nova_data:
            improvement = nova_data.get('improvement', 0)
            print(f"   🤖 Nova Pro: +{improvement:.1f}% better acceptance rate")
        
        print(f"\n💡 RECOMMENDATION:")
        if passed >= total * 0.8:  # 80%+ pass rate
            print("   ✅ APPROVE: Locale discovery shows significant improvements")
            print("   📈 Ready to implement in production /antoine code")
            print("   🚀 Expected benefits: Faster discovery, better path quality, higher Nova Pro acceptance")
        else:
            print("   ⚠️  REVIEW: Some tests failed - investigate before production")
            print("   🔧 Address failing tests before implementing in /antoine")
        
        print("=" * 80)


def main():
    """Run the complete locale discovery test suite."""
    tester = LocaleDiscoveryTester()
    
    print("This test provides concrete data before modifying production /antoine code.")
    print("Results will show performance improvements and validate the concept.\n")
    
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 ALL TESTS PASSED - Locale discovery ready for production!")
    else:
        print("\n⚠️ SOME TESTS FAILED - Review results before proceeding")
    
    return success


if __name__ == "__main__":
    main()