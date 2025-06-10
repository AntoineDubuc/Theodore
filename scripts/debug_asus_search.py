#!/usr/bin/env python3
"""
Debug script to test ASUS similarity search and understand why LLM fallback isn't working
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, 'src')

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_asus_discovery():
    """Test ASUS discovery flow step by step"""
    try:
        # Import required modules
        from src.main_pipeline import TheodoreIntelligencePipeline
        from src.models import CompanyIntelligenceConfig
        from src.simple_enhanced_discovery import SimpleEnhancedDiscovery
        
        # Initialize pipeline
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME')
        )
        
        logger.info("✅ Pipeline initialized successfully")
        
        # Test 1: Check if ASUS exists in database
        company_name = "ASUS"
        logger.info(f"🔍 Testing if '{company_name}' exists in database...")
        
        target_company = pipeline.pinecone_client.find_company_by_name(company_name)
        if target_company:
            logger.info(f"✅ Found {company_name} in database: {target_company.name}")
            return
        else:
            logger.info(f"❌ {company_name} NOT found in database - should trigger LLM discovery")
        
        # Test 2: Initialize SimpleEnhancedDiscovery
        logger.info("🔧 Initializing SimpleEnhancedDiscovery...")
        enhanced_discovery = SimpleEnhancedDiscovery(
            ai_client=pipeline.bedrock_client,  # Use bedrock_client as ai_client
            pinecone_client=pipeline.pinecone_client,
            scraper=pipeline.scraper
        )
        logger.info("✅ SimpleEnhancedDiscovery initialized")
        
        # Test 3: Test LLM discovery for unknown company
        logger.info(f"🤖 Testing LLM discovery for unknown company: {company_name}")
        llm_results = enhanced_discovery._llm_discovery_unknown_company(company_name, limit=3)
        
        if llm_results:
            logger.info(f"✅ LLM discovery found {len(llm_results)} results:")
            for i, result in enumerate(llm_results, 1):
                logger.info(f"  {i}. {result.get('name', 'Unknown')} - {result.get('reasoning', 'No reason')}")
        else:
            logger.error(f"❌ LLM discovery returned empty results for {company_name}")
            
        # Test 4: Test full enhanced discovery
        logger.info(f"🚀 Testing full enhanced discovery for: {company_name}")
        full_results = enhanced_discovery.discover_similar_companies(company_name, limit=3)
        
        if full_results:
            logger.info(f"✅ Full discovery found {len(full_results)} results:")
            for i, result in enumerate(full_results, 1):
                logger.info(f"  {i}. {result.get('company_name', 'Unknown')} - Method: {result.get('discovery_method', 'Unknown')}")
        else:
            logger.error(f"❌ Full enhanced discovery returned empty results for {company_name}")
            
        # Test 5: Test AI client directly
        logger.info("🧠 Testing AI client directly...")
        test_prompt = f"""Find companies similar to "ASUS" for business development purposes.

IMPORTANT: Research and identify real companies that would be competitors, partners, or similar businesses to "ASUS".

Consider all possible interpretations of what "ASUS" could be:
- A technology company
- A software/SaaS company  
- A consulting firm
- A service provider
- Any other type of business

Find 3 real, similar companies and respond in JSON format:
{{
  "similar_companies": [
    {{
      "name": "Real Company Name",
      "website": "https://realcompany.com",
      "similarity_score": 0.85,
      "relationship_type": "competitor",
      "reasoning": "Brief explanation of similarity",
      "business_context": "Why they are similar to ASUS"
    }}
  ]
}}

Make sure to suggest REAL companies with actual websites, not fictional ones."""

        response = pipeline.bedrock_client.analyze_content(test_prompt)
        if response:
            logger.info(f"✅ AI client response received ({len(response)} chars)")
            logger.info(f"Response preview: {response[:300]}...")
        else:
            logger.error("❌ AI client returned empty response")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_asus_discovery()