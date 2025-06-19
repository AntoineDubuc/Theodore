#!/usr/bin/env python3
"""
Test minimal Pinecone update operation
"""

import os
import sys
from datetime import datetime

# Add project root and src to path
project_root = os.path.join(os.path.dirname(__file__), '.')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def main():
    print("🧪 Minimal Pinecone Update Test")
    print("=" * 50)
    
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Import Theodore components
        from src.main_pipeline import TheodoreIntelligencePipeline
        from src.models import CompanyIntelligenceConfig
        
        # Initialize pipeline
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME')
        )
        
        print("✅ Theodore pipeline initialized")
        
        # Get target company (Audigent from previous test)
        target_id = "71f0230f-3ea5-4870-bbdd-a8528073919c"
        target_name = "Audigent"
        
        print(f"🎯 Target company: {target_name} (ID: {target_id})")
        
        # Test 1: Simple metadata update with minimal fields
        print(f"\n🧪 Test 1: Minimal metadata update")
        minimal_metadata = {
            'company_name': target_name,
            'test_classification': 'AdTech',
            'test_is_saas': True,
            'test_timestamp': datetime.now().isoformat()
        }
        
        print(f"📝 Updating with minimal metadata: {minimal_metadata}")
        
        try:
            update_response = pipeline.pinecone_client.index.update(
                id=target_id,
                metadata=minimal_metadata
            )
            print(f"📤 Update response: {update_response}")
            
            # Validate immediately
            fetch_response = pipeline.pinecone_client.index.fetch([target_id])
            if hasattr(fetch_response, 'vectors') and target_id in fetch_response.vectors:
                fetched_metadata = fetch_response.vectors[target_id].metadata
                print(f"✅ Immediate validation:")
                print(f"   Test classification: {fetched_metadata.get('test_classification')}")
                print(f"   Test timestamp: {fetched_metadata.get('test_timestamp')}")
                
                if fetched_metadata.get('test_classification') == 'AdTech':
                    print(f"🎉 Test 1 SUCCESSFUL!")
                else:
                    print(f"❌ Test 1 FAILED")
            else:
                print(f"❌ Test 1 FAILED - no fetch response")
                
        except Exception as e:
            print(f"❌ Test 1 error: {e}")
        
        # Test 2: Get original metadata and update with classifications
        print(f"\n🧪 Test 2: Update existing metadata with classification")
        
        try:
            # Fetch current metadata
            fetch_response = pipeline.pinecone_client.index.fetch([target_id])
            if hasattr(fetch_response, 'vectors') and target_id in fetch_response.vectors:
                current_metadata = fetch_response.vectors[target_id].metadata
                print(f"📋 Current metadata has {len(current_metadata)} fields")
                
                # Add classification to existing metadata
                updated_metadata = current_metadata.copy()
                updated_metadata.update({
                    'is_saas': True,
                    'saas_classification': 'AdTech',
                    'classification_confidence': 0.95,
                    'classification_justification': 'Test classification',
                    'classification_timestamp': datetime.now().isoformat()
                })
                
                print(f"📝 Updating with {len(updated_metadata)} total fields")
                
                update_response = pipeline.pinecone_client.index.update(
                    id=target_id,
                    metadata=updated_metadata
                )
                print(f"📤 Update response: {update_response}")
                
                # Validate
                import time
                time.sleep(1)
                fetch_response = pipeline.pinecone_client.index.fetch([target_id])
                if hasattr(fetch_response, 'vectors') and target_id in fetch_response.vectors:
                    fetched_metadata = fetch_response.vectors[target_id].metadata
                    print(f"✅ Validation:")
                    print(f"   SaaS classification: {fetched_metadata.get('saas_classification')}")
                    print(f"   Is SaaS: {fetched_metadata.get('is_saas')}")
                    print(f"   Confidence: {fetched_metadata.get('classification_confidence')}")
                    
                    if fetched_metadata.get('saas_classification') == 'AdTech':
                        print(f"🎉 Test 2 SUCCESSFUL!")
                    else:
                        print(f"❌ Test 2 FAILED")
                else:
                    print(f"❌ Test 2 FAILED - no fetch response")
            else:
                print(f"❌ Test 2 FAILED - couldn't fetch current metadata")
                
        except Exception as e:
            print(f"❌ Test 2 error: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()