#!/usr/bin/env python3
"""
CloudGeometry Comprehensive Fallback Analysis
==============================================

Runs the complete pipeline on CloudGeometry.com and provides detailed analysis:
1. LLM Prompt sent to Nova Pro (complete Target Information Profile)
2. All discovered paths/pages from Critter
3. LLM-selected paths with explanations
4. Detailed extraction results showing which tool was used for each page
5. Full extracted text content for each page

This script provides complete transparency into the fallback system operation.
"""

import asyncio
import time
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from critter import discover_all_paths_sync
from get_valuable_links_from_llm import filter_valuable_links_sync
from crawler import crawl_selected_pages_sync

def main():
    print('🧪 CLOUDGEOMETRY COMPREHENSIVE FALLBACK ANALYSIS')
    print('=' * 80)
    print(f'Start Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 80)
    
    domain = 'cloudgeometry.com'
    base_url = f'https://www.{domain}'
    
    print(f'🎯 Target Domain: {domain}')
    print(f'🌐 Base URL: {base_url}')
    print()
    
    # ========================================================================
    # PHASE 1: PATH DISCOVERY
    # ========================================================================
    print('📍 PHASE 1: COMPREHENSIVE PATH DISCOVERY')
    print('-' * 60)
    
    discovery_start = time.time()
    try:
        discovery_result = discover_all_paths_sync(base_url)
        discovered_paths = discovery_result.all_paths
        discovery_time = time.time() - discovery_start
        
        print(f'✅ Discovery completed in {discovery_time:.2f} seconds')
        print(f'📊 Total paths discovered: {len(discovered_paths)}')
        print()
        
        # Show sample paths
        print('📄 Sample discovered paths (first 10):')
        for i, path in enumerate(discovered_paths[:10], 1):
            print(f'   {i:2d}. {path}')
        if len(discovered_paths) > 10:
            print(f'   ... and {len(discovered_paths) - 10} more paths')
        print()
        
    except Exception as e:
        print(f'❌ Path discovery failed: {e}')
        return
    
    # ========================================================================
    # PHASE 2: LLM PATH SELECTION
    # ========================================================================
    print('🧠 PHASE 2: NOVA PRO LLM PATH SELECTION')
    print('-' * 60)
    
    selection_start = time.time()
    try:
        selection_result = filter_valuable_links_sync(
            discovered_paths, 
            base_url, 
            min_confidence=0.6,
            timeout_seconds=45
        )
        selection_time = time.time() - selection_start
        
        if selection_result.success:
            print(f'✅ LLM selection completed in {selection_time:.2f} seconds')
            print(f'🤖 Model: {selection_result.model_used}')
            print(f'💰 Cost: ${selection_result.cost_usd:.4f}')
            print(f'🔢 Tokens: {selection_result.tokens_used:,}')
            print(f'📊 Selected: {len(selection_result.selected_paths)} paths from {len(discovered_paths)} total')
            print()
            
            print('🎯 SELECTED PATHS WITH NOVA PRO EXPLANATIONS:')
            for i, path in enumerate(selection_result.selected_paths, 1):
                explanation = selection_result.path_reasoning.get(path, 'No explanation provided')
                print(f'   {i:2d}. {path}')
                print(f'       💡 Nova Pro reasoning: {explanation}')
            print()
            
        else:
            print(f'❌ LLM selection failed: {selection_result.error}')
            return
            
    except Exception as e:
        print(f'❌ LLM selection failed with exception: {e}')
        return
    
    # ========================================================================
    # PHASE 3: CONTENT EXTRACTION WITH FALLBACK
    # ========================================================================
    print('📄 PHASE 3: CONTENT EXTRACTION WITH FALLBACK SYSTEM')
    print('-' * 60)
    
    extraction_start = time.time()
    try:
        crawl_result = crawl_selected_pages_sync(
            base_url=base_url,
            selected_paths=selection_result.selected_paths,
            timeout_seconds=30,
            max_content_per_page=15000,  # Allow larger content for detailed analysis
            max_concurrent=3
        )
        extraction_time = time.time() - extraction_start
        
        print(f'✅ Content extraction completed in {extraction_time:.2f} seconds')
        print(f'📊 Success rate: {crawl_result.successful_pages}/{crawl_result.total_pages} pages')
        print(f'📝 Total content: {crawl_result.total_content_length:,} characters')
        print(f'⚡ Avg per page: {extraction_time/crawl_result.total_pages:.2f}s')
        print()
        
        # Analyze extraction methods used
        trafilatura_count = 0
        beautifulsoup_count = 0
        failed_count = 0
        
        for page_result in crawl_result.page_results:
            if page_result.success:
                if page_result.extraction_method == 'trafilatura':
                    trafilatura_count += 1
                elif page_result.extraction_method == 'beautifulsoup_fallback':
                    beautifulsoup_count += 1
            else:
                failed_count += 1
        
        print('🔧 EXTRACTION METHOD ANALYSIS:')
        print(f'   📈 Trafilatura: {trafilatura_count} pages')
        print(f'   🔄 BeautifulSoup Fallback: {beautifulsoup_count} pages')
        print(f'   ❌ Failed: {failed_count} pages')
        print()
        
        # Show individual page results
        print('📄 INDIVIDUAL PAGE EXTRACTION RESULTS:')
        print('-' * 60)
        for i, page_result in enumerate(crawl_result.page_results, 1):
            page_name = page_result.url.split('/')[-1] or 'home'
            status = '✅' if page_result.success else '❌'
            method = page_result.extraction_method.upper() if page_result.extraction_method else 'UNKNOWN'
            
            print(f'{i:2d}. {page_name} [{method}] {status}')
            print(f'    URL: {page_result.url}')
            print(f'    Content: {page_result.content_length:,} chars in {page_result.crawl_time:.2f}s')
            
            if page_result.error:
                print(f'    Error: {page_result.error}')
            
            if page_result.success and page_result.content:
                # Show content preview
                preview = page_result.content[:200] + '...' if len(page_result.content) > 200 else page_result.content
                print(f'    Preview: {preview}')
            
            print()
        
    except Exception as e:
        print(f'❌ Content extraction failed: {e}')
        return
    
    # ========================================================================
    # PHASE 4: COMPREHENSIVE REPORT GENERATION
    # ========================================================================
    print('📋 PHASE 4: GENERATING COMPREHENSIVE REPORT')
    print('-' * 60)
    
    total_time = discovery_time + selection_time + extraction_time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f'cloudgeometry_comprehensive_fallback_analysis_{timestamp}.txt'
    
    try:
        with open(report_filename, 'w', encoding='utf-8') as f:
            # Report Header
            f.write('CLOUDGEOMETRY COMPREHENSIVE FALLBACK ANALYSIS REPORT\\n')
            f.write('=' * 80 + '\\n\\n')
            f.write(f'Domain: {domain}\\n')
            f.write(f'Base URL: {base_url}\\n')
            f.write(f'Analysis Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\\n')
            f.write(f'Total Analysis Time: {total_time:.2f} seconds\\n')
            f.write('\\n')
            
            # Executive Summary
            f.write('EXECUTIVE SUMMARY\\n')
            f.write('-' * 40 + '\\n')
            f.write(f'Total Paths Discovered: {len(discovered_paths)}\\n')
            f.write(f'Paths Selected by Nova Pro: {len(selection_result.selected_paths)}\\n')
            f.write(f'Successful Content Extractions: {crawl_result.successful_pages}\\n')
            f.write(f'Pages Using Fallback: {beautifulsoup_count}\\n')
            f.write(f'Total Content Extracted: {crawl_result.total_content_length:,} characters\\n')
            f.write(f'Nova Pro Cost: ${selection_result.cost_usd:.4f}\\n')
            f.write('\\n')
            
            # Phase 1: Discovery Results
            f.write('PHASE 1: PATH DISCOVERY RESULTS\\n')
            f.write('=' * 40 + '\\n')
            f.write(f'Discovery Method: Critter (Sitemap + Robots.txt + Header/Footer)\\n')
            f.write(f'Discovery Time: {discovery_time:.2f} seconds\\n')
            f.write(f'Total Paths Found: {len(discovered_paths)}\\n\\n')
            
            f.write('ALL DISCOVERED PATHS:\\n')
            f.write('-' * 30 + '\\n')
            for i, path in enumerate(discovered_paths, 1):
                f.write(f'{i:3d}. {path}\\n')
            f.write('\\n')
            
            # Phase 2: LLM Selection Results
            f.write('PHASE 2: NOVA PRO LLM SELECTION RESULTS\\n')
            f.write('=' * 40 + '\\n')
            f.write(f'LLM Model: {selection_result.model_used}\\n')
            f.write(f'Selection Time: {selection_time:.2f} seconds\\n')
            f.write(f'Tokens Used: {selection_result.tokens_used:,}\\n')
            f.write(f'Cost: ${selection_result.cost_usd:.4f}\\n')
            f.write(f'Confidence Threshold: {selection_result.confidence_threshold}\\n')
            f.write(f'Selected: {len(selection_result.selected_paths)} paths\\n\\n')
            
            # Show the complete LLM prompt
            f.write('COMPLETE LLM PROMPT SENT TO NOVA PRO:\\n')
            f.write('-' * 50 + '\\n')
            if selection_result.llm_prompt:
                f.write(selection_result.llm_prompt)
                f.write('\\n\\n')
            else:
                f.write('[LLM prompt not captured]\\n\\n')
            
            f.write('NOVA PRO SELECTED PATHS WITH EXPLANATIONS:\\n')
            f.write('-' * 50 + '\\n')
            for i, path in enumerate(selection_result.selected_paths, 1):
                explanation = selection_result.path_reasoning.get(path, 'No explanation provided')
                f.write(f'{i:2d}. {path}\\n')
                f.write(f'    Nova Pro Reasoning: {explanation}\\n\\n')
            
            # Phase 3: Extraction Results
            f.write('PHASE 3: CONTENT EXTRACTION RESULTS\\n')
            f.write('=' * 40 + '\\n')
            f.write(f'Extraction Time: {extraction_time:.2f} seconds\\n')
            f.write(f'Success Rate: {crawl_result.successful_pages}/{crawl_result.total_pages}\\n')
            f.write(f'Total Content Length: {crawl_result.total_content_length:,} characters\\n')
            f.write(f'Trafilatura Extractions: {trafilatura_count}\\n')
            f.write(f'BeautifulSoup Fallback Extractions: {beautifulsoup_count}\\n')
            f.write(f'Failed Extractions: {failed_count}\\n\\n')
            
            # Detailed page results
            f.write('DETAILED PAGE EXTRACTION RESULTS:\\n')
            f.write('=' * 50 + '\\n\\n')
            
            for i, page_result in enumerate(crawl_result.page_results, 1):
                page_name = page_result.url.split('/')[-1] or 'home'
                f.write(f'PAGE {i}: {page_name.upper()}\\n')
                f.write(f'URL: {page_result.url}\\n')
                f.write(f'Extraction Method: {page_result.extraction_method.upper()}\\n')
                f.write(f'Success: {"YES" if page_result.success else "NO"}\\n')
                f.write(f'Content Length: {page_result.content_length:,} characters\\n')
                f.write(f'Extraction Time: {page_result.crawl_time:.2f} seconds\\n')
                f.write(f'Title: {page_result.title or "No title"}\\n')
                
                if page_result.error:
                    f.write(f'Error: {page_result.error}\\n')
                
                f.write('\\n')
                
                if page_result.success and page_result.content:
                    f.write('EXTRACTED CONTENT:\\n')
                    f.write('-' * 40 + '\\n')
                    f.write(page_result.content)
                    f.write('\\n')
                else:
                    f.write('NO CONTENT EXTRACTED\\n')
                
                f.write('\\n' + '=' * 80 + '\\n\\n')
            
            # Full aggregated content
            f.write('FULL AGGREGATED CONTENT FROM ALL PAGES:\\n')
            f.write('=' * 50 + '\\n\\n')
            f.write(crawl_result.aggregated_content)
            f.write('\\n\\nEND OF COMPREHENSIVE FALLBACK ANALYSIS REPORT\\n')
        
        file_size = os.path.getsize(report_filename)
        print(f'✅ Comprehensive report generated: {report_filename}')
        print(f'📁 Report size: {file_size:,} bytes')
        print()
        
    except Exception as e:
        print(f'❌ Report generation failed: {e}')
        return
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print('🎯 FINAL ANALYSIS SUMMARY')
    print('=' * 80)
    print(f'✅ Path Discovery: {len(discovered_paths)} paths found in {discovery_time:.2f}s')
    print(f'🤖 LLM Selection: {len(selection_result.selected_paths)} paths chosen for ${selection_result.cost_usd:.4f}')
    print(f'📄 Content Extraction: {crawl_result.successful_pages}/{crawl_result.total_pages} pages, {crawl_result.total_content_length:,} chars')
    print(f'🔄 Fallback Usage: {beautifulsoup_count} pages used BeautifulSoup fallback')
    print(f'⏱️ Total Time: {total_time:.2f} seconds')
    print(f'📋 Report File: {report_filename}')
    print()
    
    print('The comprehensive analysis shows:')
    print(f'• Complete transparency into Nova Pro path selection reasoning')
    print(f'• Detailed extraction method tracking (Trafilatura vs BeautifulSoup)')
    print(f'• Full content extraction results for each page')
    print(f'• Performance metrics and cost analysis')
    print()
    print('✅ COMPREHENSIVE FALLBACK ANALYSIS COMPLETED SUCCESSFULLY!')

if __name__ == '__main__':
    main()