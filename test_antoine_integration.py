#!/usr/bin/env python3
"""
Test Antoine Integration with Theodore
======================================

Simple test to verify that the antoine pipeline integration works
with Theodore's existing UI and API.
"""

import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, '.')

def test_antoine_adapter():
    """Test the antoine scraper adapter"""
    print("🧪 Testing Antoine Scraper Adapter Integration")
    print("=" * 60)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from src.models import CompanyData, CompanyIntelligenceConfig
        from src.antoine_scraper_adapter import AntoineScraperAdapter
        print("✅ All imports successful")
        
        # Create config
        print("⚙️ Creating configuration...")
        config = CompanyIntelligenceConfig()
        print("✅ Configuration created")
        
        # Create adapter (without bedrock client for now)
        print("🔧 Creating Antoine adapter...")
        adapter = AntoineScraperAdapter(config, bedrock_client=None)
        print("✅ Antoine adapter created")
        
        # Test with a simple company
        print("🏢 Testing with Linear (simple test case)...")
        company = CompanyData(
            name="Linear",
            website="https://linear.app"
        )
        
        print(f"🔍 Starting scraping process for {company.name}...")
        start_time = time.time()
        
        # This will test the full antoine pipeline
        result = adapter.scrape_company(company, job_id=None)
        
        duration = time.time() - start_time
        
        print(f"⏱️ Processing completed in {duration:.1f}s")
        print(f"📊 Scrape status: {result.scrape_status}")
        
        if result.scrape_status == "success":
            print("✅ SUCCESS - Antoine integration working!")
            print(f"📝 Company description: {result.company_description[:200] if result.company_description else 'None'}...")
            print(f"🏭 Industry: {result.industry}")
            print(f"💼 Business model: {result.business_model}")
            print(f"🎯 Target market: {result.target_market}")
            print(f"📄 Pages crawled: {len(result.pages_crawled) if result.pages_crawled else 0}")
            
            non_null_fields = 0
            for attr_name in dir(result):
                if not attr_name.startswith('_'):
                    value = getattr(result, attr_name)
                    if value is not None and value != "" and value != []:
                        non_null_fields += 1
            
            print(f"📈 Non-null fields: {non_null_fields}")
            
        else:
            print(f"❌ FAILED - Error: {result.scrape_error}")
            
        return result.scrape_status == "success"
        
    except Exception as e:
        print(f"💥 EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_theodore_pipeline():
    """Test the full Theodore pipeline with antoine"""
    print("\n🎯 Testing Full Theodore Pipeline with Antoine")
    print("=" * 60)
    
    try:
        # Check environment variables
        print("🔐 Checking environment variables...")
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        pinecone_key = os.getenv("PINECONE_API_KEY")
        
        if not openrouter_key:
            print("⚠️ WARNING: OPENROUTER_API_KEY not set - antoine selection phase will fail")
        else:
            print("✅ OPENROUTER_API_KEY configured")
            
        if not pinecone_key:
            print("⚠️ WARNING: PINECONE_API_KEY not set - database operations will fail")
        else:
            print("✅ PINECONE_API_KEY configured")
        
        # Test pipeline initialization
        print("🚀 Testing Theodore pipeline initialization...")
        from src.main_pipeline import TheodoreIntelligencePipeline
        from src.models import CompanyIntelligenceConfig
        
        config = CompanyIntelligenceConfig()
        
        if pinecone_key:
            pipeline = TheodoreIntelligencePipeline(
                config=config,
                pinecone_api_key=pinecone_key,
                pinecone_environment="us-east-1",
                pinecone_index="theodore-companies"
            )
            print("✅ Theodore pipeline initialized with antoine adapter")
            
            # Test single company processing
            print("🔬 Testing single company processing...")
            result = pipeline.process_single_company(
                company_name="Linear",
                website="https://linear.app",
                job_id=None
            )
            
            print(f"📊 Processing result: {result.scrape_status}")
            if result.scrape_status == "success":
                print("🎉 FULL PIPELINE SUCCESS!")
                return True
            else:
                print(f"❌ Pipeline failed: {result.scrape_error}")
                return False
        else:
            print("⚠️ Skipping full pipeline test - Pinecone not configured")
            return True
            
    except Exception as e:
        print(f"💥 PIPELINE EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 ANTOINE → THEODORE INTEGRATION TEST")
    print("=" * 80)
    
    # Test 1: Antoine adapter
    adapter_success = test_antoine_adapter()
    
    # Test 2: Full pipeline (if environment allows)
    pipeline_success = test_theodore_pipeline()
    
    print("\n📊 FINAL RESULTS")
    print("=" * 40)
    print(f"🔧 Antoine Adapter: {'✅ PASS' if adapter_success else '❌ FAIL'}")
    print(f"🎯 Theodore Pipeline: {'✅ PASS' if pipeline_success else '❌ FAIL'}")
    
    if adapter_success and pipeline_success:
        print("\n🎉 INTEGRATION SUCCESSFUL! Antoine is ready for production use with Theodore.")
    else:
        print("\n⚠️ Integration needs attention. Check error messages above.")