#!/usr/bin/env python3
"""
Test the retry mechanism for Nova Pro selection
"""

import sys
import os
import asyncio

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from src.antoine_selection import filter_valuable_links_sync

def test_retry_mechanism():
    """Test that retry triggers when fewer than 8 paths are selected"""
    
    # Test paths that Nova Pro might be too selective with
    test_paths = [
        "/",
        "/about",
        "/contact",
        "/products",
        "/careers",
        "/blog",
        "/news",
        "/investors",
        "/privacy",
        "/terms",
        "/login",
        "/signup",
        "/support",
        "/faq",
        "/sitemap"
    ]
    
    base_url = "https://example.com"
    
    print("=" * 80)
    print("TESTING RETRY MECHANISM")
    print("=" * 80)
    print(f"\nInput: {len(test_paths)} paths")
    print(f"Base URL: {base_url}")
    print(f"Initial confidence: 0.6")
    print(f"Retry threshold: 8 paths")
    print(f"Retry confidence: 0.3")
    
    # Run the selection
    result = filter_valuable_links_sync(
        test_paths,
        base_url,
        min_confidence=0.6,
        timeout_seconds=30
    )
    
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Success: {result.success}")
    print(f"Paths selected: {len(result.selected_paths)}")
    print(f"Final confidence used: {result.confidence_threshold}")
    print(f"Total cost: ${result.cost_usd:.4f}")
    
    if result.selected_paths:
        print("\nSelected paths:")
        for path in result.selected_paths:
            print(f"  - {path}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_retry_mechanism()