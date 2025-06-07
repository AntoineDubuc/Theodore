#!/usr/bin/env python3
"""
Add test companies with enhanced similarity metrics for testing
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

def add_test_companies():
    """Add companies for similarity testing with enhanced extraction"""
    
    # Companies that should be similar
    test_companies = [
        # AI companies (should be highly similar)
        ("OpenAI", "https://openai.com"),
        ("Anthropic", "https://anthropic.com"),
        
        # Fintech companies (should be highly similar)  
        ("Stripe", "https://stripe.com"),
        
        # Different industry (should be dissimilar)
        ("Netflix", "https://netflix.com"),
    ]
    
    load_dotenv()
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT', 'us-west1-gcp'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    print("🚀 Adding Test Companies with Enhanced Similarity Features")
    print("=" * 60)
    
    # Clear existing data first
    print("🗑️ Clearing existing data...")
    try:
        pipeline.pinecone_client.clear_all_records()
        print("✅ Database cleared")
    except Exception as e:
        print(f"⚠️ Clear failed (may be expected): {e}")
    
    # Add new companies with similarity extraction
    for name, website in test_companies:
        print(f"\n🔄 Processing {name}...")
        
        try:
            # Check if already exists
            existing = pipeline.pinecone_client.find_company_by_name(name)
            if existing:
                print(f"✅ {name} already exists in database")
                continue
            
            # Process company with new similarity features
            company = pipeline.process_single_company(name, website)
            
            if company and company.embedding:
                print(f"✅ Successfully processed {name}")
                print(f"   Industry: {company.industry}")
                print(f"   Stage: {company.company_stage}")
                print(f"   Tech Level: {company.tech_sophistication}")
                print(f"   Business Model: {company.business_model_type}")
                print(f"   Geographic Scope: {company.geographic_scope}")
                
                # Show confidence scores if available
                if hasattr(company, 'stage_confidence') and company.stage_confidence:
                    print(f"   Stage Confidence: {company.stage_confidence:.2f}")
                if hasattr(company, 'tech_confidence') and company.tech_confidence:
                    print(f"   Tech Confidence: {company.tech_confidence:.2f}")
                if hasattr(company, 'industry_confidence') and company.industry_confidence:
                    print(f"   Industry Confidence: {company.industry_confidence:.2f}")
            else:
                print(f"❌ Failed to process {name}")
        
        except Exception as e:
            print(f"❌ Error processing {name}: {e}")
    
    print(f"\n🎉 Test company processing complete!")
    
    # Get final stats
    stats = pipeline.pinecone_client.get_index_stats()
    total_companies = stats.get('total_vectors', 0)
    print(f"📊 Final database status: {total_companies} companies")

def test_new_similarities():
    """Test similarities with newly added companies"""
    print("\n🧪 Testing Similarities with New Companies")
    print("=" * 45)
    
    load_dotenv()
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT', 'us-west1-gcp'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    # Test similarity analysis
    test_company = "OpenAI"
    print(f"\n🎯 Analyzing similarities for: {test_company}")
    
    try:
        insights = pipeline.analyze_company_similarity(test_company)
        
        if "error" in insights:
            print(f"❌ Analysis failed: {insights['error']}")
        else:
            target = insights["target_company"]
            similar = insights.get("similar_companies", [])
            recommendations = insights.get("sales_recommendations", [])
            
            print(f"✅ Target Company Analysis:")
            print(f"   Name: {target['name']}")
            print(f"   Stage: {target.get('stage', 'Unknown')}")
            print(f"   Tech Level: {target.get('tech_level', 'Unknown')}")
            print(f"   Industry: {target.get('industry', 'Unknown')}")
            
            if similar:
                print(f"\n🔗 Similar Companies Found ({len(similar)}):")
                for i, comp in enumerate(similar, 1):
                    print(f"   {i}. {comp['company_name']} (Score: {comp['similarity_score']:.3f})")
                    print(f"      {comp['explanation']}")
                    print(f"      Confidence: {comp['confidence']:.3f}")
            else:
                print(f"\n⚠️ No similar companies found")
            
            if recommendations:
                print(f"\n💼 Sales Recommendations:")
                for rec in recommendations:
                    print(f"   • {rec}")
    
    except Exception as e:
        print(f"❌ Similarity test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run the test company addition and validation"""
    add_test_companies()
    test_new_similarities()
    
    print("\n" + "=" * 60)
    print("🏁 Test Company Setup Complete!")
    print("\nNow you can test the web UI or run more similarity tests.")

if __name__ == "__main__":
    main()