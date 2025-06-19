#!/usr/bin/env python3
"""
Test the Google search discovery functionality
This uses the same code as the UI's /api/discover endpoint
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.simple_enhanced_discovery import SimpleEnhancedDiscovery
from src.bedrock_client import BedrockClient
from src.pinecone_client import PineconeClient
from src.intelligent_company_scraper import IntelligentCompanyScraperSync

def test_discovery_with_google_search():
    """Test discovery for a company not in database to trigger Google search"""
    
    print("🧪 Testing enhanced discovery with Google search fallback...")
    print("=" * 60)
    
    try:
        # Initialize clients (same as in app.py)
        print("🔧 Initializing clients...")
        bedrock_client = BedrockClient()
        pinecone_client = PineconeClient()
        scraper = IntelligentCompanyScraperSync()
        
        # Initialize discovery (same as in app.py discover_similar_companies)
        enhanced_discovery = SimpleEnhancedDiscovery(
            ai_client=bedrock_client,
            pinecone_client=pinecone_client,
            scraper=scraper
        )
        
        # Test with a company likely not in database
        test_company = "Acme Innovations"
        limit = 5
        
        print(f"\n🔍 Testing discovery for: {test_company}")
        print(f"📊 Requested limit: {limit} companies")
        
        # Run discovery (this is exactly what the UI does)
        results = enhanced_discovery.discover_similar_companies(
            company_name=test_company,
            limit=limit
        )
        
        print(f"\n✅ Discovery complete! Found {len(results)} companies:")
        print("-" * 60)
        
        for i, company in enumerate(results, 1):
            print(f"\n{i}. {company.get('company_name', 'Unknown')}")
            print(f"   Website: {company.get('website', 'N/A')}")
            print(f"   Discovery Method: {company.get('discovery_method', 'Unknown')}")
            print(f"   Sources: {', '.join(company.get('sources', []))}")
            print(f"   Confidence: {company.get('confidence', 0):.2f}")
            print(f"   Reasoning: {company.get('reasoning', ['N/A'])[0]}")
            
            # Check if this came from Google search
            if 'google' in company.get('sources', []):
                print(f"   🌐 FOUND VIA GOOGLE SEARCH!")
        
        # Count sources
        google_count = sum(1 for c in results if 'google' in c.get('sources', []))
        llm_count = sum(1 for c in results if 'llm' in c.get('sources', []))
        vector_count = sum(1 for c in results if 'vector' in c.get('sources', []))
        
        print(f"\n📊 Discovery Source Summary:")
        print(f"   LLM suggestions: {llm_count}")
        print(f"   Vector search: {vector_count}")
        print(f"   Google search: {google_count}")
        
        if google_count > 0:
            print(f"\n🎉 SUCCESS! Google search enhancement is working!")
            print(f"   Found {google_count} companies via web search")
        else:
            print(f"\n⚠️  No Google search results found")
            print(f"   This might mean the LLM found enough results already")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_discovery_with_google_search()