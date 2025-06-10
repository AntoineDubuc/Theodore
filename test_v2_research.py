#!/usr/bin/env python3
"""
Quick test script to debug V2 research engine
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.v2_research import V2ResearchEngineSync
from src.bedrock_client import BedrockClient
from src.models import CompanyIntelligenceConfig
import json

def test_research():
    """Test the research engine directly"""
    print("🔬 Testing V2 Research Engine...")
    
    # Initialize
    config = CompanyIntelligenceConfig()
    try:
        ai_client = BedrockClient(config)
        research_engine = V2ResearchEngineSync(ai_client)
        print("✅ Engine initialized")
        
        # Test with a simple company
        print("\n🏢 Testing with Five Guys...")
        result = research_engine.research_company(
            company_name="Five Guys",
            website_url="https://www.fiveguys.com"
        )
        
        print(f"\n📊 Result type: {type(result)}")
        print(f"📊 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict):
            # Check for structured data
            structured_fields = [
                'company_description', 'industry', 'business_model', 
                'value_proposition', 'target_market', 'key_services'
            ]
            
            print(f"\n🔍 Structured data check:")
            for field in structured_fields:
                value = result.get(field)
                print(f"  {field}: {type(value)} = {str(value)[:100]}...")
            
            # Check completion
            total_fields = [
                'company_name', 'website', 'industry', 'business_model', 'company_size',
                'tech_stack', 'has_chat_widget', 'has_forms', 'pain_points', 'key_services',
                'competitive_advantages', 'target_market', 'company_description', 'value_proposition',
                'founding_year', 'location', 'employee_count_range', 'company_culture',
                'funding_status', 'social_media', 'contact_info', 'leadership_team',
                'recent_news', 'certifications', 'partnerships', 'awards', 'company_stage',
                'tech_sophistication', 'geographic_scope', 'business_model_type',
                'decision_maker_type', 'sales_complexity', 'ai_summary'
            ]
            
            completed = sum(1 for field in total_fields if result.get(field) not in [None, '', [], {}])
            completion_rate = (completed / len(total_fields)) * 100
            
            print(f"\n📈 Completion: {completed}/{len(total_fields)} fields = {completion_rate:.1f}%")
            
            # Show the raw result for debugging
            print(f"\n🔍 Raw result (first 500 chars):")
            print(json.dumps(result, indent=2, default=str)[:500] + "...")
            
        else:
            print(f"❌ Expected dict, got: {result}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_research()