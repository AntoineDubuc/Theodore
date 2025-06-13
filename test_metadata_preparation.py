#!/usr/bin/env python3
"""
Test to understand what _prepare_optimized_metadata() is actually doing
This will show us exactly why rich data fields are being excluded.
"""

import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def test_metadata_preparation():
    """Test what _prepare_optimized_metadata actually produces"""
    print("🔬 METADATA PREPARATION TEST")
    print("=" * 35)
    
    try:
        # Initialize components
        from src.models import CompanyIntelligenceConfig, CompanyData
        from src.pinecone_client import PineconeClient
        
        config = CompanyIntelligenceConfig()
        pinecone_client = PineconeClient(
            config=config,
            api_key=os.getenv('PINECONE_API_KEY'),
            environment=os.getenv('PINECONE_ENVIRONMENT', 'us-west1-gcp'),
            index_name=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        )
        
        print("✅ Components initialized")
        
        # Create a CompanyData object with rich data (like what should come from research)
        rich_company_data = CompanyData(
            name="Test Rich Company",
            website="https://test.com",
            industry="Technology",
            business_model="B2B",
            target_market="Enterprise customers",
            company_size="Large",
            # Rich data fields that should be preserved
            ai_summary="This is a comprehensive AI-generated summary of the company that contains detailed insights about their business operations, market position, competitive advantages, and strategic direction. This text should be preserved in the database for complete company intelligence.",
            company_description="A detailed company description that explains their core business, mission, vision, and approach to serving their customers in the technology sector.",
            value_proposition="Their unique value proposition centers around innovative technology solutions that help enterprise customers streamline operations and reduce costs.",
            key_services=["Cloud Infrastructure", "Data Analytics", "AI Consulting", "Custom Software Development"],
            competitive_advantages=["Advanced AI Technology", "Industry Expertise", "Global Scale", "24/7 Support"],
            tech_stack=["Python", "React", "AWS", "Kubernetes", "TensorFlow"],
            pain_points=["Complex integration requirements", "Scaling challenges", "Legacy system dependencies"],
            # Similarity fields
            company_stage="Growth",
            tech_sophistication="High",
            business_model_type="SaaS",
            geographic_scope="Global",
            decision_maker_type="Technical",
            # Other fields
            founding_year="2015",
            location="San Francisco, CA",
            employee_count_range="1000-5000",
            funding_status="Series C",
            has_chat_widget=True,
            has_forms=True
        )
        
        print(f"📊 Created rich CompanyData object with populated fields:")
        
        # Count populated fields
        populated_fields = []
        for field_name in ['ai_summary', 'company_description', 'value_proposition', 'key_services', 
                          'competitive_advantages', 'tech_stack', 'pain_points']:
            value = getattr(rich_company_data, field_name, None)
            if value and value != '' and value != []:
                if isinstance(value, str):
                    populated_fields.append(f"{field_name}: {len(value)} chars")
                elif isinstance(value, list):
                    populated_fields.append(f"{field_name}: {len(value)} items")
                    
        for field in populated_fields:
            print(f"  ✅ {field}")
            
        # Test _prepare_optimized_metadata
        print(f"\n🔍 Testing _prepare_optimized_metadata()...")
        try:
            optimized_metadata = pinecone_client._prepare_optimized_metadata(rich_company_data)
            
            print(f"📊 Optimized metadata contains {len(optimized_metadata)} fields:")
            
            # Check which rich fields made it through
            rich_fields_in_metadata = []
            rich_fields_missing = []
            
            rich_field_names = ['ai_summary', 'company_description', 'value_proposition', 'key_services', 
                               'competitive_advantages', 'tech_stack', 'pain_points']
            
            for field_name in rich_field_names:
                if field_name in optimized_metadata:
                    value = optimized_metadata[field_name]
                    if value and value != '' and value != []:
                        if isinstance(value, str):
                            rich_fields_in_metadata.append(f"{field_name}: {len(value)} chars")
                        elif isinstance(value, list):
                            rich_fields_in_metadata.append(f"{field_name}: {len(value)} items")
                        else:
                            rich_fields_in_metadata.append(f"{field_name}: {type(value).__name__}")
                    else:
                        rich_fields_missing.append(f"{field_name}: EMPTY in metadata")
                else:
                    rich_fields_missing.append(f"{field_name}: NOT in metadata")
            
            print(f"\n✅ Rich fields PRESERVED in metadata ({len(rich_fields_in_metadata)}):")
            for field in rich_fields_in_metadata:
                print(f"  ✅ {field}")
                
            print(f"\n❌ Rich fields LOST in metadata ({len(rich_fields_missing)}):")
            for field in rich_fields_missing:
                print(f"  ❌ {field}")
                
            # Show all metadata fields
            print(f"\n📋 ALL metadata fields created:")
            for key, value in optimized_metadata.items():
                if isinstance(value, str):
                    display_value = f"'{value[:50]}...'" if len(value) > 50 else f"'{value}'"
                elif isinstance(value, list):
                    display_value = f"[{len(value)} items]"
                else:
                    display_value = str(value)
                print(f"  {key}: {type(value).__name__} = {display_value}")
                
            # Check metadata size
            import json
            metadata_str = json.dumps(optimized_metadata)
            metadata_size = len(metadata_str.encode('utf-8'))
            print(f"\n📏 Optimized metadata size: {metadata_size:,} bytes")
            print(f"📊 40KB limit: {40960:,} bytes")
            
            if metadata_size > 40960:
                print(f"⚠️ EXCEEDS 40KB LIMIT by {metadata_size - 40960:,} bytes")
            else:
                print(f"✅ Within 40KB limit ({40960 - metadata_size:,} bytes remaining)")
                
        except Exception as e:
            print(f"❌ _prepare_optimized_metadata failed: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def examine_current_optimization_logic():
    """Look at what the current _prepare_optimized_metadata actually does"""
    print(f"\n📖 EXAMINING OPTIMIZATION LOGIC")
    print("=" * 35)
    
    try:
        # Read the actual implementation
        import inspect
        from src.pinecone_client import PineconeClient
        from src.models import CompanyIntelligenceConfig
        
        config = CompanyIntelligenceConfig()
        client = PineconeClient(config, "dummy", "dummy", "dummy")
        
        # Get the source code of _prepare_optimized_metadata
        source = inspect.getsource(client._prepare_optimized_metadata)
        
        print("🔍 Current _prepare_optimized_metadata logic:")
        print("-" * 50)
        
        # Extract the field mapping logic
        lines = source.split('\n')
        in_metadata_section = False
        
        for line in lines:
            if 'metadata = {' in line:
                in_metadata_section = True
            if in_metadata_section:
                if line.strip().startswith('"') or line.strip().startswith("'"):
                    # This is a metadata field definition
                    field_line = line.strip()
                    if ':' in field_line:
                        field_name = field_line.split(':')[0].strip(' "\'')
                        print(f"  📝 {field_name}")
                if '}' in line and in_metadata_section:
                    break
                    
    except Exception as e:
        print(f"❌ Could not examine logic: {e}")

def test_proposed_solution():
    """Test the proposed solution: add missing rich fields to metadata preparation"""
    print(f"\n🧪 TESTING PROPOSED SOLUTION")
    print("=" * 30)
    
    try:
        # Initialize components
        from src.models import CompanyIntelligenceConfig, CompanyData
        from src.pinecone_client import PineconeClient
        
        config = CompanyIntelligenceConfig()
        pinecone_client = PineconeClient(
            config=config,
            api_key=os.getenv('PINECONE_API_KEY'),
            environment=os.getenv('PINECONE_ENVIRONMENT', 'us-west1-gcp'),
            index_name=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        )
        
        print("✅ Components initialized")
        
        # Create a test company with rich data
        test_company = CompanyData(
            name="Test Solution Company",
            website="https://testsolution.com",
            industry="Technology",
            business_model="B2B",
            target_market="Enterprise customers",
            company_size="Large",
            # Rich data fields that should be preserved
            ai_summary="This is an AI-generated summary that should be preserved in the database for complete company intelligence. It contains detailed insights about business operations and strategic direction.",
            company_description="A detailed company description that explains their core business, mission, and market approach.",
            value_proposition="Their unique value proposition centers around innovative solutions for enterprise customers.",
            key_services=["Service A", "Service B", "Service C"],
            competitive_advantages=["Advantage 1", "Advantage 2", "Advantage 3"],
            tech_stack=["Python", "React", "AWS"],
            pain_points=["Challenge 1", "Challenge 2"],
            # Similarity fields
            company_stage="Growth",
            tech_sophistication="High",
            business_model_type="SaaS"
        )
        
        print(f"📊 Created test company with rich data")
        
        # STEP 1: Test current metadata preparation (shows the problem)
        print(f"\n🔍 STEP 1: Current metadata preparation (showing the problem)")
        current_metadata = pinecone_client._prepare_optimized_metadata(test_company)
        
        rich_field_names = ['ai_summary', 'company_description', 'value_proposition', 'key_services', 
                           'competitive_advantages', 'tech_stack', 'pain_points']
        
        print(f"Current metadata contains {len(current_metadata)} fields")
        missing_rich_fields = []
        preserved_rich_fields = []
        
        for field_name in rich_field_names:
            if field_name in current_metadata and current_metadata[field_name]:
                preserved_rich_fields.append(field_name)
            else:
                missing_rich_fields.append(field_name)
        
        print(f"✅ Rich fields preserved: {len(preserved_rich_fields)} - {preserved_rich_fields}")
        print(f"❌ Rich fields missing: {len(missing_rich_fields)} - {missing_rich_fields}")
        
        # STEP 2: Create enhanced metadata preparation function
        print(f"\n🛠️ STEP 2: Creating enhanced metadata preparation")
        
        def _prepare_enhanced_metadata(company: CompanyData):
            """Enhanced metadata preparation that includes rich data fields"""
            
            def safe_get(value, default="Unknown"):
                """Safely get value with default"""
                return value if value and str(value).strip() else default
            
            def safe_list_to_str(items, separator=", "):
                """Convert list to string safely"""
                if not items:
                    return ""
                if isinstance(items, str):
                    return items
                return separator.join(str(item) for item in items if item)
            
            # Start with current metadata
            metadata = {
                # Core identification
                "company_name": safe_get(company.name),
                "website": safe_get(company.website),
                
                # Basic business info
                "industry": safe_get(company.industry),
                "business_model": safe_get(company.business_model),
                "target_market": safe_get(company.target_market),
                "company_size": safe_get(company.company_size),
                
                # Similarity dimensions
                "company_stage": safe_get(company.company_stage),
                "tech_sophistication": safe_get(company.tech_sophistication),
                "business_model_type": safe_get(company.business_model_type),
                
                # *** THE FIX: ADD MISSING RICH DATA FIELDS ***
                "ai_summary": safe_get(company.ai_summary, ""),
                "company_description": safe_get(company.company_description, ""),
                "value_proposition": safe_get(company.value_proposition, ""),
                "key_services": safe_list_to_str(company.key_services),
                "competitive_advantages": safe_list_to_str(company.competitive_advantages),
                "tech_stack": safe_list_to_str(company.tech_stack),
                "pain_points": safe_list_to_str(company.pain_points),
                
                # Processing metadata
                "has_description": bool(company.company_description and company.company_description.strip()),
                "scrape_status": safe_get(getattr(company, 'scrape_status', None), "unknown"),
                "last_updated": company.last_updated.isoformat() if company.last_updated else "",
            }
            
            return metadata
        
        # STEP 3: Test enhanced metadata preparation
        print(f"\n✅ STEP 3: Testing enhanced metadata preparation")
        enhanced_metadata = _prepare_enhanced_metadata(test_company)
        
        print(f"Enhanced metadata contains {len(enhanced_metadata)} fields")
        enhanced_missing = []
        enhanced_preserved = []
        
        for field_name in rich_field_names:
            if field_name in enhanced_metadata and enhanced_metadata[field_name]:
                enhanced_preserved.append(field_name)
            else:
                enhanced_missing.append(field_name)
        
        print(f"✅ Rich fields preserved: {len(enhanced_preserved)} - {enhanced_preserved}")
        print(f"❌ Rich fields missing: {len(enhanced_missing)} - {enhanced_missing}")
        
        # STEP 4: Check metadata size
        print(f"\n📏 STEP 4: Checking metadata size")
        import json
        
        current_size = len(json.dumps(current_metadata).encode('utf-8'))
        enhanced_size = len(json.dumps(enhanced_metadata).encode('utf-8'))
        
        print(f"Current metadata size: {current_size:,} bytes")
        print(f"Enhanced metadata size: {enhanced_size:,} bytes")
        print(f"Size increase: {enhanced_size - current_size:,} bytes")
        print(f"40KB limit: {40960:,} bytes")
        
        if enhanced_size > 40960:
            print(f"⚠️ EXCEEDS 40KB LIMIT by {enhanced_size - 40960:,} bytes")
        else:
            print(f"✅ Within 40KB limit ({40960 - enhanced_size:,} bytes remaining)")
        
        # STEP 5: Success validation
        print(f"\n🎯 STEP 5: Solution validation")
        
        if len(enhanced_preserved) > len(preserved_rich_fields):
            print(f"✅ SUCCESS: Enhanced metadata preserves {len(enhanced_preserved)} rich fields vs {len(preserved_rich_fields)} in current")
        else:
            print(f"❌ FAILURE: No improvement in rich field preservation")
        
        if enhanced_size <= 40960:
            print(f"✅ SUCCESS: Enhanced metadata stays within 40KB limit")
        else:
            print(f"❌ FAILURE: Enhanced metadata exceeds 40KB limit")
        
        if len(enhanced_missing) == 0:
            print(f"✅ SUCCESS: All rich fields are now preserved in metadata")
        else:
            print(f"⚠️ PARTIAL: {len(enhanced_missing)} rich fields still missing: {enhanced_missing}")
        
        # STEP 6: Implementation guidance
        print(f"\n📋 STEP 6: Implementation guidance")
        print("To implement this fix:")
        print("1. Edit src/pinecone_client.py")
        print("2. Modify _prepare_optimized_metadata() method around line 402")
        print("3. Add the missing rich fields to the metadata dictionary:")
        for field in ['ai_summary', 'value_proposition', 'key_services', 'competitive_advantages', 'tech_stack', 'pain_points']:
            if field in missing_rich_fields:
                if field in ['key_services', 'competitive_advantages', 'tech_stack', 'pain_points']:
                    print(f"   '{field}': safe_join(company.{field}),")
                else:
                    print(f"   '{field}': safe_get(company.{field}, ''),")
        
        print("4. Test the change with save-to-index functionality")
        print("5. Verify completion percentages improve in the UI")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def final_diagnosis():
    """Provide final diagnosis and solution"""
    print(f"\n🎯 FINAL DIAGNOSIS")
    print("=" * 20)
    
    print("The metadata preparation step determines what gets stored.")
    print("If rich fields aren't in _prepare_optimized_metadata, they're lost.")
    print("\n💡 SOLUTION:")
    print("1. ✅ Identify which rich fields are missing from _prepare_optimized_metadata")
    print("2. ✅ Add those fields to the metadata preparation")
    print("3. ✅ Ensure metadata stays under 40KB limit")
    print("4. ✅ Test that retrieval works correctly")
    print("\n⚠️ ALTERNATIVE:")
    print("If metadata gets too large, implement true hybrid storage:")
    print("1. Essential fields → Pinecone metadata")
    print("2. Rich text fields → JSON files") 
    print("3. Combined retrieval in get_company_details")

if __name__ == "__main__":
    print("🚀 METADATA PREPARATION ANALYSIS")
    print(f"Timestamp: {datetime.now()}")
    
    test_metadata_preparation()
    examine_current_optimization_logic()
    test_proposed_solution()  # NEW: Test the solution
    final_diagnosis()
    
    print(f"\n✅ ANALYSIS COMPLETE")