#!/usr/bin/env python3
"""
Investigate what's actually stored in Pinecone for the FreeConvert company
"""

import sys
import os
sys.path.append('src')
from dotenv import load_dotenv
load_dotenv()

def investigate_freeconvert_data():
    print("🔍 INVESTIGATING STORED FREECONVERT DATA")
    print("="*60)
    
    try:
        from pinecone_client import PineconeClient
        from main_pipeline import find_company_by_name
        
        # Check what's stored in Pinecone
        print("1. CHECKING PINECONE STORAGE")
        print("-" * 30)
        
        # Search for FreeConvert in Pinecone
        companies = find_company_by_name("FreeConvert")
        
        if companies:
            print(f"✅ Found {len(companies)} FreeConvert entries in Pinecone")
            
            for i, company in enumerate(companies, 1):
                print(f"\n📊 COMPANY #{i}:")
                print(f"  ID: {company.get('id', 'N/A')}")
                print(f"  Name: {company.get('name', 'N/A')}")
                print(f"  Website: {company.get('website', 'N/A')}")
                
                # Check company_description field
                description = company.get('company_description', '')
                print(f"  Company Description Length: {len(description)} characters")
                print(f"  Company Description Preview: '{description[:200]}{'...' if len(description) > 200 else ''}'")
                
                # Check raw_content field
                raw_content = company.get('raw_content', '')
                print(f"  Raw Content Length: {len(raw_content)} characters")  
                print(f"  Raw Content Preview: '{raw_content[:200]}{'...' if len(raw_content) > 200 else ''}'")
                
                # Check other relevant fields
                pages_crawled = company.get('pages_crawled', [])
                print(f"  Pages Crawled: {len(pages_crawled)} pages")
                if pages_crawled:
                    print(f"  Sample Pages: {pages_crawled[:3]}")
                
        else:
            print("❌ No FreeConvert entries found in Pinecone")
            
    except Exception as e:
        print(f"❌ Pinecone investigation failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Check process logs for specific job
    print(f"\n2. CHECKING PROCESSING LOGS")
    print("-" * 30)
    
    try:
        import json
        with open('logs/processing_progress.json', 'r') as f:
            progress_data = json.load(f)
        
        # Look for the specific job that returned 148 chars
        target_job = "company_1750216888626" 
        
        if target_job in progress_data.get('jobs', {}):
            job_data = progress_data['jobs'][target_job]
            print(f"✅ Found job {target_job} in logs")
            print(f"  Company: {job_data.get('company_name')}")
            print(f"  Status: {job_data.get('status')}")
            print(f"  Results: {job_data.get('results', {})}")
            print(f"  Summary: {job_data.get('result_summary')}")
            
            # Check phases
            phases = job_data.get('phases', [])
            print(f"  Phases logged: {len(phases)}")
            for phase in phases:
                print(f"    - {phase.get('name')}: {phase.get('status')} ({phase.get('duration', 'N/A')}s)")
                if phase.get('details'):
                    details = phase['details']
                    if 'intelligence_length' in details:
                        print(f"      Intelligence Length: {details['intelligence_length']} chars")
        else:
            print(f"❌ Job {target_job} not found in processing logs")
            print(f"Available jobs: {list(progress_data.get('jobs', {}).keys())[-5:]}")
            
    except Exception as e:
        print(f"❌ Log investigation failed: {e}")
        import traceback
        traceback.print_exc()

def check_pipeline_processing():
    print(f"\n3. TESTING PIPELINE DIRECTLY")
    print("-" * 30)
    
    try:
        from main_pipeline import TheodoreIntelligencePipeline
        from models import CompanyIntelligenceConfig
        
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME')
        )
        
        print("✅ Pipeline initialized")
        
        # Try processing a small test case
        print("🧪 Testing with simple example...")
        result = pipeline.process_single_company(
            "Test Company", 
            "https://www.example.com",
            job_id="test_investigation"
        )
        
        if result:
            print(f"✅ Pipeline returned result")
            print(f"  Company Description Length: {len(result.company_description or '')}")
            print(f"  Raw Content Length: {len(result.raw_content or '')}")
            print(f"  Description Preview: '{(result.company_description or '')[:200]}'")
        else:
            print("❌ Pipeline returned None")
            
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigate_freeconvert_data()
    check_pipeline_processing()