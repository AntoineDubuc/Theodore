#!/usr/bin/env python3
"""
Test Pinecone update operation directly
"""

import os
import sys
from datetime import datetime

# Add project root and src to path
project_root = os.path.join(os.path.dirname(__file__), '.')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def main():
    print("🔍 Pinecone Update Test")
    print("=" * 40)
    
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
        
        # Get the first unclassified company
        print("\n📊 Fetching unclassified company...")
        query_result = pipeline.pinecone_client.index.query(
            vector=[0.0] * 1536,
            top_k=1000,
            include_metadata=True,
            include_values=False
        )
        
        # Find first unclassified company
        target_company = None
        for match in query_result.matches:
            metadata = match.metadata or {}
            is_classified = metadata.get('saas_classification') is not None
            if not is_classified:
                target_company = {
                    'id': match.id,
                    'name': metadata.get('company_name', 'Unknown'),
                    'metadata': metadata
                }
                break
        
        if not target_company:
            print("❌ No unclassified companies found")
            return
        
        print(f"🎯 Target company: {target_company['name']} (ID: {target_company['id']})")
        print(f"📋 Current metadata keys: {list(target_company['metadata'].keys())}")
        
        # Prepare new metadata
        new_metadata = target_company['metadata'].copy()
        new_metadata.update({
            'is_saas': True,
            'saas_classification': 'Test Classification',
            'classification_confidence': 0.95,
            'classification_justification': 'Test classification for debugging',
            'classification_timestamp': datetime.now().isoformat(),
            'test_update': 'debug_test_' + datetime.now().strftime('%H%M%S')
        })
        
        print(f"\n📝 Updating metadata...")
        print(f"   Adding classification: Test Classification")
        print(f"   Adding test marker: {new_metadata['test_update']}")
        
        # Perform update
        try:
            update_response = pipeline.pinecone_client.index.update(
                id=target_company['id'],
                metadata=new_metadata
            )
            print(f"📤 Update response: {update_response}")
            
            # Wait for consistency
            import time
            print(f"⏱️  Waiting 3 seconds for consistency...")
            time.sleep(3)
            
            # Verify update
            print(f"\n🔍 Verifying update...")
            fetch_response = pipeline.pinecone_client.index.fetch([target_company['id']])
            print(f"📥 Fetch response type: {type(fetch_response)}")
            print(f"📥 Fetch response: {fetch_response}")
            
            if hasattr(fetch_response, 'vectors') and target_company['id'] in fetch_response.vectors:
                fetched_vector = fetch_response.vectors[target_company['id']]
                if hasattr(fetched_vector, 'metadata'):
                    fetched_metadata = fetched_vector.metadata
                    print(f"✅ Fetched metadata successfully")
                    print(f"   Classification: {fetched_metadata.get('saas_classification')}")
                    print(f"   Test marker: {fetched_metadata.get('test_update')}")
                    print(f"   Timestamp: {fetched_metadata.get('classification_timestamp')}")
                    
                    if fetched_metadata.get('saas_classification') == 'Test Classification':
                        print(f"🎉 Update SUCCESSFUL!")
                    else:
                        print(f"❌ Update FAILED - classification not found")
                else:
                    print(f"❌ No metadata in fetched vector")
            else:
                print(f"❌ Vector not found in fetch response")
                
        except Exception as e:
            print(f"❌ Update error: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()