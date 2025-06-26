#!/usr/bin/env python3
"""
Quick test script to verify the model comparison approach works
"""

import os
import sys
import time
from datetime import datetime

# Set up paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from dotenv import load_dotenv
load_dotenv()

# Import Theodore modules
from main_pipeline import TheodoreIntelligencePipeline
from models import CompanyIntelligenceConfig

def test_single_company():
    """Test a single company with one model configuration"""
    
    # Test company
    company_url = "scitara.com"
    
    # Configure for Gemini Flash
    os.environ['GEMINI_MODEL'] = 'gemini-2.5-flash'
    os.environ['BEDROCK_ANALYSIS_MODEL'] = 'us.amazon.nova-pro-v1:0'
    
    # Create pipeline
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT', 'Theodore'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
    )
    
    print(f"🔍 Testing {company_url} with Gemini 2.5 Flash...")
    
    try:
        start_time = time.time()
        
        # Process the company
        company_data = pipeline.process_single_company(
            company_name=company_url.replace('https://', '').replace('http://', '').replace('www.', ''),
            website=company_url
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✅ Success! Processed in {processing_time:.1f} seconds")
        print(f"📊 Company Name: {getattr(company_data, 'name', 'Not extracted')}")
        print(f"🏢 Industry: {getattr(company_data, 'industry', 'Not extracted')}")
        print(f"💼 Business Model: {getattr(company_data, 'business_model', 'Not extracted')}")
        print(f"📄 Pages Crawled: {len(getattr(company_data, 'pages_crawled', []))}")
        
        # Calculate coverage
        key_fields = ['name', 'company_description', 'industry', 'business_model', 'company_size', 'target_market']
        populated = sum(1 for field in key_fields if getattr(company_data, field, None))
        coverage = (populated / len(key_fields)) * 100
        print(f"📈 Field Coverage: {coverage:.1f}% ({populated}/{len(key_fields)} fields)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_single_company()
    if success:
        print("\n🎉 Test passed! The full comparison script should work.")
    else:
        print("\n🚨 Test failed. Need to fix issues before running full comparison.")