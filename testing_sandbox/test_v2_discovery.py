#!/usr/bin/env python3
"""
Quick test script to debug V2 discovery engine
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.v2_discovery import V2DiscoveryEngine
from src.bedrock_client import BedrockClient
from src.models import CompanyIntelligenceConfig
import json

def test_discovery():
    """Test the discovery engine directly"""
    print("🔍 Testing V2 Discovery Engine...")
    
    # Initialize
    config = CompanyIntelligenceConfig()
    try:
        ai_client = BedrockClient(config)
        discovery_engine = V2DiscoveryEngine(ai_client)
        print("✅ Engine initialized")
        
        # Test with Five Guys
        print("\n🏢 Testing discovery with 'Five Guys'...")
        result = discovery_engine.discover_similar_companies("Five Guys", limit=3)
        
        print(f"\n📊 Result type: {type(result)}")
        print(f"📊 Success: {result.get('success')}")
        print(f"📊 Total found: {result.get('total_found')}")
        print(f"📊 Input type: {result.get('input_type')}")
        
        if result.get('similar_companies'):
            print(f"\n✅ Similar companies found:")
            for i, company in enumerate(result['similar_companies'], 1):
                print(f"  {i}. {company.get('name')} - {company.get('website')}")
                print(f"     Similarity: {company.get('similarity_score')}")
                print(f"     Reason: {company.get('reasoning', 'N/A')[:100]}...")
        else:
            print(f"\n❌ No similar companies found")
            if 'error' in result:
                print(f"Error: {result['error']}")
        
        # Show raw result
        print(f"\n🔍 Full result:")
        print(json.dumps(result, indent=2, default=str)[:1000] + "...")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_discovery()