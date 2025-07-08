#!/usr/bin/env python3
"""
Debug test to investigate LLM responses and understand why specific companies failed
Focuses on: jelli.com, adtheorent.com, and lotlinx.com
"""

import sys
import json
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, '.')

from src.antoine_scraper_adapter import AntoineScraperAdapter
from src.models import CompanyIntelligenceConfig
from src.bedrock_client import BedrockClient
from src.gemini_client import GeminiClient
from antoine.models import OpenRouterConfig
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def test_company_with_detailed_logging(company_url: str):
    """Test a single company with extremely detailed logging"""
    print(f"\n{'='*80}")
    print(f"🔍 TESTING: {company_url}")
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
    
    # Create OpenRouter config for Antoine
    openrouter_config = OpenRouterConfig(
        api_key=os.getenv('OPENROUTER_API_KEY', 'dummy-key'),
        models={
            'extraction': 'google/gemini-2.0-flash-exp',
            'path_selection': 'amazon/nova-pro-v1:0'
        },
        anthropic_beta_header='',
        settings={}
    )
    
    # Create scraper with detailed logging
    scraper = AntoineScraperAdapter(
        config=config,
        bedrock_client=bedrock_client,
        gemini_client=gemini_client,
        openrouter_config=openrouter_config
    )
    
    # Override methods to capture raw responses
    original_discover = scraper.antoine_crawler.discovery
    original_select = scraper.antoine_crawler.selection
    original_crawl = scraper.antoine_crawler.crawling
    original_extract = scraper.antoine_crawler.extraction
    
    discovered_paths = []
    llm_responses = {}
    
    def logged_discovery(*args, **kwargs):
        print(f"\n📡 PHASE 1: DISCOVERY")
        print(f"URL: {args[0] if args else kwargs.get('url', 'N/A')}")
        result = original_discover(*args, **kwargs)
        discovered_paths.extend(result.discovered_paths)
        print(f"✅ Discovered {len(result.discovered_paths)} paths")
        for i, path in enumerate(result.discovered_paths[:10]):  # Show first 10
            print(f"   [{i+1}] {path}")
        if len(result.discovered_paths) > 10:
            print(f"   ... and {len(result.discovered_paths) - 10} more")
        return result
    
    def logged_selection(*args, **kwargs):
        print(f"\n🎯 PHASE 2: SELECTION (LLM Path Analysis)")
        print(f"Analyzing {len(discovered_paths)} discovered paths...")
        
        # Capture the raw LLM response
        from antoine.scrapers.path_selection import PathSelector
        selector = PathSelector(openrouter_config)
        
        # Get the prompt that will be sent
        prompt = selector._create_selection_prompt(discovered_paths, max_pages=10)
        print(f"\n📝 LLM PROMPT (first 1000 chars):")
        print(prompt[:1000])
        print(f"... (total {len(prompt)} chars)")
        
        try:
            # Make the actual LLM call
            print(f"\n🧠 Calling LLM: {openrouter_config.models['path_selection']}")
            start_time = time.time()
            
            # Try to get the raw response
            import requests
            headers = {
                'Authorization': f'Bearer {openrouter_config.api_key}',
                'Content-Type': 'application/json'
            }
            
            if 'nova' in openrouter_config.models['path_selection']:
                # Direct Bedrock call for Nova
                print("Using Bedrock Nova Pro model...")
                response_text = bedrock_client.analyze_company(prompt, temperature=0.1)
                llm_responses['selection'] = {
                    'model': 'amazon/nova-pro-v1:0',
                    'raw_response': response_text,
                    'duration': time.time() - start_time
                }
                print(f"\n📊 LLM Response ({len(response_text)} chars):")
                print(response_text[:2000])  # First 2000 chars
            else:
                # OpenRouter call
                response = requests.post(
                    'https://openrouter.ai/api/v1/completions',
                    headers=headers,
                    json={
                        'model': openrouter_config.models['path_selection'],
                        'prompt': prompt,
                        'max_tokens': 4000,
                        'temperature': 0.1
                    }
                )
                llm_responses['selection'] = {
                    'status_code': response.status_code,
                    'raw_response': response.text,
                    'duration': time.time() - start_time
                }
                print(f"\n📊 LLM Response Status: {response.status_code}")
                print(f"Raw Response: {response.text[:2000]}")
            
            # Now call the original selection method
            result = original_select(*args, **kwargs)
            print(f"\n✅ Selected {len(result.selected_paths)} paths:")
            for i, path in enumerate(result.selected_paths):
                print(f"   [{i+1}] {path}")
            return result
            
        except Exception as e:
            print(f"\n❌ SELECTION ERROR: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            llm_responses['selection_error'] = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'traceback': traceback.format_exc()
            }
            raise
    
    def logged_crawl(*args, **kwargs):
        print(f"\n🕷️ PHASE 3: CRAWLING")
        result = original_crawl(*args, **kwargs)
        print(f"✅ Crawled {len(result.crawled_pages)} pages successfully")
        for url, content in list(result.crawled_pages.items())[:3]:  # Show first 3
            print(f"   - {url}: {len(content)} chars")
        return result
    
    def logged_extraction(*args, **kwargs):
        print(f"\n🧠 PHASE 4: EXTRACTION")
        result = original_extract(*args, **kwargs)
        print(f"✅ Extraction complete")
        print(f"   Company: {result.company_name}")
        print(f"   Description: {result.company_description[:200] if result.company_description else 'None'}...")
        return result
    
    # Apply logging wrappers
    scraper.antoine_crawler.discovery = logged_discovery
    scraper.antoine_crawler.selection = logged_selection
    scraper.antoine_crawler.crawling = logged_crawl
    scraper.antoine_crawler.extraction = logged_extraction
    
    # Run the scraper
    try:
        result = scraper.scrape(company_url)
        print(f"\n✅ SUCCESS: {company_url}")
        print(f"Final result fields populated: {sum(1 for k, v in result.__dict__.items() if v and k != 'embedding')}")
        
    except Exception as e:
        print(f"\n❌ FAILED: {company_url}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Save detailed debug info
    debug_info = {
        'company_url': company_url,
        'timestamp': datetime.now().isoformat(),
        'discovered_paths': discovered_paths,
        'llm_responses': llm_responses,
        'error': None
    }
    
    debug_filename = f"debug_{company_url.replace('.', '_')}_{int(time.time())}.json"
    with open(debug_filename, 'w') as f:
        json.dump(debug_info, f, indent=2)
    print(f"\n💾 Debug info saved to: {debug_filename}")
    
    return llm_responses


def main():
    """Test the three failing companies"""
    failing_companies = [
        'jelli.com',
        'adtheorent.com', 
        'lotlinx.com'
    ]
    
    print("🔍 LLM Response Debug Test")
    print("=" * 80)
    print("Testing companies that failed in batch processing:")
    for company in failing_companies:
        print(f"  - {company}")
    print("=" * 80)
    
    all_responses = {}
    
    for company in failing_companies:
        print(f"\n{'='*80}")
        print(f"Testing {company}...")
        print(f"{'='*80}")
        
        try:
            responses = test_company_with_detailed_logging(company)
            all_responses[company] = responses
        except Exception as e:
            print(f"\n❌ Failed to test {company}: {e}")
            all_responses[company] = {'error': str(e)}
        
        # Add delay between tests
        print("\n⏳ Waiting 5 seconds before next test...")
        time.sleep(5)
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 SUMMARY OF LLM RESPONSES")
    print(f"{'='*80}")
    
    for company, responses in all_responses.items():
        print(f"\n{company}:")
        if 'error' in responses:
            print(f"  ❌ Error: {responses['error']}")
        elif 'selection' in responses:
            selection = responses['selection']
            print(f"  Model: {selection.get('model', 'unknown')}")
            print(f"  Duration: {selection.get('duration', 0):.2f}s")
            if 'raw_response' in selection:
                print(f"  Response length: {len(selection['raw_response'])} chars")
                # Check for JSON in response
                if '{' in selection['raw_response']:
                    print("  ✅ Contains JSON structure")
                else:
                    print("  ❌ No JSON found in response")
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    main()