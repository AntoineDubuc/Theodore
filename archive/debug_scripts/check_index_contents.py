#!/usr/bin/env python3
"""
Check what's actually in the Pinecone index
"""

import logging
from dotenv import load_dotenv

from src.models import CompanyIntelligenceConfig
from src.chunked_pinecone_client import ChunkedPineconeClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_index_contents():
    """Check what's actually stored in Pinecone"""
    
    load_dotenv()
    
    print("🔍 CHECKING PINECONE INDEX CONTENTS")
    print("=" * 40)
    
    config = CompanyIntelligenceConfig()
    
    # Connect to the index
    import os
    pinecone_client = ChunkedPineconeClient(
        config=config,
        api_key=os.getenv("PINECONE_API_KEY"),
        environment="us-east-1",
        index_name="theodore-chunked"
    )
    
    # Get index stats
    stats = pinecone_client.get_index_stats()
    print(f"📊 Index Statistics:")
    print(f"   Total vectors: {stats.get('total_vectors', 0)}")
    print(f"   Dimension: {stats.get('dimension', 0)}")
    print(f"   Index fullness: {stats.get('index_fullness', 0):.2%}")
    
    if stats.get('total_vectors', 0) > 0:
        print(f"\n✅ Index contains {stats.get('total_vectors')} vectors")
        
        # Query for all vectors
        try:
            response = pinecone_client.index.query(
                vector=[0.0] * 1536,
                top_k=20,
                include_metadata=True,
                include_values=False
            )
            
            print(f"\n📋 Found {len(response.matches)} vectors:")
            
            for i, match in enumerate(response.matches, 1):
                print(f"\n   {i}. ID: {match.id}")
                print(f"      Score: {match.score:.6f}")
                
                if match.metadata:
                    print(f"      Company: {match.metadata.get('company_name', 'Unknown')}")
                    print(f"      Chunk Type: {match.metadata.get('chunk_type', 'Unknown')}")
                    print(f"      Industry: {match.metadata.get('industry', 'Unknown')}")
                    print(f"      Business Model: {match.metadata.get('business_model', 'Unknown')}")
                    print(f"      Location: {match.metadata.get('location_city', 'Unknown')}")
                else:
                    print(f"      No metadata")
            
            return True
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return False
    
    else:
        print(f"\n⚠️ Index is empty - no vectors found")
        return False

if __name__ == "__main__":
    success = check_index_contents()
    
    if success:
        print(f"\n✅ Data found in Pinecone index")
    else:
        print(f"\n❌ No data found in Pinecone index")