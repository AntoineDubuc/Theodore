#!/usr/bin/env python3
"""
Fix classification consistency - ensure all records have both saas_classification and is_saas fields
"""

import os
import sys
from datetime import datetime

# Add project root and src to path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def main():
    print("🔧 Classification Consistency Repair")
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
        
        # SaaS categories (should have is_saas = True)
        SAAS_CATEGORIES = {
            'AdTech', 'AI/ML Platform', 'Analytics Platform', 'API Management',
            'Business Intelligence', 'CRM', 'Customer Support', 'DevOps Platform',
            'E-commerce Platform', 'HR Tech', 'Marketing Automation', 'Project Management',
            'Security Platform', 'Social Media Management'
        }
        
        # Fetch all companies from Pinecone
        print("\n📊 Fetching all companies...")
        query_result = pipeline.pinecone_client.index.query(
            vector=[0.0] * 1536,
            top_k=1000,
            include_metadata=True,
            include_values=False
        )
        
        inconsistent_records = []
        total_companies = len(query_result.matches)
        
        # Find inconsistent records
        for match in query_result.matches:
            metadata = match.metadata or {}
            company_name = metadata.get('company_name', 'Unknown')
            saas_classification = metadata.get('saas_classification')
            is_saas = metadata.get('is_saas')
            
            # Check if classification exists but is_saas is missing
            if saas_classification and is_saas is None:
                # Determine correct is_saas value based on category
                should_be_saas = saas_classification in SAAS_CATEGORIES
                
                inconsistent_records.append({
                    'id': match.id,
                    'name': company_name,
                    'metadata': metadata,
                    'saas_classification': saas_classification,
                    'should_be_saas': should_be_saas
                })
        
        print(f"📈 Analysis Results:")
        print(f"   Total companies: {total_companies}")
        print(f"   Inconsistent records: {len(inconsistent_records)}")
        
        if not inconsistent_records:
            print("✅ All classification data is consistent!")
            return
        
        print(f"\n🔧 Fixing {len(inconsistent_records)} inconsistent records...")
        
        successful_fixes = 0
        
        for i, record in enumerate(inconsistent_records):
            company_name = record['name']
            metadata = record['metadata']
            should_be_saas = record['should_be_saas']
            
            print(f"[{i+1}/{len(inconsistent_records)}] Fixing: {company_name}")
            print(f"   Category: {record['saas_classification']}")
            print(f"   Setting is_saas: {should_be_saas}")
            
            try:
                # Update metadata with correct is_saas value
                updated_metadata = metadata.copy()
                updated_metadata['is_saas'] = should_be_saas
                updated_metadata['consistency_fix_timestamp'] = datetime.now().isoformat()
                
                # Update in Pinecone
                pipeline.pinecone_client.index.update(
                    id=record['id'],
                    set_metadata=updated_metadata
                )
                
                successful_fixes += 1
                print(f"   ✅ Fixed successfully")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print(f"\n🎉 Consistency Fix Summary:")
        print(f"   Records processed: {len(inconsistent_records)}")
        print(f"   Successful fixes: {successful_fixes}")
        print(f"   Success rate: {round(successful_fixes/len(inconsistent_records)*100, 1)}%")
        
        # Verify fixes
        print(f"\n🔍 Verifying fixes...")
        import time
        time.sleep(2)
        
        # Re-query to verify
        verify_result = pipeline.pinecone_client.index.query(
            vector=[0.0] * 1536,
            top_k=1000,
            include_metadata=True,
            include_values=False
        )
        
        missing_is_saas = 0
        for match in verify_result.matches:
            metadata = match.metadata or {}
            if metadata.get('saas_classification') and metadata.get('is_saas') is None:
                missing_is_saas += 1
        
        print(f"   Records still missing is_saas: {missing_is_saas}")
        
        if missing_is_saas == 0:
            print("✅ All classification inconsistencies resolved!")
        else:
            print("⚠️ Some inconsistencies remain - manual review needed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()