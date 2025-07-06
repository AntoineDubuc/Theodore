#!/usr/bin/env python3
"""
Test fixes for:
1. Including all discovered paths in report
2. Using markdown (visible text only) instead of HTML
"""

import asyncio
import os
import time
from critter import discover_all_paths_sync
from get_valuable_links_from_llm import filter_valuable_links_sync
from crawler import crawl_selected_pages_sync


def test_fixes():
    """Test the fixes with a small subset"""
    
    print('🧪 TESTING FIXES: Input Paths + Text-Only Extraction')
    print('=' * 60)
    
    # Step 1: Critter discovery (small subset)
    print('\n📡 Step 1: Discovering paths with Critter...')
    base_url = 'https://digitalremedy.com'
    discovery_result = discover_all_paths_sync(base_url)
    
    all_paths = discovery_result.all_paths
    print(f'✅ Critter found {len(all_paths)} paths')
    
    # Show first 10 paths as sample
    print(f'\n📋 Sample discovered paths (first 10):')
    for i, path in enumerate(all_paths[:10], 1):
        print(f'   {i:2d}. {path}')
    if len(all_paths) > 10:
        print(f'   ... and {len(all_paths) - 10} more')
    
    # Step 2: Nova Pro filtering (smaller subset for testing)
    test_paths = all_paths[:50]  # Test with first 50 paths only
    print(f'\n🤖 Step 2: Testing Nova Pro with {len(test_paths)} paths...')
    filter_result = filter_valuable_links_sync(test_paths, discovery_result.url)
    
    if not filter_result.success:
        print(f'❌ Nova Pro filtering failed: {filter_result.error}')
        return
    
    selected_paths = filter_result.selected_paths
    print(f'✅ Nova Pro selected {len(selected_paths)} paths')
    print(f'💰 Cost: ${filter_result.cost_usd:.4f}')
    
    # Step 3: Test crawler with just 2 pages
    test_crawl_paths = selected_paths[:2]  # Just test 2 pages
    print(f'\n🕷️  Step 3: Testing crawler with {len(test_crawl_paths)} pages...')
    crawl_result = crawl_selected_pages_sync(
        base_url=discovery_result.url,
        selected_paths=test_crawl_paths,
        timeout_seconds=30,
        max_content_per_page=5000,  # Smaller for testing
        max_concurrent=2
    )
    
    print(f'✅ Crawled {crawl_result.successful_pages}/{crawl_result.total_pages} pages')
    print(f'📊 Total content: {crawl_result.total_content_length:,} characters')
    
    # Step 4: Verify text-only extraction
    print(f'\n🔍 Step 4: Verifying text-only extraction...')
    if crawl_result.page_results:
        sample_page = crawl_result.page_results[0]
        sample_content = sample_page.content[:500]
        
        # Check for HTML tags
        html_tags_found = '<' in sample_content and '>' in sample_content
        if html_tags_found:
            print(f'⚠️  HTML tags still found in content!')
            print(f'Sample content: {sample_content}')
        else:
            print(f'✅ Clean text extraction confirmed (no HTML tags)')
            print(f'Sample content: {sample_content}')
    
    # Step 5: Create test report
    print(f'\n💾 Step 5: Creating test report...')
    
    test_dir = 'test'
    os.makedirs(test_dir, exist_ok=True)
    
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(test_dir, f'test_fixes_{timestamp}.txt')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('TEST FIXES REPORT\n')
        f.write('=' * 60 + '\n\n')
        
        # Test summary
        f.write('🧪 TEST SUMMARY:\n')
        f.write(f'Total Paths Discovered: {len(all_paths)}\n')
        f.write(f'Paths Tested with Nova Pro: {len(test_paths)}\n')
        f.write(f'Paths Selected by Nova Pro: {len(selected_paths)}\n')
        f.write(f'Pages Crawled: {crawl_result.successful_pages}\n')
        f.write(f'Text-Only Extraction: {"✅ Success" if not html_tags_found else "❌ Failed"}\n\n')
        
        # FIX 1: All discovered paths (input to Nova Pro)
        f.write('📡 ALL DISCOVERED PATHS (INPUT TO NOVA PRO):\n')
        f.write('-' * 50 + '\n')
        for i, path in enumerate(all_paths, 1):
            f.write(f'{i:3d}. {path}\n')
        f.write('\n')
        
        # Nova Pro selected paths
        f.write('🎯 NOVA PRO SELECTED PATHS:\n')
        f.write('-' * 40 + '\n')
        for i, path in enumerate(selected_paths, 1):
            f.write(f'{i:2d}. {path}\n')
        f.write('\n')
        
        # FIX 2: Extracted content (should be text-only)
        f.write('🕷️  EXTRACTED CONTENT (TEXT-ONLY):\n')
        f.write('=' * 60 + '\n\n')
        f.write(crawl_result.aggregated_content)
        
        f.write('\n\nEND OF TEST REPORT\n')
    
    print(f'✅ Test report saved to: {output_file}')
    print(f'📁 File size: {os.path.getsize(output_file):,} bytes')
    
    # Show verification results
    print(f'\n🎉 FIX VERIFICATION RESULTS:')
    print(f'   ✅ Fix 1: All {len(all_paths)} discovered paths included in report')
    print(f'   {"✅" if not html_tags_found else "❌"} Fix 2: Text-only extraction (no HTML tags)')
    
    return output_file


if __name__ == "__main__":
    test_fixes()