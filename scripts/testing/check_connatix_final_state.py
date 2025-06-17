#!/usr/bin/env python3
"""
Check the final state of Connatix after enhanced processing.
"""

import os
import sys

sys.path.append('.')
from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Load environment
load_dotenv()

def check_connatix_final_state():
    """Check final state of Connatix"""
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    print("=" * 80)
    print("CHECKING CONNATIX FINAL STATE")
    print("=" * 80)
    
    # Get current Connatix data
    connatix = pipeline.pinecone_client.find_company_by_name("connatix.com")
    
    if not connatix:
        print("❌ Connatix not found")
        return
    
    metadata = connatix.__dict__ if hasattr(connatix, '__dict__') else {}
    
    print("📊 ALL FIELDS IN DATABASE:")
    print("-" * 40)
    
    # Show all non-None fields
    for key, value in sorted(metadata.items()):
        if not key.startswith('_') and value is not None:
            if isinstance(value, str):
                display_value = value[:100] + "..." if len(value) > 100 else value
            elif isinstance(value, (list, dict)):
                display_value = f"{type(value).__name__}({len(value)} items)"
            else:
                display_value = str(value)
            
            print(f"✅ {key:25}: {display_value}")
    
    # Check if enhanced fields are present
    enhanced_fields = [
        'founding_year', 'location', 'employee_count_range', 'company_description',
        'value_proposition', 'leadership_team', 'contact_info', 'social_media',
        'funding_status', 'partnerships', 'awards', 'company_culture'
    ]
    
    print(f"\n📈 ENHANCED FIELDS CHECK:")
    print("-" * 40)
    found_enhanced = 0
    
    for field in enhanced_fields:
        value = metadata.get(field)
        if value and str(value).strip() and str(value).lower() not in ['unknown', 'not specified', 'n/a']:
            found_enhanced += 1
            if isinstance(value, (list, dict)):
                print(f"✅ {field:25}: {value}")
            else:
                display = str(value)[:80] + "..." if len(str(value)) > 80 else str(value)
                print(f"✅ {field:25}: {display}")
        else:
            print(f"❌ {field:25}: Not found")
    
    print(f"\n📊 SUMMARY:")
    print(f"Enhanced fields found: {found_enhanced}/{len(enhanced_fields)}")
    print(f"Success rate: {(found_enhanced/len(enhanced_fields)*100):.1f}%")
    
    # Check raw content and scraping results
    raw_content = metadata.get('raw_content')
    pages_crawled = metadata.get('pages_crawled')
    scrape_status = metadata.get('scrape_status')
    
    print(f"\n🔍 SCRAPING DETAILS:")
    print(f"Scrape status: {scrape_status}")
    print(f"Raw content: {len(raw_content) if raw_content else 0} chars")
    print(f"Pages crawled: {len(pages_crawled) if pages_crawled else 0}")
    
    if pages_crawled:
        print(f"Pages include:")
        for page in pages_crawled[:5]:
            print(f"  - {page}")
        if len(pages_crawled) > 5:
            print(f"  ... and {len(pages_crawled) - 5} more")
    
    # Test direct bedrock analysis
    print(f"\n🧪 TESTING BEDROCK ANALYSIS DIRECTLY:")
    if raw_content:
        try:
            from src.models import CompanyData
            test_company = CompanyData(
                name="connatix.com",
                website="https://connatix.com",
                raw_content=raw_content
            )
            
            analysis = pipeline.bedrock_client.analyze_company_content(test_company)
            
            print(f"Bedrock analysis result: {type(analysis)}")
            if isinstance(analysis, dict):
                enhanced_in_analysis = 0
                for field in enhanced_fields:
                    if field in analysis and analysis[field]:
                        enhanced_in_analysis += 1
                        print(f"✅ Bedrock found {field}: {analysis[field]}")
                
                print(f"\n🎯 BEDROCK SUCCESS: {enhanced_in_analysis}/{len(enhanced_fields)} enhanced fields")
                
                # Check why these aren't in the stored data
                if enhanced_in_analysis > found_enhanced:
                    print(f"🔴 ISSUE: Bedrock extracts {enhanced_in_analysis} fields but only {found_enhanced} are stored!")
                    print(f"       This indicates a data persistence problem in _apply_analysis_to_company()")
        
        except Exception as e:
            print(f"❌ Bedrock test error: {e}")
    else:
        print(f"❌ No raw content to test with")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_connatix_final_state()