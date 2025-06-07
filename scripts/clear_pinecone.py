#!/usr/bin/env python3
"""
Script to clear all data from Pinecone index
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.models import CompanyIntelligenceConfig
from src.pinecone_client import PineconeClient

def main():
    """Clear all data from Pinecone index"""
    
    # Load environment variables
    load_dotenv()
    
    print("🗑️ Clearing Pinecone Database...")
    
    # Configuration
    config = CompanyIntelligenceConfig()
    
    # Initialize Pinecone client
    try:
        pinecone_client = PineconeClient(
            config=config,
            api_key=os.getenv('PINECONE_API_KEY'),
            environment=os.getenv('PINECONE_ENVIRONMENT'),
            index_name=os.getenv('PINECONE_INDEX_NAME')
        )
        print("✅ Connected to Pinecone")
    except Exception as e:
        print(f"❌ Failed to connect to Pinecone: {e}")
        return
    
    # Get current stats
    stats = pinecone_client.get_index_stats()
    current_count = stats.get('total_vectors', 0)
    
    print(f"📊 Current vectors in database: {current_count}")
    
    if current_count == 0:
        print("✅ Database is already empty")
        return
    
    # Auto-confirm for script execution
    print(f"⚠️ Proceeding to delete all {current_count} vectors...")
    
    try:
        # Delete all vectors from the index
        pinecone_client.index.delete(delete_all=True)
        print("✅ All vectors deleted from Pinecone index")
        
        # Verify deletion
        import time
        print("⏳ Waiting for deletion to complete...")
        time.sleep(3)  # Give it a moment to process
        
        new_stats = pinecone_client.get_index_stats()
        new_count = new_stats.get('total_vectors', 0)
        
        print(f"📊 Vectors remaining: {new_count}")
        
        if new_count == 0:
            print("🎉 Database successfully cleared!")
        else:
            print(f"⚠️ Still {new_count} vectors remaining (may take time to sync)")
        
    except Exception as e:
        print(f"❌ Failed to clear database: {e}")

if __name__ == "__main__":
    main()