#!/usr/bin/env python3
"""
Simple batch reprocess test focusing on the improvements
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import time

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.main_pipeline import TheodoreIntelligencePipeline
from src.models import CompanyIntelligenceConfig
from dotenv import load_dotenv

load_dotenv()

# Test companies from the sheet
TEST_COMPANIES = [
    {"name": "jelli.com", "website": "https://www.jelli.com"},
    {"name": "tritondigital.com", "website": "https://www.tritondigital.com"},
    {"name": "lotlinx.com", "website": "https://www.lotlinx.com"},
    {"name": "adtheorent.com", "website": "https://www.adtheorent.com"},
    {"name": "nativo.com", "website": "https://www.nativo.com"}
]

def test_batch_reprocess():
    """Test reprocessing with focus on extraction improvements"""
    
    print("🔄 Batch Reprocessing Test with Enhanced Extraction")
    print("=" * 70)
    print("Testing extraction improvements on 5 companies from the sheet")
    print("\nTarget fields: Location, Founded Year, Employee Count, Contact Info")
    print("=" * 70)
    
    # Initialize pipeline
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    results = []
    
    for i, company in enumerate(TEST_COMPANIES, 1):
        print(f"\n📍 [{i}/{len(TEST_COMPANIES)}] Processing: {company['name']}")
        start_time = time.time()
        
        try:
            result = pipeline.process_single_company(
                company['name'], 
                company['website']
            )
            
            process_time = time.time() - start_time
            
            # Check extraction results
            extracted_data = {
                'company': company['name'],
                'status': result.scrape_status,
                'process_time': f"{process_time:.1f}s",
                'location': result.location,
                'founding_year': result.founding_year,
                'employee_count': result.employee_count_range,
                'contact_info': len(result.contact_info) if result.contact_info else 0,
                'social_media': len(result.social_media) if result.social_media else 0,
                'products_count': len(result.products_services_offered) if result.products_services_offered else 0,
                'certifications': len(result.certifications) if result.certifications else 0,
                'raw_content_length': len(result.raw_content) if result.raw_content else 0
            }
            
            results.append(extracted_data)
            
            # Show immediate results
            if result.scrape_status == "success":
                print(f"   ✅ Success in {process_time:.1f}s")
                if result.location:
                    print(f"   📍 Location: {result.location}")
                if result.founding_year:
                    print(f"   📅 Founded: {result.founding_year}")
                if result.employee_count_range:
                    print(f"   👥 Employees: {result.employee_count_range}")
                if result.contact_info:
                    print(f"   📧 Contact info: {len(result.contact_info)} items")
                if result.social_media:
                    print(f"   🔗 Social media: {len(result.social_media)} profiles")
                    
                if not any([result.location, result.founding_year, result.employee_count_range]):
                    print(f"   ⚠️  No target fields extracted (content: {extracted_data['raw_content_length']} chars)")
            else:
                print(f"   ❌ Failed: {result.scrape_error}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results.append({
                'company': company['name'],
                'status': 'error',
                'error': str(e)
            })
    
    # Summary
    print(f"\n\n📊 BATCH PROCESSING SUMMARY")
    print("=" * 70)
    
    successful = [r for r in results if r.get('status') == 'success']
    print(f"Success rate: {len(successful)}/{len(TEST_COMPANIES)} ({len(successful)/len(TEST_COMPANIES)*100:.0f}%)")
    
    # Count field extractions
    location_count = sum(1 for r in results if r.get('location'))
    founding_count = sum(1 for r in results if r.get('founding_year'))
    employee_count = sum(1 for r in results if r.get('employee_count'))
    contact_count = sum(1 for r in results if r.get('contact_info', 0) > 0)
    social_count = sum(1 for r in results if r.get('social_media', 0) > 0)
    
    print(f"\n📈 Field Extraction Results:")
    print(f"   Location: {location_count}/{len(TEST_COMPANIES)} ({location_count/len(TEST_COMPANIES)*100:.0f}%)")
    print(f"   Founded Year: {founding_count}/{len(TEST_COMPANIES)} ({founding_count/len(TEST_COMPANIES)*100:.0f}%)")
    print(f"   Employee Count: {employee_count}/{len(TEST_COMPANIES)} ({employee_count/len(TEST_COMPANIES)*100:.0f}%)")
    print(f"   Contact Info: {contact_count}/{len(TEST_COMPANIES)} ({contact_count/len(TEST_COMPANIES)*100:.0f}%)")
    print(f"   Social Media: {social_count}/{len(TEST_COMPANIES)} ({social_count/len(TEST_COMPANIES)*100:.0f}%)")
    
    # Show details
    print(f"\n📋 Detailed Results:")
    print("-" * 70)
    for r in results:
        if r.get('status') == 'success':
            print(f"\n{r['company']}:")
            print(f"   Content scraped: {r.get('raw_content_length', 0):,} chars")
            if r.get('location'):
                print(f"   ✓ Location: {r['location']}")
            if r.get('founding_year'):
                print(f"   ✓ Founded: {r['founding_year']}")
            if r.get('employee_count'):
                print(f"   ✓ Employees: {r['employee_count']}")
            if r.get('products_count', 0) > 0:
                print(f"   ✓ Products/Services: {r['products_count']} items")
    
    print(f"\n💡 Analysis:")
    avg_content = sum(r.get('raw_content_length', 0) for r in results) / len(results) if results else 0
    print(f"   Average content extracted: {avg_content:,.0f} chars")
    
    if avg_content < 1000:
        print(f"   ⚠️  Low content extraction - may need to adjust scraping strategy")
    else:
        print(f"   ✅ Good content extraction volume")
    
    if location_count == 0 and founding_count == 0:
        print(f"   ⚠️  Target fields not being extracted - check pattern matching")
    else:
        print(f"   ✅ Pattern extraction is working for some fields")

if __name__ == "__main__":
    test_batch_reprocess()