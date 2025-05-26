#!/usr/bin/env python3
"""
Verify what's actually stored in the chunked Pinecone index
"""

import logging
import time
from dotenv import load_dotenv

from src.models import CompanyIntelligenceConfig
from src.chunked_pinecone_client import ChunkedPineconeClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_chunked_storage():
    """Verify what's stored in the chunked index"""
    
    load_dotenv()
    
    print("🔍 VERIFYING CHUNKED PINECONE STORAGE")
    print("=" * 50)
    
    config = CompanyIntelligenceConfig()
    
    # Connect to chunked index
    import os
    pinecone_client = ChunkedPineconeClient(
        config=config,
        api_key=os.getenv("PINECONE_API_KEY"),
        environment="us-east-1",
        index_name="theodore-chunked"
    )
    
    # Wait a moment for serverless index to be ready
    print("⏳ Waiting for serverless index to be ready...")
    time.sleep(10)
    
    # Get index stats
    print("\n📊 Index Statistics:")
    stats = pinecone_client.get_index_stats()
    print(f"   Total vectors: {stats.get('total_vectors', 0)}")
    print(f"   Dimension: {stats.get('dimension', 0)}")
    print(f"   Index fullness: {stats.get('index_fullness', 0):.2%}")
    
    if stats.get('total_vectors', 0) > 0:
        print(f"\n✅ Index contains {stats.get('total_vectors')} vectors")
        
        # Try to query for any vectors using a zero vector
        print(f"\n🔍 Querying for all vectors...")
        
        try:
            # Query with zero vector to get all vectors
            response = pinecone_client.index.query(
                vector=[0.0] * 1536,
                top_k=20,
                include_metadata=True,
                include_values=False
            )
            
            print(f"📋 Query returned {len(response.matches)} vectors:")
            
            for i, match in enumerate(response.matches, 1):
                print(f"\n   {i}. ID: {match.id}")
                print(f"      Score: {match.score:.6f}")
                
                if match.metadata:
                    print(f"      Metadata:")
                    for key, value in match.metadata.items():
                        if isinstance(value, str) and len(value) > 50:
                            print(f"        {key}: {value[:50]}...")
                        else:
                            print(f"        {key}: {value}")
                else:
                    print(f"      No metadata")
            
            # Try specific fetch by ID if we have results
            if response.matches:
                first_id = response.matches[0].id
                print(f"\n🔎 Fetching specific vector: {first_id}")
                
                fetch_response = pinecone_client.index.fetch(ids=[first_id])
                
                if first_id in fetch_response.vectors:
                    vector_data = fetch_response.vectors[first_id]
                    print(f"✅ Successfully fetched vector")
                    print(f"   Vector dimension: {len(vector_data.values)}")
                    print(f"   Metadata fields: {len(vector_data.metadata) if vector_data.metadata else 0}")
                    
                    if vector_data.metadata:
                        print(f"   Sample metadata:")
                        for key, value in list(vector_data.metadata.items())[:5]:
                            print(f"     {key}: {value}")
                else:
                    print(f"❌ Could not fetch vector {first_id}")
        
        except Exception as e:
            print(f"❌ Query failed: {e}")
    
    else:
        print(f"\n⚠️ Index appears empty")
        
        # Check if index exists and is ready
        try:
            index_description = pinecone_client.pc.describe_index(pinecone_client.index_name)
            print(f"\n📋 Index Description:")
            print(f"   Name: {index_description.name}")
            print(f"   Status: {index_description.status}")
            print(f"   Dimension: {index_description.dimension}")
            print(f"   Metric: {index_description.metric}")
            
        except Exception as e:
            print(f"❌ Could not describe index: {e}")

if __name__ == "__main__":
    verify_chunked_storage()