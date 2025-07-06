#!/usr/bin/env python3
"""
Walmart.com Comprehensive Fallback Analysis
============================================

Runs the complete pipeline on Walmart.com and provides detailed analysis:
1. LLM Prompt sent to Nova Pro (complete Target Information Profile)
2. All discovered paths/pages from Critter
3. LLM-selected paths with explanations
4. Detailed extraction results showing which tool was used for each page
5. Full extracted text content for each page

This script tests the fallback system on a major retail website to compare
performance against tech services (CloudGeometry) and validate scalability.
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
    print('🛒 WALMART.COM COMPREHENSIVE FALLBACK ANALYSIS')
    print('=' * 80)
    print(f'Start Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 80)
    
    domain = 'walmart.com'
    base_url = f'https://www.{domain}'
    
    print(f'🎯 Target Domain: {domain}')
    print(f'🌐 Base URL: {base_url}')
    print(f'🏪 Website Type: Major Retail E-commerce')
    print(f'📊 Expected Scale: Large (1000+ paths likely)')
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
        
        # Analysis of path types for retail site
        product_paths = len([p for p in discovered_paths if any(x in p.lower() for x in ['/product', '/item', '/browse', '/shop', '/category'])])
        corporate_paths = len([p for p in discovered_paths if any(x in p.lower() for x in ['/about', '/corporate', '/investor', '/career', '/news', '/sustainability'])])
        
        print(f'📈 Path Analysis:')
        print(f'   🛍️  Product/Shopping paths: {product_paths}')
        print(f'   🏢 Corporate paths: {corporate_paths}')
        print(f'   📄 Other paths: {len(discovered_paths) - product_paths - corporate_paths}')
        print()
        
        # Show sample paths
        print('📄 Sample discovered paths (first 15):')
        for i, path in enumerate(discovered_paths[:15], 1):
            print(f'   {i:2d}. {path}')
        if len(discovered_paths) > 15:
            print(f'   ... and {len(discovered_paths) - 15} more paths')
        print()
        
    except Exception as e:
        print(f'❌ Path discovery failed: {e}')
        return
    
    # ========================================================================
    # PHASE 2: LLM PATH SELECTION
    # ========================================================================
    print('🧠 PHASE 2: NOVA PRO LLM PATH SELECTION')
    print('-' * 60)
    print('🎯 Focus: Corporate intelligence paths for company analysis')
    print('🚫 Expected filtering: Product/shopping paths should be excluded')
    print()
    
    selection_start = time.time()
    try:
        selection_result = filter_valuable_links_sync(
            discovered_paths, 
            base_url, 
            min_confidence=0.6,
            timeout_seconds=60  # Longer timeout for large path list
        )
        selection_time = time.time() - selection_start
        
        if selection_result.success:
            print(f'✅ LLM selection completed in {selection_time:.2f} seconds')
            print(f'🤖 Model: {selection_result.model_used}')
            print(f'💰 Cost: ${selection_result.cost_usd:.4f}')
            print(f'🔢 Tokens: {selection_result.tokens_used:,}')
            print(f'📊 Selected: {len(selection_result.selected_paths)} paths from {len(discovered_paths)} total')
            print(f'📉 Rejection rate: {((len(discovered_paths) - len(selection_result.selected_paths)) / len(discovered_paths) * 100):.1f}%')
            print()
            
            # Analyze selected path types
            selected_corporate = len([p for p in selection_result.selected_paths if any(x in p.lower() for x in ['/about', '/corporate', '/investor', '/career', '/news', '/sustainability'])])
            selected_product = len([p for p in selection_result.selected_paths if any(x in p.lower() for x in ['/product', '/item', '/browse', '/shop'])])
            
            print(f'🔍 SELECTION QUALITY ANALYSIS:')
            print(f'   🏢 Corporate paths selected: {selected_corporate}/{len(selection_result.selected_paths)}')
            print(f'   🛍️  Product paths selected: {selected_product}/{len(selection_result.selected_paths)}')
            print(f'   ✅ Corporate focus: {"EXCELLENT" if selected_corporate >= selected_product else "NEEDS IMPROVEMENT"}')
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
    print('🔬 Testing fallback performance on major retail website architecture')
    print('📈 Expected: More complex pages may trigger more fallbacks than CloudGeometry')
    print()
    
    extraction_start = time.time()
    try:
        crawl_result = crawl_selected_pages_sync(
            base_url=base_url,
            selected_paths=selection_result.selected_paths,
            timeout_seconds=30,
            max_content_per_page=15000,  # Allow larger content for detailed analysis
            max_concurrent=3  # Conservative for large retail site
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
        print(f'   📈 Trafilatura: {trafilatura_count} pages ({trafilatura_count/crawl_result.total_pages*100:.1f}%)')
        print(f'   🔄 BeautifulSoup Fallback: {beautifulsoup_count} pages ({beautifulsoup_count/crawl_result.total_pages*100:.1f}%)')
        print(f'   ❌ Failed: {failed_count} pages ({failed_count/crawl_result.total_pages*100:.1f}%)')
        
        fallback_rate = beautifulsoup_count / crawl_result.total_pages * 100 if crawl_result.total_pages > 0 else 0
        print(f'   📊 Fallback usage rate: {fallback_rate:.1f}%')
        
        if fallback_rate > 30:
            print(f'   🔍 ANALYSIS: High fallback rate suggests complex retail site architecture')
        elif fallback_rate > 15:
            print(f'   ✅ ANALYSIS: Moderate fallback rate - system adapting well')
        else:
            print(f'   ⭐ ANALYSIS: Low fallback rate - excellent primary extraction')
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
    report_filename = f'walmart_comprehensive_fallback_analysis_{timestamp}.txt'
    
    try:
        with open(report_filename, 'w', encoding='utf-8') as f:
            # Report Header
            f.write('WALMART.COM COMPREHENSIVE FALLBACK ANALYSIS REPORT\\n')
            f.write('=' * 80 + '\\n\\n')
            f.write(f'Domain: {domain}\\n')
            f.write(f'Base URL: {base_url}\\n')
            f.write(f'Website Type: Major Retail E-commerce\\n')
            f.write(f'Analysis Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\\n')
            f.write(f'Total Analysis Time: {total_time:.2f} seconds\\n')
            f.write('\\n')
            
            # Executive Summary
            f.write('EXECUTIVE SUMMARY\\n')
            f.write('-' * 40 + '\\n')
            f.write(f'Total Paths Discovered: {len(discovered_paths)}\\n')
            f.write(f'Paths Selected by Nova Pro: {len(selection_result.selected_paths)}\\n')
            f.write(f'Selection Efficiency: {(len(selection_result.selected_paths)/len(discovered_paths)*100):.2f}%\\n')
            f.write(f'Successful Content Extractions: {crawl_result.successful_pages}\\n')
            f.write(f'Pages Using Fallback: {beautifulsoup_count}\\n')
            f.write(f'Fallback Usage Rate: {fallback_rate:.1f}%\\n')
            f.write(f'Total Content Extracted: {crawl_result.total_content_length:,} characters\\n')
            f.write(f'Nova Pro Cost: ${selection_result.cost_usd:.4f}\\n')
            f.write('\\n')
            
            # Comparison with CloudGeometry
            f.write('COMPARISON WITH CLOUDGEOMETRY RESULTS\\n')
            f.write('-' * 40 + '\\n')
            f.write('CloudGeometry (Tech Services):\\n')
            f.write('  - Paths discovered: 304\\n')
            f.write('  - Paths selected: 8\\n')
            f.write('  - Fallback usage: 25%\\n')
            f.write('  - Content extracted: 15,145 chars\\n\\n')
            f.write(f'Walmart (Retail E-commerce):\\n')
            f.write(f'  - Paths discovered: {len(discovered_paths)}\\n')
            f.write(f'  - Paths selected: {len(selection_result.selected_paths)}\\n')
            f.write(f'  - Fallback usage: {fallback_rate:.1f}%\\n')
            f.write(f'  - Content extracted: {crawl_result.total_content_length:,} chars\\n\\n')
            
            # Phase 1: Discovery Results
            f.write('PHASE 1: PATH DISCOVERY RESULTS\\n')
            f.write('=' * 40 + '\\n')
            f.write(f'Discovery Method: Critter (Sitemap + Robots.txt + Header/Footer)\\n')
            f.write(f'Discovery Time: {discovery_time:.2f} seconds\\n')
            f.write(f'Total Paths Found: {len(discovered_paths)}\\n')
            f.write(f'Product/Shopping Paths: {product_paths}\\n')
            f.write(f'Corporate Paths: {corporate_paths}\\n')
            f.write(f'Other Paths: {len(discovered_paths) - product_paths - corporate_paths}\\n\\n')
            
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
            f.write(f'Selected: {len(selection_result.selected_paths)} paths\\n')
            f.write(f'Rejection Rate: {((len(discovered_paths) - len(selection_result.selected_paths)) / len(discovered_paths) * 100):.1f}%\\n\\n')
            
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
            f.write(f'Fallback Usage Rate: {fallback_rate:.1f}%\\n')
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
            f.write('\\n\\nEND OF WALMART COMPREHENSIVE FALLBACK ANALYSIS REPORT\\n')
        
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
    print(f'🏪 Website: Walmart.com (Major Retail E-commerce)')
    print(f'📊 Scale: {len(discovered_paths)} paths discovered vs CloudGeometry\'s 304')
    print(f'🎯 LLM Selection: {len(selection_result.selected_paths)} paths chosen for ${selection_result.cost_usd:.4f}')
    print(f'📄 Content Extraction: {crawl_result.successful_pages}/{crawl_result.total_pages} pages, {crawl_result.total_content_length:,} chars')
    print(f'🔄 Fallback Usage: {beautifulsoup_count} pages ({fallback_rate:.1f}% vs CloudGeometry\'s 25%)')
    print(f'⏱️ Total Time: {total_time:.2f} seconds')
    print(f'📋 Report File: {report_filename}')
    print()
    
    print('🔍 Key Insights:')
    if fallback_rate > 30:
        print(f'• High fallback rate indicates Walmart\'s complex retail architecture')
    elif fallback_rate < 15:
        print(f'• Low fallback rate shows excellent primary extraction on retail site')
    else:
        print(f'• Moderate fallback rate demonstrates system adaptability')
    
    if len(discovered_paths) > 500:
        print(f'• Large-scale path discovery validates system scalability')
    
    print(f'• Corporate path selection quality: {"EXCELLENT" if selected_corporate >= selected_product else "NEEDS REVIEW"}')
    print()
    print('✅ WALMART COMPREHENSIVE FALLBACK ANALYSIS COMPLETED SUCCESSFULLY!')

if __name__ == '__main__':
    main()