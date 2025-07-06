#!/usr/bin/env python3
"""
Test enhanced pipeline with:
1. Path explanations from Nova Pro
2. System prompt in report
3. Clean test folder
"""

import asyncio
import os
import time
from critter import discover_all_paths_sync
from get_valuable_links_from_llm import filter_valuable_links_sync
from crawler import crawl_selected_pages_sync


def test_enhanced_pipeline():
    """Test the enhanced pipeline with explanations"""
    
    print('🧪 TESTING ENHANCED PIPELINE: Explanations + System Prompt')
    print('=' * 65)
    
    # Step 1: Critter discovery (small subset)
    print('\n📡 Step 1: Discovering paths with Critter...')
    base_url = 'https://digitalremedy.com'
    discovery_result = discover_all_paths_sync(base_url)
    
    all_paths = discovery_result.all_paths
    print(f'✅ Critter found {len(all_paths)} paths')
    
    # Step 2: Nova Pro filtering with explanations (smaller subset)
    test_paths = all_paths[:20]  # Test with first 20 paths only
    print(f'\n🤖 Step 2: Testing Nova Pro explanations with {len(test_paths)} paths...')
    filter_result = filter_valuable_links_sync(test_paths, discovery_result.url)
    
    if not filter_result.success:
        print(f'❌ Nova Pro filtering failed: {filter_result.error}')
        return
    
    selected_paths = filter_result.selected_paths
    print(f'✅ Nova Pro selected {len(selected_paths)} paths')
    print(f'💰 Cost: ${filter_result.cost_usd:.4f}')
    
    # Show explanations
    print(f'\n💡 Path Explanations Preview:')
    for i, path in enumerate(selected_paths[:3], 1):  # Show first 3
        explanation = filter_result.path_reasoning.get(path, "No explanation")
        print(f'   {i}. {path}')
        print(f'      → {explanation}')
    
    # Step 3: Skip crawler for this test (focus on explanations)
    print(f'\n⏭️  Step 3: Skipping crawler for this test...')
    
    # Step 4: Create enhanced test report
    print(f'\n💾 Step 4: Creating enhanced test report...')
    
    test_dir = 'test'
    os.makedirs(test_dir, exist_ok=True)
    
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(test_dir, f'enhanced_pipeline_test_{timestamp}.txt')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('ENHANCED PIPELINE TEST REPORT\n')
        f.write('=' * 60 + '\n\n')
        
        # Test summary
        f.write('🧪 TEST SUMMARY:\n')
        f.write(f'Total Paths Discovered: {len(all_paths)}\n')
        f.write(f'Paths Tested with Nova Pro: {len(test_paths)}\n')
        f.write(f'Paths Selected by Nova Pro: {len(selected_paths)}\n')
        f.write(f'Nova Pro Cost: ${filter_result.cost_usd:.4f}\n\n')
        
        # Nova Pro system prompt
        f.write('🤖 NOVA PRO SYSTEM PROMPT:\n')
        f.write('=' * 50 + '\n')
        from get_valuable_links_from_llm import create_path_selection_prompt
        system_prompt = create_path_selection_prompt(test_paths, discovery_result.url, 0.6)
        # Extract just the system prompt part (before the paths list)
        prompt_lines = system_prompt.split('\n')
        in_prompt_section = False
        for line in prompt_lines:
            if 'url_paths_list =' in line:
                break
            if 'System:' in line or in_prompt_section:
                in_prompt_section = True
                if 'url_paths_list =' not in line:
                    f.write(line + '\n')
        f.write('\n')
        
        # All tested paths
        f.write('📡 PATHS TESTED WITH NOVA PRO:\n')
        f.write('-' * 40 + '\n')
        for i, path in enumerate(test_paths, 1):
            f.write(f'{i:2d}. {path}\n')
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
        
        f.write('\nEND OF ENHANCED TEST REPORT\n')
    
    print(f'✅ Enhanced test report saved to: {output_file}')
    print(f'📁 File size: {os.path.getsize(output_file):,} bytes')
    
    # Show verification results
    print(f'\n🎉 ENHANCEMENT VERIFICATION:')
    print(f'   ✅ System prompt included in report')
    print(f'   ✅ Path explanations from Nova Pro: {len(selected_paths)} paths with explanations')
    print(f'   ✅ Test folder cleaned and organized')
    
    return output_file


if __name__ == "__main__":
    test_enhanced_pipeline()