#!/usr/bin/env python3
"""
Test script to verify similarity discovery with web scraping integration
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, 'src')

from main_pipeline import TheodoreIntelligencePipeline
from models import CompanyIntelligenceConfig
from simple_enhanced_discovery import SimpleEnhancedDiscovery

def test_similarity_with_scraping():
    """Test the enhanced similarity discovery with scraping"""
    
    print("🧪 Testing Theodore Similarity Discovery with Web Scraping")
    print("=" * 60)
    
    try:
        # Initialize pipeline
        print("1. Initializing Theodore pipeline...")
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME')
        )
        print("✅ Pipeline initialized successfully")
        
        # Initialize enhanced discovery with scraper
        print("\n2. Initializing enhanced discovery with scraper...")
        enhanced_discovery = SimpleEnhancedDiscovery(
            bedrock_client=pipeline.bedrock_client,
            pinecone_client=pipeline.pinecone_client,
            scraper=pipeline.scraper
        )
        print("✅ Enhanced discovery initialized with scraper")
        
        # Test discovery for a company NOT in the database (should trigger LLM + scraping)
        print("\n3. Testing discovery for unknown company (should use LLM + scraping)...")
        test_company = "Alienware"  # Company likely not in our database
        
        print(f"   Searching for companies similar to: {test_company}")
        results = enhanced_discovery.discover_similar_companies(
            company_name=test_company,
            limit=3
        )
        
        print(f"\n4. Results for '{test_company}':")
        print("-" * 40)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"\n   Result {i}:")
                print(f"   Company: {result.get('company_name', 'N/A')}")
                print(f"   Website: {result.get('website', 'N/A')}")
                print(f"   Discovery Method: {result.get('discovery_method', 'N/A')}")
                print(f"   Confidence: {result.get('confidence', 0):.2f}")
                print(f"   Is Scraped Data: {result.get('is_scraped_data', False)}")
                print(f"   Scrape Status: {result.get('scrape_status', 'N/A')}")
                
                if result.get('is_scraped_data'):
                    print(f"   Industry: {result.get('industry', 'N/A')}")
                    print(f"   Business Model: {result.get('business_model', 'N/A')}")
                    print(f"   Description: {result.get('company_description', 'N/A')[:100]}...")
                
                if result.get('scrape_status') == 'failed':
                    print(f"   Scrape Error: {result.get('scrape_error', 'N/A')}")
        else:
            print("   No results found")
        
        print(f"\n✅ Test completed! Found {len(results)} similar companies")
        
        # Show summary of scraping performance
        scraped_count = sum(1 for r in results if r.get('is_scraped_data'))
        print(f"\n📊 Scraping Summary:")
        print(f"   Total results: {len(results)}")
        print(f"   Successfully scraped: {scraped_count}")
        print(f"   Scraping success rate: {scraped_count/len(results)*100:.1f}%" if results else "N/A")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_similarity_with_scraping()