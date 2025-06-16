#!/usr/bin/env python3
"""
Isolated test to diagnose Pinecone storage issues and understand current patterns
This test will:
1. Check what's currently stored in Pinecone for Walmart
2. Test the existing storage/retrieval methods
3. Identify why rich data is being lost
4. Propose the correct fix without touching main codebase
"""

import os
import json
from dotenv import load_dotenv
from datetime import datetime

# Load environment
load_dotenv()

def test_current_pinecone_storage():
    """Test current Pinecone storage patterns"""
    print("🔬 PINECONE STORAGE DIAGNOSIS")
    print("=" * 50)
    
    try:
        # Initialize components
        from src.models import CompanyIntelligenceConfig
        from src.pinecone_client import PineconeClient
        
        config = CompanyIntelligenceConfig()
        pinecone_client = PineconeClient(
            config=config,
            api_key=os.getenv('PINECONE_API_KEY'),
            environment=os.getenv('PINECONE_ENVIRONMENT', 'us-west1-gcp'),
            index_name=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        )
        
        print("✅ Pinecone client initialized")
        
        # Find Walmart in the database
        print("\n🔍 STEP 1: Finding Walmart in Pinecone")
        walmart_company = pinecone_client.find_company_by_name("Walmart")
        
        if walmart_company:
            print(f"✅ Found Walmart with ID: {walmart_company.id}")
            print(f"📊 Basic info - Name: {walmart_company.name}, Industry: {walmart_company.industry}")
            
            # Check what fields are populated
            populated_fields = []
            empty_fields = []
            
            for field_name in dir(walmart_company):
                if not field_name.startswith('_') and hasattr(walmart_company, field_name):
                    value = getattr(walmart_company, field_name)
                    if value is not None and value != '' and value != [] and not callable(value):
                        populated_fields.append(f"{field_name}: {type(value).__name__}")
                    elif not callable(value):
                        empty_fields.append(field_name)
            
            print(f"\n📈 POPULATED FIELDS ({len(populated_fields)}):")
            for field in populated_fields[:10]:  # Show first 10
                print(f"  ✅ {field}")
            if len(populated_fields) > 10:
                print(f"  ... and {len(populated_fields) - 10} more")
                
            print(f"\n📉 EMPTY FIELDS ({len(empty_fields)}):")
            for field in empty_fields[:10]:  # Show first 10
                print(f"  ❌ {field}")
            if len(empty_fields) > 10:
                print(f"  ... and {len(empty_fields) - 10} more")
                
            # Check specific rich data fields
            print(f"\n🔍 STEP 2: Checking Rich Data Fields")
            rich_fields = {
                'ai_summary': walmart_company.ai_summary,
                'company_description': walmart_company.company_description,
                'value_proposition': walmart_company.value_proposition,
                'key_services': walmart_company.key_services,
                'competitive_advantages': walmart_company.competitive_advantages
            }
            
            for field_name, value in rich_fields.items():
                if value and value != '' and value != []:
                    print(f"  ✅ {field_name}: {len(str(value))} chars")
                else:
                    print(f"  ❌ {field_name}: EMPTY")
                    
        else:
            print("❌ Walmart not found in Pinecone")
            return
            
        # Test direct Pinecone fetch
        print(f"\n🔍 STEP 3: Direct Pinecone Metadata Check")
        try:
            result = pinecone_client.index.fetch(ids=[walmart_company.id])
            if walmart_company.id in result.vectors:
                metadata = result.vectors[walmart_company.id].metadata or {}
                print(f"📊 Raw Pinecone metadata fields: {len(metadata)}")
                
                # Check for rich data in metadata
                rich_metadata_fields = ['ai_summary', 'company_description', 'value_proposition']
                for field in rich_metadata_fields:
                    if field in metadata:
                        value = metadata[field]
                        if value and value != '':
                            print(f"  ✅ {field} in metadata: {len(str(value))} chars")
                        else:
                            print(f"  ❌ {field} in metadata: EMPTY")
                    else:
                        print(f"  ❌ {field}: NOT IN METADATA")
                        
                # Calculate metadata size
                metadata_str = json.dumps(metadata)
                metadata_size = len(metadata_str.encode('utf-8'))
                print(f"📏 Total metadata size: {metadata_size:,} bytes")
                
                if metadata_size > 40960:  # 40KB limit
                    print(f"⚠️ METADATA EXCEEDS 40KB LIMIT! ({metadata_size:,} bytes)")
                else:
                    print(f"✅ Metadata within 40KB limit")
                    
            else:
                print("❌ Could not fetch vector data")
                
        except Exception as e:
            print(f"❌ Direct fetch failed: {e}")
            
        # Check for existing JSON files
        print(f"\n🔍 STEP 4: Checking for Hybrid Storage")
        json_file_path = f"data/company_details/{walmart_company.id}.json"
        if os.path.exists(json_file_path):
            print(f"✅ JSON file exists: {json_file_path}")
            try:
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                print(f"📊 JSON file contains {len(json_data)} fields")
                
                # Check rich data in JSON
                for field in rich_metadata_fields:
                    if field in json_data:
                        value = json_data[field]
                        if value and value != '':
                            print(f"  ✅ {field} in JSON: {len(str(value))} chars")
                        else:
                            print(f"  ❌ {field} in JSON: EMPTY")
                    else:
                        print(f"  ❌ {field}: NOT IN JSON")
                        
            except Exception as e:
                print(f"❌ Could not read JSON file: {e}")
        else:
            print(f"❌ No JSON file found at {json_file_path}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_metadata_size_limits():
    """Test what happens when we exceed Pinecone metadata limits"""
    print(f"\n🧪 METADATA SIZE LIMIT TEST")
    print("=" * 30)
    
    # Create sample rich data
    sample_data = {
        'company_name': 'Test Company',
        'ai_summary': 'A' * 10000,  # 10KB of text
        'company_description': 'B' * 15000,  # 15KB of text
        'value_proposition': 'C' * 20000,  # 20KB of text
        'key_services': ['Service ' + str(i) for i in range(1000)],  # Large array
    }
    
    # Test metadata size
    metadata_str = json.dumps(sample_data)
    metadata_size = len(metadata_str.encode('utf-8'))
    
    print(f"📏 Sample metadata size: {metadata_size:,} bytes")
    print(f"📊 40KB limit: {40960:,} bytes")
    
    if metadata_size > 40960:
        print(f"⚠️ WOULD EXCEED LIMIT by {metadata_size - 40960:,} bytes")
        
        # Show what gets truncated
        print(f"\n🔍 Field sizes:")
        for field, value in sample_data.items():
            if isinstance(value, str):
                size = len(value.encode('utf-8'))
                print(f"  {field}: {size:,} bytes")
            elif isinstance(value, list):
                size = len(json.dumps(value).encode('utf-8'))
                print(f"  {field}: {size:,} bytes (array)")
    else:
        print(f"✅ Within limit")

def proposed_solution():
    """Outline the correct solution based on findings"""
    print(f"\n💡 PROPOSED SOLUTION")
    print("=" * 20)
    
    print("Based on diagnosis, the solution should:")
    print("1. ✅ Use existing _prepare_optimized_metadata() for essential fields")
    print("2. ✅ Store rich data separately (JSON files or vector content)")
    print("3. ✅ Modify get_full_company_data() to combine both sources")
    print("4. ✅ Update v2_app.py /api/company/<id> to use combined retrieval")
    print("5. ❌ DO NOT duplicate existing hybrid storage code")
    
    print(f"\n🎯 ROOT CAUSE HYPOTHESIS:")
    print("- Rich data IS being sent to save-to-index")
    print("- But it's being TRUNCATED by Pinecone 40KB metadata limit") 
    print("- Existing hybrid storage might not be working correctly")
    print("- JSON files aren't being created/read properly")

if __name__ == "__main__":
    print("🚀 STARTING PINECONE STORAGE DIAGNOSIS")
    print(f"Timestamp: {datetime.now()}")
    
    test_current_pinecone_storage()
    test_metadata_size_limits()
    proposed_solution()
    
    print(f"\n✅ DIAGNOSIS COMPLETE")