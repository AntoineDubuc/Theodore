#!/usr/bin/env python3
"""
Test Rogers extraction with all fixes applied
"""

import sys
import os
import json
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load env vars
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

from src.main_pipeline import TheodoreIntelligencePipeline
from src.models import CompanyData, CompanyIntelligenceConfig

def test_rogers_with_fixes():
    """Test Rogers extraction end-to-end with all fixes"""
    
    print("=" * 80)
    print("ROGERS END-TO-END TEST WITH FIXES")
    print("=" * 80)
    print("\nFixes applied:")
    print("1. ✅ Classification module import fixed")
    print("2. ✅ is_saas defaults to False instead of None")
    print("3. ✅ Timeout increased to 60 seconds")
    print("4. ✅ Path filtering for large websites")
    print("=" * 80)
    
    # Initialize pipeline
    print("\n📍 Initializing Theodore pipeline...")
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment='gcp-starter',
        pinecone_index=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
    )
    
    # Create company data
    company = CompanyData(
        name="Rogers Communications",
        website="https://www.rogers.com"
    )
    
    print(f"\n🏢 Testing: {company.name}")
    print(f"🌐 Website: {company.website}")
    
    # Process the company
    print("\n🚀 Starting extraction process...")
    start_time = time.time()
    
    try:
        # Process single company
        result = pipeline.process_single_company(
            company_name=company.name,
            website=company.website
        )
        
        elapsed_time = time.time() - start_time
        print(f"\n✅ Processing completed in {elapsed_time:.1f} seconds")
        
        # Check results
        print("\n📊 EXTRACTION RESULTS:")
        print(f"Scrape status: {result.scrape_status}")
        
        if result.scrape_status == "success":
            print("\n✅ Key fields extracted:")
            
            fields_to_check = [
                ('company_description', 'Company Description'),
                ('industry', 'Industry'),
                ('business_model', 'Business Model'),
                ('location', 'Location'),
                ('founding_year', 'Founded'),
                ('employee_count_range', 'Employees'),
                ('products_services_offered', 'Products/Services'),
                ('is_saas', 'Is SaaS'),
                ('saas_classification', 'SaaS Classification')
            ]
            
            for field, label in fields_to_check:
                value = getattr(result, field, None)
                if value and value != "unknown":
                    if isinstance(value, str) and len(value) > 60:
                        print(f"  ✅ {label}: {value[:60]}...")
                    else:
                        print(f"  ✅ {label}: {value}")
                else:
                    print(f"  ❌ {label}: Not found")
            
            # Count successful fields
            all_fields = vars(result)
            non_empty = sum(1 for k, v in all_fields.items() 
                          if v and v != "unknown" and v != [] and v != {})
            print(f"\n📈 Total fields populated: {non_empty}/{len(all_fields)}")
            
            # Check if stored in Pinecone
            print("\n🔍 Checking Pinecone storage...")
            stored_company = pipeline.pinecone_client.find_company_by_name("Rogers Communications")
            if stored_company:
                print("✅ Successfully stored in Pinecone!")
                print(f"   Company ID: {stored_company.id}")
            else:
                print("❌ Not found in Pinecone")
            
            # Save full result
            with open('rogers_fixed_result.json', 'w') as f:
                json.dump(vars(result), f, indent=2, default=str)
            print(f"\n💾 Full result saved to: rogers_fixed_result.json")
            
        else:
            print(f"\n❌ Extraction failed: {result.scrape_error}")
            
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rogers_with_fixes()