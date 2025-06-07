#!/usr/bin/env python3
"""
Check what's actually in the Pinecone database
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

def check_database():
    """Check what companies are in Pinecone"""
    print("🔍 Checking Pinecone Database Contents")
    print("=" * 40)
    
    load_dotenv()
    
    try:
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME')
        )
        
        # Get database stats
        stats = pipeline.pinecone_client.get_index_stats()
        total_companies = stats.get('total_vectors', 0)
        
        print(f"📊 Total companies in database: {total_companies}")
        
        if total_companies == 0:
            print("❌ Database is empty!")
            return
        
        # Get all companies
        print("\n🏢 Companies in database:")
        all_companies = pipeline.pinecone_client.find_companies_by_filters({}, top_k=50)
        
        for i, company in enumerate(all_companies, 1):
            metadata = company.get('metadata', {})
            company_id = company.get('company_id', 'Unknown')
            
            print(f"\n{i}. {metadata.get('company_name', 'Unknown')} (ID: {company_id[:8]}...)")
            print(f"   Industry: {metadata.get('industry', 'Unknown')}")
            print(f"   Stage: {metadata.get('company_stage', 'Unknown')}")
            print(f"   Tech Level: {metadata.get('tech_sophistication', 'Unknown')}")
            print(f"   Business Model: {metadata.get('business_model_type', 'Unknown')}")
            print(f"   Geographic Scope: {metadata.get('geographic_scope', 'Unknown')}")
        
        # Specifically check for Cloud Geometry
        print(f"\n🔍 Searching specifically for 'Cloud Geometry'...")
        cloud_geometry = pipeline.pinecone_client.find_company_by_name("Cloud Geometry")
        
        if cloud_geometry:
            print("✅ Found Cloud Geometry!")
            print(f"   ID: {cloud_geometry.id}")
            print(f"   Name: {cloud_geometry.name}")
            print(f"   Website: {getattr(cloud_geometry, 'website', 'Unknown')}")
            print(f"   Industry: {getattr(cloud_geometry, 'industry', 'Unknown')}")
            print(f"   Stage: {getattr(cloud_geometry, 'company_stage', 'Unknown')}")
            print(f"   Tech Level: {getattr(cloud_geometry, 'tech_sophistication', 'Unknown')}")
            print(f"   Has Embedding: {cloud_geometry.embedding is not None}")
        else:
            print("❌ Cloud Geometry NOT found in database")
            
            # Try partial search
            print("\n🔍 Trying partial name searches...")
            partial_searches = ["Cloud", "Geometry", "cloud", "geometry"]
            
            for search_term in partial_searches:
                print(f"   Searching for '{search_term}'...")
                partial_companies = pipeline.pinecone_client.find_companies_by_filters({}, top_k=20)
                matches = [c for c in partial_companies if search_term.lower() in c.get('metadata', {}).get('company_name', '').lower()]
                if matches:
                    for match in matches:
                        print(f"     Found: {match['metadata'].get('company_name', 'Unknown')}")
                else:
                    print(f"     No matches for '{search_term}'")
        
        # Test the new similarity analysis method
        if all_companies:
            test_company_name = all_companies[0]['metadata'].get('company_name', 'Unknown')
            print(f"\n🧪 Testing similarity analysis with: {test_company_name}")
            
            try:
                insights = pipeline.analyze_company_similarity(test_company_name)
                if "error" in insights:
                    print(f"❌ Similarity analysis failed: {insights['error']}")
                else:
                    print(f"✅ Similarity analysis working!")
                    similar_count = len(insights.get('similar_companies', []))
                    print(f"   Found {similar_count} similar companies")
            except Exception as e:
                print(f"❌ Similarity analysis error: {e}")
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database()