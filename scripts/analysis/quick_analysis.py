#!/usr/bin/env python3
"""
Quick analysis of current database state to show what data we actually have.
"""

import os
import sys
sys.path.append('.')
from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

load_dotenv()

def analyze_current_data():
    print("=" * 60)
    print("THEODORE DATABASE ANALYSIS - CURRENT STATE")
    print("=" * 60)
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    # Get all companies
    query_result = pipeline.pinecone_client.index.query(
        vector=[0.0] * 1536,
        top_k=30,
        include_metadata=True,
        include_values=False
    )
    
    companies = []
    for match in query_result.matches:
        companies.append({
            'id': match.id,
            'name': match.metadata.get('company_name', 'Unknown'),
            'website': match.metadata.get('website', ''),
            'metadata': match.metadata
        })
    
    print(f"📊 Found {len(companies)} companies in database")
    
    # Key fields we care about
    key_fields = [
        'products_services_offered', 'job_listings_count', 'job_listings', 
        'job_listings_details', 'leadership_team', 'location', 'founding_year',
        'value_proposition', 'company_culture', 'partnerships', 'contact_info'
    ]
    
    print(f"\n📈 FIELD COVERAGE ANALYSIS:")
    print("-" * 50)
    
    for field in key_fields:
        populated = 0
        empty = 0
        none_values = 0
        
        for company in companies:
            value = company['metadata'].get(field)
            
            if value is None:
                none_values += 1
            elif isinstance(value, str):
                if value.strip() == "" or value == "None":
                    empty += 1
                else:
                    populated += 1
            elif isinstance(value, list):
                if len(value) == 0:
                    empty += 1
                else:
                    populated += 1
            elif isinstance(value, (int, float)):
                if value == 0:
                    empty += 1
                else:
                    populated += 1
            else:
                populated += 1
        
        coverage = (populated / len(companies) * 100) if companies else 0
        print(f"{field:25} | {populated:2}/{len(companies):2} populated ({coverage:5.1f}%) | {empty} empty | {none_values} None")
    
    print(f"\n🔍 DETAILED EXAMPLES (First 3 companies):")
    print("=" * 60)
    
    for i, company in enumerate(companies[:3]):
        print(f"\n{i+1}. {company['name']} ({company['website']})")
        print("-" * 40)
        
        for field in key_fields:
            value = company['metadata'].get(field, 'NOT_FOUND')
            
            if isinstance(value, str) and len(value) > 100:
                display_value = value[:100] + "..."
            else:
                display_value = value
                
            print(f"  {field:20}: {display_value}")
    
    # Check specific problematic fields
    print(f"\n🚨 PROBLEMATIC FIELD ANALYSIS:")
    print("-" * 50)
    
    products_empty = sum(1 for c in companies if not c['metadata'].get('products_services_offered') or c['metadata'].get('products_services_offered') == "")
    jobs_empty = sum(1 for c in companies if not c['metadata'].get('job_listings_count') or c['metadata'].get('job_listings_count') == 0)
    
    print(f"Products/Services empty: {products_empty}/{len(companies)} companies")
    print(f"Job listings empty: {jobs_empty}/{len(companies)} companies")
    
    # Show what we actually have for products/services
    print(f"\n📦 PRODUCTS/SERVICES EXAMPLES:")
    for company in companies[:5]:
        products = company['metadata'].get('products_services_offered', 'NONE')
        if products and products != "NONE" and len(products) > 5:
            print(f"  {company['name']}: {products[:100]}...")
    
    print(f"\n✅ ANALYSIS COMPLETE!")
    print(f"   🌐 Web interface: http://localhost:5002")
    print(f"   📊 Database has {len(companies)} companies")
    
    return companies

if __name__ == "__main__":
    analyze_current_data()