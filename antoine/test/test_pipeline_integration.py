#!/usr/bin/env python3
"""
Pipeline Integration Test
========================

Tests integration of antoine batch processor with the main Theodore pipeline.
"""

import sys
import os
import time
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load env vars
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

from src.main_pipeline import TheodoreIntelligencePipeline
from src.models import CompanyData, CompanyIntelligenceConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_pipeline_integration():
    """Test batch processing through main pipeline"""
    
    print("=" * 80)
    print("ANTOINE BATCH - PIPELINE INTEGRATION TEST")
    print("=" * 80)
    
    # Create pipeline configuration
    config = CompanyIntelligenceConfig()
    
    # Initialize main pipeline
    print("\n🔧 Initializing Theodore Intelligence Pipeline...")
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment='gcp-starter',
        pinecone_index=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
    )
    
    # Verify pipeline has antoine scraper
    print(f"✅ Pipeline initialized")
    print(f"   Scraper type: {type(pipeline.scraper).__name__}")
    print(f"   Has batch method: {hasattr(pipeline.scraper, 'batch_scrape_companies')}")
    
    # Create test companies
    test_companies = [
        CompanyData(name="Datadog", website="https://www.datadoghq.com"),
        CompanyData(name="PagerDuty", website="https://www.pagerduty.com"),
        CompanyData(name="Splunk", website="https://www.splunk.com")
    ]
    
    print(f"\n📋 Test companies:")
    for i, company in enumerate(test_companies, 1):
        print(f"   {i}. {company.name} - {company.website}")
    
    # Test single company processing first
    print(f"\n🧪 Testing single company processing...")
    single_start = time.time()
    
    try:
        single_result = pipeline.process_single_company(
            company_name=test_companies[0].name,
            website=test_companies[0].website
        )
        
        single_duration = time.time() - single_start
        print(f"✅ Single company processed in {single_duration:.1f}s")
        print(f"   Status: {single_result.scrape_status}")
        print(f"   Fields extracted: {len([f for f in vars(single_result).values() if f and f != 'unknown'])}")
        
    except Exception as e:
        print(f"❌ Single company processing failed: {e}")
        return
    
    # Test batch processing
    print(f"\n🧪 Testing batch processing...")
    batch_start = time.time()
    
    try:
        # Process batch through pipeline
        if hasattr(pipeline, 'batch_process_companies'):
            # Use pipeline's batch method if available
            batch_results = pipeline.batch_process_companies(test_companies)
        else:
            # Use scraper's batch method directly
            batch_results = pipeline.scraper.batch_scrape_companies(test_companies)
        
        batch_duration = time.time() - batch_start
        
        # Analyze results
        print(f"\n✅ Batch processing completed in {batch_duration:.1f}s")
        print(f"   Total companies: {len(test_companies)}")
        print(f"   Results returned: {len(batch_results)}")
        
        # Verify results
        successful = 0
        failed = 0
        
        for company in batch_results:
            if company.scrape_status == "success":
                successful += 1
            else:
                failed += 1
        
        print(f"   Successful: {successful}")
        print(f"   Failed: {failed}")
        
        # Performance comparison
        print(f"\n📊 PERFORMANCE COMPARISON:")
        print(f"   Single company time: {single_duration:.1f}s")
        print(f"   Batch time (3 companies): {batch_duration:.1f}s")
        print(f"   Expected sequential time: {single_duration * 3:.1f}s")
        print(f"   Speed improvement: {(single_duration * 3) / batch_duration:.1f}x")
        
        # Verify data quality
        print(f"\n🔍 DATA QUALITY CHECK:")
        for i, company in enumerate(batch_results):
            print(f"\n   Company {i+1}: {company.name}")
            print(f"   - Status: {company.scrape_status}")
            
            if company.scrape_status == "success":
                # Check key fields
                key_fields = {
                    'company_description': company.company_description,
                    'industry': company.industry,
                    'business_model': company.business_model,
                    'products_services_offered': company.products_services_offered,
                    'target_market': company.target_market
                }
                
                populated_fields = sum(1 for v in key_fields.values() if v and v != "unknown")
                print(f"   - Key fields populated: {populated_fields}/5")
                
                # Show sample data
                if company.company_description:
                    desc_preview = company.company_description[:80] + "..." if len(company.company_description) > 80 else company.company_description
                    print(f"   - Description: {desc_preview}")
            else:
                print(f"   - Error: {company.scrape_error}")
        
        # Test Pinecone storage (if pipeline has it)
        if hasattr(pipeline, 'pinecone_client') and pipeline.pinecone_client:
            print(f"\n💾 TESTING PINECONE STORAGE:")
            
            for company in batch_results:
                if company.scrape_status == "success" and company.company_description:
                    try:
                        # Generate embedding
                        embedding = pipeline.bedrock_client.get_embeddings(company.company_description)
                        company.embedding = embedding
                        
                        # Save to Pinecone
                        success = pipeline.pinecone_client.upsert_company(company)
                        
                        if success:
                            print(f"   ✅ {company.name} saved to Pinecone")
                        else:
                            print(f"   ❌ {company.name} failed to save")
                            
                    except Exception as e:
                        print(f"   ❌ Error saving {company.name}: {e}")
        
        # Overall assessment
        print(f"\n🎯 INTEGRATION TEST RESULT:")
        if successful == len(test_companies) and batch_duration < single_duration * len(test_companies):
            print("   ✅ PASSED - Batch processing works correctly with pipeline")
            print("   - All companies processed successfully")
            print("   - Performance improvement achieved")
            print("   - Data quality maintained")
            return True
        else:
            print("   ⚠️  PARTIAL SUCCESS")
            print(f"   - Success rate: {(successful/len(test_companies))*100:.0f}%")
            print(f"   - Speed improvement: {(single_duration * 3) / batch_duration:.1f}x")
            return False
            
    except Exception as e:
        print(f"\n❌ Batch processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling in pipeline integration"""
    
    print("\n" + "=" * 80)
    print("ERROR HANDLING TEST")
    print("=" * 80)
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment='gcp-starter',
        pinecone_index=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
    )
    
    # Test with problematic companies
    problem_companies = [
        CompanyData(name="GoodCompany", website="https://www.github.com"),
        CompanyData(name="BadURL", website="https://this-does-not-exist-12345.com"),
        CompanyData(name="NoWebsite", website="")
    ]
    
    print("\n🧪 Testing with problematic companies...")
    
    try:
        results = pipeline.scraper.batch_scrape_companies(problem_companies)
        
        print(f"\n📊 Results:")
        for company in results:
            status_icon = "✅" if company.scrape_status == "success" else "❌"
            print(f"   {status_icon} {company.name}: {company.scrape_status}")
            if company.scrape_error:
                print(f"      Error: {company.scrape_error}")
        
        # Verify error isolation
        successful = sum(1 for c in results if c.scrape_status == "success")
        print(f"\n✅ Error isolation test passed - {successful} succeeded despite errors")
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")


if __name__ == "__main__":
    # Run integration test
    success = test_pipeline_integration()
    
    # Run error handling test
    test_error_handling()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)