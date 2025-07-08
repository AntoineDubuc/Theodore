#!/usr/bin/env python3
"""
Test script to diagnose Bell.ca extraction issues
"""

import sys
import os
import json
import asyncio
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from src.antoine_scraper_adapter import AntoineScraperAdapter
from src.bedrock_client import BedrockClient
from config.settings import settings

async def test_bell_extraction():
    """Test Bell.ca extraction specifically"""
    print("\n" + "="*80)
    print("BELL.CA EXTRACTION TEST")
    print("="*80)
    
    # Initialize components
    scraper = AntoineScraper()
    bedrock_client = BedrockClient(
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region=settings.aws_region
    )
    
    # Test parameters
    test_url = "https://www.bell.ca"
    company_name = "Bell"
    
    print(f"\n🔍 Testing extraction for: {test_url}")
    print(f"Company name: {company_name}")
    
    # Step 1: Test crawling
    print("\n" + "-"*60)
    print("STEP 1: CRAWLING TEST")
    print("-"*60)
    
    try:
        crawl_result = await scraper.crawl_page(test_url)
        
        if crawl_result.success:
            print(f"✅ Crawling successful")
            print(f"   - Content length: {len(crawl_result.html)} characters")
            print(f"   - Markdown length: {len(crawl_result.markdown)} characters")
            print(f"   - Links found: {len(crawl_result.links)}")
            
            # Save raw content for analysis
            with open('test_bell_raw_content.html', 'w', encoding='utf-8') as f:
                f.write(crawl_result.html)
            print(f"   - Raw HTML saved to: test_bell_raw_content.html")
            
            with open('test_bell_markdown.md', 'w', encoding='utf-8') as f:
                f.write(crawl_result.markdown)
            print(f"   - Markdown saved to: test_bell_markdown.md")
            
            # Show content preview
            print(f"\n📄 Content preview (first 500 chars):")
            print(crawl_result.markdown[:500])
            
        else:
            print(f"❌ Crawling failed: {crawl_result.error}")
            return
            
    except Exception as e:
        print(f"❌ Crawling error: {e}")
        return
    
    # Step 2: Test extraction
    print("\n" + "-"*60)
    print("STEP 2: EXTRACTION TEST")
    print("-"*60)
    
    try:
        result = await scraper.get_company_info(test_url, company_name)
        
        print(f"\n📊 Extraction Results:")
        print(json.dumps(result, indent=2))
        
        # Analyze each field
        print("\n🔍 Field Analysis:")
        for field, value in result.items():
            if value and value != "Not found" and value != [] and value != {}:
                print(f"✅ {field}: {value}")
            else:
                print(f"❌ {field}: Empty/Not found")
        
        # Save full result
        with open('test_bell_extraction_result.json', 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Full result saved to: test_bell_extraction_result.json")
        
    except Exception as e:
        print(f"❌ Extraction error: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 3: Test Nova extraction directly
    print("\n" + "-"*60)
    print("STEP 3: NOVA MODEL DIRECT TEST")
    print("-"*60)
    
    try:
        # Create a focused prompt for Bell
        test_prompt = f"""
        Analyze this website content for Bell Canada and extract company information.
        
        CONTENT:
        {crawl_result.markdown[:10000]}
        
        Extract the following information:
        1. Company description (what does Bell do?)
        2. Industries they operate in
        3. Any contact information visible
        4. Location information
        5. Social media links
        
        Return as JSON.
        """
        
        print("🤖 Testing Nova model directly...")
        nova_response = bedrock_client.generate_text(test_prompt, model="nova")
        print(f"\n📝 Nova Response:")
        print(nova_response)
        
        # Save Nova response
        with open('test_bell_nova_response.txt', 'w') as f:
            f.write(nova_response)
        print(f"\n💾 Nova response saved to: test_bell_nova_response.txt")
        
    except Exception as e:
        print(f"❌ Nova test error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_bell_extraction())