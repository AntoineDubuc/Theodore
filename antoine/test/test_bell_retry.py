#!/usr/bin/env python3
"""
Test Bell.ca with retry mechanism
"""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from src.antoine_discovery import discover_all_paths_sync
from src.antoine_selection import filter_valuable_links_sync

def test_bell_with_retry():
    """Test Bell.ca selection with retry mechanism"""
    
    test_url = "https://www.bell.ca"
    
    print("=" * 80)
    print("BELL.CA SELECTION WITH RETRY TEST")
    print("=" * 80)
    
    # Phase 1: Discovery
    print("\n📍 PHASE 1: DISCOVERY")
    discovery_result = discover_all_paths_sync(test_url, timeout_seconds=30)
    
    print(f"✅ Discovered {len(discovery_result.all_paths)} paths")
    
    # Show some sample paths
    print("\nSample paths:")
    for i, path in enumerate(discovery_result.all_paths[:10]):
        print(f"  {i+1}. {path}")
    
    # Phase 2: Selection with retry
    print("\n📍 PHASE 2: SELECTION (WITH RETRY)")
    selection_result = filter_valuable_links_sync(
        discovery_result.all_paths,
        test_url,
        min_confidence=0.6,
        timeout_seconds=60  # Increased timeout for retry
    )
    
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print(f"Success: {selection_result.success}")
    print(f"Paths selected: {len(selection_result.selected_paths)}")
    print(f"Final confidence: {selection_result.confidence_threshold}")
    print(f"Total tokens: {selection_result.tokens_used}")
    print(f"Total cost: ${selection_result.cost_usd:.4f}")
    
    if selection_result.selected_paths:
        print("\nSelected paths:")
        for i, path in enumerate(selection_result.selected_paths[:20]):
            print(f"  {i+1}. {path}")
        if len(selection_result.selected_paths) > 20:
            print(f"  ... and {len(selection_result.selected_paths) - 20} more")
    else:
        print("\n⚠️  No paths selected even with retry!")
        
    # Save results
    with open('bell_retry_test_results.json', 'w') as f:
        json.dump({
            'url': test_url,
            'paths_discovered': len(discovery_result.all_paths),
            'paths_selected': len(selection_result.selected_paths),
            'selected_paths': selection_result.selected_paths,
            'confidence_used': selection_result.confidence_threshold,
            'success': selection_result.success,
            'error': selection_result.error if not selection_result.success else None
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: bell_retry_test_results.json")

if __name__ == "__main__":
    test_bell_with_retry()