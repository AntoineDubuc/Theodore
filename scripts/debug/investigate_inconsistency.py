#!/usr/bin/env python3
"""
Investigate why different runs produce inconsistent results
"""

import sys
import os
import json
sys.path.append('src')
from dotenv import load_dotenv
load_dotenv()

def compare_execution_paths():
    print("🔍 INVESTIGATING EXECUTION PATH DIFFERENCES")
    print("="*60)
    
    # Check if different jobs use different methods
    print("1. CHECKING JOB EXECUTION METHODS")
    print("-" * 40)
    
    try:
        with open('logs/processing_progress.json', 'r') as f:
            progress_data = json.load(f)
        
        freeconvert_jobs = []
        for job_id, job_data in progress_data.get('jobs', {}).items():
            if job_data.get('company_name') == 'FreeConvert':
                freeconvert_jobs.append((job_id, job_data))
        
        print(f"Found {len(freeconvert_jobs)} FreeConvert jobs:")
        
        for job_id, job_data in freeconvert_jobs:
            print(f"\n📊 JOB: {job_id}")
            print(f"  Status: {job_data.get('status')}")
            print(f"  Total Duration: {job_data.get('total_duration', 'N/A')}s")
            print(f"  Pages Processed: {job_data.get('results', {}).get('pages_processed', 'N/A')}")
            
            phases = job_data.get('phases', [])
            print(f"  Phases: {len(phases)}")
            
            if phases:
                print("  Phase Details:")
                for phase in phases:
                    name = phase.get('name')
                    status = phase.get('status')
                    duration = phase.get('duration', 'N/A')
                    details = phase.get('details', {})
                    
                    print(f"    - {name}: {status} ({duration}s)")
                    
                    # Check for key metrics
                    if 'pages_selected' in details:
                        print(f"      Pages Selected: {details['pages_selected']}")
                    if 'successful_extractions' in details:
                        print(f"      Successful Extractions: {details['successful_extractions']}")
                    if 'intelligence_length' in details:
                        print(f"      Intelligence Length: {details['intelligence_length']} chars")
            else:
                print("  ⚠️ No phases logged (subprocess execution)")
                
    except Exception as e:
        print(f"❌ Failed to compare execution paths: {e}")

def test_subprocess_vs_direct():
    print(f"\n2. TESTING SUBPROCESS VS DIRECT EXECUTION")
    print("-" * 40)
    
    try:
        # Test 1: Direct scraper execution (like our test)
        print("🧪 TEST 1: Direct Scraper Execution")
        from intelligent_company_scraper import IntelligentCompanyScraper
        from models import CompanyData, CompanyIntelligenceConfig
        import asyncio
        
        config = CompanyIntelligenceConfig()
        scraper = IntelligentCompanyScraper(config)
        
        company_data = CompanyData(
            name='FreeConvert-Test-Direct', 
            website='https://www.freeconvert.com'
        )
        
        async def test_direct():
            result = await scraper.scrape_company_intelligent(company_data, job_id="direct_test")
            return result
        
        direct_result = asyncio.run(test_direct())
        print(f"  ✅ Direct Result:")
        print(f"    Description Length: {len(direct_result.company_description or '')}")
        print(f"    Pages Crawled: {len(direct_result.pages_crawled or [])}")
        print(f"    Status: {direct_result.scrape_status}")
        
    except Exception as e:
        print(f"  ❌ Direct execution failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        # Test 2: Pipeline execution (like API calls)
        print(f"\n🧪 TEST 2: Pipeline Execution (like API)")
        from main_pipeline import TheodoreIntelligencePipeline
        
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME')
        )
        
        pipeline_result = pipeline.process_single_company(
            "FreeConvert-Test-Pipeline", 
            "https://www.freeconvert.com",
            job_id="pipeline_test"
        )
        
        print(f"  ✅ Pipeline Result:")
        if pipeline_result:
            print(f"    Description Length: {len(pipeline_result.company_description or '')}")
            print(f"    Pages Crawled: {len(pipeline_result.pages_crawled or [])}")
            print(f"    Status: {pipeline_result.scrape_status}")
        else:
            print(f"    ❌ Pipeline returned None")
            
    except Exception as e:
        print(f"  ❌ Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()

def check_caching_effects():
    print(f"\n3. CHECKING CACHING EFFECTS")
    print("-" * 40)
    
    try:
        # Check if Crawl4AI has cache that might affect results
        print("🔍 Checking for Crawl4AI cache files...")
        
        # Common cache locations
        cache_dirs = [
            "~/.crawl4ai",
            "~/.cache/crawl4ai", 
            "/tmp/crawl4ai",
            "./crawl4ai_cache"
        ]
        
        cache_found = False
        for cache_dir in cache_dirs:
            expanded_path = os.path.expanduser(cache_dir)
            if os.path.exists(expanded_path):
                cache_found = True
                try:
                    files = os.listdir(expanded_path)
                    print(f"  ✅ Found cache at {expanded_path}: {len(files)} files")
                    
                    # Look for freeconvert-related cache
                    freeconvert_files = [f for f in files if 'freeconvert' in f.lower()]
                    if freeconvert_files:
                        print(f"    🎯 FreeConvert cache files: {len(freeconvert_files)}")
                        for f in freeconvert_files[:3]:
                            print(f"      - {f}")
                except:
                    print(f"  ❓ Cache at {expanded_path} (cannot read)")
        
        if not cache_found:
            print("  ❌ No Crawl4AI cache directories found")
            
    except Exception as e:
        print(f"❌ Cache investigation failed: {e}")

def analyze_timing_factors():
    print(f"\n4. ANALYZING TIMING FACTORS")
    print("-" * 40)
    
    try:
        # Check if execution time affects results
        with open('logs/processing_progress.json', 'r') as f:
            progress_data = json.load(f)
        
        freeconvert_jobs = []
        for job_id, job_data in progress_data.get('jobs', {}).items():
            if job_data.get('company_name') == 'FreeConvert':
                start_time = job_data.get('start_time')
                duration = job_data.get('total_duration')
                pages = job_data.get('results', {}).get('pages_processed', 0)
                
                freeconvert_jobs.append({
                    'job_id': job_id,
                    'start_time': start_time,
                    'duration': duration,
                    'pages': pages
                })
        
        # Sort by start time
        freeconvert_jobs.sort(key=lambda x: x['start_time'] or '')
        
        print("📊 FreeConvert Jobs by Time:")
        for job in freeconvert_jobs:
            print(f"  {job['start_time']}: {job['pages']} pages in {job['duration']}s (Job: {job['job_id']})")
        
        # Check for patterns
        if len(freeconvert_jobs) > 1:
            pages_results = [job['pages'] for job in freeconvert_jobs if job['pages']]
            if pages_results:
                print(f"\n📈 Results Analysis:")
                print(f"  Page counts: {pages_results}")
                print(f"  Min pages: {min(pages_results)}")
                print(f"  Max pages: {max(pages_results)}")
                print(f"  Variance: {max(pages_results) - min(pages_results)} pages")
                
                if max(pages_results) - min(pages_results) > 50:
                    print("  🚨 HIGH VARIANCE detected - inconsistent results!")
                
    except Exception as e:
        print(f"❌ Timing analysis failed: {e}")

if __name__ == "__main__":
    compare_execution_paths()
    test_subprocess_vs_direct()
    check_caching_effects()
    analyze_timing_factors()