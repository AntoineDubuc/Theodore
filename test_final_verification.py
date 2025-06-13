#!/usr/bin/env python3
"""
Final Verification Test - Test with a fresh company to verify the fix
This will save a new company and verify all rich fields are in Pinecone metadata
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_fresh_company_save():
    """Test saving a fresh company with the implemented fix"""
    print("🎯 FINAL VERIFICATION: Fresh Company Save Test")
    print("=" * 60)
    
    base_url = "http://localhost:5004"
    company_name = "TestCorp Fresh Verification"
    
    # Create test data with all rich fields
    research_data = {
        "company_name": company_name,
        "website": "https://testcorp.com",
        "industry": "Technology",
        "business_model": "B2B SaaS",
        "target_market": "Enterprise customers",
        "company_size": "Medium",
        
        # Rich data fields
        "ai_summary": "TestCorp is a technology company focused on innovative solutions for enterprise customers. This AI summary contains comprehensive insights about their business model and market position.",
        "company_description": "TestCorp provides enterprise software solutions with a focus on scalability and security.",
        "value_proposition": "Delivering enterprise-grade software solutions that scale with your business needs.",
        "key_services": ["Cloud Infrastructure", "Data Analytics", "Security Solutions"],
        "competitive_advantages": ["Advanced Technology", "24/7 Support", "Industry Expertise"],
        "tech_stack": ["Python", "React", "AWS", "Kubernetes"],
        "pain_points": ["Complex integration", "Legacy system support"],
        
        # Metadata
        "company_stage": "Growth",
        "tech_sophistication": "High",
        "business_model_type": "SaaS"
    }
    
    print(f"📋 Created test data for {company_name}")
    
    # Save to index
    save_payload = {
        "company_name": company_name,
        "research_data": research_data
    }
    
    print("📤 Saving to index...")
    response = requests.post(
        f"{base_url}/api/v2/save-to-index",
        json=save_payload,
        timeout=60
    )
    
    if response.status_code != 200:
        print(f"❌ Save failed: {response.status_code} - {response.text}")
        return False
    
    print("✅ Save to index succeeded")
    
    # Verify in Pinecone
    print("🔍 Verifying in Pinecone...")
    
    try:
        from src.models import CompanyIntelligenceConfig
        from src.pinecone_client import PineconeClient
        
        config = CompanyIntelligenceConfig()
        pinecone_client = PineconeClient(
            config=config,
            api_key=os.getenv('PINECONE_API_KEY'),
            environment=os.getenv('PINECONE_ENVIRONMENT', 'us-west1-gcp'),
            index_name=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        )
        
        # Find the company
        company = pinecone_client.find_company_by_name(company_name)
        if not company:
            print(f"❌ {company_name} not found in Pinecone")
            return False
        
        print(f"✅ Found {company_name} in Pinecone")
        
        # Get metadata
        metadata = pinecone_client.get_company_metadata(company.id)
        if not metadata:
            print("❌ No metadata found")
            return False
        
        print(f"📊 Metadata contains {len(metadata)} fields")
        
        # Check rich fields
        rich_fields = ['ai_summary', 'company_description', 'value_proposition', 'key_services', 'competitive_advantages', 'tech_stack', 'pain_points']
        preserved_count = 0
        
        for field in rich_fields:
            if field in metadata and metadata[field]:
                preserved_count += 1
                if isinstance(metadata[field], str):
                    preview = metadata[field][:50] + "..." if len(metadata[field]) > 50 else metadata[field]
                    print(f"✅ {field}: '{preview}'")
                else:
                    print(f"✅ {field}: {metadata[field]}")
            else:
                print(f"❌ {field}: MISSING from metadata")
        
        print(f"\n📈 FINAL RESULT: {preserved_count}/{len(rich_fields)} rich fields preserved in Pinecone")
        
        if preserved_count == len(rich_fields):
            print("🎉 SUCCESS: All rich fields are now preserved in Pinecone metadata!")
            print("✅ The fix is working correctly")
            print("✅ UI will show proper completion percentages")
            return True
        else:
            print("❌ FAILURE: Rich fields still not being preserved")
            return False
            
    except Exception as e:
        print(f"❌ Verification exception: {e}")
        return False

if __name__ == "__main__":
    print("🚀 FINAL VERIFICATION TEST")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    success = test_fresh_company_save()
    
    if success:
        print("\n🎉 IMPLEMENTATION SUCCESSFUL!")
        print("✅ Both fixes are working correctly:")
        print("  - FieldInfo serialization error: FIXED")
        print("  - Rich data preservation: FIXED") 
        print("  - UI completion percentages: WILL BE CORRECT")
        print("\n🎯 You can now use the UI workflow without issues!")
    else:
        print("\n💥 IMPLEMENTATION NEEDS MORE WORK")
        print("❌ The fixes are not yet fully working")
    
    print(f"\n✅ TEST COMPLETE")