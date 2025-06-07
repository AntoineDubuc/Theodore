#!/usr/bin/env python3
"""
Extract and display raw data stored in Pinecone
"""

import os
import sys
import json
from dotenv import load_dotenv
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.models import CompanyIntelligenceConfig
from src.pinecone_client import PineconeClient

def main():
    """Extract raw Pinecone data"""
    
    # Load environment variables
    load_dotenv()
    
    print("🔍 Extracting Raw Pinecone Data...")
    
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
    
    # Get all vectors with full metadata
    try:
        dummy_vector = [0.0] * config.pinecone_dimension
        query_response = pinecone_client.index.query(
            vector=dummy_vector,
            top_k=100,  # Get all companies
            include_metadata=True,
            include_values=True  # Include the actual embedding vectors
        )
        
        print(f"📊 Found {len(query_response.matches)} companies")
        
        # Extract and format raw data
        raw_data = []
        for match in query_response.matches:
            company_data = {
                'id': match.id,
                'score': match.score,
                'metadata': match.metadata,
                'embedding_sample': match.values[:10] if match.values else None,  # First 10 dimensions as sample
                'embedding_length': len(match.values) if match.values else 0
            }
            raw_data.append(company_data)
        
        # Save raw data to JSON
        output_file = "pinecone_raw_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, indent=2, default=str)
        
        print(f"✅ Raw data saved to {output_file}")
        
        # Also create a readable markdown version
        create_readable_report(raw_data)
        
    except Exception as e:
        print(f"❌ Failed to extract raw data: {e}")
        return

def create_readable_report(raw_data):
    """Create a human-readable report of the raw data"""
    
    report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    markdown = f"""# Raw Pinecone Data Extract

**Generated:** {report_time}  
**Total Records:** {len(raw_data)}

"""
    
    for i, company in enumerate(raw_data, 1):
        metadata = company.get('metadata', {})
        
        markdown += f"## Company {i}: {metadata.get('company_name', 'Unknown')}\n\n"
        markdown += f"**Vector ID:** `{company['id']}`  \n"
        markdown += f"**Similarity Score:** {company['score']:.6f}  \n"
        markdown += f"**Embedding Dimensions:** {company['embedding_length']}  \n"
        
        if company.get('embedding_sample'):
            sample_str = ', '.join([f"{x:.4f}" for x in company['embedding_sample']])
            markdown += f"**Embedding Sample (first 10):** [{sample_str}...]  \n"
        
        markdown += "\n### Metadata Fields:\n\n"
        
        # Display all metadata fields
        for key, value in metadata.items():
            if value:  # Only show non-empty values
                if isinstance(value, bool):
                    value_str = "✅ Yes" if value else "❌ No"
                elif isinstance(value, list):
                    value_str = ", ".join(str(v) for v in value) if value else "None"
                else:
                    value_str = str(value)
                
                # Format key nicely
                formatted_key = key.replace('_', ' ').title()
                markdown += f"- **{formatted_key}:** {value_str}\n"
        
        markdown += "\n---\n\n"
    
    # Add technical details
    markdown += "## Technical Details\n\n"
    markdown += "### Vector Storage Information\n"
    markdown += "- **Vector Dimension:** 1536 (Amazon Titan Embeddings)\n"
    markdown += "- **Distance Metric:** Cosine Similarity\n"
    markdown += "- **Storage Format:** Pinecone Serverless (AWS us-west-2)\n"
    markdown += "- **Metadata Fields:** Full company intelligence from Crawl4AI\n"
    
    if raw_data:
        sample_metadata_keys = list(raw_data[0].get('metadata', {}).keys())
        markdown += f"\n### Available Metadata Fields ({len(sample_metadata_keys)} total):\n"
        for key in sorted(sample_metadata_keys):
            markdown += f"- `{key}`\n"
    
    markdown += "\n### Data Sources\n"
    markdown += "- **Web Scraping:** Crawl4AI multi-page extraction\n"
    markdown += "- **AI Analysis:** AWS Bedrock (planned)\n"
    markdown += "- **Embeddings:** Amazon Titan Text Embeddings\n"
    markdown += "- **Pages Crawled:** Homepage, About, Services, Products, Team, Contact, etc.\n"
    
    # Save readable report
    output_file = "pinecone_raw_data_readable.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"✅ Readable report saved to {output_file}")

if __name__ == "__main__":
    main()