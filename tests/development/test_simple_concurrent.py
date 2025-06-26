#!/usr/bin/env python3
"""
Simple REAL test of concurrent processing with 2 companies
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

# Add project root to path  
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.main_pipeline import TheodoreIntelligencePipeline
from src.models import CompanyIntelligenceConfig

def test_real_concurrency():
    """Quick test with 2 companies processed concurrently"""
    
    print("🧪 QUICK REAL CONCURRENCY TEST")
    print("=" * 50)
    
    # Check API keys
    if not os.getenv('PINECONE_API_KEY') or not os.getenv('GEMINI_API_KEY'):
        print("❌ Missing API keys - cannot run real test")
        return
    
    # Initialize pipeline
    try:
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT', 'us-east-1'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        )
        print("✅ Pipeline initialized")
    except Exception as e:
        print(f"❌ Pipeline initialization failed: {e}")
        return
    
    # Test companies
    test_companies = [
        ("Test Company A", "https://stripe.com"),
        ("Test Company B", "https://zoom.us")
    ]
    
    def process_company(company_name, website):
        """Process a single company"""
        start_time = time.time()
        try:
            print(f"🔍 Starting: {company_name}")
            result = pipeline.process_single_company(company_name, website)
            duration = time.time() - start_time
            print(f"✅ Completed: {company_name} in {duration:.1f}s")
            return {"success": True, "duration": duration, "company": company_name}
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Failed: {company_name} in {duration:.1f}s - {str(e)[:100]}")
            return {"success": False, "duration": duration, "company": company_name, "error": str(e)}
    
    # Test 1: Sequential processing  
    print(f"\n🔄 SEQUENTIAL TEST:")
    seq_start = time.time()
    seq_results = []
    
    for company_name, website in test_companies:
        result = process_company(company_name, website)
        seq_results.append(result)
    
    seq_duration = time.time() - seq_start
    seq_successful = sum(1 for r in seq_results if r["success"])
    
    print(f"📊 Sequential: {seq_duration:.1f}s total, {seq_successful}/{len(test_companies)} successful")
    
    # Test 2: Concurrent processing
    print(f"\n🚀 CONCURRENT TEST (2 workers):")
    con_start = time.time()
    con_results = []
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(process_company, name, website) for name, website in test_companies]
        con_results = [future.result() for future in futures]
    
    con_duration = time.time() - con_start
    con_successful = sum(1 for r in con_results if r["success"])
    
    print(f"📊 Concurrent: {con_duration:.1f}s total, {con_successful}/{len(test_companies)} successful")
    
    # Compare
    if seq_duration > 0 and con_duration > 0:
        improvement = seq_duration / con_duration
        print(f"\n📈 PERFORMANCE COMPARISON:")
        print(f"   Sequential: {seq_duration:.1f}s")
        print(f"   Concurrent: {con_duration:.1f}s")
        print(f"   Improvement: {improvement:.1f}x")
        
        if improvement >= 1.5:
            print("✅ SUCCESS: Concurrent processing is significantly faster!")
        elif improvement >= 1.1:
            print("✅ GOOD: Concurrent processing shows improvement")
        else:
            print("⚠️ LIMITED: Minimal improvement from concurrency")
    
    print(f"\n✅ REAL CONCURRENCY TEST COMPLETE")

if __name__ == "__main__":
    test_real_concurrency()