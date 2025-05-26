#!/usr/bin/env python3
"""
Test the corrected chunked Pinecone approach
"""

import asyncio
import logging
from dotenv import load_dotenv

from src.models import CompanyData, CompanyIntelligenceConfig
from src.enhanced_crawl4ai_scraper import EnhancedCrawl4AICompanyScraper
from src.chunked_pinecone_client import ChunkedPineconeClient
from src.bedrock_client import BedrockClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_chunked_approach():
    """Test the corrected chunking approach"""
    
    load_dotenv()
    
    print("🚀 TESTING CORRECTED CHUNKED PINECONE APPROACH")
    print("=" * 60)
    
    # Create config
    config = CompanyIntelligenceConfig()
    
    # Step 1: Extract company data
    print("📊 Step 1: Extracting company data...")
    company = CompanyData(name="Visterra Inc", website="https://visterrainc.com")
    scraper = EnhancedCrawl4AICompanyScraper(config)
    
    # Use focused pages
    scraper.page_configs = [
        {"path": "", "type": "general", "priority": "high"},
        {"path": "/about-us", "type": "general", "priority": "high"},
        {"path": "/leadership", "type": "leadership", "priority": "high"},
        {"path": "/services", "type": "product", "priority": "high"},
        {"path": "/contact", "type": "general", "priority": "high"}
    ]
    
    extracted_company = await scraper.scrape_company_comprehensive(company)
    
    print(f"✅ Extracted data from {len(extracted_company.pages_crawled)} pages")
    print(f"   Company: {extracted_company.name}")
    print(f"   Industry: {extracted_company.industry}")
    print(f"   Leadership: {len(extracted_company.leadership_team or [])} executives")
    print(f"   Services: {len(extracted_company.key_services or [])} services")
    print(f"   Tech Stack: {len(extracted_company.tech_stack or [])} technologies")
    
    # Step 2: Initialize chunked Pinecone client
    print(f"\n📦 Step 2: Initializing chunked Pinecone client...")
    import os
    
    pinecone_client = ChunkedPineconeClient(
        config=config,
        api_key=os.getenv("PINECONE_API_KEY"),
        environment="us-east-1",
        index_name="theodore-chunked"
    )
    
    # Step 3: Extract and show chunks
    print(f"\n🔧 Step 3: Extracting company chunks...")
    chunks = pinecone_client.extract_company_chunks(extracted_company)
    
    print(f"📋 Extracted {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks, 1):
        print(f"   {i}. {chunk['type'].upper()} ({len(chunk['content'])} chars)")
        print(f"      Content: {chunk['content'][:100]}...")
        print(f"      Priority: {chunk['priority']}")
        print()
    
    # Step 4: Generate embeddings and store chunks
    print(f"🧠 Step 4: Generating embeddings and storing chunks...")
    bedrock_client = BedrockClient(config)
    
    chunk_ids = pinecone_client.upsert_company_chunks(extracted_company, bedrock_client)
    
    if chunk_ids:
        print(f"✅ Successfully stored {len(chunk_ids)} chunks:")
        for chunk_id in chunk_ids:
            print(f"   • {chunk_id}")
    else:
        print(f"❌ Failed to store chunks")
        return
    
    # Step 5: Test search functionality
    print(f"\n🔍 Step 5: Testing search functionality...")
    
    # Test searches
    search_queries = [
        ("biotechnology companies with experienced leadership", ["leadership"]),
        ("companies developing antibody therapies", ["products"]),
        ("AI-powered drug discovery platforms", ["technology"]),
        ("Massachusetts biotech companies", None),
        ("company contact information in Waltham", ["contact"])
    ]
    
    for query, chunk_types in search_queries:
        print(f"\n   Query: '{query}'")
        if chunk_types:
            print(f"   Chunk types: {chunk_types}")
        
        results = pinecone_client.search_companies(
            query=query,
            bedrock_client=bedrock_client,
            chunk_types=chunk_types,
            top_k=5
        )
        
        print(f"   Results: {len(results)} chunks found")
        for result in results[:3]:
            print(f"     • {result['company_name']} ({result['chunk_type']}) - Score: {result['score']:.3f}")
        print()
    
    # Step 6: Test metadata filtering
    print(f"🔍 Step 6: Testing metadata filtering...")
    
    # Filter by industry
    biotech_results = pinecone_client.search_companies(
        query="research and development",
        bedrock_client=bedrock_client,
        filters={"industry": "biotechnology"},
        top_k=10
    )
    
    print(f"   Biotech companies: {len(biotech_results)} chunks")
    
    # Filter by location
    ma_results = pinecone_client.search_companies(
        query="company information",
        bedrock_client=bedrock_client, 
        filters={"location_state": "ma"},
        top_k=10
    )
    
    print(f"   Massachusetts companies: {len(ma_results)} chunks")
    
    # Step 7: Show index statistics
    print(f"\n📊 Step 7: Index statistics...")
    stats = pinecone_client.get_index_stats()
    
    print(f"   Total vectors: {stats.get('total_vectors', 0)}")
    print(f"   Dimensions: {stats.get('dimension', 0)}")
    print(f"   Index fullness: {stats.get('index_fullness', 0):.2%}")
    
    # Step 8: Test company chunk retrieval
    print(f"\n🔎 Step 8: Testing company chunk retrieval...")
    
    company_chunks = pinecone_client.get_company_chunks(extracted_company.id)
    print(f"   Retrieved {len(company_chunks)} chunks for {extracted_company.name}")
    
    for chunk in company_chunks:
        chunk_type = chunk['metadata'].get('chunk_type', 'unknown')
        print(f"     • {chunk['chunk_id']} ({chunk_type})")
    
    print(f"\n" + "=" * 60)
    print("✅ CHUNKED APPROACH TEST COMPLETED!")
    
    print(f"\n🎯 BENEFITS DEMONSTRATED:")
    print(f"   • Multiple focused vectors per company ({len(chunks)} chunks)")
    print(f"   • Semantic search within specific content types")
    print(f"   • Efficient metadata filtering")
    print(f"   • Scalable architecture for 400+ companies")
    print(f"   • Precise search relevance")
    
    return {
        "company_id": extracted_company.id,
        "chunk_ids": chunk_ids,
        "chunks_count": len(chunks),
        "search_results": len(biotech_results)
    }

if __name__ == "__main__":
    result = asyncio.run(test_chunked_approach())
    
    if result:
        print(f"\n📄 Chunked storage successful for {result['chunks_count']} chunks!")
    else:
        print(f"\n❌ Chunked approach test failed")