#!/usr/bin/env python3
"""
Test script for single company processing
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

def main():
    """Test single company processing"""
    
    # Load environment variables
    load_dotenv()
    
    print("🤖 Theodore Company Intelligence Test")
    print("=" * 50)
    
    # Configuration
    config = CompanyIntelligenceConfig()
    
    # Check environment variables
    required_env_vars = [
        'PINECONE_API_KEY',
        'PINECONE_ENVIRONMENT', 
        'PINECONE_INDEX_NAME',
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_REGION',
        'OPENAI_API_KEY'  # Required for AI extraction
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease create a .env file with the required variables.")
        return
    
    print("✅ Environment variables loaded")
    
    # Initialize pipeline
    try:
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME')
        )
        print("✅ Pipeline initialized")
    except Exception as e:
        print(f"❌ Failed to initialize pipeline: {e}")
        return
    
    # Test company (using Visterra as example)
    test_company_name = "Visterra"
    test_company_website = "https://visterrainc.com"
    
    print(f"\n🔍 Processing test company: {test_company_name}")
    print(f"📍 Website: {test_company_website}")
    print("-" * 50)
    
    try:
        # Process single company
        result = pipeline.process_single_company(
            company_name=test_company_name,
            website=test_company_website
        )
        
        # Display results
        print(f"\n📊 Processing Results for {result.name}")
        print("=" * 50)
        print(f"🌐 Website: {result.website}")
        print(f"📋 Scrape Status: {result.scrape_status}")
        
        if result.scrape_status == "success":
            print(f"🏢 Industry: {result.industry or 'Unknown'}")
            print(f"🏗️ Business Model: {result.business_model or 'Unknown'}")
            print(f"📈 Company Size: {result.company_size or 'Unknown'}")
            print(f"🎯 Target Market: {result.target_market or 'Unknown'}")
            
            if result.tech_stack:
                print(f"⚙️ Technologies: {', '.join(result.tech_stack)}")
            
            if result.key_services:
                print(f"🛠️ Key Services: {', '.join(result.key_services)}")
            
            if result.pain_points:
                print(f"🎯 Pain Points: {', '.join(result.pain_points)}")
            
            print(f"💬 Has Chat Widget: {'Yes' if result.has_chat_widget else 'No'}")
            print(f"📝 Has Forms: {'Yes' if result.has_forms else 'No'}")
            
            if result.ai_summary:
                print(f"\n🤖 AI Summary:")
                print("-" * 30)
                print(result.ai_summary)
            
            if result.embedding:
                print(f"\n📊 Embedding: Generated ({len(result.embedding)} dimensions)")
                print("✅ Stored in Pinecone")
            else:
                print("\n❌ No embedding generated")
            
            # Test similarity search
            print(f"\n🔍 Finding similar companies...")
            similar_companies = pipeline.find_similar_companies_for_company(
                result.id, top_k=5
            )
            
            if similar_companies:
                print(f"Found {len(similar_companies)} similar companies:")
                for i, similar in enumerate(similar_companies, 1):
                    company_name = similar['metadata'].get('company_name', 'Unknown')
                    similarity_score = similar['similarity_score']
                    print(f"  {i}. {company_name} (similarity: {similarity_score:.3f})")
            else:
                print("No similar companies found (database may be empty)")
        
        else:
            print(f"❌ Scraping failed: {result.scrape_error}")
        
        print("\n" + "=" * 50)
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()