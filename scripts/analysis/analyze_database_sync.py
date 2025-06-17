#!/usr/bin/env python3
"""
Analyze database synchronization issues with enhanced extraction.
"""

import os
import sys

sys.path.append('.')
from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Load environment
load_dotenv()

def analyze_database_sync():
    """Analyze database sync issues"""
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    print("=" * 80)
    print("ANALYZING DATABASE SYNCHRONIZATION ISSUES")
    print("=" * 80)
    
    # Get all companies from database
    companies = pipeline.pinecone_client.find_companies_by_filters({}, top_k=15)
    
    print(f"📊 FOUND {len(companies)} COMPANIES IN DATABASE")
    print()
    
    for i, company in enumerate(companies[:10], 1):
        metadata = company.get('metadata', {})
        company_name = metadata.get('company_name', f'Company_{i}')
        
        print(f"{i:2d}. {company_name}")
        print(f"    ID: {company.get('id', 'No ID')}")
        
        # Check critical data
        critical_fields = [
            'raw_content', 'pages_crawled', 'scrape_status', 
            'founding_year', 'location', 'leadership_team', 'contact_info'
        ]
        
        for field in critical_fields:
            value = metadata.get(field)
            if field == 'raw_content':
                length = len(value) if value else 0
                print(f"    📄 {field}: {length:,} chars")
            elif field == 'pages_crawled':
                count = len(value) if value else 0
                print(f"    🔗 {field}: {count} pages")
            elif value:
                if isinstance(value, (list, dict)):
                    print(f"    ✅ {field}: {value}")
                else:
                    display = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                    print(f"    ✅ {field}: {display}")
            else:
                print(f"    ❌ {field}: Empty")
        
        print()
    
    # Test direct retrieval vs process_single_company
    test_company = "connatix.com"
    print(f"🧪 TESTING RETRIEVAL CONSISTENCY FOR {test_company}")
    print("-" * 50)
    
    # Method 1: Direct retrieval
    direct_company = pipeline.pinecone_client.find_company_by_name(test_company)
    if direct_company:
        direct_metadata = direct_company.__dict__ if hasattr(direct_company, '__dict__') else {}
        raw_content_direct = direct_metadata.get('raw_content')
        pages_direct = direct_metadata.get('pages_crawled')
        
        print(f"📋 DIRECT RETRIEVAL:")
        print(f"   Raw content: {len(raw_content_direct) if raw_content_direct else 0:,} chars")
        print(f"   Pages crawled: {len(pages_direct) if pages_direct else 0}")
        print(f"   Object type: {type(direct_company)}")
        print(f"   Has __dict__: {hasattr(direct_company, '__dict__')}")
        
        # Show all non-empty fields
        print(f"   Non-empty fields:")
        field_count = 0
        for key, value in direct_metadata.items():
            if not key.startswith('_') and value is not None:
                if isinstance(value, str) and value.strip():
                    field_count += 1
                elif isinstance(value, (list, dict)) and len(value) > 0:
                    field_count += 1
                elif isinstance(value, (int, float)) and value > 0:
                    field_count += 1
        print(f"   Total non-empty fields: {field_count}")
    else:
        print(f"❌ Direct retrieval failed")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    analyze_database_sync()