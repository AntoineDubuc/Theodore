#!/usr/bin/env python3
"""
Simple Batch Processing Test
===========================

Basic test of antoine batch processing with 5 companies to validate
the parallel processing infrastructure.
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

from antoine.batch.batch_processor import AntoineBatchProcessor
from src.models import CompanyIntelligenceConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_simple_batch():
    """Test batch processing with 5 well-known companies"""
    
    print("=" * 80)
    print("ANTOINE BATCH PROCESSING - SIMPLE TEST")
    print("=" * 80)
    
    # Test companies (mix of easy and complex sites)
    test_companies = [
        {"name": "Stripe", "website": "https://stripe.com"},
        {"name": "Shopify", "website": "https://www.shopify.com"},
        {"name": "Slack", "website": "https://slack.com"},
        {"name": "Notion", "website": "https://www.notion.so"},
        {"name": "Linear", "website": "https://linear.app"}
    ]
    
    print(f"\n📋 Test companies:")
    for i, company in enumerate(test_companies, 1):
        print(f"   {i}. {company['name']} - {company['website']}")
    
    # Create configuration
    config = CompanyIntelligenceConfig()
    
    # Create batch processor with 3 concurrent companies
    print(f"\n🔧 Creating batch processor with max_concurrent_companies=3")
    batch_processor = AntoineBatchProcessor(
        config=config,
        bedrock_client=None,  # Will be created internally
        max_concurrent_companies=3,
        enable_resource_pooling=True
    )
    
    # Process the batch
    print(f"\n🚀 Starting batch processing...")
    start_time = time.time()
    
    try:
        result = batch_processor.process_batch(
            test_companies,
            batch_name="simple_test"
        )
        
        elapsed_time = time.time() - start_time
        
        # Display results
        print(f"\n✅ Batch processing completed in {elapsed_time:.1f} seconds")
        print(f"\n📊 BATCH RESULTS:")
        print(f"   Total companies: {result.total_companies}")
        print(f"   Successful: {result.successful}")
        print(f"   Failed: {result.failed}")
        print(f"   Duration: {result.total_duration:.1f}s")
        print(f"   Throughput: {result.companies_per_minute:.1f} companies/minute")
        
        # Resource statistics
        print(f"\n📈 RESOURCE STATISTICS:")
        for key, value in result.resource_stats.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.2f}")
            else:
                print(f"   {key}: {value}")
        
        # Individual company results
        print(f"\n🏢 COMPANY RESULTS:")
        for company in result.company_results:
            status_emoji = "✅" if company.scrape_status == "success" else "❌"
            print(f"\n   {status_emoji} {company.name}")
            print(f"      Status: {company.scrape_status}")
            
            if company.scrape_status == "success":
                # Count non-null fields
                field_count = 0
                for field_name in ['company_description', 'industry', 'business_model', 
                                 'location', 'products_services_offered', 'target_market',
                                 'value_proposition', 'founding_year', 'employee_count_range']:
                    if getattr(company, field_name, None) and getattr(company, field_name) != "unknown":
                        field_count += 1
                
                print(f"      Fields extracted: {field_count}")
                print(f"      Pages crawled: {len(company.pages_crawled or [])}")
                print(f"      Crawl duration: {company.crawl_duration:.1f}s")
                
                # Show sample data
                if company.company_description:
                    desc_preview = company.company_description[:100] + "..." if len(company.company_description) > 100 else company.company_description
                    print(f"      Description: {desc_preview}")
            else:
                print(f"      Error: {company.scrape_error}")
        
        # Error summary
        if result.errors:
            print(f"\n⚠️  ERRORS:")
            for company_name, error in result.errors.items():
                print(f"   {company_name}: {error}")
        
        # Performance comparison
        print(f"\n📊 PERFORMANCE ANALYSIS:")
        print(f"   Sequential time (estimated): {result.resource_stats.get('avg_seconds_per_company', 0) * result.total_companies:.1f}s")
        print(f"   Parallel time (actual): {result.total_duration:.1f}s")
        print(f"   Speed improvement: {result.resource_stats.get('parallel_efficiency', 0):.1f}x")
        
    except Exception as e:
        print(f"\n❌ Batch processing failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        batch_processor.shutdown()
        print(f"\n🔚 Batch processor shutdown complete")


if __name__ == "__main__":
    test_simple_batch()