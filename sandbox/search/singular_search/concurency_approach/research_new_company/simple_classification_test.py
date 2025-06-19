#!/usr/bin/env python3
"""
Simple SaaS Classification Test
Basic test to validate classification system functionality
"""

import sys
import os
import time
import json
import logging
from datetime import datetime

# Add Theodore root to path
sys.path.append('/Users/antoinedubuc/Desktop/AI_Goodies/Theodore')

try:
    # Test basic imports
    from src.models import CompanyIntelligenceConfig
    from src.pinecone_client import PineconeClient
    print("✅ Successfully imported Theodore components")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_access():
    """Test basic database access and classification data retrieval"""
    
    print("🧪 SIMPLE SAAS CLASSIFICATION TEST")
    print("=" * 60)
    print("🎯 Testing: Basic database access and classification retrieval")
    print("📅 Test Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    try:
        # Create config
        config = CompanyIntelligenceConfig(
            output_format="json",
            use_ai_analysis=True,
            max_pages=10,
            aws_region="us-east-1",
            bedrock_analysis_model="amazon.nova-pro-v1:0"
        )
        
        # Get environment variables
        pinecone_api_key = os.getenv('PINECONE_API_KEY')
        pinecone_index = os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        
        if not pinecone_api_key:
            print("❌ PINECONE_API_KEY environment variable not found")
            print("ℹ️ Please set PINECONE_API_KEY in your environment")
            return False
        
        print(f"🔑 Using Pinecone API Key: {pinecone_api_key[:8]}...")
        print(f"📊 Using Pinecone Index: {pinecone_index}")
        print()
        
        # Initialize Pinecone client
        print("🔌 Initializing Pinecone client...")
        pinecone_client = PineconeClient(
            config=config,
            api_key=pinecone_api_key,
            environment="gcp-starter",  # Default for free tier
            index_name=pinecone_index
        )
        print("✅ Pinecone client initialized successfully")
        
        # Test database access
        print("\n📊 Testing database access...")
        start_time = time.time()
        
        try:
            # Try to get companies using available method (get up to 1000 with empty filter)
            all_companies = pinecone_client.find_companies_by_filters(filters={}, top_k=1000)
            access_time = time.time() - start_time
            
            if all_companies is None:
                print("⚠️ Database access returned None")
                return False
            
            total_companies = len(all_companies)
            print(f"✅ Database access successful in {access_time:.2f}s")
            print(f"📈 Total companies in database: {total_companies}")
            
            if total_companies == 0:
                print("⚠️ No companies found in database")
                print("ℹ️ This is normal for a new Theodore installation")
                return True
            
            # Analyze classification coverage
            print("\n🏷️ Analyzing classification coverage...")
            
            classified_count = 0
            saas_count = 0
            non_saas_count = 0
            categories = {}
            
            for company in all_companies:
                metadata = company.get('metadata', {})
                saas_classification = metadata.get('saas_classification')
                is_saas = metadata.get('is_saas')
                
                if saas_classification and saas_classification != "Unclassified":
                    classified_count += 1
                    
                    # Count categories
                    categories[saas_classification] = categories.get(saas_classification, 0) + 1
                    
                    # Count SaaS vs Non-SaaS
                    if is_saas:
                        saas_count += 1
                    else:
                        non_saas_count += 1
            
            # Display results
            coverage_percentage = classified_count / total_companies * 100 if total_companies > 0 else 0
            
            print(f"📊 Classification Coverage:")
            print(f"   Total Companies: {total_companies}")
            print(f"   Classified: {classified_count} ({coverage_percentage:.1f}%)")
            print(f"   SaaS Companies: {saas_count}")
            print(f"   Non-SaaS Companies: {non_saas_count}")
            
            if categories:
                print(f"\n🏷️ Top Categories:")
                sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
                for category, count in sorted_categories[:5]:
                    print(f"   {category}: {count} companies")
            
            # Test individual company lookup
            print("\n🔍 Testing individual company lookup...")
            
            test_companies = ["Stripe", "Notion", "Tesla", "Shopify", "Linear"]
            found_companies = []
            
            for company_name in test_companies:
                try:
                    company_data = pinecone_client.find_company_by_name(company_name)
                    if company_data:
                        found_companies.append(company_name)
                        # company_data is a CompanyData object, not a dict
                        classification = getattr(company_data, 'saas_classification', 'Not classified')
                        is_saas = getattr(company_data, 'is_saas', None)
                        confidence = getattr(company_data, 'classification_confidence', None)
                        
                        print(f"   ✅ {company_name}: {classification}")
                        if is_saas is not None:
                            print(f"      Type: {'SaaS' if is_saas else 'Non-SaaS'}")
                        if confidence is not None:
                            print(f"      Confidence: {confidence:.2f}")
                    else:
                        print(f"   ❌ {company_name}: Not found")
                except Exception as e:
                    print(f"   ❌ {company_name}: Error - {e}")
            
            print(f"\n📈 Found {len(found_companies)}/{len(test_companies)} test companies")
            
            # Assessment
            print(f"\n🎯 ASSESSMENT:")
            
            if total_companies >= 10 and coverage_percentage >= 50:
                print("✅ EXCELLENT: Good database coverage with classifications")
                print("✅ Ready for SaaS classification integration testing")
            elif total_companies >= 5:
                print("⚠️ MODERATE: Some companies available, classification coverage varies")
                print("⚠️ Consider running more company research to build database")
            else:
                print("❌ LOW: Limited database content")
                print("❌ Need to research companies before testing classification retrieval")
            
            return True
            
        except Exception as e:
            print(f"❌ Database access failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test execution"""
    
    success = test_database_access()
    
    if success:
        print("\n🏁 Simple classification test completed!")
        print("📄 Review results above to determine next steps")
    else:
        print("\n💥 Test failed - check configuration and try again")
    
    return success

if __name__ == "__main__":
    main()