#!/usr/bin/env python3
"""
CloudGeometry Parallel Pipeline Test (10 Concurrent)
===================================================

Tests the complete Theodore pipeline on CloudGeometry.com with REAL data
and increased parallelism (10 concurrent pages vs previous 3).

Measures performance improvement from increased parallel crawling.

1. Critter discovers actual paths from cloudgeometry.com
2. Nova Pro LLM selects valuable paths using get_valuable_links_from_llm.py
3. Crawler extracts real content with 10 concurrent pages (increased from 3)
4. Field extraction processes actual crawled content with operational metadata
5. Comprehensive performance comparison report

NO MOCK DATA. ONLY REAL PIPELINE EXECUTION WITH ENHANCED PARALLELISM.
"""

import sys
import os
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from critter import discover_all_paths_sync
    from get_valuable_links_from_llm import filter_valuable_links_sync
    from crawler import crawl_selected_pages_sync
    from distill_out_fields import extract_company_fields_sync
    MODULES_AVAILABLE = True
    print("✅ All pipeline modules imported successfully")
except ImportError as e:
    print(f"❌ Failed to import pipeline modules: {e}")
    MODULES_AVAILABLE = False


def main():
    """Execute the complete real Theodore pipeline with increased parallelism"""
    
    print("🚀 CLOUDGEOMETRY PARALLEL PIPELINE EXECUTION (10 CONCURRENT)")
    print("=" * 80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔄 INCREASED PARALLELISM: max_concurrent=10 (vs previous 3)")
    print("=" * 80)
    
    if not MODULES_AVAILABLE:
        print("❌ Required modules not available. Cannot run pipeline.")
        return
    
    domain = 'cloudgeometry.com'
    base_url = f'https://www.{domain}'
    
    print(f"🎯 Target: {base_url}")
    print(f"📊 Pipeline: Critter → Nova Pro → Crawler (10x parallel) → Field Extraction")
    print(f"⚠️ Using REAL data only - no mocks or simulations")
    print()
    
    # Store all results for comprehensive analysis
    pipeline_results = {
        'domain': domain,
        'base_url': base_url,
        'start_time': time.time(),
        'test_type': 'parallel_performance_test',
        'max_concurrent': 10,
        'previous_max_concurrent': 3,
        'phases': {}
    }
    
    # ========================================================================
    # PHASE 1: REAL CRITTER PATH DISCOVERY
    # ========================================================================
    print("🔍 PHASE 1: REAL CRITTER PATH DISCOVERY")
    print("-" * 60)
    print(f"🌐 Discovering all paths from {base_url}")
    print("📋 Sources: robots.txt + sitemap.xml + navigation crawling")
    print()
    
    phase1_start = time.time()
    try:
        discovery_result = discover_all_paths_sync(base_url)
        discovered_paths = discovery_result.all_paths
        phase1_time = time.time() - phase1_start
        
        print(f"✅ Critter discovery completed in {phase1_time:.2f} seconds")
        print(f"📊 Total paths discovered: {len(discovered_paths)}")
        print()
        
        # Show sample paths
        print("📄 Sample discovered paths (first 15):")
        for i, path in enumerate(discovered_paths[:15], 1):
            print(f"   {i:2d}. {path}")
        if len(discovered_paths) > 15:
            print(f"   ... and {len(discovered_paths) - 15} more paths")
        print()
        
        # Store phase 1 results
        pipeline_results['phases']['phase1_discovery'] = {
            'success': True,
            'paths_discovered': len(discovered_paths),
            'all_paths': discovered_paths,
            'processing_time': phase1_time,
            'discovery_method': 'critter_real'
        }
        
    except Exception as e:
        print(f"❌ Critter discovery failed: {e}")
        pipeline_results['phases']['phase1_discovery'] = {
            'success': False,
            'error': str(e),
            'processing_time': time.time() - phase1_start
        }
        return pipeline_results
    
    # ========================================================================
    # PHASE 2: REAL NOVA PRO PATH SELECTION
    # ========================================================================
    print("🧠 PHASE 2: REAL NOVA PRO PATH SELECTION")
    print("-" * 60)
    print(f"🎯 Nova Pro analyzing {len(discovered_paths)} paths")
    print("💡 LLM will select most valuable paths for company intelligence")
    print()
    
    phase2_start = time.time()
    try:
        selection_result = filter_valuable_links_sync(
            discovered_paths, 
            base_url, 
            min_confidence=0.6,
            timeout_seconds=120
        )
        phase2_time = time.time() - phase2_start
        
        if selection_result.success:
            print(f"✅ Nova Pro selection completed in {phase2_time:.2f} seconds")
            print(f"🤖 Model: {selection_result.model_used}")
            print(f"💰 Cost: ${selection_result.cost_usd:.4f}")
            print(f"🔢 Tokens: {selection_result.tokens_used:,}")
            print(f"📊 Selected: {len(selection_result.selected_paths)} paths from {len(discovered_paths)} total")
            print(f"📉 Rejection rate: {((len(discovered_paths) - len(selection_result.selected_paths)) / len(discovered_paths) * 100):.1f}%")
            print()
            
            print("🎯 NOVA PRO SELECTED PATHS WITH REASONING:")
            for i, path in enumerate(selection_result.selected_paths, 1):
                reasoning = selection_result.path_reasoning.get(path, 'No reasoning provided')
                print(f"   {i:2d}. {path}")
                print(f"       💡 Nova Pro reasoning: {reasoning}")
            print()
            
            # Store phase 2 results
            pipeline_results['phases']['phase2_selection'] = {
                'success': True,
                'paths_selected': len(selection_result.selected_paths),
                'selected_paths': selection_result.selected_paths,
                'path_reasoning': selection_result.path_reasoning,
                'model_used': selection_result.model_used,
                'cost_usd': selection_result.cost_usd,
                'tokens_used': selection_result.tokens_used,
                'processing_time': phase2_time,
                'llm_prompt': selection_result.llm_prompt
            }
            
        else:
            print(f"❌ Nova Pro selection failed: {selection_result.error}")
            pipeline_results['phases']['phase2_selection'] = {
                'success': False,
                'error': selection_result.error,
                'processing_time': phase2_time
            }
            return pipeline_results
            
    except Exception as e:
        print(f"❌ Nova Pro selection failed with exception: {e}")
        pipeline_results['phases']['phase2_selection'] = {
            'success': False,
            'error': str(e),
            'processing_time': time.time() - phase2_start
        }
        return pipeline_results
    
    # ========================================================================
    # PHASE 3: ENHANCED PARALLEL CONTENT EXTRACTION
    # ========================================================================
    print("📄 PHASE 3: ENHANCED PARALLEL CONTENT EXTRACTION (10 CONCURRENT)")
    print("-" * 60)
    print(f"🔬 Crawling {len(selection_result.selected_paths)} selected paths")
    print("🚀 ENHANCED PARALLELISM: 10 concurrent pages (vs previous 3)")
    print("🔄 Using Trafilatura + BeautifulSoup fallback system")
    print()
    
    phase3_start = time.time()
    try:
        crawl_result = crawl_selected_pages_sync(
            base_url=base_url,
            selected_paths=selection_result.selected_paths,
            timeout_seconds=30,
            max_content_per_page=15000,
            max_concurrent=10  # INCREASED FROM 3 TO 10
        )
        phase3_time = time.time() - phase3_start
        
        print(f"✅ Content extraction completed in {phase3_time:.2f} seconds")
        print(f"📊 Success rate: {crawl_result.successful_pages}/{crawl_result.total_pages} pages")
        print(f"📝 Total content: {crawl_result.total_content_length:,} characters")
        print(f"⚡ Avg per page: {phase3_time/crawl_result.total_pages:.2f}s")
        print(f"🚀 PARALLELISM BOOST: 10 concurrent vs previous 3")
        print()
        
        # Analyze extraction methods used
        trafilatura_count = len([p for p in crawl_result.page_results if p.success and p.extraction_method == 'trafilatura'])
        beautifulsoup_count = len([p for p in crawl_result.page_results if p.success and p.extraction_method == 'beautifulsoup_fallback'])
        failed_count = len([p for p in crawl_result.page_results if not p.success])
        
        print("🔧 EXTRACTION METHOD ANALYSIS:")
        print(f"   📈 Trafilatura: {trafilatura_count} pages")
        print(f"   🔄 BeautifulSoup Fallback: {beautifulsoup_count} pages")
        print(f"   ❌ Failed: {failed_count} pages")
        print()
        
        # Show individual page results
        print("📄 INDIVIDUAL PAGE EXTRACTION RESULTS:")
        for i, page_result in enumerate(crawl_result.page_results, 1):
            page_name = page_result.url.split('/')[-1] or 'home'
            status = '✅' if page_result.success else '❌'
            method = page_result.extraction_method.upper() if page_result.extraction_method else 'FAILED'
            
            print(f"   {i:2d}. {page_name} [{method}] {status} - {page_result.content_length:,} chars")
            if not page_result.success and page_result.error:
                print(f"       Error: {page_result.error}")
        print()
        
        # Store phase 3 results with performance metrics
        pipeline_results['phases']['phase3_extraction'] = {
            'success': True,
            'total_pages': crawl_result.total_pages,
            'successful_pages': crawl_result.successful_pages,
            'total_content_length': crawl_result.total_content_length,
            'aggregated_content': crawl_result.aggregated_content,
            'max_concurrent': 10,
            'page_results': [
                {
                    'url': p.url,
                    'success': p.success,
                    'content_length': p.content_length,
                    'extraction_method': p.extraction_method,
                    'title': p.title,
                    'crawl_time': p.crawl_time,
                    'content_preview': p.content[:200] + '...' if p.content and len(p.content) > 200 else p.content,
                    'error': p.error
                } for p in crawl_result.page_results
            ],
            'trafilatura_pages': trafilatura_count,
            'beautifulsoup_pages': beautifulsoup_count,
            'failed_pages': failed_count,
            'processing_time': phase3_time,
            'avg_time_per_page': phase3_time / crawl_result.total_pages,
            'performance_improvement_test': True
        }
        
    except Exception as e:
        print(f"❌ Content extraction failed: {e}")
        pipeline_results['phases']['phase3_extraction'] = {
            'success': False,
            'error': str(e),
            'processing_time': time.time() - phase3_start
        }
        return pipeline_results
    
    # ========================================================================
    # PHASE 4: REAL FIELD EXTRACTION WITH OPERATIONAL METADATA
    # ========================================================================
    print("🧠 PHASE 4: REAL FIELD EXTRACTION WITH OPERATIONAL METADATA")
    print("-" * 60)
    print(f"🎯 Extracting structured fields from {crawl_result.total_content_length:,} characters")
    print("🤖 Using Nova Pro for Target Information Profile extraction")
    print("📊 Including operational metadata (tokens, cost, timing)")
    print()
    
    phase4_start = time.time()
    try:
        field_result = extract_company_fields_sync(
            crawl_result,
            company_name="CloudGeometry",
            timeout_seconds=120,
            pipeline_metadata=pipeline_results['phases']
        )
        phase4_time = time.time() - phase4_start
        
        if field_result.success:
            print(f"✅ Field extraction completed in {phase4_time:.2f} seconds")
            print(f"🤖 Model: {field_result.model_used}")
            print(f"💰 Cost: ${field_result.cost_usd:.4f}")
            print(f"🔢 Tokens: {field_result.tokens_used:,}")
            print(f"📊 Fields extracted: {len(field_result.extracted_fields)}")
            print(f"🎯 Overall confidence: {field_result.overall_confidence:.2f}")
            print()
            
            # Store phase 4 results
            pipeline_results['phases']['phase4_fields'] = {
                'success': True,
                'extracted_fields': field_result.extracted_fields,
                'field_confidence_scores': field_result.field_confidence_scores,
                'overall_confidence': field_result.overall_confidence,
                'model_used': field_result.model_used,
                'cost_usd': field_result.cost_usd,
                'tokens_used': field_result.tokens_used,
                'processing_time': phase4_time,
                'source_attribution': field_result.source_attribution
            }
            
        else:
            print(f"❌ Field extraction failed: {field_result.error}")
            pipeline_results['phases']['phase4_fields'] = {
                'success': False,
                'error': field_result.error,
                'processing_time': phase4_time
            }
            
    except Exception as e:
        print(f"❌ Field extraction failed with exception: {e}")
        pipeline_results['phases']['phase4_fields'] = {
            'success': False,
            'error': str(e),
            'processing_time': time.time() - phase4_start
        }
    
    # ========================================================================
    # PERFORMANCE ANALYSIS & COMPARISON
    # ========================================================================
    total_time = time.time() - pipeline_results['start_time']
    pipeline_results['total_time'] = total_time
    
    print("🏁 PARALLEL PERFORMANCE TEST RESULTS")
    print("=" * 80)
    
    # Calculate total costs
    total_cost = 0
    if pipeline_results['phases'].get('phase2_selection', {}).get('success'):
        total_cost += pipeline_results['phases']['phase2_selection']['cost_usd']
    if pipeline_results['phases'].get('phase4_fields', {}).get('success'):
        total_cost += pipeline_results['phases']['phase4_fields']['cost_usd']
    
    print(f"🏢 Company: CloudGeometry")
    print(f"🌐 Domain: {base_url}")
    print(f"⏱️ Total time: {total_time:.2f} seconds")
    print(f"💰 Total cost: ${total_cost:.4f}")
    print(f"🚀 Parallelism: 10 concurrent pages (vs previous 3)")
    print()
    
    # Phase-by-phase results with performance focus
    phases = [
        ('phase1_discovery', 'Critter Path Discovery'),
        ('phase2_selection', 'Nova Pro Path Selection'),
        ('phase3_extraction', 'Enhanced Parallel Content Extraction'),
        ('phase4_fields', 'Field Extraction')
    ]
    
    print("📊 PERFORMANCE BREAKDOWN:")
    for phase_key, phase_name in phases:
        phase_data = pipeline_results['phases'].get(phase_key, {})
        status = '✅' if phase_data.get('success') else '❌'
        time_taken = phase_data.get('processing_time', 0)
        
        if phase_key == 'phase3_extraction' and phase_data.get('success'):
            avg_per_page = phase_data.get('avg_time_per_page', 0)
            print(f"{status} {phase_name}: {time_taken:.2f}s (avg {avg_per_page:.2f}s/page)")
        else:
            print(f"{status} {phase_name}: {time_taken:.2f}s")
    
    print()
    
    # Performance comparison section
    if pipeline_results['phases'].get('phase3_extraction', {}).get('success'):
        extraction_time = pipeline_results['phases']['phase3_extraction']['processing_time']
        pages_crawled = pipeline_results['phases']['phase3_extraction']['total_pages']
        avg_time_per_page = extraction_time / pages_crawled
        
        print("🚀 PARALLEL PERFORMANCE ANALYSIS:")
        print(f"   📊 Pages crawled: {pages_crawled}")
        print(f"   ⏱️ Total extraction time: {extraction_time:.2f} seconds")
        print(f"   ⚡ Average per page: {avg_time_per_page:.2f} seconds")
        print(f"   🔄 Concurrency: 10 parallel pages")
        print(f"   📈 Expected improvement vs sequential: ~{(pages_crawled * 2) / extraction_time:.1f}x faster")
        print()
    
    # Save complete results for analysis
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"cloudgeometry_parallel_results_{timestamp}.json"
    
    try:
        import json
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(pipeline_results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📁 Complete results saved to: {results_file}")
        print()
        
    except Exception as e:
        print(f"⚠️ Failed to save results file: {e}")
    
    print("✅ PARALLEL CLOUDGEOMETRY PIPELINE EXECUTION COMPLETED!")
    print("📋 All data is REAL - no mocks or simulations used")
    print("🚀 Enhanced with 10 concurrent page crawling for performance testing")
    
    return pipeline_results


if __name__ == "__main__":
    main()