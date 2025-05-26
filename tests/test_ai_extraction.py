#!/usr/bin/env python3
"""
Test script for AI-powered extraction using new Crawl4AI implementation
"""

import os
import sys
import asyncio
import json
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

from src.models import CompanyData, CompanyIntelligenceConfig
from src.crawl4ai_scraper import Crawl4AICompanyScraper

async def test_ai_extraction():
    """Test AI-powered extraction on Visterra"""
    
    # Load environment variables from project root
    env_path = os.path.join(project_root, '.env')
    load_dotenv(env_path)
    
    print("🤖 Theodore AI Extraction Test")
    print("=" * 50)
    
    # Check for OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key or openai_key == "your-openai-api-key-here":
        print("❌ OpenAI API key not found or not set properly")
        print("Please set OPENAI_API_KEY in your .env file")
        return
    
    print("✅ OpenAI API key found")
    
    # Configuration
    config = CompanyIntelligenceConfig()
    
    # Create test company data
    test_company = CompanyData(
        name="Visterra",
        website="https://visterrainc.com"
    )
    
    print(f"\n🔍 Testing AI extraction on: {test_company.name}")
    print(f"📍 Website: {test_company.website}")
    print("-" * 50)
    
    try:
        # Initialize AI scraper
        scraper = Crawl4AICompanyScraper(config)
        
        # Perform AI-powered extraction
        print("🚀 Starting AI-powered web crawling...")
        result = await scraper.scrape_company_comprehensive(test_company)
        
        # Display results
        print(f"\n📊 AI Extraction Results for {result.name}")
        print("=" * 60)
        print(f"🌐 Website: {result.website}")
        print(f"📋 Scrape Status: {result.scrape_status}")
        crawl_duration = result.crawl_duration or 0
        crawl_depth = result.crawl_depth or 0
        print(f"⏱️ Crawl Duration: {crawl_duration:.2f}s")
        print(f"📄 Pages Crawled: {crawl_depth}")
        
        if result.scrape_status == "success":
            print("\n📈 EXTRACTED INTELLIGENCE:")
            print("-" * 30)
            
            # Company basics
            if result.company_description:
                print(f"📝 Description: {result.company_description}")
            if result.founding_year:
                print(f"📅 Founded: {result.founding_year}")
            if result.location:
                print(f"📍 Location: {result.location}")
            if result.employee_count_range:
                print(f"👥 Employee Count: {result.employee_count_range}")
            
            # Business details
            if result.industry:
                print(f"🏢 Industry: {result.industry}")
            if result.business_model:
                print(f"🏗️ Business Model: {result.business_model}")
            if result.target_market:
                print(f"🎯 Target Market: {result.target_market}")
            if result.value_proposition:
                print(f"💎 Value Proposition: {result.value_proposition}")
            
            # Technology
            if result.tech_stack:
                print(f"⚙️ Technologies: {', '.join(result.tech_stack)}")
            
            # Services
            if result.key_services:
                print(f"🛠️ Key Services: {', '.join(result.key_services)}")
            
            # Leadership
            if result.leadership_team:
                print(f"👔 Leadership: {', '.join(result.leadership_team)}")
            
            # Contact info
            if result.contact_info:
                print(f"📞 Contact Info: {json.dumps(result.contact_info, indent=2)}")
            
            # Additional insights
            if result.competitive_advantages:
                print(f"🌟 Competitive Advantages: {', '.join(result.competitive_advantages)}")
            
            # Show crawled pages
            if result.pages_crawled:
                print(f"\n📄 Successfully crawled {len(result.pages_crawled)} pages:")
                for i, page in enumerate(result.pages_crawled, 1):
                    print(f"  {i}. {page}")
            
        else:
            print(f"❌ AI extraction failed: {result.scrape_error}")
        
        print("\n" + "=" * 60)
        print("✅ AI extraction test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run the async test"""
    asyncio.run(test_ai_extraction())

if __name__ == "__main__":
    main()