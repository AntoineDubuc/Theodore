#!/usr/bin/env python3
"""
Check what's actually in the theodore-companies Pinecone index
"""

import logging
import os
from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.pinecone_client import PineconeClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_pinecone_index():
    """Check what's stored in Pinecone index"""
    
    load_dotenv()
    
    print("🔍 CHECKING THEODORE-COMPANIES PINECONE INDEX")
    print("=" * 50)
    
    config = CompanyIntelligenceConfig()
    
    # Connect to Pinecone
    pinecone_client = PineconeClient(
        config=config,
        api_key=os.getenv("PINECONE_API_KEY"),
        environment="us-east-1",
        index_name="theodore-companies"
    )
    
    try:
        # Get index stats
        stats = pinecone_client.index.describe_index_stats()
        print(f"📊 Index Statistics:")
        print(f"   Total vectors: {stats.total_vector_count}")
        print(f"   Index fullness: {stats.index_fullness}")
        print(f"   Dimension: {stats.dimension}")
        
        if stats.total_vector_count > 0:
            print(f"\n✅ Index contains {stats.total_vector_count} vectors")
            
            # Try to query for any vectors
            print(f"\n🔍 Searching for all vectors...")
            
            # Create a dummy vector for search (same dimension as index)
            dummy_vector = [0.0] * stats.dimension
            
            # Query to get all vectors
            query_result = pinecone_client.index.query(
                vector=dummy_vector,
                top_k=10,
                include_metadata=True,
                include_values=False
            )
            
            print(f"📋 Found {len(query_result.matches)} vectors:")
            
            for i, match in enumerate(query_result.matches, 1):
                print(f"\n   {i}. Vector ID: {match.id}")
                print(f"      Score: {match.score:.6f}")
                
                if match.metadata:
                    print(f"      Metadata ({len(match.metadata)} fields):")
                    for key, value in list(match.metadata.items())[:10]:  # Show first 10 fields
                        if isinstance(value, list):
                            print(f"        {key}: {len(value)} items")
                            if value:
                                print(f"          First item: {value[0]}")
                        elif isinstance(value, str) and len(value) > 100:
                            print(f"        {key}: {value[:100]}...")
                        else:
                            print(f"        {key}: {value}")
                    
                    if len(match.metadata) > 10:
                        print(f"        ... and {len(match.metadata) - 10} more fields")
                else:
                    print(f"      No metadata")
            
            # Try to fetch a specific vector if we know the ID
            if query_result.matches:
                first_id = query_result.matches[0].id
                print(f"\n🔎 Fetching vector {first_id}...")
                
                fetch_result = pinecone_client.index.fetch(ids=[first_id])
                
                if first_id in fetch_result.vectors:
                    vector_data = fetch_result.vectors[first_id]
                    print(f"✅ Successfully fetched vector")
                    print(f"   Values: {len(vector_data.values)} dimensions")
                    print(f"   Metadata fields: {len(vector_data.metadata) if vector_data.metadata else 0}")
                    
                    if vector_data.metadata:
                        print(f"\n📋 Complete Metadata:")
                        for key, value in vector_data.metadata.items():
                            if isinstance(value, list):
                                print(f"   {key}: {len(value)} items")
                                for j, item in enumerate(value[:3], 1):
                                    print(f"     {j}. {item}")
                                if len(value) > 3:
                                    print(f"     ... and {len(value)-3} more")
                            elif isinstance(value, str) and len(value) > 200:
                                print(f"   {key}: {value[:200]}...")
                            else:
                                print(f"   {key}: {value}")
                else:
                    print(f"❌ Failed to fetch vector {first_id}")
        
        else:
            print(f"\n⚠️ Index is empty - no vectors stored")
            
    except Exception as e:
        print(f"❌ Error checking index: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_pinecone_index()