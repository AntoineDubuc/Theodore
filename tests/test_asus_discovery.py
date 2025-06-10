#!/usr/bin/env python3
"""
Test ASUS similarity discovery to debug LLM calling
"""

import os
import sys
import json
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, 'src')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_asus_discovery():
    """Test ASUS discovery step by step"""
    print("🔍 Testing ASUS Discovery Step by Step")
    print("=" * 50)
    
    try:
        # Step 1: Initialize components
        print("\n📋 Step 1: Initializing components...")
        
        from models import CompanyIntelligenceConfig
        from pinecone_client import PineconeClient
        from gemini_client import GeminiClient
        from simple_enhanced_discovery import SimpleEnhancedDiscovery
        
        config = CompanyIntelligenceConfig()
        
        # Initialize Pinecone client
        pinecone_client = PineconeClient(
            config=config,
            api_key=os.getenv('PINECONE_API_KEY'),
            environment=os.getenv('PINECONE_ENVIRONMENT'),
            index_name=os.getenv('PINECONE_INDEX_NAME')
        )
        print("✅ Pinecone client initialized")
        
        # Initialize Gemini client
        gemini_client = GeminiClient(config)
        print("✅ Gemini client initialized")
        
        # Initialize discovery service
        discovery = SimpleEnhancedDiscovery(
            ai_client=gemini_client,
            pinecone_client=pinecone_client
        )
        print("✅ Discovery service initialized")
        
        # Step 2: Test company lookup
        print("\n📋 Step 2: Testing company lookup in database...")
        target_company = pinecone_client.find_company_by_name("ASUS")
        print(f"Company lookup result: {target_company}")
        
        if target_company:
            print("✅ ASUS found in database - will use hybrid discovery")
        else:
            print("❌ ASUS not found in database - will use LLM-only discovery")
        
        # Step 3: Test LLM discovery directly
        print("\n📋 Step 3: Testing LLM discovery directly...")
        
        try:
            llm_results = discovery._llm_discovery_unknown_company("ASUS", 5)
            print(f"LLM discovery returned {len(llm_results)} results")
            
            if llm_results:
                print("✅ LLM discovery successful!")
                for i, result in enumerate(llm_results, 1):
                    print(f"  {i}. {result.get('name', 'Unknown')} - {result.get('similarity_score', 0)} - {result.get('reasoning', 'No reason')}")
            else:
                print("❌ LLM discovery returned empty results")
                
        except Exception as e:
            print(f"❌ LLM discovery failed with error: {e}")
            import traceback
            traceback.print_exc()
        
        # Step 4: Test full discovery pipeline
        print("\n📋 Step 4: Testing full discovery pipeline...")
        
        try:
            full_results = discovery.discover_similar_companies("ASUS", 5)
            print(f"Full discovery returned {len(full_results)} results")
            
            if full_results:
                print("✅ Full discovery successful!")
                for i, result in enumerate(full_results, 1):
                    print(f"  {i}. {result.get('company_name', 'Unknown')} - {result.get('confidence', 0)} - {result.get('discovery_method', 'Unknown')}")
            else:
                print("❌ Full discovery returned empty results")
                
        except Exception as e:
            print(f"❌ Full discovery failed with error: {e}")
            import traceback
            traceback.print_exc()
        
        # Step 5: Test Gemini client directly
        print("\n📋 Step 5: Testing Gemini client directly...")
        
        try:
            test_prompt = """Find companies similar to "ASUS" for business development purposes.

IMPORTANT: Research and identify real companies that would be competitors, partners, or similar businesses to "ASUS".

Find 3 real, similar companies and respond in JSON format:
{
  "similar_companies": [
    {
      "name": "Real Company Name",
      "website": "https://realcompany.com",
      "similarity_score": 0.85,
      "relationship_type": "competitor",
      "reasoning": "Brief explanation of similarity",
      "business_context": "Why they are similar to ASUS"
    }
  ]
}

Make sure to suggest REAL companies with actual websites, not fictional ones."""

            raw_response = gemini_client.analyze_content(test_prompt)
            print(f"Raw Gemini response length: {len(raw_response) if raw_response else 0}")
            
            if raw_response:
                print("✅ Gemini client responded!")
                print(f"First 300 chars: {raw_response[:300]}...")
                
                # Try to parse JSON
                try:
                    json_start = raw_response.find('{')
                    json_end = raw_response.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_text = raw_response[json_start:json_end]
                        data = json.loads(json_text)
                        companies = data.get('similar_companies', [])
                        print(f"✅ JSON parsing successful! Found {len(companies)} companies")
                        
                        for i, comp in enumerate(companies, 1):
                            print(f"  {i}. {comp.get('name', 'Unknown')} - {comp.get('similarity_score', 0)}")
                    else:
                        print("❌ No JSON found in response")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing failed: {e}")
                    
            else:
                print("❌ Gemini client returned empty response")
                
        except Exception as e:
            print(f"❌ Gemini client test failed: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n🎯 Summary:")
        print("=" * 50)
        print("If ASUS is showing 'not in system', check:")
        print("1. Is ASUS actually in the Pinecone database?")
        print("2. Is the LLM discovery working correctly?")
        print("3. Is the JSON parsing working?")
        print("4. Are there any errors in the discovery pipeline?")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_asus_discovery()