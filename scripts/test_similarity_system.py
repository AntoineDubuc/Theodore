#!/usr/bin/env python3
"""
Quick test script for Theodore's advanced similarity system
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from src.models import CompanyData, CompanyIntelligenceConfig
from src.similarity_engine import SimilarityEngine
from src.main_pipeline import TheodoreIntelligencePipeline

def test_similarity_calculation():
    """Test basic similarity calculations with mock companies"""
    print("🧪 Testing Similarity Calculation Engine...")
    print("=" * 50)
    
    # Create test companies with similarity metrics
    companies = {
        "OpenAI": CompanyData(
            name="OpenAI",
            website="https://openai.com",
            industry="artificial intelligence",
            company_stage="growth",
            tech_sophistication="high",
            business_model_type="saas",
            geographic_scope="global",
            stage_confidence=0.9,
            tech_confidence=0.95,
            industry_confidence=0.9
        ),
        "Anthropic": CompanyData(
            name="Anthropic",
            website="https://anthropic.com", 
            industry="artificial intelligence",
            company_stage="growth",
            tech_sophistication="high",
            business_model_type="saas",
            geographic_scope="global",
            stage_confidence=0.85,
            tech_confidence=0.9,
            industry_confidence=0.9
        ),
        "Stripe": CompanyData(
            name="Stripe",
            website="https://stripe.com",
            industry="fintech",
            company_stage="enterprise",
            tech_sophistication="high",
            business_model_type="saas", 
            geographic_scope="global",
            stage_confidence=0.95,
            tech_confidence=0.9,
            industry_confidence=0.9
        ),
        "Visterra": CompanyData(
            name="Visterra",
            website="https://visterra.com",
            industry="biotechnology",
            company_stage="startup",
            tech_sophistication="medium",
            business_model_type="services",
            geographic_scope="regional",
            stage_confidence=0.8,
            tech_confidence=0.7,
            industry_confidence=0.8
        )
    }
    
    # Initialize similarity engine
    similarity_engine = SimilarityEngine()
    
    # Test expected high similarity pairs
    print("\n📊 EXPECTED HIGH SIMILARITY:")
    high_similarity_tests = [
        ("OpenAI", "Anthropic", "> 0.8"),
        ("Stripe", "Square (mock)", "> 0.8")
    ]
    
    for company_a, company_b, expected in high_similarity_tests:
        if company_a in companies and company_b.split(" ")[0] in ["Anthropic"]:
            result = similarity_engine.calculate_similarity(
                companies[company_a], 
                companies["Anthropic"] if "Anthropic" in company_b else companies["Stripe"]
            )
            print(f"  {company_a} vs {company_b}: {result['overall_similarity']:.3f} {expected}")
            print(f"    Explanation: {result['explanation']}")
            print(f"    Confidence: {result['overall_confidence']:.3f}")
    
    # Test expected low similarity pairs
    print("\n📊 EXPECTED LOW SIMILARITY:")
    low_similarity_tests = [
        ("OpenAI", "Visterra", "< 0.4"),
        ("Stripe", "Visterra", "< 0.4")
    ]
    
    for company_a, company_b, expected in low_similarity_tests:
        if company_a in companies and company_b in companies:
            result = similarity_engine.calculate_similarity(
                companies[company_a], 
                companies[company_b]
            )
            print(f"  {company_a} vs {company_b}: {result['overall_similarity']:.3f} {expected}")
            print(f"    Explanation: {result['explanation']}")
    
    # Test find similar companies functionality
    print("\n🔍 FIND SIMILAR COMPANIES TEST:")
    all_companies = list(companies.values())
    similar_to_openai = similarity_engine.find_similar_companies(
        companies["OpenAI"],
        all_companies,
        threshold=0.7,
        limit=3
    )
    
    print(f"  Companies similar to OpenAI (threshold 0.7):")
    for company, result in similar_to_openai:
        print(f"    {company.name}: {result['overall_similarity']:.3f}")
    
    print("\n✅ Similarity Calculation Tests Complete!")

def test_pipeline_integration():
    """Test if pipeline can be initialized (without processing companies)"""
    print("\n🔧 Testing Pipeline Integration...")
    print("=" * 40)
    
    try:
        # Load environment
        load_dotenv()
        
        # Initialize configuration
        config = CompanyIntelligenceConfig()
        
        # Try to initialize pipeline
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME')
        )
        
        print("✅ Pipeline initialization successful")
        print("✅ All similarity methods available:")
        
        # Check that new methods exist
        methods_to_check = [
            'analyze_company_similarity',
            'find_companies_like', 
            'get_similarity_report'
        ]
        
        for method in methods_to_check:
            if hasattr(pipeline, method):
                print(f"  ✅ {method}")
            else:
                print(f"  ❌ {method} missing")
        
        # Test Pinecone enhanced methods
        print("\n✅ Enhanced Pinecone methods available:")
        pinecone_methods = [
            'find_similar_companies_enhanced',
            'get_similarity_insights'
        ]
        
        for method in pinecone_methods:
            if hasattr(pipeline.pinecone_client, method):
                print(f"  ✅ {method}")
            else:
                print(f"  ❌ {method} missing")
                
    except Exception as e:
        print(f"❌ Pipeline initialization failed: {e}")
        print("   This is expected if credentials are not configured")

def test_similarity_prompts():
    """Test similarity prompt imports"""
    print("\n📝 Testing Similarity Prompts...")
    print("=" * 35)
    
    try:
        from src.similarity_prompts import (
            COMPANY_STAGE_PROMPT,
            TECH_SOPHISTICATION_PROMPT, 
            BUSINESS_MODEL_PROMPT,
            extract_similarity_metrics,
            parse_llm_response
        )
        
        print("✅ All similarity prompts imported successfully")
        print(f"✅ Company stage prompt: {len(COMPANY_STAGE_PROMPT)} chars")
        print(f"✅ Tech sophistication prompt: {len(TECH_SOPHISTICATION_PROMPT)} chars")
        print(f"✅ Business model prompt: {len(BUSINESS_MODEL_PROMPT)} chars")
        print("✅ Extraction functions available")
        
    except Exception as e:
        print(f"❌ Similarity prompts import failed: {e}")

def main():
    """Run all tests"""
    print("🚀 THEODORE ADVANCED SIMILARITY SYSTEM TESTS")
    print("=" * 60)
    
    # Test 1: Basic similarity calculations
    test_similarity_calculation()
    
    # Test 2: Prompt imports
    test_similarity_prompts()
    
    # Test 3: Pipeline integration
    test_pipeline_integration()
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS COMPLETE!")
    print("\nNext steps:")
    print("1. Add real companies to test end-to-end similarity")
    print("2. Test web UI integration") 
    print("3. Validate with real company data")

if __name__ == "__main__":
    main()