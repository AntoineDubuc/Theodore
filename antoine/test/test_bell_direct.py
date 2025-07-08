#!/usr/bin/env python3
"""
Direct test of Bell.ca extraction using antoine modules
"""

import sys
import os
import json
import asyncio
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Import antoine components directly
from src.antoine_discovery import discover_all_paths_sync
from src.antoine_selection import filter_valuable_links_sync
from src.antoine_crawler import crawl_selected_pages_sync
from src.antoine_extraction import extract_company_fields

def test_bell_extraction():
    """Test Bell.ca extraction using antoine 4-phase pipeline"""
    print("\n" + "="*80)
    print("BELL.CA DIRECT EXTRACTION TEST")
    print("="*80)
    
    test_url = "https://www.bell.ca"
    company_name = "Bell"
    
    print(f"\n🔍 Testing extraction for: {test_url}")
    print(f"Company name: {company_name}")
    
    # Phase 1: Discovery
    print("\n" + "-"*60)
    print("PHASE 1: DISCOVERY")
    print("-"*60)
    
    try:
        discovery_result = discover_all_paths_sync(test_url, timeout_seconds=30)
        
        print(f"✅ Discovery completed:")
        print(f"   - Total paths found: {len(discovery_result.all_paths)}")
        print(f"   - Navigation paths: {len(discovery_result.navigation_paths)}")
        print(f"   - Content paths: {len(discovery_result.content_paths)}")
        print(f"   - Restricted paths: {len(discovery_result.restricted_paths)}")
        
        # Show some discovered paths
        print(f"\n📄 Sample paths discovered:")
        for i, path in enumerate(discovery_result.all_paths[:10]):
            print(f"   {i+1}. {path}")
        
        if len(discovery_result.all_paths) > 10:
            print(f"   ... and {len(discovery_result.all_paths) - 10} more")
            
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Phase 2: Selection
    print("\n" + "-"*60)
    print("PHASE 2: SELECTION")
    print("-"*60)
    
    try:
        selection_result = filter_valuable_links_sync(
            discovery_result.all_paths,
            test_url,
            min_confidence=0.6,
            timeout_seconds=30
        )
        
        print(f"✅ Selection completed:")
        print(f"   - Links selected: {len(selection_result.selected_paths)}")
        print(f"   - Processing time: {selection_result.processing_time:.2f}s")
        
        print(f"\n🎯 Selected paths:")
        for i, path in enumerate(selection_result.selected_paths):
            print(f"   {i+1}. {path}")
        
        if not selection_result.selected_paths:
            print("\n⚠️  WARNING: No paths selected by Nova Pro even after retry!")
            print("The retry mechanism should have been triggered automatically.")
            
    except Exception as e:
        print(f"❌ Selection failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Phase 3: Crawling
    print("\n" + "-"*60)
    print("PHASE 3: CRAWLING")
    print("-"*60)
    
    try:
        crawl_result = crawl_selected_pages_sync(
            test_url,
            selection_result.selected_paths,
            timeout_seconds=30,
            max_concurrent=5
        )
        
        print(f"✅ Crawling completed:")
        print(f"   - Pages crawled successfully: {crawl_result.successful_pages}")
        print(f"   - Pages failed: {crawl_result.failed_pages}")
        print(f"   - Total content length: {len(crawl_result.aggregated_content)} chars")
        print(f"   - Processing time: {crawl_result.total_crawl_time:.2f}s")
        
        # Save aggregated content
        with open('test_bell_aggregated_content.txt', 'w', encoding='utf-8') as f:
            f.write(crawl_result.aggregated_content)
        print(f"   - Content saved to: test_bell_aggregated_content.txt")
        
        # Show page results
        print(f"\n📄 Page crawl results:")
        if hasattr(crawl_result, 'page_results'):
            for page_result in crawl_result.page_results:
                if page_result.success:
                    print(f"   ✅ {page_result.url}: {len(page_result.content)} chars")
                else:
                    print(f"   ❌ {page_result.url}: {page_result.error}")
            
    except Exception as e:
        print(f"❌ Crawling failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Phase 4: Extraction
    print("\n" + "-"*60)
    print("PHASE 4: EXTRACTION")
    print("-"*60)
    
    try:
        extraction_result = extract_company_fields(
            crawl_result,
            company_name,
            timeout_seconds=60
        )
        
        print(f"✅ Extraction completed:")
        print(f"   - Success: {extraction_result.success}")
        print(f"   - Fields extracted: {len(extraction_result.extracted_fields)}")
        print(f"   - Processing time: {extraction_result.processing_time:.2f}s")
        
        # Show extracted fields
        print(f"\n📊 Extracted Fields:")
        for field, value in extraction_result.extracted_fields.items():
            if value and value != "Not found" and value != [] and value != {}:
                print(f"   ✅ {field}: {value}")
            else:
                print(f"   ❌ {field}: Empty/Not found")
        
        # Save full result
        with open('test_bell_extraction_result.json', 'w') as f:
            json.dump({
                'url': test_url,
                'company_name': company_name,
                'discovery': {
                    'total_paths': len(discovery_result.all_paths),
                    'navigation_paths': len(discovery_result.navigation_paths),
                    'content_paths': len(discovery_result.content_paths),
                    'restricted_paths': len(discovery_result.restricted_paths)
                },
                'selection': {
                    'selected_paths': selection_result.selected_paths,
                    'count': len(selection_result.selected_paths)
                },
                'crawling': {
                    'successful_pages': crawl_result.successful_pages,
                    'failed_pages': crawl_result.failed_pages,
                    'content_length': len(crawl_result.aggregated_content)
                },
                'extraction': {
                    'success': extraction_result.success,
                    'extracted_fields': extraction_result.extracted_fields,
                    'error': extraction_result.error
                }
            }, f, indent=2)
        print(f"\n💾 Full result saved to: test_bell_extraction_result.json")
        
        # Also save Nova response if available
        if hasattr(extraction_result, 'nova_response'):
            with open('test_bell_nova_response.txt', 'w') as f:
                f.write(str(extraction_result.nova_response))
            print(f"💾 Nova response saved to: test_bell_nova_response.txt")
            
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    test_bell_extraction()