#!/usr/bin/env python3
"""
Test job extraction on a company that likely has job listings.
"""

import os
import sys

sys.path.append('.')
from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Load environment
load_dotenv()

def test_job_extraction():
    """Test job extraction on Alienware"""
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    print("=" * 60)
    print("TESTING JOB EXTRACTION ON ALIENWARE")
    print("=" * 60)
    
    company_name = "Alienware"
    
    # Reprocess to test job extraction
    try:
        updated_company = pipeline.process_single_company(company_name, "https://alienware.com")
        
        print(f"✅ Successfully reprocessed {company_name}")
        print(f"   Scrape status: {updated_company.scrape_status}")
        print(f"   Job listings count: {updated_company.job_listings_count}")
        print(f"   Job listings: {updated_company.job_listings}")
        print(f"   Job listings details: {updated_company.job_listings_details}")
        print(f"   Has job listings: {updated_company.has_job_listings}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_job_extraction()