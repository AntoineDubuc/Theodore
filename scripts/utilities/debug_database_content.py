#!/usr/bin/env python3
"""
Debug what's actually in the Theodore database
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src')

from models import CompanyIntelligenceConfig
from pinecone_client import PineconeClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def debug_database():
    """Check what's in the database"""
    print("🔍 DEBUGGING THEODORE DATABASE CONTENT")
    print("=" * 60)
    
    try:
        # Initialize Pinecone
        config = CompanyIntelligenceConfig()
        pinecone_client = PineconeClient(
            config=config,
            api_key=os.getenv('PINECONE_API_KEY'),
            environment=os.getenv('PINECONE_ENVIRONMENT', 'us-east-1'),
            index_name=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        )
        
        print(f"✅ Connected to Pinecone index: {os.getenv('PINECONE_INDEX_NAME')}")
        
        # Get index stats
        stats = pinecone_client.index.describe_index_stats()
        print(f"📊 Total vectors: {stats.total_vector_count}")
        print(f"📊 Index dimension: {stats.dimension}")
        
        # Query for any companies
        print(f"\n🔍 Sampling database content...")
        
        query_result = pinecone_client.index.query(
            vector=[0.0] * 1536,
            top_k=10,
            include_metadata=True,
            include_values=False
        )
        
        print(f"📋 Found {len(query_result.matches)} entries")
        
        for i, match in enumerate(query_result.matches, 1):
            metadata = match.metadata
            print(f"\n{i}. ID: {match.id}")
            print(f"   Score: {match.score:.4f}")
            
            # Check available fields
            available_fields = list(metadata.keys()) if metadata else []
            print(f"   Available fields ({len(available_fields)}): {', '.join(available_fields[:10])}")
            
            # Key fields check
            key_fields = {
                'name': metadata.get('name'),
                'website': metadata.get('website'),
                'ai_summary': len(metadata.get('ai_summary', '')) if metadata.get('ai_summary') else 0,
                'company_description': len(metadata.get('company_description', '')) if metadata.get('company_description') else 0,
                'industry': metadata.get('industry'),
                'value_proposition': len(metadata.get('value_proposition', '')) if metadata.get('value_proposition') else 0
            }
            
            print(f"   Key fields:")
            for field, value in key_fields.items():
                if field in ['ai_summary', 'company_description', 'value_proposition']:
                    print(f"     {field}: {value} chars")
                else:
                    print(f"     {field}: {value}")
            
            # Classification status
            classification_fields = {
                'saas_classification': metadata.get('saas_classification'),
                'classification_confidence': metadata.get('classification_confidence'),
                'is_saas': metadata.get('is_saas')
            }
            
            has_classification = any(v is not None for v in classification_fields.values())
            print(f"   Classification: {'✅ Present' if has_classification else '❌ Missing'}")
            
            if has_classification:
                for field, value in classification_fields.items():
                    print(f"     {field}: {value}")
        
        # Field availability summary
        print(f"\n📊 FIELD AVAILABILITY SUMMARY")
        print("=" * 40)
        
        field_counts = {}
        for match in query_result.matches:
            if match.metadata:
                for field in match.metadata.keys():
                    field_counts[field] = field_counts.get(field, 0) + 1
        
        for field, count in sorted(field_counts.items()):
            percentage = (count / len(query_result.matches)) * 100
            print(f"   {field:25}: {count:2}/{len(query_result.matches)} ({percentage:3.0f}%)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_database()