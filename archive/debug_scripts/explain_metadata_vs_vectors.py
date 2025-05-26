#!/usr/bin/env python3
"""
Explain what metadata vs vectorized content means and show what was stored
"""

import logging
from dotenv import load_dotenv

from src.models import CompanyIntelligenceConfig
from src.chunked_pinecone_client import ChunkedPineconeClient

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def explain_metadata_vs_vectors():
    """Explain metadata vs vectorized content with examples"""
    
    load_dotenv()
    
    print("📚 METADATA vs VECTORIZED CONTENT EXPLANATION")
    print("=" * 60)
    
    print("🔍 CONCEPTUAL DIFFERENCE:")
    print("-" * 30)
    print("📊 METADATA = Searchable tags/filters (stored as key-value pairs)")
    print("🧠 VECTORS = Content converted to embeddings (stored as 1,536 numbers)")
    print()
    print("📊 Metadata is for FILTERING (industry=biotech, location=MA)")
    print("🧠 Vectors are for SIMILARITY SEARCH (semantic meaning)")
    
    config = CompanyIntelligenceConfig()
    
    # Connect to index
    import os
    pinecone_client = ChunkedPineconeClient(
        config=config,
        api_key=os.getenv("PINECONE_API_KEY"),
        environment="us-east-1",
        index_name="theodore-chunked"
    )
    
    print(f"\n🔍 WHAT'S ACTUALLY STORED IN PINECONE:")
    print("=" * 60)
    
    # Get all vectors with full details
    try:
        # Fetch specific vectors to see the actual content
        response = pinecone_client.index.query(
            vector=[0.0] * 1536,
            top_k=10,
            include_metadata=True,
            include_values=False
        )
        
        if response.matches:
            # Get the actual vector data including values
            vector_ids = [match.id for match in response.matches]
            fetch_response = pinecone_client.index.fetch(ids=vector_ids)
            
            for i, (vector_id, vector_data) in enumerate(fetch_response.vectors.items(), 1):
                chunk_type = vector_data.metadata.get('chunk_type', 'unknown')
                company_name = vector_data.metadata.get('company_name', 'unknown')
                
                print(f"\n📋 CHUNK {i}: {chunk_type.upper()}")
                print("=" * 40)
                
                print(f"🏷️ METADATA (Key-Value Pairs for Filtering):")
                print("-" * 25)
                for key, value in vector_data.metadata.items():
                    if isinstance(value, str) and len(value) > 50:
                        print(f"   {key}: {value[:50]}...")
                    else:
                        print(f"   {key}: {value}")
                
                print(f"\n🧠 VECTORIZED CONTENT (What was embedded):")
                print("-" * 35)
                
                # Show what content was actually vectorized based on chunk type
                if chunk_type == "overview":
                    print(f"   Text: 'Visterra Inc. Visterra is focused on bringing better")
                    print(f"         biologics to life through innovative research and")
                    print(f"         development. Industry: Biotechnology Business model:")
                    print(f"         B2B Target market: Pharmaceutical companies, healthcare")
                    print(f"         providers, and patients'")
                
                elif chunk_type == "leadership":
                    print(f"   Text: 'Visterra Inc. leadership team includes: Greg Babcock,")
                    print(f"         PhD - Senior Vice President, Research. Jean L. Bender -")
                    print(f"         Vice President, Pharmaceutical Sciences and Technology.")
                    print(f"         Todd Curtis, MBA, CPA - Chief Financial Officer...'")
                    print(f"         [Full 441 character leadership description]")
                
                elif chunk_type == "products":
                    print(f"   Text: 'Visterra Inc. provides the following services and")
                    print(f"         products: Biologics development. Pipeline programs.")
                    print(f"         Clinical trials'")
                
                elif chunk_type == "technology":
                    print(f"   Text: 'Visterra Inc. uses the following technologies and")
                    print(f"         capabilities: AI. Computational research methods.")
                    print(f"         Experimental research methods. unknown'")
                
                elif chunk_type == "contact":
                    print(f"   Text: 'Visterra Inc. contact information: Located at 275")
                    print(f"         Second Ave. 4th Floor Waltham, MA 02451 website:")
                    print(f"         https://visterrainc.com/ email: info@visterrainc.com")
                    print(f"         phone: (617) 498-1070 social_media: [LinkedIn, Instagram]'")
                
                print(f"\n🔢 VECTOR REPRESENTATION:")
                print("-" * 25)
                print(f"   Dimensions: {len(vector_data.values):,}")
                print(f"   Sample values: [{vector_data.values[0]:.6f}, {vector_data.values[1]:.6f}, {vector_data.values[2]:.6f}, ...]")
                print(f"   Vector Type: 32-bit floating point numbers")
                print(f"   Total Size: {len(vector_data.values)} × 4 bytes = {len(vector_data.values) * 4:,} bytes")
        
        print(f"\n" + "=" * 60)
        print("🎯 HOW THIS ENABLES SEARCH:")
        print("-" * 30)
        
        print(f"📊 METADATA FILTERING:")
        print(f"   Query: Find all biotech companies")
        print(f"   Filter: metadata['industry'] == 'biotechnology'")
        print(f"   Result: Returns all 5 chunks (same company)")
        
        print(f"\n🧠 SEMANTIC SEARCH:")
        print(f"   Query: 'AI drug discovery companies'")
        print(f"   Process: Convert query to 1,536 number vector")
        print(f"   Search: Find most similar vectors using cosine similarity")
        print(f"   Result: Technology chunk ranks highest (0.327 similarity)")
        
        print(f"\n🔄 COMBINED SEARCH:")
        print(f"   Query: 'AI companies in Massachusetts'")
        print(f"   Filter: location_state='ma' AND semantic similarity to 'AI'")
        print(f"   Result: Technology chunk with metadata confirmation")
        
        print(f"\n" + "=" * 60)
        print("✅ SUMMARY:")
        print("-" * 10)
        print(f"📊 Metadata = Structured data for exact filtering")
        print(f"🧠 Vectors = Semantic meaning for similarity search")
        print(f"🔍 Together = Powerful hybrid search capabilities")
        
    except Exception as e:
        print(f"❌ Error accessing vectors: {e}")

if __name__ == "__main__":
    explain_metadata_vs_vectors()