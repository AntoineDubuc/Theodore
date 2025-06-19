#!/usr/bin/env python3
"""
Enhanced auto-classification script with Pinecone update validation
"""

import os
import sys
from datetime import datetime
import time

# Add project root and src to path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def main():
    print("🤖 Enhanced Auto-Classification with Validation")
    print("=" * 60)
    
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
        
        # Fetch all companies from Pinecone
        print("\n📊 Fetching companies from Pinecone...")
        query_result = pipeline.pinecone_client.index.query(
            vector=[0.0] * 1536,
            top_k=1000,
            include_metadata=True,
            include_values=False
        )
        
        # Find unclassified companies
        unclassified_companies = []
        classified_count = 0
        
        for match in query_result.matches:
            metadata = match.metadata or {}
            company_name = metadata.get('company_name', 'Unknown')
            
            # Check if classified
            is_classified = metadata.get('saas_classification') is not None
            if is_classified:
                classified_count += 1
            else:
                unclassified_companies.append({
                    'id': match.id,
                    'name': company_name,
                    'metadata': metadata
                })
        
        total_companies = len(query_result.matches)
        print(f"📈 Found {total_companies} total companies")
        print(f"✅ Already classified: {classified_count}")
        print(f"❌ Unclassified: {len(unclassified_companies)}")
        
        if not unclassified_companies:
            print("\n🎉 All companies are already classified!")
            return
        
        # Process a smaller batch for testing
        batch_size = min(5, len(unclassified_companies))
        companies_to_process = unclassified_companies[:batch_size]
        
        print(f"\n🏷️ Auto-classifying {len(companies_to_process)} companies...")
        
        successful_classifications = 0
        pinecone_failures = 0
        results = []
        
        for i, company_info in enumerate(companies_to_process):
            company_name = company_info['name']
            metadata = company_info['metadata']
            
            print(f"\n[{i+1}/{len(companies_to_process)}] 🏷️ Classifying: {company_name}")
            
            try:
                # Prepare company data for classification
                company_data = {
                    'name': company_name,
                    'website': metadata.get('website', ''),
                    'industry': metadata.get('industry', ''),
                    'description': metadata.get('value_proposition', ''),
                    'products_services': metadata.get('products_services_offered', '')
                }
                
                # Perform classification
                classification_result = classifier.classify_company(company_data)
                
                if classification_result and classification_result.get('success'):
                    # Update company metadata with classification
                    updated_metadata = metadata.copy()
                    updated_metadata.update({
                        'is_saas': classification_result['is_saas'],
                        'saas_classification': classification_result['category'],
                        'classification_confidence': classification_result['confidence'],
                        'classification_justification': classification_result['justification'],
                        'classification_timestamp': datetime.now().isoformat()
                    })
                    
                    print(f"   📝 Updating metadata in Pinecone...")
                    
                    # Update in Pinecone with validation
                    try:
                        update_response = pipeline.pinecone_client.index.update(
                            id=company_info['id'],
                            metadata=updated_metadata
                        )
                        print(f"   📤 Pinecone update response: {update_response}")
                        
                        # Wait briefly for consistency
                        time.sleep(0.5)
                        
                        # Validate the update by fetching the record
                        print(f"   🔍 Validating update...")
                        fetch_response = pipeline.pinecone_client.index.fetch([company_info['id']])
                        
                        if fetch_response and 'vectors' in fetch_response:
                            fetched_data = fetch_response['vectors'].get(company_info['id'])
                            if fetched_data and 'metadata' in fetched_data:
                                fetched_metadata = fetched_data['metadata']
                                updated_category = fetched_metadata.get('saas_classification')
                                
                                if updated_category == classification_result['category']:
                                    print(f"   ✅ Pinecone update validated successfully!")
                                    successful_classifications += 1
                                    saas_status = "SaaS" if classification_result['is_saas'] else "Non-SaaS"
                                    confidence = round(classification_result['confidence'] * 100)
                                    
                                    result = {
                                        'company': company_name,
                                        'category': classification_result['category'],
                                        'is_saas': classification_result['is_saas'],
                                        'confidence': confidence
                                    }
                                    results.append(result)
                                    
                                    print(f"   🎯 {classification_result['category']} ({saas_status}) - {confidence}% confidence")
                                else:
                                    print(f"   ❌ Pinecone update validation failed! Expected: {classification_result['category']}, Got: {updated_category}")
                                    pinecone_failures += 1
                            else:
                                print(f"   ❌ No metadata in fetched record")
                                pinecone_failures += 1
                        else:
                            print(f"   ❌ Failed to fetch record for validation")
                            pinecone_failures += 1
                            
                    except Exception as e:
                        print(f"   ❌ Pinecone update error: {e}")
                        pinecone_failures += 1
                        
                else:
                    print(f"   ❌ Classification failed")
                    results.append({
                        'company': company_name,
                        'error': 'Classification failed'
                    })
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results.append({
                    'company': company_name,
                    'error': str(e)
                })
        
        # Print summary
        print(f"\n🎉 Classification Summary:")
        print(f"   Total processed: {len(companies_to_process)}")
        print(f"   Successful: {successful_classifications}")
        print(f"   Classification failures: {len(companies_to_process) - successful_classifications - pinecone_failures}")
        print(f"   Pinecone update failures: {pinecone_failures}")
        print(f"   Success rate: {round(successful_classifications/len(companies_to_process)*100, 1)}%")
        
        # Print results breakdown
        if successful_classifications > 0:
            print(f"\n📊 Successful Classifications:")
            for result in results:
                if 'category' in result:
                    print(f"   • {result['company']}: {result['category']} ({'SaaS' if result['is_saas'] else 'Non-SaaS'})")
        
        # Final validation - check overall statistics
        print(f"\n🔍 Final validation - querying updated statistics...")
        time.sleep(2)  # Wait for eventual consistency
        
        query_result_final = pipeline.pinecone_client.index.query(
            vector=[0.0] * 1536,
            top_k=1000,
            include_metadata=True,
            include_values=False
        )
        
        final_classified_count = 0
        for match in query_result_final.matches:
            metadata = match.metadata or {}
            is_classified = metadata.get('saas_classification') is not None
            if is_classified:
                final_classified_count += 1
        
        expected_classified_count = classified_count + successful_classifications
        print(f"   Expected classified: {expected_classified_count}")
        print(f"   Actual classified: {final_classified_count}")
        
        if final_classified_count == expected_classified_count:
            print(f"   ✅ Final validation successful!")
        else:
            print(f"   ❌ Final validation failed - mismatch detected")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()