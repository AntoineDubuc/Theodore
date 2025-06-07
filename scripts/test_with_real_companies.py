#!/usr/bin/env python3
"""
Test Theodore's advanced similarity system with real companies in the database
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

def test_with_existing_companies():
    """Test similarity system with companies already in the database"""
    print("🔍 Testing Theodore Similarity with Real Companies")
    print("=" * 55)
    
    load_dotenv()
    
    try:
        # Initialize pipeline
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME')
        )
        
        # Get database statistics
        stats = pipeline.pinecone_client.get_index_stats()
        total_companies = stats.get('total_vectors', 0)
        
        print(f"📊 Database Status: {total_companies} companies in index")
        
        if total_companies == 0:
            print("❌ No companies found in database")
            print("💡 Add some companies first:")
            print("   python3 -c \"")
            print("   from src.main_pipeline import TheodoreIntelligencePipeline")
            print("   from src.models import CompanyIntelligenceConfig")
            print("   import os")
            print("   from dotenv import load_dotenv")
            print("   load_dotenv()")
            print("   config = CompanyIntelligenceConfig()")
            print("   pipeline = TheodoreIntelligencePipeline(config, os.getenv('PINECONE_API_KEY'), os.getenv('PINECONE_ENVIRONMENT'), os.getenv('PINECONE_INDEX_NAME'))")
            print("   pipeline.process_single_company('OpenAI', 'https://openai.com')")
            print("   pipeline.process_single_company('Anthropic', 'https://anthropic.com')")
            print("   \"")
            return
        
        # Test finding companies by filters
        print("\n🔍 Testing Metadata Filtering...")
        
        # Get all companies 
        all_companies = pipeline.pinecone_client.find_companies_by_filters({}, top_k=50)
        
        if all_companies:
            print(f"✅ Found {len(all_companies)} companies in database")
            
            # Show first few companies
            print("\n📋 Sample Companies:")
            for i, company in enumerate(all_companies[:5]):
                metadata = company.get('metadata', {})
                print(f"  {i+1}. {metadata.get('company_name', 'Unknown')}")
                print(f"     Industry: {metadata.get('industry', 'Unknown')}")
                print(f"     Stage: {metadata.get('company_stage', 'Unknown')}")
                print(f"     Tech Level: {metadata.get('tech_sophistication', 'Unknown')}")
                print()
            
            # Test similarity analysis with first company
            if len(all_companies) >= 2:
                print("🧪 Testing Similarity Analysis...")
                
                first_company = all_companies[0]['metadata'].get('company_name', 'Unknown')
                print(f"\n🎯 Analyzing similarities for: {first_company}")
                
                # Test the new similarity analysis method
                insights = pipeline.analyze_company_similarity(first_company)
                
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
                        for i, comp in enumerate(similar[:3], 1):
                            print(f"   {i}. {comp['company_name']} (Score: {comp['similarity_score']:.3f})")
                            print(f"      {comp['explanation']}")
                    else:
                        print(f"\n⚠️ No similar companies found")
                        print("   This could mean:")
                        print("   - Companies don't have similarity metrics extracted yet")
                        print("   - Need to reprocess companies with new similarity features")
                    
                    if recommendations:
                        print(f"\n💼 Sales Recommendations:")
                        for rec in recommendations:
                            print(f"   • {rec}")
                
                # Test similarity report generation
                print(f"\n📄 Generating Similarity Report...")
                report = pipeline.get_similarity_report(first_company)
                print("Report preview:")
                print(report[:500] + "..." if len(report) > 500 else report)
        
        else:
            print("❌ No companies found in filters test")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_enhanced_pinecone_methods():
    """Test enhanced Pinecone client methods directly"""
    print("\n🔧 Testing Enhanced Pinecone Methods...")
    print("=" * 45)
    
    load_dotenv()
    
    try:
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME')
        )
        
        # Get a company to test with
        all_companies = pipeline.pinecone_client.find_companies_by_filters({}, top_k=5)
        
        if all_companies:
            test_company_id = all_companies[0]['company_id']
            test_company_name = all_companies[0]['metadata'].get('company_name', 'Unknown')
            
            print(f"🎯 Testing with company: {test_company_name} (ID: {test_company_id[:8]}...)")
            
            # Test enhanced similarity search
            print("\n1. Testing find_similar_companies_enhanced...")
            enhanced_results = pipeline.pinecone_client.find_similar_companies_enhanced(
                test_company_id,
                similarity_threshold=0.1,  # Low threshold to get some results
                top_k=3
            )
            
            print(f"   Found {len(enhanced_results)} similar companies")
            for result in enhanced_results:
                print(f"   - {result['company_name']}: {result['similarity_score']:.3f}")
            
            # Test similarity insights
            print("\n2. Testing get_similarity_insights...")
            insights = pipeline.pinecone_client.get_similarity_insights(test_company_id)
            
            if "error" in insights:
                print(f"   ❌ {insights['error']}")
            else:
                print(f"   ✅ Insights generated for {insights['target_company']['name']}")
                similar_count = len(insights.get('similar_companies', []))
                print(f"   ✅ Found {similar_count} similar companies")
        
        else:
            print("❌ No companies available for testing enhanced methods")
            
    except Exception as e:
        print(f"❌ Enhanced methods test failed: {e}")

def main():
    """Run all real-company tests"""
    print("🚀 THEODORE REAL COMPANY SIMILARITY TESTS")
    print("=" * 50)
    
    test_with_existing_companies()
    test_enhanced_pinecone_methods()
    
    print("\n" + "=" * 50)
    print("🏁 Real Company Tests Complete!")

if __name__ == "__main__":
    main()