#!/usr/bin/env python3
"""
Batch Processing Stress Test
===========================

Stress test for antoine batch processing with a larger number of companies
to validate scalability and identify bottlenecks.
"""

import sys
import os
import time
import random

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load env vars
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

from antoine.batch.batch_processor import AntoineBatchProcessor
from src.models import CompanyIntelligenceConfig


# List of tech companies for stress testing
TECH_COMPANIES = [
    # SaaS Companies
    {"name": "Salesforce", "website": "https://www.salesforce.com"},
    {"name": "HubSpot", "website": "https://www.hubspot.com"},
    {"name": "Zendesk", "website": "https://www.zendesk.com"},
    {"name": "Atlassian", "website": "https://www.atlassian.com"},
    {"name": "ServiceNow", "website": "https://www.servicenow.com"},
    {"name": "Workday", "website": "https://www.workday.com"},
    {"name": "DocuSign", "website": "https://www.docusign.com"},
    {"name": "Zoom", "website": "https://zoom.us"},
    {"name": "Box", "website": "https://www.box.com"},
    {"name": "Dropbox", "website": "https://www.dropbox.com"},
    
    # Dev Tools
    {"name": "GitHub", "website": "https://github.com"},
    {"name": "GitLab", "website": "https://about.gitlab.com"},
    {"name": "Vercel", "website": "https://vercel.com"},
    {"name": "Netlify", "website": "https://www.netlify.com"},
    {"name": "CircleCI", "website": "https://circleci.com"},
    
    # E-commerce
    {"name": "Amazon", "website": "https://www.amazon.com"},
    {"name": "eBay", "website": "https://www.ebay.com"},
    {"name": "Etsy", "website": "https://www.etsy.com"},
    {"name": "Wayfair", "website": "https://www.wayfair.com"},
    {"name": "Instacart", "website": "https://www.instacart.com"},
    
    # Tech Giants
    {"name": "Google", "website": "https://www.google.com"},
    {"name": "Microsoft", "website": "https://www.microsoft.com"},
    {"name": "Apple", "website": "https://www.apple.com"},
    {"name": "Meta", "website": "https://about.meta.com"},
    {"name": "Netflix", "website": "https://www.netflix.com"},
]


def test_stress_batch(num_companies=10, max_concurrent=5):
    """Run stress test with specified number of companies"""
    
    print("=" * 80)
    print(f"ANTOINE BATCH PROCESSING - STRESS TEST")
    print(f"Testing with {num_companies} companies, {max_concurrent} concurrent")
    print("=" * 80)
    
    # Select random companies
    if num_companies > len(TECH_COMPANIES):
        # Duplicate some companies if needed
        test_companies = TECH_COMPANIES * (num_companies // len(TECH_COMPANIES) + 1)
        test_companies = test_companies[:num_companies]
    else:
        test_companies = random.sample(TECH_COMPANIES, num_companies)
    
    print(f"\n📋 Selected {len(test_companies)} companies for testing")
    
    # Create batch processor
    config = CompanyIntelligenceConfig()
    batch_processor = AntoineBatchProcessor(
        config=config,
        bedrock_client=None,
        max_concurrent_companies=max_concurrent,
        enable_resource_pooling=True
    )
    
    # Memory usage tracking
    import psutil
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    print(f"\n🚀 Starting stress test...")
    print(f"   Initial memory: {initial_memory:.1f} MB")
    
    try:
        # Process batch
        start_time = time.time()
        
        result = batch_processor.process_batch(
            test_companies,
            batch_name=f"stress_test_{num_companies}"
        )
        
        elapsed = time.time() - start_time
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Display results
        print(f"\n✅ Stress test completed in {elapsed:.1f} seconds")
        
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"   Total companies: {result.total_companies}")
        print(f"   Successful: {result.successful} ({(result.successful/result.total_companies)*100:.1f}%)")
        print(f"   Failed: {result.failed}")
        print(f"   Duration: {result.total_duration:.1f}s")
        print(f"   Throughput: {result.companies_per_minute:.1f} companies/minute")
        
        print(f"\n💾 MEMORY USAGE:")
        print(f"   Initial: {initial_memory:.1f} MB")
        print(f"   Final: {final_memory:.1f} MB")
        print(f"   Increase: {memory_increase:.1f} MB")
        print(f"   Per company: {memory_increase/result.total_companies:.1f} MB")
        
        print(f"\n📈 PERFORMANCE METRICS:")
        print(f"   Total pages crawled: {result.resource_stats.get('total_pages_crawled', 0)}")
        print(f"   Avg pages per company: {result.resource_stats.get('avg_pages_per_company', 0):.1f}")
        print(f"   Avg time per company: {result.resource_stats.get('avg_seconds_per_company', 0):.1f}s")
        print(f"   Parallel efficiency: {result.resource_stats.get('parallel_efficiency', 0):.1%}")
        
        # Error analysis
        if result.errors:
            print(f"\n⚠️  ERROR ANALYSIS:")
            error_types = {}
            for company, error in result.errors.items():
                error_type = "timeout" if "timeout" in error.lower() else \
                            "ssl" if "ssl" in error.lower() else \
                            "connection" if "connection" in error.lower() else \
                            "other"
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            for error_type, count in error_types.items():
                print(f"   {error_type}: {count}")
        
        # Success rate by company size (estimated by pages crawled)
        if result.company_results:
            print(f"\n📏 COMPLEXITY ANALYSIS:")
            
            small = [c for c in result.company_results if len(c.pages_crawled or []) <= 10]
            medium = [c for c in result.company_results if 10 < len(c.pages_crawled or []) <= 20]
            large = [c for c in result.company_results if len(c.pages_crawled or []) > 20]
            
            print(f"   Small sites (≤10 pages): {len(small)} companies")
            print(f"   Medium sites (11-20 pages): {len(medium)} companies")
            print(f"   Large sites (>20 pages): {len(large)} companies")
        
        # Cost estimation
        print(f"\n💰 COST ESTIMATION:")
        # Rough estimates based on Nova Pro pricing
        total_tokens = sum(getattr(c, 'total_tokens_used', 0) for c in result.company_results)
        estimated_cost = (total_tokens / 1000) * 0.0008  # Nova Pro pricing
        print(f"   Estimated API cost: ${estimated_cost:.2f}")
        print(f"   Cost per company: ${estimated_cost/max(result.successful, 1):.4f}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Stress test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        batch_processor.shutdown()
        print(f"\n🔚 Batch processor shutdown complete")


def run_scaling_test():
    """Run tests with increasing scale"""
    
    print("🔬 RUNNING SCALING TESTS")
    print("=" * 80)
    
    test_configs = [
        (5, 2),    # 5 companies, 2 concurrent
        (10, 3),   # 10 companies, 3 concurrent
        (20, 5),   # 20 companies, 5 concurrent
    ]
    
    results_summary = []
    
    for num_companies, max_concurrent in test_configs:
        print(f"\n\n{'='*60}")
        print(f"Test: {num_companies} companies, {max_concurrent} concurrent")
        print(f"{'='*60}")
        
        result = test_stress_batch(num_companies, max_concurrent)
        
        if result:
            results_summary.append({
                'companies': num_companies,
                'concurrent': max_concurrent,
                'success_rate': (result.successful / result.total_companies) * 100,
                'throughput': result.companies_per_minute,
                'duration': result.total_duration
            })
        
        # Wait between tests
        if num_companies < 20:
            print(f"\n⏳ Waiting 5 seconds before next test...")
            time.sleep(5)
    
    # Print summary
    print(f"\n\n{'='*80}")
    print("📊 SCALING TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Companies | Concurrent | Success Rate | Throughput | Duration")
    print(f"{'-'*60}")
    
    for r in results_summary:
        print(f"{r['companies']:9d} | {r['concurrent']:10d} | {r['success_rate']:11.1f}% | {r['throughput']:10.1f} | {r['duration']:8.1f}s")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Run specific test
        num_companies = int(sys.argv[1])
        max_concurrent = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        test_stress_batch(num_companies, max_concurrent)
    else:
        # Run scaling test
        run_scaling_test()