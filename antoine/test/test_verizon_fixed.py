#!/usr/bin/env python3
"""
Test Verizon with fallback paths fix
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load env vars
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

from src.main_pipeline import TheodoreIntelligencePipeline
from src.models import CompanyData, CompanyIntelligenceConfig

def test_verizon_with_fix():
    """Test Verizon extraction with fallback paths"""
    
    print("=" * 80)
    print("VERIZON TEST WITH FALLBACK PATHS")
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
        name="Verizon",
        website="https://www.verizon.com"
    )
    
    print(f"\n🏢 Testing: {company.name}")
    print(f"🌐 Website: {company.website}")
    
    # Process the company
    print("\n🚀 Starting extraction process...")
    print("Note: Discovery may timeout due to massive sitemap structure")
    print("Fallback paths will be used if discovery fails")
    
    start_time = time.time()
    
    try:
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
                ('products_services_offered', 'Products/Services')
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
            
            # Check pages crawled
            pages_crawled = getattr(result, 'pages_crawled', [])
            print(f"\n📄 Pages crawled: {len(pages_crawled)}")
            if pages_crawled:
                for i, page in enumerate(pages_crawled[:5]):
                    print(f"  {i+1}. {page}")
                if len(pages_crawled) > 5:
                    print(f"  ... and {len(pages_crawled) - 5} more")
                    
        else:
            print(f"\n❌ Extraction failed: {result.scrape_error}")
            
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_verizon_with_fix()