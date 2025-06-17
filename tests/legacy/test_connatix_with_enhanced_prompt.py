#!/usr/bin/env python3
"""
Test Connatix specifically with enhanced prompt to verify it works.
"""

import os
import sys

sys.path.append('.')
from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Load environment
load_dotenv()

def test_connatix_enhanced():
    """Test Connatix with enhanced extraction"""
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    print("=" * 80)
    print("TESTING CONNATIX WITH ENHANCED EXTRACTION")
    print("=" * 80)
    
    # Get before state
    before_company = pipeline.pinecone_client.find_company_by_name("connatix.com")
    before_metadata = before_company.__dict__ if before_company and hasattr(before_company, '__dict__') else {}
    
    # Critical fields to check
    critical_fields = [
        'founding_year', 'location', 'employee_count_range', 'leadership_team',
        'contact_info', 'social_media', 'funding_status', 'partnerships', 'awards'
    ]
    
    def is_filled(value):
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip() != '' and value.lower() not in ['unknown', 'not specified', 'n/a', 'none']
        if isinstance(value, (list, dict)):
            return len(value) > 0
        if isinstance(value, (int, float)):
            return value > 0
        return bool(value)
    
    print("📊 BEFORE STATE:")
    before_filled = [field for field in critical_fields if is_filled(before_metadata.get(field))]
    print(f"   Filled fields: {len(before_filled)}/{len(critical_fields)}")
    if before_filled:
        print(f"   Had: {', '.join(before_filled)}")
    
    # Reprocess
    print(f"\n🔄 Reprocessing connatix.com...")
    try:
        updated_company = pipeline.process_single_company("connatix.com", "https://connatix.com")
        
        # Get fresh data
        after_company = pipeline.pinecone_client.find_company_by_name("connatix.com")
        if after_company:
            after_metadata = after_company.__dict__ if hasattr(after_company, '__dict__') else {}
            
            print("📊 AFTER STATE:")
            after_filled = [field for field in critical_fields if is_filled(after_metadata.get(field))]
            improvement = len(after_filled) - len(before_filled)
            
            print(f"   Filled fields: {len(after_filled)}/{len(critical_fields)} ({improvement:+d})")
            
            # Show specific improvements
            new_fields = set(after_filled) - set(before_filled)
            if new_fields:
                print(f"   🆕 NEW: {', '.join(new_fields)}")
                
                # Show specific values
                for field in ['leadership_team', 'founding_year', 'location', 'contact_info']:
                    if field in new_fields:
                        value = after_metadata.get(field)
                        if field == 'leadership_team' and isinstance(value, list):
                            print(f"   👥 {field}: {value}")
                        elif field == 'contact_info' and isinstance(value, dict):
                            print(f"   📞 {field}: {value}")
                        else:
                            print(f"   📋 {field}: {value}")
            else:
                print(f"   ❌ No improvements found")
            
            # Check if raw_content was populated
            raw_content = after_metadata.get('raw_content', '')
            print(f"\n📄 Raw content length: {len(raw_content)} chars")
            
            # Check AI analysis
            ai_fields = ['industry', 'business_model', 'company_size', 'target_market']
            ai_filled = [field for field in ai_fields if is_filled(after_metadata.get(field))]
            print(f"🧠 AI analysis fields: {len(ai_filled)}/{len(ai_fields)} filled")
            for field in ai_filled:
                print(f"   {field}: {after_metadata.get(field)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_connatix_enhanced()