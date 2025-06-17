#!/usr/bin/env python3
"""
Step-by-step debugging of the research pipeline
Test each component individually to find where it breaks
"""

import asyncio
import json
import sys
import os
import time
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

async def test_step_1_basic_crawl4ai():
    """Test 1: Basic Crawl4AI functionality"""
    print("🧪 STEP 1: Testing basic Crawl4AI...")
    try:
        from crawl4ai import AsyncWebCrawler
        from crawl4ai.async_configs import CacheMode
        
        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(
                url="https://openai.com",
                cache_mode=CacheMode.BYPASS
            )
            
        return {
            "success": True,
            "content_length": len(result.markdown or ''),
            "url": result.url,
            "status": "Basic crawling works"
        }
    except Exception as e:
        return {"success": False, "error": str(e), "step": "basic_crawl4ai"}

async def test_step_2_models_import():
    """Test 2: Models and config import"""
    print("🧪 STEP 2: Testing models and config...")
    try:
        from src.models import CompanyData, CompanyIntelligenceConfig
        
        config = CompanyIntelligenceConfig()
        company = CompanyData(name="Test Company", website="https://openai.com")
        
        return {
            "success": True,
            "config_created": True,
            "company_created": True,
            "status": "Models and config work"
        }
    except Exception as e:
        return {"success": False, "error": str(e), "step": "models_import"}

async def test_step_3_bedrock_client():
    """Test 3: BedrockClient without credentials"""
    print("🧪 STEP 3: Testing BedrockClient...")
    try:
        from src.models import CompanyIntelligenceConfig
        from src.bedrock_client import BedrockClient
        
        config = CompanyIntelligenceConfig()
        start_time = time.time()
        bedrock_client = BedrockClient(config)
        init_time = time.time() - start_time
        
        # Try a simple call to see what happens
        start_time = time.time()
        try:
            response = bedrock_client.analyze_content("test")
            call_time = time.time() - start_time
            response_success = len(response) > 0
        except Exception as e:
            call_time = time.time() - start_time
            response_success = False
            response_error = str(e)
        
        return {
            "success": True,
            "init_time": init_time,
            "call_time": call_time,
            "response_success": response_success,
            "response_error": response_error if not response_success else None,
            "status": "BedrockClient created but may fail on calls"
        }
    except Exception as e:
        return {"success": False, "error": str(e), "step": "bedrock_client"}

async def test_step_4_intelligent_scraper_init():
    """Test 4: IntelligentCompanyScraper initialization"""
    print("🧪 STEP 4: Testing IntelligentCompanyScraper initialization...")
    try:
        from src.models import CompanyData, CompanyIntelligenceConfig
        from src.bedrock_client import BedrockClient
        from src.intelligent_company_scraper import IntelligentCompanyScraper
        
        config = CompanyIntelligenceConfig()
        bedrock_client = BedrockClient(config)
        
        start_time = time.time()
        scraper = IntelligentCompanyScraper(config, bedrock_client)
        init_time = time.time() - start_time
        
        return {
            "success": True,
            "init_time": init_time,
            "scraper_created": True,
            "status": "IntelligentCompanyScraper initialized"
        }
    except Exception as e:
        return {"success": False, "error": str(e), "step": "scraper_init"}

async def test_step_5_scraper_without_llm():
    """Test 5: Try scraping without LLM calls (mock/bypass)"""
    print("🧪 STEP 5: Testing scraper phases without LLM...")
    try:
        from src.models import CompanyData, CompanyIntelligenceConfig
        from src.bedrock_client import BedrockClient
        from src.intelligent_company_scraper import IntelligentCompanyScraper
        
        config = CompanyIntelligenceConfig()
        bedrock_client = BedrockClient(config)
        scraper = IntelligentCompanyScraper(config, bedrock_client)
        
        # Test individual phases that don't require LLM
        company_data = CompanyData(name="OpenAI", website="https://openai.com")
        base_url = scraper._normalize_url(company_data.website)
        
        start_time = time.time()
        # Try link discovery (first phase)
        all_links = await scraper._discover_all_links(base_url)
        link_discovery_time = time.time() - start_time
        
        return {
            "success": True,
            "base_url": base_url,
            "links_found": len(all_links),
            "link_discovery_time": link_discovery_time,
            "sample_links": all_links[:5],
            "status": "Link discovery works"
        }
    except Exception as e:
        return {"success": False, "error": str(e), "step": "scraper_without_llm"}

async def test_step_6_full_scraper_with_timeout():
    """Test 6: Full scraper with quick timeout"""
    print("🧪 STEP 6: Testing full scraper with 10s timeout...")
    try:
        from src.models import CompanyData, CompanyIntelligenceConfig
        from src.bedrock_client import BedrockClient
        from src.intelligent_company_scraper import IntelligentCompanyScraper
        
        config = CompanyIntelligenceConfig()
        bedrock_client = BedrockClient(config)
        scraper = IntelligentCompanyScraper(config, bedrock_client)
        
        company_data = CompanyData(name="OpenAI", website="https://openai.com")
        
        start_time = time.time()
        
        # Add a timeout to the full scraping
        try:
            result = await asyncio.wait_for(
                scraper.scrape_company_intelligent(company_data, "test_job"),
                timeout=10.0
            )
            duration = time.time() - start_time
            
            return {
                "success": True,
                "duration": duration,
                "scrape_status": result.scrape_status,
                "scrape_error": result.scrape_error,
                "content_length": len(result.company_description or ''),
                "status": "Full scraping completed"
            }
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return {
                "success": False,
                "error": "Timeout after 10 seconds",
                "duration": duration,
                "step": "full_scraper_timeout"
            }
            
    except Exception as e:
        return {"success": False, "error": str(e), "step": "full_scraper"}

async def main():
    """Run all diagnostic tests"""
    print("🔍 RESEARCH PIPELINE DIAGNOSTICS")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    tests = [
        ("Basic Crawl4AI", test_step_1_basic_crawl4ai),
        ("Models Import", test_step_2_models_import), 
        ("BedrockClient", test_step_3_bedrock_client),
        ("Scraper Init", test_step_4_intelligent_scraper_init),
        ("Link Discovery", test_step_5_scraper_without_llm),
        ("Full Scraper", test_step_6_full_scraper_with_timeout)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"🧪 Running: {test_name}")
        try:
            result = await test_func()
            if result["success"]:
                print(f"✅ {test_name}: {result.get('status', 'PASSED')}")
            else:
                print(f"❌ {test_name}: {result.get('error', 'FAILED')}")
                print(f"   Failed at step: {result.get('step', 'unknown')}")
            results.append({"test": test_name, **result})
        except Exception as e:
            print(f"💥 {test_name}: EXCEPTION - {str(e)}")
            results.append({"test": test_name, "success": False, "error": str(e), "exception": True})
        print()
    
    print("=" * 50)
    print("📊 SUMMARY:")
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status}: {result['test']}")
        if not result["success"]:
            print(f"      Error: {result.get('error', 'Unknown')}")
    
    print("\n📋 Full Results:")
    print(json.dumps(results, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())