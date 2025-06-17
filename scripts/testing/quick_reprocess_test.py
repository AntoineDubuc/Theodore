#!/usr/bin/env python3
"""
Quick test to reprocess one company and show the data improvements.
"""

import os
import sys
import json
from datetime import datetime

sys.path.append('.')
from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Load environment
load_dotenv()

def quick_test():
    """Quick test reprocessing"""
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    # Test company
    company_name = "connatix.com"
    
    print("=" * 60)
    print("QUICK REPROCESSING TEST")
    print("=" * 60)
    
    # Get BEFORE state
    before_company = pipeline.pinecone_client.find_company_by_name(company_name)
    if not before_company:
        print(f"❌ Company {company_name} not found")
        return
    
    before_metadata = before_company.__dict__ if hasattr(before_company, '__dict__') else {}
    
    # Check critical fields
    critical_fields = [
        'founding_year', 'location', 'employee_count_range', 'leadership_team',
        'contact_info', 'social_media', 'company_description', 'value_proposition'
    ]
    
    def is_filled(value):
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip() != '' and value.lower() not in ['unknown', 'not specified', 'n/a']
        if isinstance(value, (list, dict)):
            return len(value) > 0
        return bool(value)
    
    before_filled = [field for field in critical_fields if is_filled(before_metadata.get(field))]
    
    print(f"📊 BEFORE: {len(before_filled)}/{len(critical_fields)} fields filled")
    if before_filled:
        print(f"   Had: {', '.join(before_filled)}")
    
    # Show specific values
    print(f"\n📋 BEFORE VALUES:")
    for field in ['leadership_team', 'founding_year', 'location', 'contact_info']:
        value = before_metadata.get(field)
        if is_filled(value):
            print(f"   ✅ {field}: {value}")
        else:
            print(f"   ❌ {field}: Empty")
    
    # Reprocess
    print(f"\n🔄 Reprocessing {company_name}...")
    try:
        updated_company = pipeline.process_single_company(company_name, "https://connatix.com")
        
        # Get AFTER state
        after_company = pipeline.pinecone_client.find_company_by_name(company_name)
        if after_company:
            after_metadata = after_company.__dict__ if hasattr(after_company, '__dict__') else {}
            
            after_filled = [field for field in critical_fields if is_filled(after_metadata.get(field))]
            improvement = len(after_filled) - len(before_filled)
            
            print(f"📊 AFTER: {len(after_filled)}/{len(critical_fields)} fields filled ({improvement:+d})")
            
            # Show specific improvements
            new_fields = set(after_filled) - set(before_filled)
            if new_fields:
                print(f"🆕 NEW: {', '.join(new_fields)}")
            
            print(f"\n📋 AFTER VALUES:")
            for field in ['leadership_team', 'founding_year', 'location', 'contact_info']:
                value = after_metadata.get(field)
                if is_filled(value):
                    if field in new_fields:
                        print(f"   🆕 {field}: {value}")
                    else:
                        print(f"   ✅ {field}: {value}")
                else:
                    print(f"   ❌ {field}: Empty")
            
            # Show scraping details
            pages_crawled = after_metadata.get('pages_crawled', [])
            raw_content = after_metadata.get('raw_content') or ''
            raw_content_len = len(raw_content)
            
            print(f"\n🔍 SCRAPING:")
            print(f"   Pages crawled: {len(pages_crawled)}")
            print(f"   Raw content: {raw_content_len:,} chars")
            print(f"   Scrape status: {after_metadata.get('scrape_status')}")
            
            # Test AI analysis directly if we have content
            if raw_content:
                print(f"\n🧪 TESTING AI ANALYSIS:")
                try:
                    from src.models import CompanyData
                    test_company = CompanyData(
                        name="connatix.com",
                        website="https://connatix.com",
                        raw_content=raw_content
                    )
                    
                    analysis = pipeline.bedrock_client.analyze_company_content(test_company)
                    
                    if isinstance(analysis, dict):
                        found_enhanced = 0
                        for field in critical_fields:
                            if field in analysis and analysis[field]:
                                found_enhanced += 1
                                print(f"   ✅ AI found {field}: {analysis[field]}")
                        
                        print(f"\n🎯 AI EXTRACTED: {found_enhanced}/{len(critical_fields)} fields")
                        if found_enhanced > len(after_filled):
                            print(f"🔴 ISSUE: AI extracts {found_enhanced} fields but only {len(after_filled)} stored!")
                            print(f"       Data persistence problem in _apply_analysis_to_company()")
                    else:
                        print(f"   ❌ AI analysis failed: {analysis}")
                        
                except Exception as e:
                    print(f"   ❌ AI test error: {e}")
            
            if improvement > 0:
                print(f"\n🎉 SUCCESS: Enhanced extraction added {improvement} new fields!")
            else:
                print(f"\n😐 No improvements detected")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    quick_test()