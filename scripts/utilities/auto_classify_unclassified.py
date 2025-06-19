#!/usr/bin/env python3
"""
Auto-classify unclassified companies to make classification data visible

This script will automatically classify all unclassified companies
without user interaction, making it suitable for CI/CD or automated runs.
"""

import os
import sys
from datetime import datetime

# Add project root and src to path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def main():
    print("🤖 Auto-Classification Script")
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
        
        # Auto-classify with a reasonable batch size
        batch_size = min(10, len(unclassified_companies))
        companies_to_process = unclassified_companies[:batch_size]
        
        print(f"\n🏷️ Auto-classifying {len(companies_to_process)} companies...")
        
        successful_classifications = 0
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
                    
                    # Update in Pinecone
                    pipeline.pinecone_client.index.update(
                        id=company_info['id'],
                        set_metadata=updated_metadata
                    )
                    
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
                    
                    print(f"   ✅ {classification_result['category']} ({saas_status}) - {confidence}% confidence")
                    
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
        print(f"   Failed: {len(companies_to_process) - successful_classifications}")
        print(f"   Success rate: {round(successful_classifications/len(companies_to_process)*100, 1)}%")
        
        # Print results breakdown
        if successful_classifications > 0:
            print(f"\n📊 New Classifications:")
            saas_count = 0
            categories = {}
            
            for result in results:
                if 'category' in result:
                    category = result['category']
                    categories[category] = categories.get(category, 0) + 1
                    if result['is_saas']:
                        saas_count += 1
                    
                    print(f"   • {result['company']}: {category} ({'SaaS' if result['is_saas'] else 'Non-SaaS'})")
            
            print(f"\n📈 Updated Database Stats:")
            new_classified_total = classified_count + successful_classifications
            new_classification_percentage = round((new_classified_total / total_companies) * 100, 1)
            print(f"   Total companies: {total_companies}")
            print(f"   Classified: {new_classified_total} ({new_classification_percentage}%)")
            print(f"   Remaining unclassified: {len(unclassified_companies) - successful_classifications}")
            
            print(f"\n🏷️ Category breakdown from this run:")
            for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                print(f"   {category}: {count}")
        
        print(f"\n💡 Refresh the Theodore UI to see the updated classification data!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()