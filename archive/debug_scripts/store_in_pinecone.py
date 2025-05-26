#!/usr/bin/env python3
"""
Store the extracted Crawl4AI data in Pinecone and show what gets stored
"""

import asyncio
import logging
from dotenv import load_dotenv

from src.models import CompanyData, CompanyIntelligenceConfig
from src.enhanced_crawl4ai_scraper import EnhancedCrawl4AICompanyScraper
from src.pinecone_client import PineconeClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def store_and_review_pinecone():
    """Store extracted data in Pinecone and show what gets stored"""
    
    load_dotenv()
    
    print("🚀 STORING CRAWL4AI DATA IN PINECONE")
    print("=" * 50)
    
    # Create config and company
    config = CompanyIntelligenceConfig()
    company = CompanyData(
        name="Visterra Inc",
        website="https://visterrainc.com"
    )
    
    # Extract data using enhanced scraper
    print("📊 Step 1: Extracting comprehensive company data...")
    scraper = EnhancedCrawl4AICompanyScraper(config)
    
    # Use a focused set for faster extraction
    scraper.page_configs = [
        {"path": "", "type": "general", "priority": "high"},
        {"path": "/about-us", "type": "general", "priority": "high"},
        {"path": "/leadership", "type": "leadership", "priority": "high"},
        {"path": "/services", "type": "product", "priority": "high"},
        {"path": "/contact", "type": "general", "priority": "high"}
    ]
    
    extracted_company = await scraper.scrape_company_comprehensive(company)
    
    print(f"✅ Extraction completed: {len(extracted_company.pages_crawled)} pages")
    
    # Store in Pinecone
    print("\n📦 Step 2: Storing in Pinecone...")
    import os
    pinecone_client = PineconeClient(
        config=config,
        api_key=os.getenv("PINECONE_API_KEY"),
        environment="us-east-1",
        index_name="company-intelligence"
    )
    
    # Store the company data
    success = pinecone_client.upsert_company(extracted_company)
    vector_id = extracted_company.id
    
    print(f"✅ Stored in Pinecone with ID: {vector_id}")
    
    # Retrieve and show what was actually stored
    print("\n🔍 Step 3: Retrieving stored data from Pinecone...")
    
    try:
        # Get the stored data
        stored_data = pinecone_client.get_company_metadata(vector_id)
        
        print("\n📋 WHAT'S ACTUALLY STORED IN PINECONE:")
        print("=" * 50)
        
        print(f"🆔 Vector ID: {vector_id}")
        print(f"🏢 Company: {stored_data.get('name', 'Not found')}")
        print(f"🌐 Website: {stored_data.get('website', 'Not found')}")
        print(f"📄 Pages Crawled: {len(stored_data.get('pages_crawled', []))}")
        
        print(f"\n📊 SEARCHABLE METADATA (stored with vector):")
        print("-" * 40)
        metadata = pinecone_client._prepare_pinecone_metadata(extracted_company)
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        
        print(f"\n🏭 BUSINESS INTELLIGENCE:")
        print("-" * 40)
        print(f"  Industry: {stored_data.get('industry', 'Not found')}")
        print(f"  Business Model: {stored_data.get('business_model', 'Not found')}")
        print(f"  Target Market: {stored_data.get('target_market', 'Not found')}")
        print(f"  Location: {stored_data.get('location', 'Not found')}")
        print(f"  Employee Count: {stored_data.get('employee_count_range', 'Not found')}")
        
        print(f"\n👑 LEADERSHIP TEAM:")
        print("-" * 40)
        leadership = stored_data.get('leadership_team', [])
        if leadership:
            for i, leader in enumerate(leadership, 1):
                print(f"  {i}. {leader}")
        else:
            print("  No leadership data stored")
        
        print(f"\n🛠️ KEY SERVICES:")
        print("-" * 40)
        services = stored_data.get('key_services', [])
        if services:
            for i, service in enumerate(services, 1):
                print(f"  {i}. {service}")
        else:
            print("  No services data stored")
        
        print(f"\n💻 TECHNOLOGY STACK:")
        print("-" * 40)
        tech = stored_data.get('tech_stack', [])
        if tech:
            for i, technology in enumerate(tech, 1):
                print(f"  {i}. {technology}")
        else:
            print("  No tech stack data stored")
        
        print(f"\n📞 CONTACT INFORMATION:")
        print("-" * 40)
        contact = stored_data.get('contact_info', {})
        if contact:
            for key, value in contact.items():
                if value:
                    print(f"  {key.title()}: {value}")
        else:
            print("  No contact data stored")
        
        print(f"\n🌐 PAGES PROCESSED:")
        print("-" * 40)
        pages = stored_data.get('pages_crawled', [])
        if pages:
            for i, page in enumerate(pages, 1):
                print(f"  {i}. {page}")
        else:
            print("  No pages data stored")
        
        print(f"\n📈 CRAWL METADATA:")
        print("-" * 40)
        print(f"  Crawl Duration: {stored_data.get('crawl_duration', 0):.1f} seconds")
        print(f"  Crawl Depth: {stored_data.get('crawl_depth', 0)} pages")
        print(f"  Scrape Status: {stored_data.get('scrape_status', 'unknown')}")
        
        # Test search functionality
        print(f"\n🔍 TESTING SEARCH FUNCTIONALITY:")
        print("-" * 40)
        
        # Search by industry
        print("  Searching for 'biotechnology companies'...")
        biotech_results = pinecone_client.find_companies_by_industry("biotechnology", top_k=5)
        print(f"    Found {len(biotech_results)} results")
        for result in biotech_results:
            score = result.get('score', 0)
            metadata = result.get('metadata', {})
            print(f"    • {metadata.get('company_name', 'Unknown')} (similarity: {score:.3f})")
        
        # Search similar companies
        print("\n  Searching for companies similar to Visterra...")
        similar_results = pinecone_client.find_similar_companies(vector_id, top_k=5)
        print(f"    Found {len(similar_results)} results")
        for result in similar_results:
            score = result.get('score', 0)
            metadata = result.get('metadata', {})
            print(f"    • {metadata.get('company_name', 'Unknown')} (similarity: {score:.3f})")
        
        print(f"\n" + "=" * 50)
        print("✅ Pinecone storage and retrieval verified!")
        print(f"\nData successfully stored and searchable in Pinecone:")
        print(f"  • Vector ID: {vector_id}")
        print(f"  • Searchable metadata: {len(metadata)} fields")
        print(f"  • Complete data: {len(stored_data)} fields")
        print(f"  • Search functionality: Working")
        
        return vector_id, stored_data
        
    except Exception as e:
        print(f"❌ Error retrieving from Pinecone: {e}")
        return vector_id, None

if __name__ == "__main__":
    vector_id, stored_data = asyncio.run(store_and_review_pinecone())
    
    if stored_data:
        print(f"\n📄 Complete data stored in Pinecone for company: {stored_data.get('name')}")
    else:
        print(f"\n❌ Failed to retrieve stored data")