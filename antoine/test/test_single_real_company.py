#!/usr/bin/env python3
"""
Test Single Real Company
=======================

Test with a single real company to verify the batch processor works.
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load env vars
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)

from src.antoine_scraper_adapter import AntoineScraperAdapter
from src.models import CompanyData, CompanyIntelligenceConfig


def test_single_company():
    """Test with a single real company"""
    
    print("=" * 80)
    print("SINGLE COMPANY TEST - STRIPE")
    print("=" * 80)
    
    # Create company
    company = CompanyData(
        name="Stripe",
        website="https://stripe.com"
    )
    
    print(f"\n🏢 Testing: {company.name}")
    print(f"🌐 Website: {company.website}")
    
    # Create scraper
    config = CompanyIntelligenceConfig()
    scraper = AntoineScraperAdapter(config)
    
    print("\n🚀 Starting extraction...")
    start_time = time.time()
    
    try:
        result = scraper.scrape_company(company)
        elapsed = time.time() - start_time
        
        print(f"\n✅ Completed in {elapsed:.1f}s")
        print(f"   Status: {result.scrape_status}")
        
        if result.scrape_status == "success":
            print("\n📊 EXTRACTED DATA:")
            print(f"   Industry: {result.industry}")
            print(f"   Business Model: {result.business_model}")
            print(f"   Location: {result.location}")
            print(f"   Pages crawled: {len(result.pages_crawled or [])}")
            
            if result.company_description:
                print(f"\n   Description: {result.company_description[:150]}...")
            
            # Count non-null fields
            field_count = sum(1 for attr in dir(result) 
                            if not attr.startswith('_') 
                            and getattr(result, attr) 
                            and getattr(result, attr) != "unknown")
            
            print(f"\n   Total fields extracted: {field_count}")
            
            print("\n✅ SINGLE COMPANY TEST PASSED")
            return True
        else:
            print(f"\n❌ Extraction failed: {result.scrape_error}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_single_company()
    sys.exit(0 if success else 1)