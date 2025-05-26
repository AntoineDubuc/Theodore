#!/usr/bin/env python3
"""
Direct test to verify Visterra data in Pinecone
"""

import os
import sys
from dotenv import load_dotenv
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.models import CompanyIntelligenceConfig
from src.pinecone_client import PineconeClient

def main():
    """Test direct Pinecone queries"""
    
    load_dotenv()
    
    print("🔍 Testing Pinecone Data for Visterra...")
    
    config = CompanyIntelligenceConfig()
    
    pinecone_client = PineconeClient(
        config=config,
        api_key=os.getenv('PINECONE_API_KEY'),
        environment=os.getenv('PINECONE_ENVIRONMENT'),
        index_name=os.getenv('PINECONE_INDEX_NAME')
    )
    
    # Get stats
    stats = pinecone_client.get_index_stats()
    print(f"📊 Index Stats: {stats}")
    
    # Try different query approaches
    print("\n🔍 Method 1: Query with metadata filter")
    try:
        query_response = pinecone_client.index.query(
            vector=[0.0] * 1536,
            top_k=100,
            include_metadata=True,
            filter={"company_name": {"$eq": "Visterra"}}
        )
        print(f"Found {len(query_response.matches)} companies with name filter")
        for match in query_response.matches:
            print(f"- {match.metadata.get('company_name', 'Unknown')}")
    except Exception as e:
        print(f"Error with name filter: {e}")
    
    print("\n🔍 Method 2: Query all vectors")
    try:
        query_response = pinecone_client.index.query(
            vector=[0.0] * 1536,
            top_k=100,
            include_metadata=True
        )
        print(f"Found {len(query_response.matches)} total companies")
        for match in query_response.matches:
            company_name = match.metadata.get('company_name', 'Unknown')
            industry = match.metadata.get('industry', 'Unknown')
            print(f"- {company_name} ({industry})")
    except Exception as e:
        print(f"Error with general query: {e}")
    
    print("\n🔍 Method 3: List all index contents")
    try:
        # Alternative approach - describe the index
        index_description = pinecone_client.index.describe_index_stats()
        print(f"Index description: {index_description}")
    except Exception as e:
        print(f"Error describing index: {e}")

if __name__ == "__main__":
    main()