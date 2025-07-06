#!/usr/bin/env python3
"""
Test to verify the complete field list shows up in the report
"""

import os
import time


def test_prompt_display():
    """Test prompt display with complete field list"""
    
    print('🔍 TESTING PROMPT DISPLAY WITH COMPLETE FIELD LIST')
    print('=' * 60)
    
    # Create test report with fixed prompt extraction
    test_dir = 'test'
    os.makedirs(test_dir, exist_ok=True)
    
    # Clean up first
    for file in os.listdir(test_dir):
        if file.endswith('.txt'):
            os.remove(os.path.join(test_dir, file))
    
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(test_dir, f'prompt_display_test_{timestamp}.txt')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('PROMPT DISPLAY TEST\n')
        f.write('=' * 60 + '\n\n')
        
        # Test the fixed prompt extraction logic
        f.write('🤖 NOVA PRO SYSTEM PROMPT (WITH COMPLETE FIELD LIST):\n')
        f.write('=' * 60 + '\n')
        from get_valuable_links_from_llm import create_path_selection_prompt
        system_prompt = create_path_selection_prompt(['[SAMPLE_PATHS]'], 'example.com', 0.6)
        
        # Show everything, replacing the sample paths with placeholder
        prompt_lines = system_prompt.split('\n')
        skip_until_steps = False
        for line in prompt_lines:
            if 'url_paths_list = [' in line:
                f.write('url_paths_list = [ALL_DISCOVERED_PATHS_HERE]\n')
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
        
        f.write('END OF PROMPT DISPLAY TEST\n')
    
    print(f'✅ Test report saved to: {output_file}')
    print(f'📁 File size: {os.path.getsize(output_file):,} bytes')
    
    # Check if field list is included
    with open(output_file, 'r') as f:
        content = f.read()
        
    has_field_list = 'Core Company Info' in content
    has_business_model = 'Business Model & Classification' in content
    has_tech_metadata = 'Technical Metadata' in content
    
    print(f'\n🔍 Field List Verification:')
    print(f'   {"✅" if has_field_list else "❌"} Core Company Info section')
    print(f'   {"✅" if has_business_model else "❌"} Business Model & Classification section')
    print(f'   {"✅" if has_tech_metadata else "❌"} Technical Metadata section')
    
    if has_field_list and has_business_model and has_tech_metadata:
        print(f'\n🎉 SUCCESS: Complete field list is properly displayed!')
    else:
        print(f'\n❌ ISSUE: Field list is not complete in the display')
    
    return output_file, has_field_list and has_business_model and has_tech_metadata


if __name__ == "__main__":
    test_prompt_display()