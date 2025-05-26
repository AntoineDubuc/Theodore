#!/usr/bin/env python3
"""
Properly store Crawl4AI data in Pinecone with embeddings
"""

import asyncio
import logging
from dotenv import load_dotenv

from src.models import CompanyData, CompanyIntelligenceConfig
from src.enhanced_crawl4ai_scraper import EnhancedCrawl4AICompanyScraper
from src.pinecone_client import PineconeClient
from src.bedrock_client import BedrockClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def store_with_embeddings():
    """Extract, generate embeddings, and store in Pinecone"""
    
    load_dotenv()
    
    print("🚀 COMPLETE PINECONE STORAGE WITH EMBEDDINGS")
    print("=" * 60)
    
    # Create config and company
    config = CompanyIntelligenceConfig()
    company = CompanyData(
        name="Visterra Inc",
        website="https://visterrainc.com"
    )
    
    # Step 1: Extract comprehensive data
    print("📊 Step 1: Extracting comprehensive company data...")
    scraper = EnhancedCrawl4AICompanyScraper(config)
    
    # Use focused pages for demo
    scraper.page_configs = [
        {"path": "", "type": "general", "priority": "high"},
        {"path": "/about-us", "type": "general", "priority": "high"},
        {"path": "/leadership", "type": "leadership", "priority": "high"},
        {"path": "/services", "type": "product", "priority": "high"},
        {"path": "/contact", "type": "general", "priority": "high"}
    ]
    
    extracted_company = await scraper.scrape_company_comprehensive(company)
    
    print(f"✅ Extraction completed: {len(extracted_company.pages_crawled)} pages")
    print(f"   Company: {extracted_company.name}")
    print(f"   Industry: {extracted_company.industry}")
    print(f"   Leadership: {len(extracted_company.leadership_team or [])} executives")
    print(f"   Services: {len(extracted_company.key_services or [])} services")
    
    # Step 2: Generate embedding
    print(f"\n🧠 Step 2: Generating embedding...")
    bedrock_client = BedrockClient(config)
    
    # Create text for embedding
    embedding_text = f"{extracted_company.company_description or ''} {' '.join(extracted_company.key_services or [])} {extracted_company.industry or ''} {extracted_company.target_market or ''}"
    embedding_text = embedding_text.strip()
    
    print(f"   Embedding text: {embedding_text[:100]}...")
    
    embedding = bedrock_client.generate_embedding(embedding_text)
    
    if embedding:
        extracted_company.embedding = embedding
        print(f"✅ Generated embedding: {len(embedding)} dimensions")
    else:
        print(f"❌ Failed to generate embedding")
        return None
    
    # Step 3: Store in Pinecone
    print(f"\n📦 Step 3: Storing in Pinecone...")
    import os
    pinecone_client = PineconeClient(
        config=config,
        api_key=os.getenv("PINECONE_API_KEY"),
        environment="us-east-1",
        index_name="theodore-companies"
    )
    
    success = pinecone_client.upsert_company(extracted_company)
    
    if success:
        print(f"✅ Successfully stored in Pinecone")
        vector_id = extracted_company.id
    else:
        print(f"❌ Failed to store in Pinecone")
        return None
    
    # Step 4: Verify storage
    print(f"\n🔍 Step 4: Verifying Pinecone storage...")
    
    try:
        # Get metadata
        stored_metadata = pinecone_client.get_company_metadata(vector_id)
        
        if stored_metadata:
            print(f"\n📋 SUCCESSFULLY STORED IN PINECONE:")
            print("=" * 50)
            print(f"🆔 Vector ID: {vector_id}")
            print(f"🏢 Company: {stored_metadata.get('name', 'Not found')}")
            print(f"🏭 Industry: {stored_metadata.get('industry', 'Not found')}")
            print(f"💼 Business Model: {stored_metadata.get('business_model', 'Not found')}")
            print(f"📍 Location: {stored_metadata.get('location', 'Not found')}")
            
            # Show leadership team
            leadership = stored_metadata.get('leadership_team', [])
            print(f"\n👑 Leadership Team ({len(leadership)} executives):")
            for i, leader in enumerate(leadership[:5], 1):
                print(f"   {i}. {leader}")
            
            # Show services
            services = stored_metadata.get('key_services', [])
            print(f"\n🛠️ Key Services ({len(services)} services):")
            for i, service in enumerate(services, 1):
                print(f"   {i}. {service}")
            
            # Show contact info
            contact = stored_metadata.get('contact_info', {})
            print(f"\n📞 Contact Information:")
            for key, value in contact.items():
                if value:
                    print(f"   {key.title()}: {value}")
            
            print(f"\n📄 Pages Crawled: {len(stored_metadata.get('pages_crawled', []))}")
            
        else:
            print(f"❌ No metadata found for {vector_id}")
            return None
        
        # Step 5: Test search
        print(f"\n🔍 Step 5: Testing search functionality...")
        
        # Search by industry
        industry_results = pinecone_client.find_companies_by_industry("biotechnology", top_k=10)
        print(f"   Industry search results: {len(industry_results)} companies")
        
        for result in industry_results[:3]:
            metadata = result.get('metadata', {})
            score = result.get('score', 0)
            print(f"   • {metadata.get('name', 'Unknown')} (score: {score:.3f})")
        
        # Search similar companies
        similar_results = pinecone_client.find_similar_companies(vector_id, top_k=5)
        print(f"\n   Similar companies: {len(similar_results)} found")
        
        for result in similar_results[:3]:
            metadata = result.get('metadata', {})
            score = result.get('score', 0)
            print(f"   • {metadata.get('name', 'Unknown')} (similarity: {score:.3f})")
        
        print(f"\n" + "=" * 60)
        print("✅ COMPLETE SUCCESS!")
        print(f"\nVisterra Inc data is now properly stored in Pinecone:")
        print(f"   • Vector ID: {vector_id}")
        print(f"   • Index: theodore-companies")
        print(f"   • Embedding: {len(extracted_company.embedding)} dimensions")
        print(f"   • Metadata: Complete company intelligence")
        print(f"   • Search: Fully functional")
        
        return vector_id, stored_metadata
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(store_with_embeddings())
    
    if result:
        vector_id, metadata = result
        print(f"\n📄 Complete Visterra data now available in theodore-companies index!")
    else:
        print(f"\n❌ Storage failed")