#!/usr/bin/env python3
"""
Test the enhanced extraction prompt with Connatix leadership data.
"""

import os
import sys
import asyncio

sys.path.append('.')
from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Load environment
load_dotenv()

def test_enhanced_extraction():
    """Test enhanced extraction on Connatix"""
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    print("=" * 80)
    print("TESTING ENHANCED EXTRACTION: CONNATIX")
    print("=" * 80)
    print("Testing improved bedrock_client.py prompt with comprehensive field extraction")
    print()
    
    # Reprocess Connatix with the enhanced prompt
    try:
        print("🔄 Reprocessing Connatix with enhanced extraction...")
        company_data = pipeline.process_single_company("connatix.com", "https://connatix.com")
        
        print(f"✅ Reprocessing completed!")
        print(f"   Status: {company_data.scrape_status}")
        
        # Get the updated company from database
        updated_company = pipeline.pinecone_client.find_company_by_name("connatix.com")
        
        if updated_company:
            metadata = updated_company.__dict__ if hasattr(updated_company, '__dict__') else {}
            
            print("\n📊 EXTRACTION RESULTS:")
            print("=" * 50)
            
            # Test the specific fields we're trying to improve
            critical_fields = {
                'leadership_team': 'Leadership Team',
                'founding_year': 'Founding Year', 
                'location': 'Location',
                'employee_count_range': 'Employee Count',
                'contact_info': 'Contact Information',
                'social_media': 'Social Media',
                'company_culture': 'Company Culture',
                'partnerships': 'Partnerships',
                'awards': 'Awards',
                'funding_status': 'Funding Status'
            }
            
            improvements_found = 0
            
            for field_key, field_name in critical_fields.items():
                value = metadata.get(field_key)
                
                # Check if we have meaningful data
                has_data = False
                if value:
                    if isinstance(value, str) and value.strip() and value.lower() not in ['unknown', 'not specified', 'n/a']:
                        has_data = True
                    elif isinstance(value, (list, dict)) and len(value) > 0:
                        has_data = True
                    elif isinstance(value, (int, float)) and value > 0:
                        has_data = True
                
                if has_data:
                    print(f"✅ {field_name}: EXTRACTED")
                    if isinstance(value, (list, dict)):
                        print(f"   Value: {value}")
                    else:
                        preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                        print(f"   Value: {preview}")
                    improvements_found += 1
                else:
                    print(f"❌ {field_name}: Not extracted")
            
            print(f"\n📈 IMPROVEMENT SUMMARY:")
            print(f"   Fields extracted: {improvements_found}/{len(critical_fields)}")
            print(f"   Success rate: {(improvements_found/len(critical_fields)*100):.1f}%")
            
            # Show the full company description/content to verify we have the right content
            if metadata.get('company_description'):
                desc = metadata['company_description']
                print(f"\n📝 CONTENT PREVIEW (first 300 chars):")
                print(f"   {desc[:300]}...")
                
                # Check if leadership content is mentioned in the description
                if 'leadership' in desc.lower() or 'ceo' in desc.lower() or 'founder' in desc.lower():
                    print(f"   ✅ Leadership content detected in scraped content")
                else:
                    print(f"   ⚠️  No leadership mentions found in scraped content")
            
            # Specifically test leadership extraction
            leadership_data = metadata.get('leadership_team')
            if leadership_data:
                print(f"\n👥 LEADERSHIP EXTRACTION SUCCESS:")
                if isinstance(leadership_data, list):
                    for i, leader in enumerate(leadership_data, 1):
                        print(f"   {i}. {leader}")
                else:
                    print(f"   {leadership_data}")
            else:
                print(f"\n❌ LEADERSHIP EXTRACTION FAILED")
                print(f"   The enhanced prompt did not extract leadership data")
                print(f"   This suggests either:")
                print(f"   1. Leadership content wasn't in the scraped pages")
                print(f"   2. LLM couldn't parse the leadership information")
                print(f"   3. Content format is complex (images, tables, etc.)")
            
        else:
            print("❌ Could not retrieve updated company data")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_enhanced_extraction()