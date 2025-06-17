#!/usr/bin/env python3
"""
Real AI Integration Test for SaaS Classification System
Tests with actual Theodore AI models and real company data
"""

import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

from models import CompanyData, SaaSCategory, ClassificationResult, CompanyIntelligenceConfig
from classification.saas_classifier import SaaSBusinessModelClassifier
from bedrock_client import BedrockClient
from pinecone_client import PineconeClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_with_real_bedrock_client():
    """Test classification with real Bedrock client"""
    print("🧪 Testing with real Bedrock AI client...")
    
    try:
        # Create config for Bedrock client
        config = CompanyIntelligenceConfig()
        
        # Initialize real Bedrock client
        bedrock_client = BedrockClient(config)
        print(f"   ✅ Bedrock client initialized")
        print(f"   📊 Using model: {config.bedrock_analysis_model}")
        print(f"   🌍 Region: {config.bedrock_region}")
        
        # Create classifier with real AI client
        classifier = SaaSBusinessModelClassifier(bedrock_client)
        print(f"   ✅ Classifier initialized with real AI client")
        
        return classifier, bedrock_client
        
    except Exception as e:
        print(f"   ❌ Failed to initialize Bedrock client: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def get_real_company_from_database():
    """Get a real company from Theodore database for testing"""
    print("🔍 Fetching real company from Theodore database...")
    
    try:
        # Initialize Pinecone client
        pinecone_client = PineconeClient(
            api_key=os.getenv('PINECONE_API_KEY'),
            environment=os.getenv('PINECONE_ENVIRONMENT', 'us-east-1'),
            index_name=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        )
        
        # Query for any company with AI summary
        query_result = pinecone_client.index.query(
            vector=[0.0] * 1536,  # Dummy vector for metadata query
            top_k=5,
            include_metadata=True,
            include_values=False,
            filter={"ai_summary": {"$exists": True}}  # Only companies with AI summaries
        )
        
        if not query_result.matches:
            print("   ⚠️ No companies found in database with AI summaries")
            return None
        
        # Get first company with good data
        for match in query_result.matches:
            metadata = match.metadata
            if metadata.get('ai_summary') and len(metadata.get('ai_summary', '')) > 50:
                company = CompanyData(
                    id=match.id,
                    name=metadata.get('name', 'Unknown'),
                    website=metadata.get('website', ''),
                    ai_summary=metadata.get('ai_summary', ''),
                    value_proposition=metadata.get('value_proposition', ''),
                    company_description=metadata.get('company_description', ''),
                    industry=metadata.get('industry', ''),
                    products_services_offered=metadata.get('products_services_offered', [])
                )
                
                print(f"   ✅ Found company: {company.name}")
                print(f"   📊 AI Summary length: {len(company.ai_summary)} chars")
                print(f"   🌐 Website: {company.website}")
                print(f"   🏢 Industry: {company.industry}")
                
                return company
        
        print("   ⚠️ No companies found with sufficient AI summary data")
        return None
        
    except Exception as e:
        print(f"   ❌ Error accessing database: {e}")
        return None


def create_test_company():
    """Create a realistic test company for classification"""
    print("🏭 Creating realistic test company...")
    
    company = CompanyData(
        name="DataViz Pro",
        website="https://datavizpro.com",
        ai_summary="DataViz Pro provides advanced data visualization and business intelligence software for enterprises. The platform offers real-time dashboard creation, automated reporting, and collaborative analytics tools. Companies use DataViz Pro to transform complex datasets into actionable insights through interactive charts, graphs, and custom visualizations. The software integrates with popular data sources and offers subscription-based pricing with tiered feature access.",
        value_proposition="Transform your data into actionable insights with enterprise-grade visualization tools",
        company_description="Leading provider of business intelligence and data visualization solutions",
        industry="Business Intelligence Software",
        products_services_offered=["Data Visualization Platform", "Real-time Dashboards", "Automated Reporting", "Analytics Tools"]
    )
    
    print(f"   ✅ Created test company: {company.name}")
    print(f"   📊 Should classify as: Data/BI/Analytics (SaaS)")
    
    return company


def test_real_classification(classifier, company):
    """Test classification with real AI and real company data"""
    print(f"\n🔬 Testing real classification for: {company.name}")
    print("=" * 60)
    
    try:
        # Show input data
        print("📋 INPUT DATA:")
        print(f"   Company: {company.name}")
        print(f"   Website: {company.website}")
        print(f"   Industry: {company.industry}")
        print(f"   AI Summary (first 150 chars): {company.ai_summary[:150]}...")
        print(f"   Products/Services: {company.products_services_offered}")
        
        print("\n🤖 CALLING REAL AI MODEL...")
        start_time = datetime.now()
        
        # Perform real classification
        result = classifier.classify_company(company)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"⏱️ Processing time: {processing_time:.2f} seconds")
        
        print("\n📊 CLASSIFICATION RESULT:")
        print(f"   Category: {result.category.value}")
        print(f"   Is SaaS: {result.is_saas}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Justification: {result.justification}")
        print(f"   Model Version: {result.model_version}")
        print(f"   Timestamp: {result.timestamp}")
        
        # Validate result quality
        print("\n✅ VALIDATION:")
        if result.confidence >= 0.5:
            print(f"   ✅ High confidence classification ({result.confidence:.2f})")
        else:
            print(f"   ⚠️ Low confidence classification ({result.confidence:.2f})")
        
        if len(result.justification) >= 20:
            print(f"   ✅ Detailed justification ({len(result.justification)} chars)")
        else:
            print(f"   ⚠️ Short justification ({len(result.justification)} chars)")
        
        if result.category != SaaSCategory.UNCLASSIFIED:
            print(f"   ✅ Specific category assigned: {result.category.value}")
        else:
            print(f"   ⚠️ Unclassified result")
        
        print(f"\n🎯 EXPECTED vs ACTUAL:")
        print(f"   Expected: Data/BI/Analytics (SaaS)")
        print(f"   Actual: {result.category.value} ({'SaaS' if result.is_saas else 'Non-SaaS'})")
        
        return result
        
    except Exception as e:
        print(f"❌ Classification failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_real_ai_test():
    """Run complete real AI integration test"""
    print("🚀 STARTING REAL AI CLASSIFICATION TEST")
    print("=" * 60)
    
    # Test 1: Initialize real AI client
    classifier, bedrock_client = test_with_real_bedrock_client()
    if not classifier:
        print("❌ Cannot proceed without AI client")
        return False
    
    # Test 2: Try to get real company from database
    real_company = get_real_company_from_database()
    
    # Test 3: Use test company if no real company available
    if real_company:
        print(f"\n🎯 Testing with REAL company from database")
        test_result_real = test_real_classification(classifier, real_company)
    else:
        print(f"\n⚠️ No real company available, skipping database test")
        test_result_real = None
    
    # Test 4: Test with controlled test company
    print(f"\n🎯 Testing with CONTROLLED test company")
    test_company = create_test_company()
    test_result_controlled = test_real_classification(classifier, test_company)
    
    # Final assessment
    print("\n" + "=" * 60)
    print("📊 FINAL ASSESSMENT")
    
    if test_result_real:
        print(f"✅ Real company test: SUCCESS")
        print(f"   Category: {test_result_real.category.value}")
        print(f"   Confidence: {test_result_real.confidence:.2f}")
    else:
        print(f"⚠️ Real company test: SKIPPED (no database company)")
    
    if test_result_controlled:
        print(f"✅ Controlled test: SUCCESS")
        print(f"   Category: {test_result_controlled.category.value}")
        print(f"   Confidence: {test_result_controlled.confidence:.2f}")
        
        # Check if controlled test gave expected result
        expected_saas = True
        actual_saas = test_result_controlled.is_saas
        
        if expected_saas == actual_saas:
            print(f"   ✅ SaaS classification correct!")
        else:
            print(f"   ⚠️ SaaS classification unexpected: expected {expected_saas}, got {actual_saas}")
    else:
        print(f"❌ Controlled test: FAILED")
        return False
    
    print("\n🎉 Real AI integration test completed!")
    
    if test_result_controlled and test_result_controlled.confidence > 0.5:
        print("✅ SaaS Classification System works with real AI!")
        return True
    else:
        print("⚠️ Classification system needs improvement")
        return False


if __name__ == "__main__":
    success = run_real_ai_test()
    sys.exit(0 if success else 1)