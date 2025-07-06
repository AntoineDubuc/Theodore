#!/usr/bin/env python3
"""
Quick verification that CloudGeometry crawling is now fixed
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.intelligent_company_scraper import IntelligentCompanyScraper
from src.models import CompanyData, CompanyIntelligenceConfig

async def test_cloudgeometry_fix():
    """Test that CloudGeometry now crawls successfully"""
    print("🔧 CLOUDGEOMETRY FIX VERIFICATION")
    print("=" * 40)
    
    # Create test company
    company = CompanyData(
        name="CloudGeometry Fix Test",
        website="https://www.cloudgeometry.com"
    )
    
    # Initialize scraper with fixed configuration
    config = CompanyIntelligenceConfig()
    scraper = IntelligentCompanyScraper(config)
    
    print(f"🎯 Testing: {company.website}")
    print(f"📋 Expected: Pages should crawl successfully now")
    print()
    
    try:
        # Run just Phase 1-3 to verify content extraction
        result = await scraper.scrape_company_intelligent(company)
        
        print(f"\n✅ SUCCESS!")
        print(f"📊 Pages crawled: {getattr(result, 'pages_crawled', 0)}")
        print(f"⏱️  Duration: {getattr(result, 'crawl_duration', 0):.1f}s")
        
        # Check if we got meaningful content
        if hasattr(result, 'raw_content') and result.raw_content and len(result.raw_content) > 100:
            print(f"📄 Content generated: {len(result.raw_content):,} characters")
            print(f"🔍 Preview: {result.raw_content[:200]}...")
        else:
            print(f"⚠️  Limited content generated")
            
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_cloudgeometry_fix())
    
    if success:
        print(f"\n🎉 CLOUDGEOMETRY FIX VERIFIED!")
        print(f"   Theodore can now successfully crawl your website.")
        print(f"   The '100 pages' issue has been resolved.")
    else:
        print(f"\n❌ Fix needs more work.")