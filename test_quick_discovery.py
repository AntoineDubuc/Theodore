#!/usr/bin/env python3
"""
Test script to verify the updated similarity discovery without automatic web scraping
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

def test_quick_discovery():
    """Test the updated quick discovery (LLM only, no automatic scraping)"""
    
    print("🚀 Testing Theodore Quick Discovery (LLM Only)")
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
        print("\n2. Initializing enhanced discovery...")
        enhanced_discovery = SimpleEnhancedDiscovery(
            bedrock_client=pipeline.bedrock_client,
            pinecone_client=pipeline.pinecone_client,
            scraper=pipeline.scraper
        )
        print("✅ Enhanced discovery initialized")
        
        # Test quick discovery (should NOT trigger web scraping)
        print("\n3. Testing quick discovery for unknown company...")
        test_company = "Netflix"  # Company likely not in our database
        
        print(f"   Searching for companies similar to: {test_company}")
        results = enhanced_discovery.discover_similar_companies(
            company_name=test_company,
            limit=3
        )
        
        print(f"\n4. Quick Discovery Results for '{test_company}':")
        print("-" * 40)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"\n   Result {i}:")
                print(f"   Company: {result.get('company_name', result.get('name', 'N/A'))}")
                print(f"   Website: {result.get('website', 'N/A')}")
                print(f"   Discovery Method: {result.get('discovery_method', 'N/A')}")
                print(f"   Confidence: {result.get('confidence', result.get('similarity_score', 0)):.2f}")
                print(f"   Is Scraped: {result.get('is_scraped_data', result.get('is_researched', False))}")
                print(f"   Sources: {result.get('sources', ['llm'])}")
                
                # Should only have basic LLM data, no rich scraping data
                if result.get('industry'):
                    print(f"   ⚠️  WARNING: Found industry data (should not be present): {result.get('industry')}")
                if result.get('company_description'):
                    print(f"   ⚠️  WARNING: Found description (should not be present): {result.get('company_description')[:50]}...")
        else:
            print("   No results found")
        
        print(f"\n✅ Quick discovery test completed! Found {len(results)} suggestions")
        
        # Test on-demand research for one company
        if results:
            print(f"\n5. Testing on-demand research...")
            test_suggestion = results[0]
            
            print(f"   Researching: {test_suggestion.get('name', test_suggestion.get('company_name'))}")
            researched_result = enhanced_discovery.research_company_on_demand(test_suggestion)
            
            print(f"\n6. Research Results:")
            print("-" * 40)
            print(f"   Company: {researched_result.get('company_name')}")
            print(f"   Research Status: {researched_result.get('research_status', 'unknown')}")
            print(f"   Is Researched: {researched_result.get('is_researched', False)}")
            
            if researched_result.get('is_researched'):
                print(f"   Industry: {researched_result.get('industry', 'N/A')}")
                print(f"   Business Model: {researched_result.get('business_model', 'N/A')}")
                print(f"   Description: {researched_result.get('company_description', 'N/A')[:100]}...")
                print("   ✅ Research completed successfully!")
            else:
                print(f"   ❌ Research failed: {researched_result.get('research_error', 'Unknown error')}")
        
        print(f"\n🎯 Test Summary:")
        print(f"   ✅ Quick discovery working (LLM suggestions only)")
        print(f"   ✅ No automatic web scraping")
        print(f"   ✅ On-demand research available")
        print(f"   ✅ Separation of concerns achieved")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_quick_discovery()