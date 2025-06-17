#!/usr/bin/env python3
"""
Test fresh retrieval to verify our data persistence fix worked.
"""

import os
import sys

sys.path.append('.')
from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Load environment
load_dotenv()

def test_fresh_retrieval():
    """Test fresh data retrieval"""
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    print("=" * 80)
    print("TESTING FRESH DATA RETRIEVAL AFTER FIX")
    print("=" * 80)
    
    # Get all companies fresh from database
    companies = pipeline.pinecone_client.find_companies_by_filters({}, top_k=15)
    
    print(f"📊 FOUND {len(companies)} COMPANIES")
    print()
    
    # Check connatix specifically
    connatix_found = False
    for i, company in enumerate(companies, 1):
        metadata = company.get('metadata', {})
        company_name = metadata.get('company_name', f'Company_{i}')
        
        if 'connatix' in company_name.lower():
            connatix_found = True
            print(f"🎯 FOUND CONNATIX: {company_name}")
            print(f"   ID: {company.get('id')}")
            
            # Check ALL enhanced fields
            enhanced_fields = [
                'raw_content', 'founding_year', 'location', 'employee_count_range',
                'leadership_team', 'contact_info', 'social_media', 'company_description',
                'value_proposition', 'funding_status', 'partnerships', 'awards'
            ]
            
            filled_count = 0
            for field in enhanced_fields:
                value = metadata.get(field)
                has_data = False
                
                if value is not None:
                    if isinstance(value, str) and value.strip():
                        has_data = True
                        if field == 'raw_content':
                            print(f"   ✅ {field}: {len(value):,} chars")
                        elif len(value) > 100:
                            print(f"   ✅ {field}: {value[:100]}...")
                        else:
                            print(f"   ✅ {field}: {value}")
                    elif isinstance(value, (list, dict)) and len(value) > 0:
                        has_data = True
                        print(f"   ✅ {field}: {value}")
                    elif isinstance(value, (int, float)) and value > 0:
                        has_data = True
                        print(f"   ✅ {field}: {value}")
                
                if has_data:
                    filled_count += 1
                else:
                    print(f"   ❌ {field}: Empty/None")
            
            print(f"\n📊 CONNATIX RESULTS:")
            print(f"   Enhanced fields filled: {filled_count}/{len(enhanced_fields)}")
            print(f"   Success rate: {(filled_count/len(enhanced_fields)*100):.1f}%")
            
            break
    
    if not connatix_found:
        print("❌ Connatix not found in database")
        print("\nAvailable companies:")
        for i, company in enumerate(companies[:5], 1):
            metadata = company.get('metadata', {})
            company_name = metadata.get('company_name', f'Company_{i}')
            print(f"   {i}. {company_name}")
    
    # Also test direct retrieval by ID
    print(f"\n🧪 TESTING DIRECT RETRIEVAL:")
    try:
        # Try to find connatix by name first
        direct_company = pipeline.pinecone_client.find_company_by_name("connatix.com")
        if direct_company:
            print(f"✅ Direct retrieval successful")
            print(f"   Company ID: {direct_company.id}")
            print(f"   Raw content: {len(direct_company.raw_content) if direct_company.raw_content else 0:,} chars")
            print(f"   Leadership team: {direct_company.leadership_team}")
            print(f"   Location: {direct_company.location}")
            print(f"   Founding year: {direct_company.founding_year}")
            print(f"   Contact info: {direct_company.contact_info}")
            print(f"   Pages crawled: {len(direct_company.pages_crawled) if direct_company.pages_crawled else 0}")
        else:
            print("❌ Direct retrieval failed")
    except Exception as e:
        print(f"❌ Direct retrieval error: {e}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_fresh_retrieval()