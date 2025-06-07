#!/usr/bin/env python3
"""
Test the new intelligent URL discovery system
"""

import os
import sys
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from src.intelligent_url_discovery import IntelligentURLDiscovery
from src.bedrock_client import BedrockClient
from src.models import CompanyIntelligenceConfig

async def test_url_discovery():
    """Test intelligent URL discovery with a real company"""
    
    print("🧪 Testing Intelligent URL Discovery")
    print("=" * 50)
    
    load_dotenv()
    
    try:
        # Initialize bedrock client
        config = CompanyIntelligenceConfig()
        bedrock_client = BedrockClient(config)
        
        # Initialize URL discovery
        url_discovery = IntelligentURLDiscovery(bedrock_client)
        
        # Test companies
        test_companies = [
            ("OpenAI", "https://openai.com"),
            ("Cloud Geometry", "https://cloudgeometry.io"),
            ("Anthropic", "https://anthropic.com")
        ]
        
        for company_name, website in test_companies:
            print(f"\n🔍 Discovering URLs for {company_name}")
            print(f"   Website: {website}")
            
            try:
                # Discover URLs
                result = await url_discovery.discover_urls(website, company_name)
                
                print(f"\n📊 Results for {company_name}:")
                print(f"   ⏱️  Processing time: {result.total_processing_time:.2f}s")
                print(f"   🗺️  Sitemap found: {result.sitemap_found}")
                print(f"   🔗 URLs discovered: {len(result.discovered_urls)}")
                
                if result.robots_analysis.get('sitemap_urls'):
                    print(f"   🗂️  Sitemaps: {len(result.robots_analysis['sitemap_urls'])}")
                
                print(f"\n📋 Top URLs to crawl:")
                for i, url in enumerate(result.discovered_urls[:8], 1):
                    print(f"   {i:2d}. {url.page_type:12} | {url.priority:.2f} | {url.source:12} | {url.url}")
                
                # Test the convenience method too
                priority_list = await url_discovery.get_crawl_priority_list(website, company_name)
                print(f"\n🎯 Priority crawl list: {len(priority_list)} URLs")
                
            except Exception as e:
                print(f"❌ Failed to discover URLs for {company_name}: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n🎉 URL Discovery Tests Complete!")
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run the URL discovery test"""
    asyncio.run(test_url_discovery())

if __name__ == "__main__":
    main()