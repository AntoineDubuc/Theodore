#!/usr/bin/env python3
"""
Test single company classification with detailed debugging
"""

import os
import sys
from datetime import datetime

# Add project root and src to path
project_root = os.path.join(os.path.dirname(__file__), '.')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def main():
    print("🧪 Single Company Classification Test")
    print("=" * 50)
    
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Import Theodore components
        from src.main_pipeline import TheodoreIntelligencePipeline
        from src.models import CompanyIntelligenceConfig
        from src.classification.classification_system import SaaSBusinessModelClassifier
        
        # Initialize pipeline
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME')
        )
        
        print("✅ Theodore pipeline initialized")
        
        # Initialize classifier
        classifier = SaaSBusinessModelClassifier()
        print("✅ Classification system initialized")
        
        # Test classification on a simple company
        print("\n🏷️ Testing classification...")
        company_data = {
            'name': 'TestCompany AdTech',
            'website': 'test.com',
            'industry': 'Advertising Technology',
            'description': 'A platform for digital advertising optimization',
            'products_services': 'Ad optimization software and analytics dashboard'
        }
        
        print(f"📊 Test Company Data:")
        for key, value in company_data.items():
            print(f"   {key}: {value}")
        
        # Perform classification
        print(f"\n🔍 Running classification...")
        classification_result = classifier.classify_company(company_data)
        
        print(f"📋 Classification Result:")
        print(f"   Raw result: {classification_result}")
        
        if classification_result and classification_result.get('success'):
            print(f"   ✅ Classification successful!")
            print(f"   Category: {classification_result['category']}")
            print(f"   Is SaaS: {classification_result['is_saas']}")
            print(f"   Confidence: {classification_result['confidence']}")
            print(f"   Justification: {classification_result['justification']}")
        else:
            print(f"   ❌ Classification failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()