#!/usr/bin/env python3
"""
Debug test to investigate why specific companies failed during batch processing
Focuses on: jelli.com, adtheorent.com, and lotlinx.com
"""

import sys
import json
import time
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, '.')

from src.models import CompanyIntelligenceConfig
from src.bedrock_client import BedrockClient
from src.gemini_client import GeminiClient
from src.antoine_scraper_adapter import AntoineScraperAdapter
from src.progress_logger import start_company_processing, log_processing_phase, complete_company_processing
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_company_detailed(company_name: str):
    """Test a single company with detailed logging"""
    print(f"\n{'='*80}")
    print(f"🔍 TESTING: {company_name}")
    print(f"{'='*80}\n")
    
    # Create config
    config = CompanyIntelligenceConfig(
        api_key=os.getenv('PINECONE_API_KEY'),
        environment='us-east-1',
        index_name='theodore-companies',
        gemini_api_key=os.getenv('GEMINI_API_KEY'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_region='us-east-1'
    )
    
    # Create clients
    bedrock_client = BedrockClient(
        region=config.aws_region,
        access_key_id=config.aws_access_key_id,
        secret_access_key=config.aws_secret_access_key
    )
    
    gemini_client = GeminiClient(api_key=config.gemini_api_key)
    
    # Create scraper adapter with OpenRouter config
    openrouter_config = {
        'api_key': os.getenv('OPENROUTER_API_KEY', 'dummy-key'),
        'models': {
            'extraction': 'google/gemini-2.0-flash-exp',
            'path_selection': 'amazon/nova-pro-v1:0'
        }
    }
    
    scraper = AntoineScraperAdapter(
        config=config,
        bedrock_client=bedrock_client,
        gemini_client=gemini_client,
        openrouter_config=openrouter_config
    )
    
    # Start progress tracking
    job_id = start_company_processing(company_name)
    
    try:
        # Test each phase individually
        print("\n📡 PHASE 1: DISCOVERY")
        log_processing_phase(job_id, "discovery", "running")
        
        # Import antoine functions directly
        from src.antoine_discovery import discover_all_paths_sync
        discovered_paths = discover_all_paths_sync(company_name)
        
        print(f"✅ Discovered {len(discovered_paths)} paths")
        for i, path in enumerate(discovered_paths[:10]):
            print(f"   [{i+1}] {path}")
        if len(discovered_paths) > 10:
            print(f"   ... and {len(discovered_paths) - 10} more")
        
        log_processing_phase(job_id, "discovery", "completed", 
                           paths_found=len(discovered_paths))
        
        print("\n🎯 PHASE 2: SELECTION (LLM Path Analysis)")
        log_processing_phase(job_id, "selection", "running")
        
        # Test path selection with detailed logging
        from src.antoine_selection import filter_valuable_links_sync
        
        # Monkey-patch to capture LLM response
        import src.antoine_selection as selection_module
        original_filter = selection_module.filter_valuable_links_sync
        
        llm_response = None
        def logged_filter(urls, job_id=None):
            nonlocal llm_response
            print(f"Filtering {len(urls)} URLs...")
            
            # Try to capture the raw LLM call
            try:
                # Import the actual function that makes the LLM call
                if hasattr(selection_module, 'bedrock_client') or hasattr(selection_module, 'get_valuable_links_from_llm'):
                    print("Using Bedrock/LLM for path selection...")
                    
                # Call original function
                result = original_filter(urls, job_id)
                print(f"Selected {len(result)} paths")
                return result
                
            except Exception as e:
                print(f"❌ Selection error: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                raise
        
        selection_module.filter_valuable_links_sync = logged_filter
        
        try:
            selected_paths = filter_valuable_links_sync(discovered_paths, job_id=job_id)
            print(f"✅ Selected {len(selected_paths)} valuable paths:")
            for i, path in enumerate(selected_paths):
                print(f"   [{i+1}] {path}")
                
            log_processing_phase(job_id, "selection", "completed",
                               paths_selected=len(selected_paths))
                               
        except Exception as e:
            print(f"\n❌ SELECTION FAILED: {type(e).__name__}: {str(e)}")
            log_processing_phase(job_id, "selection", "failed", error=str(e))
            raise
        
        print("\n🕷️ PHASE 3: CRAWLING")
        log_processing_phase(job_id, "crawling", "running")
        
        from src.antoine_crawler import crawl_selected_pages_sync
        crawled_content = crawl_selected_pages_sync(selected_paths[:10], job_id=job_id)
        
        print(f"✅ Crawled {len(crawled_content)} pages:")
        for url, content in list(crawled_content.items())[:3]:
            print(f"   - {url}: {len(content)} chars")
            
        log_processing_phase(job_id, "crawling", "completed",
                           pages_crawled=len(crawled_content))
        
        print("\n🧠 PHASE 4: EXTRACTION")
        log_processing_phase(job_id, "extraction", "running")
        
        from src.antoine_extraction import extract_company_fields
        company_data = extract_company_fields(
            company_name,
            crawled_content,
            gemini_client=gemini_client,
            job_id=job_id
        )
        
        print("✅ Extraction complete:")
        print(f"   Company: {company_data.company_name}")
        print(f"   URL: {company_data.website_url}")
        print(f"   Description: {company_data.company_description[:200] if company_data.company_description else 'None'}...")
        
        # Count populated fields
        populated_fields = sum(1 for k, v in company_data.__dict__.items() 
                             if v and k not in ['embedding', 'metadata'])
        print(f"   Populated fields: {populated_fields}")
        
        log_processing_phase(job_id, "extraction", "completed")
        complete_company_processing(job_id, True, summary=f"Extracted {populated_fields} fields")
        
        return company_data
        
    except Exception as e:
        print(f"\n❌ PIPELINE FAILED: {type(e).__name__}: {str(e)}")
        complete_company_processing(job_id, False, error=str(e))
        
        # Save debug info
        debug_info = {
            'company': company_name,
            'timestamp': datetime.now().isoformat(),
            'error_type': type(e).__name__,
            'error_message': str(e),
            'discovered_paths': discovered_paths if 'discovered_paths' in locals() else [],
            'selected_paths': selected_paths if 'selected_paths' in locals() else [],
            'llm_response': llm_response
        }
        
        debug_filename = f"debug_{company_name.replace('.', '_')}_{int(time.time())}.json"
        with open(debug_filename, 'w') as f:
            json.dump(debug_info, f, indent=2)
        print(f"\n💾 Debug info saved to: {debug_filename}")
        
        raise


def main():
    """Test the three failing companies"""
    failing_companies = [
        'jelli.com',
        'adtheorent.com',
        'lotlinx.com'
    ]
    
    print("🔍 Failed Companies Debug Test")
    print("=" * 80)
    print("Testing companies that failed in batch processing:")
    for company in failing_companies:
        print(f"  - {company}")
    print("=" * 80)
    
    results = {}
    
    for company in failing_companies:
        try:
            print(f"\n\n{'='*80}")
            print(f"Starting test for {company}")
            print(f"{'='*80}")
            
            result = test_company_detailed(company)
            results[company] = {
                'status': 'success',
                'fields_populated': sum(1 for k, v in result.__dict__.items() 
                                      if v and k not in ['embedding', 'metadata'])
            }
            
        except Exception as e:
            results[company] = {
                'status': 'failed',
                'error': str(e),
                'error_type': type(e).__name__
            }
        
        # Wait between tests
        print("\n⏳ Waiting 3 seconds before next test...")
        time.sleep(3)
    
    # Summary
    print(f"\n\n{'='*80}")
    print("📊 SUMMARY")
    print(f"{'='*80}")
    
    for company, result in results.items():
        print(f"\n{company}:")
        if result['status'] == 'success':
            print(f"  ✅ Success - {result['fields_populated']} fields extracted")
        else:
            print(f"  ❌ Failed - {result['error_type']}: {result['error']}")
    
    print("\n✅ Debug test complete!")


if __name__ == "__main__":
    main()