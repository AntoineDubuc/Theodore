#!/usr/bin/env python3
"""
Direct test of Antoine pipeline phases to debug failing companies
"""

import sys
import os
import json
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Import Antoine components directly
from src.antoine_discovery import discover_all_paths_sync
from src.antoine_selection import filter_valuable_links_sync  
from src.antoine_crawler import crawl_selected_pages_sync
from src.antoine_extraction import extract_company_fields_sync

# Import clients
from src.bedrock_client import BedrockClient
from src.gemini_client import GeminiClient


def test_company_phases(company_name: str):
    """Test each phase of the Antoine pipeline for a company"""
    print(f"\n{'='*80}")
    print(f"🔍 TESTING: {company_name}")
    print(f"{'='*80}\n")
    
    results = {
        'company': company_name,
        'timestamp': datetime.now().isoformat(),
        'phases': {}
    }
    
    # Phase 1: Discovery
    print("📡 PHASE 1: DISCOVERY")
    try:
        start_time = time.time()
        discovery_result = discover_all_paths_sync(company_name)
        duration = time.time() - start_time
        
        # Extract paths from the result object
        discovered_paths = discovery_result.all_paths
        
        print(f"✅ Discovered {len(discovered_paths)} paths in {duration:.2f}s")
        
        # Show sample paths
        print("Sample paths:")
        for i, path in enumerate(discovered_paths[:10]):
            print(f"  [{i+1}] {path}")
        if len(discovered_paths) > 10:
            print(f"  ... and {len(discovered_paths) - 10} more")
        
        # Show more details
        print(f"\nDiscovery breakdown:")
        print(f"  Navigation paths: {len(discovery_result.navigation_paths)}")
        print(f"  Content paths: {len(discovery_result.content_paths)}")
        print(f"  Restricted paths: {len(discovery_result.restricted_paths)}")
        
        results['phases']['discovery'] = {
            'status': 'success',
            'duration': duration,
            'paths_found': len(discovered_paths),
            'navigation_paths': len(discovery_result.navigation_paths),
            'content_paths': len(discovery_result.content_paths),
            'sample_paths': discovered_paths[:20]
        }
        
    except Exception as e:
        print(f"❌ Discovery failed: {type(e).__name__}: {str(e)}")
        results['phases']['discovery'] = {
            'status': 'failed',
            'error': str(e),
            'error_type': type(e).__name__
        }
        return results
    
    # Phase 2: Selection
    print("\n🎯 PHASE 2: SELECTION")
    try:
        # First, let's see what the raw LLM gets
        print(f"Sending {len(discovered_paths)} paths to LLM for selection...")
        
        # Create a minimal job_id for tracking
        job_id = f"test_{company_name}_{int(time.time())}"
        
        start_time = time.time()
        # Pass the base URL which should be the company name with https://
        base_url = f"https://{company_name}" if not company_name.startswith('http') else company_name
        selection_result = filter_valuable_links_sync(discovered_paths, base_url)
        duration = time.time() - start_time
        
        # Extract selected paths from result
        selected_paths = selection_result.selected_paths
        
        print(f"✅ Selected {len(selected_paths)} paths in {duration:.2f}s")
        
        # Show selected paths
        print("Selected paths:")
        for i, path in enumerate(selected_paths):
            print(f"  [{i+1}] {path}")
        
        results['phases']['selection'] = {
            'status': 'success',
            'duration': duration,
            'paths_selected': len(selected_paths),
            'selected_paths': selected_paths
        }
        
    except Exception as e:
        print(f"❌ Selection failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        results['phases']['selection'] = {
            'status': 'failed',
            'error': str(e),
            'error_type': type(e).__name__,
            'traceback': traceback.format_exc()
        }
        
        # Save debug info even on failure
        debug_file = f"debug_{company_name.replace('.', '_')}_{int(time.time())}.json"
        with open(debug_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Debug info saved to: {debug_file}")
        
        return results
    
    # Phase 3: Crawling  
    print("\n🕷️ PHASE 3: CRAWLING")
    try:
        # Limit to first 10 paths for testing
        paths_to_crawl = selected_paths[:10]
        print(f"Crawling {len(paths_to_crawl)} pages...")
        
        start_time = time.time()
        # Need to pass base_url as first parameter
        crawl_result = crawl_selected_pages_sync(base_url, paths_to_crawl)
        duration = time.time() - start_time
        
        # Extract crawled content from result
        crawled_content = {}
        for page_result in crawl_result.page_results:
            if page_result.success and page_result.content:
                crawled_content[page_result.url] = page_result.content
        
        print(f"✅ Crawled {len(crawled_content)} pages in {duration:.2f}s")
        
        # Show crawled content summary
        print("Crawled content:")
        total_chars = 0
        for url, content in crawled_content.items():
            chars = len(content)
            total_chars += chars
            print(f"  - {url}: {chars:,} chars")
        print(f"  Total: {total_chars:,} chars")
        
        results['phases']['crawling'] = {
            'status': 'success',
            'duration': duration,
            'pages_crawled': len(crawled_content),
            'total_chars': total_chars,
            'pages': {url: len(content) for url, content in crawled_content.items()}
        }
        
    except Exception as e:
        print(f"❌ Crawling failed: {type(e).__name__}: {str(e)}")
        results['phases']['crawling'] = {
            'status': 'failed',
            'error': str(e),
            'error_type': type(e).__name__
        }
        return results
    
    # Phase 4: Extraction
    print("\n🧠 PHASE 4: EXTRACTION")
    try:
        # Use the sync extraction function with crawl result
        start_time = time.time()
        extraction_result = extract_company_fields_sync(
            crawl_result,  # Pass the entire crawl result
            company_name=company_name
        )
        duration = time.time() - start_time
        
        # Get the company data from extraction result
        company_data = extraction_result.company_data
        
        print(f"✅ Extraction completed in {duration:.2f}s")
        
        # Count populated fields
        populated_fields = sum(1 for k, v in company_data.__dict__.items() 
                             if v and k not in ['embedding', 'metadata'])
        
        print(f"Populated {populated_fields} fields:")
        for key, value in company_data.__dict__.items():
            if value and key not in ['embedding', 'metadata']:
                value_str = str(value)[:100] + '...' if len(str(value)) > 100 else str(value)
                print(f"  - {key}: {value_str}")
        
        results['phases']['extraction'] = {
            'status': 'success',
            'duration': duration,
            'fields_populated': populated_fields,
            'company_data': {k: v for k, v in company_data.__dict__.items() 
                           if k not in ['embedding', 'metadata']}
        }
        
    except Exception as e:
        print(f"❌ Extraction failed: {type(e).__name__}: {str(e)}")
        results['phases']['extraction'] = {
            'status': 'failed',
            'error': str(e),
            'error_type': type(e).__name__
        }
    
    # Save complete results
    results_file = f"results_{company_name.replace('.', '_')}_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Complete results saved to: {results_file}")
    
    return results


def main():
    """Test the failing companies"""
    failing_companies = [
        'jelli.com',
        'adtheorent.com',
        'lotlinx.com'
    ]
    
    print("🔍 Antoine Pipeline Phase Test")
    print("=" * 80)
    
    all_results = {}
    
    for company in failing_companies:
        results = test_company_phases(company)
        all_results[company] = results
        
        # Wait between tests
        print(f"\n⏳ Waiting 3 seconds before next test...")
        time.sleep(3)
    
    # Summary
    print(f"\n\n{'='*80}")
    print("📊 SUMMARY")
    print(f"{'='*80}")
    
    for company, results in all_results.items():
        print(f"\n{company}:")
        for phase_name, phase_data in results.get('phases', {}).items():
            status = phase_data.get('status', 'unknown')
            if status == 'success':
                if phase_name == 'discovery':
                    print(f"  ✅ {phase_name}: {phase_data.get('paths_found', 0)} paths")
                elif phase_name == 'selection':
                    print(f"  ✅ {phase_name}: {phase_data.get('paths_selected', 0)} paths")
                elif phase_name == 'crawling':
                    print(f"  ✅ {phase_name}: {phase_data.get('pages_crawled', 0)} pages")
                elif phase_name == 'extraction':
                    print(f"  ✅ {phase_name}: {phase_data.get('fields_populated', 0)} fields")
            else:
                error = phase_data.get('error', 'Unknown error')
                print(f"  ❌ {phase_name}: {error}")
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    main()