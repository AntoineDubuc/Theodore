#!/usr/bin/env python3
"""
Test the timeout fix with Rogers and Telus
"""

import sys
import os
import json
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from src.antoine_discovery import discover_all_paths_sync
from src.antoine_selection import filter_valuable_links_sync

def test_company(company_name, company_url):
    """Test a company with the new timeout and path filtering"""
    
    print(f"\n{'='*80}")
    print(f"TESTING: {company_name}")
    print(f"URL: {company_url}")
    print(f"{'='*80}")
    
    # Phase 1: Discovery
    print("\n📍 PHASE 1: DISCOVERY")
    start_time = time.time()
    discovery_result = discover_all_paths_sync(company_url, timeout_seconds=30)
    discovery_time = time.time() - start_time
    
    print(f"✅ Discovered {len(discovery_result.all_paths)} paths in {discovery_time:.1f}s")
    
    # Show if path filtering will be applied
    if len(discovery_result.all_paths) > 500:
        print(f"⚠️  Path filtering will be applied (> 500 paths)")
    
    # Phase 2: Selection
    print("\n📍 PHASE 2: SELECTION")
    start_time = time.time()
    selection_result = filter_valuable_links_sync(
        discovery_result.all_paths,
        company_url,
        min_confidence=0.6,
        timeout_seconds=60  # Using new 60 second timeout
    )
    selection_time = time.time() - start_time
    
    print(f"\n📊 RESULTS:")
    print(f"Success: {selection_result.success}")
    print(f"Selection time: {selection_time:.1f}s")
    
    if selection_result.success:
        print(f"Paths selected: {len(selection_result.selected_paths)}")
        print(f"Tokens used: {selection_result.tokens_used:,}")
        print(f"Cost: ${selection_result.cost_usd:.4f}")
        
        # Show first 5 selected paths
        if selection_result.selected_paths:
            print("\nFirst 5 selected paths:")
            for i, path in enumerate(selection_result.selected_paths[:5]):
                print(f"  {i+1}. {path}")
    else:
        print(f"❌ Error: {selection_result.error}")
    
    return {
        'company': company_name,
        'url': company_url,
        'paths_discovered': len(discovery_result.all_paths),
        'success': selection_result.success,
        'paths_selected': len(selection_result.selected_paths) if selection_result.success else 0,
        'selection_time': selection_time,
        'error': selection_result.error if not selection_result.success else None
    }

def main():
    """Test Rogers and Telus with the timeout fix"""
    
    print("TESTING TIMEOUT FIX FOR LARGE WEBSITES")
    print("=" * 80)
    print("Changes implemented:")
    print("1. Increased Nova Pro timeout from 30s to 60s")
    print("2. Filter to first-level paths when > 500 paths discovered")
    print("=" * 80)
    
    # Test companies
    test_companies = [
        ("Rogers Communications", "https://www.rogers.com"),
        ("Telus", "https://www.telus.com"),
        ("Bell", "https://www.bell.ca")  # Added Bell as another test
    ]
    
    results = []
    for company_name, company_url in test_companies:
        result = test_company(company_name, company_url)
        results.append(result)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    for result in results:
        status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
        print(f"\n{result['company']}: {status}")
        print(f"  - Paths discovered: {result['paths_discovered']}")
        print(f"  - Paths selected: {result['paths_selected']}")
        print(f"  - Selection time: {result['selection_time']:.1f}s")
        if not result['success']:
            print(f"  - Error: {result['error']}")
    
    # Save results
    with open('timeout_fix_test_results.json', 'w') as f:
        json.dump({
            'test_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: timeout_fix_test_results.json")

if __name__ == "__main__":
    main()