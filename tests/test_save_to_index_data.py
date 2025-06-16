#!/usr/bin/env python3
"""
Test to understand what data is actually being sent to save-to-index endpoint
This will help identify where the rich data is being lost in the process.
"""

import os
import json
import requests
from datetime import datetime

def test_research_data_structure():
    """Test what data structure the research process actually produces"""
    print("🔬 RESEARCH DATA STRUCTURE TEST")
    print("=" * 40)
    
    try:
        # Import progress logger to see what research data looks like
        from src.progress_logger import progress_logger
        
        print("📊 Checking recent research jobs...")
        all_progress = progress_logger.get_all_progress()
        
        # Find the most recent Walmart research
        walmart_jobs = []
        for job_id, job_data in all_progress.get('jobs', {}).items():
            company_name = job_data.get('company_name', '').lower()
            if 'walmart' in company_name and job_data.get('status') == 'completed':
                walmart_jobs.append((job_id, job_data))
        
        if walmart_jobs:
            # Get the most recent one
            latest_job = max(walmart_jobs, key=lambda x: x[1].get('end_time', ''))
            job_id, job_data = latest_job
            
            print(f"✅ Found recent Walmart research job: {job_id}")
            print(f"📅 End time: {job_data.get('end_time')}")
            print(f"📊 Status: {job_data.get('status')}")
            
            # Check if results exist
            if 'results' in job_data:
                results = job_data['results']
                print(f"📋 Research results contain {len(results)} fields")
                
                # Check specific rich data fields
                rich_fields = [
                    'ai_summary', 'company_description', 'value_proposition',
                    'key_services', 'competitive_advantages', 'tech_stack'
                ]
                
                print(f"\n🔍 Rich data fields in research results:")
                for field in rich_fields:
                    if field in results:
                        value = results[field]
                        if value and value != '' and value != []:
                            if isinstance(value, str):
                                print(f"  ✅ {field}: {len(value)} chars - '{value[:100]}...'")
                            elif isinstance(value, list):
                                print(f"  ✅ {field}: {len(value)} items - {value[:3]}...")
                            else:
                                print(f"  ✅ {field}: {type(value).__name__} - {value}")
                        else:
                            print(f"  ❌ {field}: EMPTY")
                    else:
                        print(f"  ❌ {field}: NOT FOUND")
                
                # Show all field names for reference
                print(f"\n📝 All fields in research results:")
                field_names = list(results.keys())
                field_names.sort()
                for i, field_name in enumerate(field_names):
                    if i < 20:  # Show first 20
                        value = results[field_name]
                        value_type = type(value).__name__
                        if isinstance(value, str) and len(value) > 50:
                            preview = f"'{value[:50]}...'"
                        elif isinstance(value, list) and len(value) > 0:
                            preview = f"[{len(value)} items]"
                        else:
                            preview = str(value)
                        print(f"    {field_name}: {value_type} = {preview}")
                    elif i == 20:
                        print(f"    ... and {len(field_names) - 20} more fields")
                        break
                        
            else:
                print(f"❌ No 'results' key in job data")
                print(f"📋 Available keys: {list(job_data.keys())}")
                
        else:
            print("❌ No completed Walmart research jobs found")
            print("📋 Available jobs:")
            for job_id, job_data in list(all_progress.get('jobs', {}).items())[:5]:
                company_name = job_data.get('company_name', 'Unknown')
                status = job_data.get('status', 'unknown')
                print(f"  {job_id}: {company_name} - {status}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_api_endpoint_simulation():
    """Simulate what gets sent to the save-to-index endpoint"""
    print(f"\n🧪 API ENDPOINT SIMULATION")
    print("=" * 30)
    
    # Create mock research data that should contain rich fields
    mock_research_data = {
        'company_name': 'Test Company',
        'website': 'https://test.com',
        'industry': 'Technology',
        'business_model': 'B2B',
        'ai_summary': 'This is a comprehensive AI summary of the company with detailed insights about their business model, market position, and strategic advantages. It contains rich information that should be preserved in the database for future analysis.',
        'company_description': 'A detailed company description that explains what they do, their mission, and their market approach.',
        'value_proposition': 'Their unique value proposition that sets them apart from competitors.',
        'key_services': ['Service A', 'Service B', 'Service C'],
        'competitive_advantages': ['Advantage 1', 'Advantage 2'],
        'tech_stack': ['Python', 'React', 'AWS'],
        'target_market': 'Enterprise customers',
        'company_stage': 'Growth',
        'tech_sophistication': 'High'
    }
    
    print(f"📤 Mock research data structure:")
    print(f"  Total fields: {len(mock_research_data)}")
    
    # Calculate total size
    data_str = json.dumps(mock_research_data)
    data_size = len(data_str.encode('utf-8'))
    print(f"  Total size: {data_size:,} bytes")
    
    # Check each field
    for field_name, value in mock_research_data.items():
        if isinstance(value, str):
            print(f"    {field_name}: {len(value)} chars")
        elif isinstance(value, list):
            print(f"    {field_name}: {len(value)} items")
        else:
            print(f"    {field_name}: {type(value).__name__}")
    
    # Test what would happen with CompanyData conversion
    print(f"\n🔄 Testing CompanyData conversion...")
    try:
        from src.models import CompanyData
        
        # Try to create CompanyData object with rich data
        company_obj = CompanyData(
            name=mock_research_data['company_name'],
            website=mock_research_data['website'],
            industry=mock_research_data['industry'],
            business_model=mock_research_data['business_model'],
            ai_summary=mock_research_data['ai_summary'],
            company_description=mock_research_data['company_description'],
            value_proposition=mock_research_data['value_proposition'],
            key_services=mock_research_data['key_services'],
            competitive_advantages=mock_research_data['competitive_advantages'],
            tech_stack=mock_research_data['tech_stack'],
            target_market=mock_research_data['target_market'],
            company_stage=mock_research_data['company_stage'],
            tech_sophistication=mock_research_data['tech_sophistication']
        )
        
        print(f"✅ CompanyData object created successfully")
        
        # Check which fields are populated
        rich_fields = ['ai_summary', 'company_description', 'value_proposition']
        for field in rich_fields:
            value = getattr(company_obj, field, None)
            if value:
                print(f"  ✅ {field}: {len(value)} chars")
            else:
                print(f"  ❌ {field}: EMPTY")
                
    except Exception as e:
        print(f"❌ CompanyData conversion failed: {e}")

def proposed_fix():
    """Outline the specific fix needed"""
    print(f"\n💡 PROPOSED FIX")
    print("=" * 15)
    
    print("Based on the diagnosis:")
    print("1. 🔍 Rich data EXISTS in research results")
    print("2. ❌ Rich data is NOT making it to Pinecone metadata")
    print("3. ❌ JSON hybrid storage is NOT being created")
    print("4. 🎯 The issue is in the save-to-index data transfer process")
    
    print(f"\n🛠️ SPECIFIC ACTIONS NEEDED:")
    print("1. Check if research_data is properly passed to save-to-index")
    print("2. Verify CompanyData object creation includes ALL rich fields")
    print("3. Ensure _prepare_optimized_metadata includes rich fields")
    print("4. Fix or implement JSON file creation for hybrid storage")
    print("5. Update get_company_details to read from JSON files")
    
    print(f"\n⚠️ ROOT CAUSE LIKELY:")
    print("- Dynamic field transfer logic is working")
    print("- But _prepare_optimized_metadata() excludes rich fields")
    print("- And JSON file creation is not happening")
    print("- So rich data gets lost in the metadata preparation step")

if __name__ == "__main__":
    print("🚀 SAVE-TO-INDEX DATA ANALYSIS")
    print(f"Timestamp: {datetime.now()}")
    
    test_research_data_structure()
    test_api_endpoint_simulation()
    proposed_fix()
    
    print(f"\n✅ ANALYSIS COMPLETE")