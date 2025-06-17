#!/usr/bin/env python3
"""
Test enhanced extraction on a single company to demonstrate improvements
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.main_pipeline import TheodoreIntelligencePipeline
from src.models import CompanyIntelligenceConfig
from dotenv import load_dotenv

load_dotenv()

def test_single_company():
    """Test enhanced extraction on one company"""
    
    # Test with connatix.com which should have good data
    test_company = {
        "name": "Connatix",
        "website": "https://www.connatix.com"
    }
    
    print(f"🔬 Testing Enhanced Extraction on: {test_company['name']}")
    print("=" * 70)
    
    try:
        # Initialize pipeline
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME')
        )
        
        # Process with enhanced extraction
        print(f"\n🚀 Processing {test_company['name']} with enhanced extraction...")
        print("   - Using intelligent page selection targeting missing data")
        print("   - Applying pattern-based extraction")
        print("   - Using Gemini for detailed extraction\n")
        
        result = pipeline.process_single_company(
            test_company['name'], 
            test_company['website']
        )
        
        if result.scrape_status != "success":
            print(f"❌ Processing failed: {result.scrape_error}")
            return
        
        print(f"✅ Successfully processed {test_company['name']}")
        
        # Check what was extracted
        print(f"\n📊 Extraction Results:")
        print("-" * 70)
        
        # Target fields we're looking for
        target_extractions = {
            'location': result.location,
            'founding_year': result.founding_year,
            'employee_count_range': result.employee_count_range,
            'contact_info': result.contact_info,  # Dict with email, phone, etc.
            'social_media': result.social_media,
            'products_services_offered': result.products_services_offered,
            'leadership_team': result.leadership_team,
            'partnerships': result.partnerships,
            'certifications': result.certifications,
            'company_stage': result.company_stage,
            'target_market': result.target_market,
            'value_proposition': result.value_proposition,
            'company_size': result.company_size,
            'key_decision_makers': result.key_decision_makers
        }
        
        # Count successful extractions
        extracted_count = 0
        for field, value in target_extractions.items():
            if value:
                if isinstance(value, list) and len(value) > 0:
                    extracted_count += 1
                    print(f"✅ {field}: {value[:3] if len(value) > 3 else value}{'...' if len(value) > 3 else ''}")
                elif isinstance(value, dict) and len(value) > 0:
                    extracted_count += 1
                    print(f"✅ {field}: {dict(list(value.items())[:2])}{'...' if len(value) > 2 else ''}")
                elif isinstance(value, (str, int)) and str(value).strip():
                    extracted_count += 1
                    display_value = str(value)
                    if len(display_value) > 50:
                        display_value = display_value[:47] + "..."
                    print(f"✅ {field}: {display_value}")
            else:
                print(f"❌ {field}: Not extracted")
        
        print(f"\n📈 Extraction Summary:")
        print(f"   Extracted {extracted_count}/{len(target_extractions)} target fields")
        print(f"   Success rate: {extracted_count/len(target_extractions)*100:.1f}%")
        
        # Show AI summary
        if result.ai_summary:
            print(f"\n📝 AI Summary:")
            print(f"   {result.ai_summary[:200]}...")
        
        # Show which pages were selected
        if hasattr(result, 'selected_pages'):
            print(f"\n🔗 Pages Selected by LLM:")
            for i, page in enumerate(result.selected_pages[:5], 1):
                print(f"   {i}. {page}")
        
        # Save detailed results
        output_file = f"enhanced_extraction_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump({
                "company": test_company['name'],
                "website": test_company['website'],
                "extraction_results": {
                    field: str(value) if value else None 
                    for field, value in target_extractions.items()
                },
                "ai_summary": result.ai_summary,
                "scrape_status": result.scrape_status,
                "extraction_rate": f"{extracted_count/len(target_extractions)*100:.1f}%"
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        # Show comparison with baseline
        print(f"\n📊 IMPROVEMENT COMPARISON:")
        print("=" * 70)
        print("BEFORE (from spreadsheet analysis):")
        print("   - Location: ❌ Empty")
        print("   - Founded Year: ❌ Empty")
        print("   - Employee Count: ❌ Empty")
        print("   - Products/Services: ❌ Empty")
        print("   - Leadership Team: ❌ Empty")
        print("\nAFTER (with enhanced extraction):")
        print(f"   - Location: {'✅ ' + str(result.location) if result.location else '❌ Empty'}")
        print(f"   - Founded Year: {'✅ ' + str(result.founding_year) if result.founding_year else '❌ Empty'}")
        print(f"   - Employee Count: {'✅ ' + str(result.employee_count_range) if result.employee_count_range else '❌ Empty'}")
        print(f"   - Contact Info: {'✅ Found ' + str(len(result.contact_info)) + ' items' if result.contact_info else '❌ Empty'}")
        print(f"   - Social Media: {'✅ Found ' + str(len(result.social_media)) + ' profiles' if result.social_media else '❌ Empty'}")
        print(f"   - Products/Services: {'✅ Found ' + str(len(result.products_services_offered)) + ' items' if result.products_services_offered else '❌ Empty'}")
        print(f"   - Leadership Team: {'✅ Found ' + str(len(result.leadership_team)) + ' people' if result.leadership_team else '❌ Empty'}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_company()