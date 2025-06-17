#!/usr/bin/env python3
"""
Debug what content was actually extracted and how the AI analysis was applied.
"""

import os
import sys

sys.path.append('.')
from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Load environment
load_dotenv()

def debug_extraction_content():
    """Debug the actual content and AI analysis"""
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    # Get the current Connatix data
    connatix = pipeline.pinecone_client.find_company_by_name("connatix.com")
    
    if not connatix:
        print("❌ Connatix not found")
        return
    
    metadata = connatix.__dict__ if hasattr(connatix, '__dict__') else {}
    
    print("=" * 80)
    print("DEBUGGING EXTRACTION CONTENT & AI ANALYSIS")
    print("=" * 80)
    
    # Check raw content
    raw_content = metadata.get('raw_content') or ''
    company_description = metadata.get('company_description') or ''
    
    print(f"📄 RAW CONTENT LENGTH: {len(raw_content)} characters")
    if raw_content:
        print(f"📄 RAW CONTENT PREVIEW (first 500 chars):")
        print(f"{raw_content[:500]}...")
        
        # Check if leadership content is in the raw content
        if 'leadership' in raw_content.lower():
            print(f"✅ 'leadership' found in raw content")
        if 'ceo' in raw_content.lower():
            print(f"✅ 'ceo' found in raw content")
        if 'founder' in raw_content.lower():
            print(f"✅ 'founder' found in raw content")
    else:
        print(f"❌ No raw content found")
    
    print(f"\n📝 COMPANY DESCRIPTION LENGTH: {len(company_description)} characters")
    if company_description:
        print(f"📝 COMPANY DESCRIPTION PREVIEW (first 300 chars):")
        print(f"{company_description[:300]}...")
    else:
        print(f"❌ No company description found")
    
    # Check if AI analysis was actually applied
    ai_fields = [
        'industry', 'business_model', 'company_size', 'tech_stack', 
        'key_services', 'pain_points', 'target_market', 'ai_summary'
    ]
    
    print(f"\n🧠 AI ANALYSIS RESULTS:")
    ai_applied = False
    for field in ai_fields:
        value = metadata.get(field)
        if value and value != 'unknown':
            print(f"✅ {field}: {value}")
            ai_applied = True
        else:
            print(f"❌ {field}: Not extracted")
    
    if not ai_applied:
        print(f"\n🔴 CRITICAL ISSUE: No AI analysis was applied!")
        print(f"   This means the bedrock_client.analyze_company_content() wasn't called")
        print(f"   or failed silently")
    
    # Test the bedrock client directly
    print(f"\n🧪 TESTING BEDROCK CLIENT DIRECTLY:")
    try:
        # Create a mock company with the raw content
        from src.models import CompanyData
        test_company = CompanyData(
            name="connatix.com",
            website="https://connatix.com",
            raw_content=raw_content[:4000]  # Limit to what bedrock prompt uses
        )
        
        print(f"📤 Sending {len(test_company.raw_content)} chars to bedrock analysis...")
        analysis_result = pipeline.bedrock_client.analyze_company_content(test_company)
        
        print(f"📥 Bedrock analysis result type: {type(analysis_result)}")
        print(f"📥 Bedrock analysis result: {analysis_result}")
        
        if isinstance(analysis_result, dict):
            print(f"\n📊 BEDROCK EXTRACTED FIELDS:")
            for key, value in analysis_result.items():
                if value and value != 'unknown':
                    print(f"✅ {key}: {value}")
                else:
                    print(f"❌ {key}: {value}")
            
            # Specifically check for leadership
            leadership = analysis_result.get('leadership_team')
            if leadership:
                print(f"\n👥 LEADERSHIP EXTRACTED BY BEDROCK:")
                print(f"   {leadership}")
            else:
                print(f"\n❌ No leadership extracted by bedrock")
        
    except Exception as e:
        print(f"❌ Error testing bedrock directly: {e}")
        import traceback
        traceback.print_exc()
    
    # Check what pages were actually crawled
    pages_crawled = metadata.get('pages_crawled', [])
    print(f"\n📋 PAGES CRAWLED ({len(pages_crawled)}):")
    for i, page in enumerate(pages_crawled, 1):
        print(f"  {i}. {page}")
        if 'leadership' in page.lower():
            print(f"     ✅ This is the leadership page!")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    debug_extraction_content()