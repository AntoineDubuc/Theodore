#!/usr/bin/env python3
"""
Full Pipeline: Critter → Nova Pro → Crawler → Save
=================================================

Runs the complete pipeline for digitalremedy.com:
1. Critter: Discover all website paths
2. Nova Pro: Filter valuable paths using LLM
3. Crawler: Extract text content from selected pages
4. Save: Dump results to test folder
"""

import asyncio
import os
import time
from critter import discover_all_paths_sync
from get_valuable_links_from_llm import filter_valuable_links_sync
from crawler import crawl_selected_pages_sync


def run_full_pipeline():
    """Run the complete pipeline for digitalremedy.com"""
    
    print('🔍 FULL PIPELINE: Critter → Nova Pro → Crawler → Save')
    print('=' * 60)
    
    # Step 1: Critter discovery
    print('\n📡 Step 1: Discovering all paths with Critter...')
    base_url = 'https://cloudgeometry.com'
    discovery_result = discover_all_paths_sync(base_url)
    
    if discovery_result.errors:
        print(f'⚠️  Discovery errors: {len(discovery_result.errors)}')
        for error in discovery_result.errors[:2]:
            print(f'   - {error}')
    
    all_paths = discovery_result.all_paths
    print(f'✅ Critter found {len(all_paths)} paths')
    
    # Step 2: Nova Pro filtering
    print('\n🤖 Step 2: Filtering valuable paths with Nova Pro...')
    filter_result = filter_valuable_links_sync(all_paths, discovery_result.url)
    
    if not filter_result.success:
        print(f'❌ Nova Pro filtering failed: {filter_result.error}')
        return
    
    selected_paths = filter_result.selected_paths
    print(f'✅ Nova Pro selected {len(selected_paths)} paths')
    print(f'💰 Cost: ${filter_result.cost_usd:.4f}')
    
    # Step 3: Crawler extraction
    print('\n🕷️  Step 3: Crawling selected pages...')
    crawl_result = crawl_selected_pages_sync(
        base_url=discovery_result.url,
        selected_paths=selected_paths,
        timeout_seconds=30,
        max_content_per_page=10000,
        max_concurrent=5
    )
    
    print(f'✅ Crawled {crawl_result.successful_pages}/{crawl_result.total_pages} pages')
    print(f'📊 Total content: {crawl_result.total_content_length:,} characters')
    
    # Step 4: Save results
    print('\n💾 Step 4: Saving results...')
    
    # Create test directory
    test_dir = 'test'
    os.makedirs(test_dir, exist_ok=True)
    
    # Save comprehensive results
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(test_dir, f'cloudgeometry_full_pipeline_{timestamp}.txt')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('CLOUDGEOMETRY.COM FULL PIPELINE RESULTS\n')
        f.write('=' * 60 + '\n\n')
        
        # Pipeline summary
        f.write('📊 PIPELINE SUMMARY:\n')
        f.write(f'Base URL: {base_url}\n')
        f.write(f'Normalized URL: {discovery_result.url}\n')
        f.write(f'Discovery Time: {discovery_result.discovery_time:.2f}s\n')
        f.write(f'Total Paths Found: {len(all_paths)}\n')
        f.write(f'Paths Selected by Nova Pro: {len(selected_paths)}\n')
        f.write(f'Nova Pro Cost: ${filter_result.cost_usd:.4f}\n')
        f.write(f'Pages Successfully Crawled: {crawl_result.successful_pages}\n')
        f.write(f'Total Content Extracted: {crawl_result.total_content_length:,} characters\n')
        f.write(f'Total Pipeline Time: {discovery_result.discovery_time + filter_result.processing_time + crawl_result.total_crawl_time:.2f}s\n\n')
        
        # Nova Pro system prompt (show complete prompt with field list)
        f.write('🤖 NOVA PRO SYSTEM PROMPT (WITH COMPLETE FIELD LIST):\n')
        f.write('=' * 60 + '\n')
        from get_valuable_links_from_llm import create_path_selection_prompt
        system_prompt = create_path_selection_prompt(['[SAMPLE_PATHS]'], discovery_result.url, 0.6)  # Use placeholder
        # Show everything, replacing the sample paths with placeholder
        prompt_lines = system_prompt.split('\n')
        skip_until_steps = False
        for line in prompt_lines:
            if 'url_paths_list = [' in line:
                f.write('url_paths_list = [ALL_364_DISCOVERED_PATHS_HERE]\n')
                skip_until_steps = True
                continue
            elif skip_until_steps and line.startswith('Steps:'):
                skip_until_steps = False
                f.write('\n' + line + '\n')
                continue
            elif skip_until_steps:
                # Skip the sample paths content
                continue
            else:
                f.write(line + '\n')
        f.write('\n')
        
        # All discovered paths (input to Nova Pro)
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
        
        # Nova Pro path explanations
        f.write('💡 NOVA PRO PATH EXPLANATIONS:\n')
        f.write('-' * 45 + '\n')
        for i, path in enumerate(selected_paths, 1):
            explanation = filter_result.path_reasoning.get(path, "No explanation provided")
            f.write(f'{i:2d}. {path}\n')
            f.write(f'    → {explanation}\n\n')
        f.write('\n')
        
        # Crawled content
        f.write('🕷️  EXTRACTED CONTENT:\n')
        f.write('=' * 60 + '\n\n')
        f.write(crawl_result.aggregated_content)
        
        f.write('\n\nEND OF PIPELINE RESULTS\n')
    
    print(f'✅ Results saved to: {output_file}')
    print(f'📁 File size: {os.path.getsize(output_file):,} bytes')
    
    # Show summary
    print('\n🎉 PIPELINE COMPLETED SUCCESSFULLY!')
    print(f'   Critter: {len(all_paths)} paths discovered')
    print(f'   Nova Pro: {len(selected_paths)} paths selected (${filter_result.cost_usd:.4f})')
    print(f'   Crawler: {crawl_result.successful_pages} pages extracted')
    print(f'   Output: {output_file}')
    
    return output_file


if __name__ == "__main__":
    run_full_pipeline()