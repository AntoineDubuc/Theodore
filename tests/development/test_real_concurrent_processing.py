#!/usr/bin/env python3
"""
REAL TEST: Actually process multiple companies concurrently to verify performance
"""

import os
import sys
import time
import asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.main_pipeline import TheodoreIntelligencePipeline
from src.models import CompanyData, CompanyIntelligenceConfig
from concurrent.futures import ThreadPoolExecutor, as_completed

def create_test_companies():
    """Create test companies for concurrent processing"""
    test_companies = [
        {"name": "Stripe", "website": "https://stripe.com"},
        {"name": "Shopify", "website": "https://shopify.com"},
        {"name": "Square", "website": "https://squareup.com"},
        {"name": "Zoom", "website": "https://zoom.us"},
        {"name": "Slack", "website": "https://slack.com"}
    ]
    
    return [
        CompanyData(
            name=company["name"],
            website=company["website"]
        ) for company in test_companies
    ]

def process_single_company(company_data, pipeline, test_id):
    """Process a single company and return timing info"""
    start_time = time.time()
    
    try:
        print(f"🔍 [{test_id}] Starting: {company_data.name}")
        
        # Process the company with correct API
        result = pipeline.process_single_company(company_data.name, company_data.website)
        
        duration = time.time() - start_time
        
        print(f"✅ [{test_id}] Completed: {company_data.name} in {duration:.1f}s")
        
        return {
            "company": company_data.name,
            "success": True,
            "duration": duration,
            "result": result,
            "test_id": test_id
        }
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ [{test_id}] Failed: {company_data.name} in {duration:.1f}s - {str(e)}")
        
        return {
            "company": company_data.name,
            "success": False,
            "duration": duration,
            "error": str(e),
            "test_id": test_id
        }

def test_sequential_processing():
    """Test sequential processing (baseline)"""
    print("\n🔄 SEQUENTIAL PROCESSING TEST (Baseline)")
    print("-" * 50)
    
    try:
        # Initialize pipeline
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT', 'us-east-1'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        )
        
        companies = create_test_companies()[:3]  # Test with 3 companies
        
        start_time = time.time()
        results = []
        
        for i, company in enumerate(companies, 1):
            result = process_single_company(company, pipeline, f"SEQ-{i}")
            results.append(result)
        
        total_duration = time.time() - start_time
        
        # Analyze results
        successful = sum(1 for r in results if r["success"])
        avg_duration = sum(r["duration"] for r in results) / len(results)
        
        print(f"\n📊 SEQUENTIAL RESULTS:")
        print(f"   Total time: {total_duration:.1f}s")
        print(f"   Success rate: {successful}/{len(results)}")
        print(f"   Average per company: {avg_duration:.1f}s")
        print(f"   Companies per minute: {len(results) / (total_duration/60):.1f}")
        
        return {
            "total_duration": total_duration,
            "success_rate": successful / len(results),
            "avg_duration": avg_duration,
            "companies_per_minute": len(results) / (total_duration/60)
        }
        
    except Exception as e:
        print(f"❌ Sequential test failed: {e}")
        return None

def test_concurrent_processing(concurrency=5):
    """Test concurrent processing with specified concurrency"""
    print(f"\n🚀 CONCURRENT PROCESSING TEST (Concurrency={concurrency})")
    print("-" * 50)
    
    try:
        # Initialize pipeline
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT', 'us-east-1'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        )
        
        companies = create_test_companies()  # Test with all 5 companies
        
        start_time = time.time()
        results = []
        
        # Process companies concurrently
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            # Submit all tasks
            future_to_company = {
                executor.submit(process_single_company, company, pipeline, f"CON-{i}"): company 
                for i, company in enumerate(companies, 1)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_company):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    company = future_to_company[future]
                    print(f"❌ Exception processing {company.name}: {e}")
                    results.append({
                        "company": company.name,
                        "success": False,
                        "duration": 0,
                        "error": str(e)
                    })
        
        total_duration = time.time() - start_time
        
        # Analyze results
        successful = sum(1 for r in results if r["success"])
        avg_duration = sum(r["duration"] for r in results if r["success"]) / max(successful, 1)
        
        print(f"\n📊 CONCURRENT RESULTS:")
        print(f"   Total time: {total_duration:.1f}s")
        print(f"   Success rate: {successful}/{len(results)}")
        print(f"   Average per company: {avg_duration:.1f}s")
        print(f"   Companies per minute: {len(results) / (total_duration/60):.1f}")
        print(f"   Concurrency factor: {concurrency}")
        
        return {
            "total_duration": total_duration,
            "success_rate": successful / len(results),
            "avg_duration": avg_duration,
            "companies_per_minute": len(results) / (total_duration/60),
            "concurrency": concurrency
        }
        
    except Exception as e:
        print(f"❌ Concurrent test failed: {e}")
        return None

def main():
    """Run the real concurrent processing test"""
    print("🧪 REAL CONCURRENT PROCESSING TEST")
    print("=" * 60)
    print("Testing actual company processing with Theodore pipeline")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check environment
    required_env = ['PINECONE_API_KEY', 'GEMINI_API_KEY']
    missing_env = [var for var in required_env if not os.getenv(var)]
    
    if missing_env:
        print(f"❌ Missing required environment variables: {missing_env}")
        print("This test requires actual API keys to run")
        return
    
    print("✅ Environment variables found")
    
    # Run tests
    try:
        # Test 1: Sequential processing (baseline)
        sequential_results = test_sequential_processing()
        
        # Test 2: Concurrent processing
        concurrent_results = test_concurrent_processing(concurrency=5)
        
        # Compare results
        if sequential_results and concurrent_results:
            print(f"\n📈 PERFORMANCE COMPARISON")
            print("-" * 50)
            
            seq_cpm = sequential_results["companies_per_minute"]
            con_cpm = concurrent_results["companies_per_minute"]
            improvement = con_cpm / seq_cpm if seq_cpm > 0 else 0
            
            print(f"Sequential processing:")
            print(f"   Companies per minute: {seq_cpm:.1f}")
            print(f"   Success rate: {sequential_results['success_rate']*100:.1f}%")
            
            print(f"Concurrent processing (5x):")
            print(f"   Companies per minute: {con_cpm:.1f}")
            print(f"   Success rate: {concurrent_results['success_rate']*100:.1f}%")
            
            print(f"Performance improvement: {improvement:.1f}x")
            
            if improvement >= 2.0:
                print("✅ EXCELLENT: Concurrent processing significantly faster")
            elif improvement >= 1.5:
                print("✅ GOOD: Concurrent processing moderately faster")
            elif improvement >= 1.1:
                print("⚠️ MARGINAL: Small improvement from concurrency")
            else:
                print("❌ POOR: Concurrent processing not faster (possible bottleneck)")
        
        print(f"\n✅ REAL CONCURRENT PROCESSING TEST COMPLETE")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()