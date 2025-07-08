#!/usr/bin/env python3
"""
Test Rogers.com extraction to debug JSON parsing issue
"""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from src.antoine_discovery import discover_all_paths_sync
from src.antoine_selection import filter_valuable_links_sync

def test_rogers():
    """Test Rogers.com selection issue"""
    
    test_url = "https://www.rogers.com"
    
    print("=" * 80)
    print("ROGERS.COM SELECTION TEST")
    print("=" * 80)
    
    # Phase 1: Discovery
    print("\n📍 PHASE 1: DISCOVERY")
    discovery_result = discover_all_paths_sync(test_url, timeout_seconds=30)
    
    print(f"✅ Discovered {len(discovery_result.all_paths)} paths")
    
    # Show some sample paths
    print("\nSample paths:")
    for i, path in enumerate(discovery_result.all_paths[:10]):
        print(f"  {i+1}. {path}")
    
    # Phase 2: Selection
    print("\n📍 PHASE 2: SELECTION")
    selection_result = filter_valuable_links_sync(
        discovery_result.all_paths,
        test_url,
        min_confidence=0.6,
        timeout_seconds=60
    )
    
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Success: {selection_result.success}")
    
    if not selection_result.success:
        print(f"❌ Error: {selection_result.error}")
        
        # Save the prompt that was sent
        if selection_result.llm_prompt:
            with open('rogers_failed_prompt.txt', 'w') as f:
                f.write(selection_result.llm_prompt)
            print("\n💾 Failed prompt saved to: rogers_failed_prompt.txt")
    else:
        print(f"Paths selected: {len(selection_result.selected_paths)}")
        print(f"Confidence: {selection_result.confidence_threshold}")
        print(f"Cost: ${selection_result.cost_usd:.4f}")
        
        if selection_result.selected_paths:
            print("\nSelected paths:")
            for i, path in enumerate(selection_result.selected_paths[:10]):
                print(f"  {i+1}. {path}")

if __name__ == "__main__":
    test_rogers()