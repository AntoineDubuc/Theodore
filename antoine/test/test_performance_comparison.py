#!/usr/bin/env python3
"""
Performance Comparison Test
==========================

Compares sequential vs batch processing performance to validate
the speed improvements of the antoine batch processor.
"""

import sys
import os
import time
import json
from datetime import datetime
import statistics

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load env vars
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

from antoine.batch.batch_processor import AntoineBatchProcessor
from src.antoine_scraper_adapter import AntoineScraperAdapter
from src.models import CompanyData, CompanyIntelligenceConfig


def process_sequential(companies, config):
    """Process companies one by one"""
    print("\n🔄 SEQUENTIAL PROCESSING")
    print("=" * 60)
    
    scraper = AntoineScraperAdapter(config)
    results = []
    times = []
    
    start_total = time.time()
    
    for i, company_dict in enumerate(companies, 1):
        print(f"\n   Processing {i}/{len(companies)}: {company_dict['name']}")
        
        company = CompanyData(
            name=company_dict['name'],
            website=company_dict['website']
        )
        
        start = time.time()
        result = scraper.scrape_company(company)
        duration = time.time() - start
        times.append(duration)
        
        results.append(result)
        
        status = "✅" if result.scrape_status == "success" else "❌"
        print(f"   {status} Completed in {duration:.1f}s")
    
    total_duration = time.time() - start_total
    
    return {
        'method': 'sequential',
        'results': results,
        'total_duration': total_duration,
        'individual_times': times,
        'avg_time_per_company': statistics.mean(times),
        'successful': sum(1 for r in results if r.scrape_status == "success"),
        'failed': sum(1 for r in results if r.scrape_status != "success")
    }


def process_batch(companies, config, max_concurrent=3):
    """Process companies in batch"""
    print(f"\n⚡ BATCH PROCESSING (max_concurrent={max_concurrent})")
    print("=" * 60)
    
    batch_processor = AntoineBatchProcessor(
        config=config,
        max_concurrent_companies=max_concurrent,
        enable_resource_pooling=True
    )
    
    try:
        start = time.time()
        batch_result = batch_processor.process_batch(companies, "performance_test")
        duration = time.time() - start
        
        print(f"\n   ✅ Batch completed in {duration:.1f}s")
        print(f"   Successful: {batch_result.successful}/{batch_result.total_companies}")
        
        return {
            'method': f'batch_{max_concurrent}',
            'results': batch_result.company_results,
            'total_duration': duration,
            'batch_result': batch_result,
            'successful': batch_result.successful,
            'failed': batch_result.failed,
            'throughput': batch_result.companies_per_minute
        }
        
    finally:
        batch_processor.shutdown()


def generate_performance_report(results_dict):
    """Generate detailed performance comparison report"""
    
    print("\n" + "=" * 80)
    print("📊 PERFORMANCE COMPARISON REPORT")
    print("=" * 80)
    
    # Summary table
    print("\n🔢 SUMMARY METRICS:")
    print(f"{'Method':<20} {'Duration':<12} {'Success':<10} {'Failed':<10} {'Speed':<10}")
    print("-" * 70)
    
    sequential_time = results_dict['sequential']['total_duration']
    
    for method, data in results_dict.items():
        duration = data['total_duration']
        speedup = sequential_time / duration if duration > 0 else 0
        
        print(f"{method:<20} {duration:<12.1f} {data['successful']:<10} {data['failed']:<10} {speedup:<10.1f}x")
    
    # Detailed analysis
    print("\n📈 DETAILED ANALYSIS:")
    
    # Sequential baseline
    seq_data = results_dict['sequential']
    print(f"\n1. Sequential Processing:")
    print(f"   - Total time: {seq_data['total_duration']:.1f}s")
    print(f"   - Average per company: {seq_data['avg_time_per_company']:.1f}s")
    print(f"   - Min/Max times: {min(seq_data['individual_times']):.1f}s / {max(seq_data['individual_times']):.1f}s")
    
    # Batch comparisons
    for method, data in results_dict.items():
        if method.startswith('batch_'):
            concurrent = method.split('_')[1]
            print(f"\n2. Batch Processing (concurrent={concurrent}):")
            print(f"   - Total time: {data['total_duration']:.1f}s")
            print(f"   - Throughput: {data.get('throughput', 0):.1f} companies/minute")
            print(f"   - Speed improvement: {sequential_time / data['total_duration']:.2f}x")
            print(f"   - Time saved: {sequential_time - data['total_duration']:.1f}s")
            
            if 'batch_result' in data:
                batch_res = data['batch_result']
                print(f"   - Parallel efficiency: {batch_res.resource_stats.get('parallel_efficiency', 0):.1%}")
    
    # Quality comparison
    print("\n🔍 QUALITY COMPARISON:")
    
    # Count fields extracted per method
    for method, data in results_dict.items():
        field_counts = []
        for company in data['results']:
            if company.scrape_status == "success":
                fields = sum(1 for attr in ['company_description', 'industry', 'business_model', 
                           'products_services_offered', 'target_market', 'value_proposition']
                           if getattr(company, attr, None) and getattr(company, attr) != "unknown")
                field_counts.append(fields)
        
        if field_counts:
            avg_fields = statistics.mean(field_counts)
            print(f"\n   {method}:")
            print(f"   - Average fields extracted: {avg_fields:.1f}")
            print(f"   - Min/Max fields: {min(field_counts)}/{max(field_counts)}")
    
    # Efficiency metrics
    print("\n⚡ EFFICIENCY METRICS:")
    
    best_batch_time = min(data['total_duration'] for method, data in results_dict.items() if method.startswith('batch_'))
    optimal_speedup = sequential_time / best_batch_time
    
    print(f"   - Best batch time: {best_batch_time:.1f}s")
    print(f"   - Optimal speedup achieved: {optimal_speedup:.2f}x")
    print(f"   - Theoretical maximum speedup: {len(companies)}x")
    print(f"   - Efficiency: {(optimal_speedup / len(companies)) * 100:.1f}%")
    
    # Save detailed results
    report_data = {
        'test_date': datetime.now().isoformat(),
        'companies_tested': len(companies),
        'results': results_dict,
        'summary': {
            'sequential_time': sequential_time,
            'best_batch_time': best_batch_time,
            'optimal_speedup': optimal_speedup,
            'efficiency_percentage': (optimal_speedup / len(companies)) * 100
        }
    }
    
    report_file = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2, default=str)
    
    print(f"\n💾 Detailed report saved to: {report_file}")
    
    return optimal_speedup >= 1.5  # Success if at least 1.5x speedup


# Test companies
companies = [
    {"name": "Twilio", "website": "https://www.twilio.com"},
    {"name": "SendGrid", "website": "https://sendgrid.com"},
    {"name": "Cloudflare", "website": "https://www.cloudflare.com"},
    {"name": "DigitalOcean", "website": "https://www.digitalocean.com"},
    {"name": "Heroku", "website": "https://www.heroku.com"}
]


def main():
    """Run performance comparison tests"""
    
    print("=" * 80)
    print("ANTOINE BATCH PROCESSOR - PERFORMANCE COMPARISON")
    print("=" * 80)
    
    print(f"\n📋 Testing with {len(companies)} companies:")
    for i, company in enumerate(companies, 1):
        print(f"   {i}. {company['name']}")
    
    config = CompanyIntelligenceConfig()
    results = {}
    
    # Sequential processing
    print("\n" + "="*60)
    seq_results = process_sequential(companies, config)
    results['sequential'] = seq_results
    
    # Wait between tests
    print("\n⏳ Waiting 5 seconds before batch test...")
    time.sleep(5)
    
    # Batch processing with different concurrency levels
    for max_concurrent in [2, 3, 5]:
        print("\n" + "="*60)
        batch_results = process_batch(companies, config, max_concurrent)
        results[f'batch_{max_concurrent}'] = batch_results
        
        if max_concurrent < 5:
            print("\n⏳ Waiting 5 seconds before next test...")
            time.sleep(5)
    
    # Generate report
    success = generate_performance_report(results)
    
    # Final verdict
    print("\n" + "="*80)
    if success:
        print("✅ PERFORMANCE TEST PASSED - Batch processing provides significant speedup")
    else:
        print("⚠️  PERFORMANCE TEST WARNING - Speedup less than expected")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)