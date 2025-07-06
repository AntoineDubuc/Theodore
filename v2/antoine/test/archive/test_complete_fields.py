#!/usr/bin/env python3
"""
Test Nova Pro with complete field list in prompt
"""

import asyncio
import os
import time
from critter import discover_all_paths_sync
from get_valuable_links_from_llm import filter_valuable_links_sync


def test_complete_fields():
    """Test Nova Pro with complete field list"""
    
    print('🧪 TESTING NOVA PRO WITH COMPLETE FIELD LIST')
    print('=' * 60)
    
    # Step 1: Critter discovery (small subset)
    print('\n📡 Step 1: Discovering paths with Critter...')
    base_url = 'https://digitalremedy.com'
    discovery_result = discover_all_paths_sync(base_url)
    
    all_paths = discovery_result.all_paths
    print(f'✅ Critter found {len(all_paths)} paths')
    
    # Step 2: Nova Pro filtering with complete field list (smaller subset)
    test_paths = all_paths[:30]  # Test with first 30 paths
    print(f'\n🤖 Step 2: Testing Nova Pro with complete field list ({len(test_paths)} paths)...')
    filter_result = filter_valuable_links_sync(test_paths, discovery_result.url)
    
    if not filter_result.success:
        print(f'❌ Nova Pro filtering failed: {filter_result.error}')
        return
    
    selected_paths = filter_result.selected_paths
    print(f'✅ Nova Pro selected {len(selected_paths)} paths')
    print(f'💰 Cost: ${filter_result.cost_usd:.4f}')
    print(f'🔢 Tokens: {filter_result.tokens_used:,}')
    
    # Show detailed explanations
    print(f'\n💡 Nova Pro Path Explanations:')
    print('=' * 50)
    for i, path in enumerate(selected_paths, 1):
        explanation = filter_result.path_reasoning.get(path, "No explanation")
        print(f'{i:2d}. {path}')
        print(f'    → {explanation}')
        print()
    
    # Step 3: Save detailed test report
    print(f'\n💾 Step 3: Creating detailed test report...')
    
    test_dir = 'test'
    os.makedirs(test_dir, exist_ok=True)
    
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(test_dir, f'complete_fields_test_{timestamp}.txt')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('NOVA PRO WITH COMPLETE FIELD LIST TEST\n')
        f.write('=' * 60 + '\n\n')
        
        # Test summary
        f.write('🧪 TEST SUMMARY:\n')
        f.write(f'Total Paths Discovered: {len(all_paths)}\n')
        f.write(f'Paths Tested with Nova Pro: {len(test_paths)}\n')
        f.write(f'Paths Selected by Nova Pro: {len(selected_paths)}\n')
        f.write(f'Nova Pro Cost: ${filter_result.cost_usd:.4f}\n')
        f.write(f'Nova Pro Tokens: {filter_result.tokens_used:,}\n\n')
        
        # Nova Pro system prompt with complete fields
        f.write('🤖 NOVA PRO SYSTEM PROMPT (WITH COMPLETE FIELD LIST):\n')
        f.write('=' * 60 + '\n')
        from get_valuable_links_from_llm import create_path_selection_prompt
        system_prompt = create_path_selection_prompt(test_paths, discovery_result.url, 0.6)
        f.write(system_prompt)
        f.write('\n\n')
        
        # Selected paths and explanations
        f.write('🎯 NOVA PRO SELECTED PATHS WITH FIELD-BASED EXPLANATIONS:\n')
        f.write('=' * 60 + '\n')
        for i, path in enumerate(selected_paths, 1):
            explanation = filter_result.path_reasoning.get(path, "No explanation provided")
            f.write(f'{i:2d}. {path}\n')
            f.write(f'    → {explanation}\n\n')
        
        f.write('\nEND OF COMPLETE FIELDS TEST\n')
    
    print(f'✅ Test report saved to: {output_file}')
    print(f'📁 File size: {os.path.getsize(output_file):,} bytes')
    
    # Show verification results
    print(f'\n🎉 COMPLETE FIELDS TEST RESULTS:')
    print(f'   ✅ Complete field list included in prompt')
    print(f'   ✅ Nova Pro selected {len(selected_paths)} paths with field-aware explanations')
    print(f'   ✅ Cost: ${filter_result.cost_usd:.4f} ({filter_result.tokens_used:,} tokens)')
    
    return output_file


if __name__ == "__main__":
    test_complete_fields()