#!/usr/bin/env python3
"""
Test script to see if Crawl4AI works in subprocess
"""
import asyncio
import json
import sys
import os
import time

# Add current directory to path
sys.path.append(os.getcwd())

async def test_crawl4ai():
    try:
        print("🧪 TEST: Starting Crawl4AI test...", file=sys.stderr)
        
        # Test 1: Basic imports
        print("🧪 TEST: Testing imports...", file=sys.stderr)
        from crawl4ai import AsyncWebCrawler
        from crawl4ai.async_configs import CacheMode
        print("✅ TEST: Crawl4AI imports successful", file=sys.stderr)
        
        # Test 2: Simple crawl
        print("🧪 TEST: Testing simple crawl...", file=sys.stderr)
        start_time = time.time()
        
        async with AsyncWebCrawler(verbose=False) as crawler:
            print("✅ TEST: Crawler created successfully", file=sys.stderr)
            
            result = await crawler.arun(
                url="https://example.com",
                cache_mode=CacheMode.BYPASS
            )
            
            print(f"✅ TEST: Crawl completed in {time.time() - start_time:.2f}s", file=sys.stderr)
            print(f"✅ TEST: Content length: {len(result.markdown or '')}", file=sys.stderr)
            
            return {
                "success": True,
                "content_length": len(result.markdown or ''),
                "url": result.url,
                "duration": time.time() - start_time
            }
            
    except Exception as e:
        print(f"❌ TEST: Error: {e}", file=sys.stderr)
        import traceback
        print(f"❌ TEST: Traceback: {traceback.format_exc()}", file=sys.stderr)
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    print("🧪 TEST: Starting async test...", file=sys.stderr)
    result = asyncio.run(test_crawl4ai())
    print(json.dumps(result, default=str))