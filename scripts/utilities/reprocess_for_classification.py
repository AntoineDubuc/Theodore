#!/usr/bin/env python3
"""
Reprocess existing Pinecone companies to trigger classification visibility

This script will:
1. Fetch all companies from Pinecone
2. Check which ones have classification data that might not be showing up
3. Refresh/update metadata to ensure classification data is properly indexed
4. Optionally run classification on unclassified companies
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Any

# Add project root and src to path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def main():
    print("🔄 Theodore Classification Reprocessing Script")
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
        print("\n📊 Fetching all companies from Pinecone...")
        query_result = pipeline.pinecone_client.index.query(
            vector=[0.0] * 1536,
            top_k=1000,
            include_metadata=True,
            include_values=False
        )
        
        total_companies = len(query_result.matches)
        print(f"Found {total_companies} companies in database")
        
        # Analyze current classification status
        classified_count = 0
        unclassified_companies = []
        classification_stats = {}
        
        print("\n🔍 Analyzing current classification status...")
        for match in query_result.matches:
            metadata = match.metadata or {}
            company_name = metadata.get('company_name', 'Unknown')
            
            # Check if classified
            is_classified = metadata.get('saas_classification') is not None
            if is_classified:
                classified_count += 1
                category = metadata.get('saas_classification', 'Unknown')
                classification_stats[category] = classification_stats.get(category, 0) + 1
                
                print(f"✅ {company_name} - {category} ({'SaaS' if metadata.get('is_saas') else 'Non-SaaS'})")
            else:
                unclassified_companies.append({
                    'id': match.id,
                    'name': company_name,
                    'metadata': metadata
                })
                print(f"❌ {company_name} - Not classified")
        
        print(f"\n📈 Current Status:")
        print(f"   Total Companies: {total_companies}")
        print(f"   Classified: {classified_count} ({round(classified_count/total_companies*100, 1)}%)")
        print(f"   Unclassified: {len(unclassified_companies)}")
        
        if classification_stats:
            print(f"\n📊 Classification Breakdown:")
            for category, count in sorted(classification_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"   {category}: {count}")
        
        # Ask user what to do
        print(f"\n🤔 What would you like to do?")
        print(f"1. Refresh metadata for all companies (fix display issues)")
        print(f"2. Classify unclassified companies ({len(unclassified_companies)} companies)")
        print(f"3. Force reclassify all companies")
        print(f"4. Just show current status and exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            refresh_metadata(pipeline, query_result.matches)
        elif choice == "2":
            classify_unclassified(pipeline, classifier, unclassified_companies)
        elif choice == "3":
            force_reclassify_all(pipeline, classifier, query_result.matches)
        elif choice == "4":
            print("👋 Exiting without changes")
        else:
            print("❌ Invalid choice. Exiting.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def refresh_metadata(pipeline, matches: List[Any]):
    """Refresh metadata for all companies to fix display issues"""
    print(f"\n🔄 Refreshing metadata for {len(matches)} companies...")
    
    updated_count = 0
    for i, match in enumerate(matches):
        try:
            metadata = match.metadata or {}
            company_name = metadata.get('company_name', 'Unknown')
            
            # Add a refresh timestamp to trigger update
            updated_metadata = metadata.copy()
            updated_metadata['last_metadata_refresh'] = datetime.now().isoformat()
            
            # Update in Pinecone
            pipeline.pinecone_client.index.update(
                id=match.id,
                metadata=updated_metadata
            )
            
            updated_count += 1
            print(f"🔄 [{i+1}/{len(matches)}] Refreshed: {company_name}")
            
        except Exception as e:
            print(f"❌ Failed to refresh {company_name}: {e}")
    
    print(f"\n✅ Refreshed metadata for {updated_count} companies")
    print("💡 The classification data should now be visible in the UI")

def classify_unclassified(pipeline, classifier, unclassified_companies: List[Dict]):
    """Classify unclassified companies"""
    if not unclassified_companies:
        print("✅ No unclassified companies found!")
        return
    
    print(f"\n🏷️ Classifying {len(unclassified_companies)} unclassified companies...")
    
    # Ask for batch size
    batch_size = min(len(unclassified_companies), 10)
    user_batch = input(f"How many companies to classify? (default: {batch_size}): ").strip()
    if user_batch:
        try:
            batch_size = min(int(user_batch), len(unclassified_companies))
        except ValueError:
            print("Invalid number, using default")
    
    companies_to_process = unclassified_companies[:batch_size]
    successful_classifications = 0
    
    for i, company_info in enumerate(companies_to_process):
        try:
            company_name = company_info['name']
            metadata = company_info['metadata']
            
            print(f"\n🏷️ [{i+1}/{len(companies_to_process)}] Classifying: {company_name}")
            
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
                
                print(f"   ✅ {classification_result['category']} ({saas_status}) - {confidence}% confidence")
                print(f"   💡 {classification_result['justification']}")
                
            else:
                print(f"   ❌ Classification failed")
                
        except Exception as e:
            print(f"   ❌ Error classifying {company_name}: {e}")
    
    print(f"\n🎉 Classification Complete!")
    print(f"   Successfully classified: {successful_classifications}/{len(companies_to_process)}")
    print(f"   Success rate: {round(successful_classifications/len(companies_to_process)*100, 1)}%")

def force_reclassify_all(pipeline, classifier, matches: List[Any]):
    """Force reclassify all companies"""
    print(f"\n⚠️  WARNING: This will reclassify ALL {len(matches)} companies!")
    confirm = input("Are you sure? Type 'yes' to continue: ").strip().lower()
    
    if confirm != 'yes':
        print("👋 Cancelled")
        return
    
    # Ask for batch size
    batch_size = min(len(matches), 10)
    user_batch = input(f"How many companies to reclassify? (default: {batch_size}): ").strip()
    if user_batch:
        try:
            batch_size = min(int(user_batch), len(matches))
        except ValueError:
            print("Invalid number, using default")
    
    companies_to_process = matches[:batch_size]
    successful_classifications = 0
    
    print(f"\n🏷️ Force reclassifying {len(companies_to_process)} companies...")
    
    for i, match in enumerate(companies_to_process):
        try:
            metadata = match.metadata or {}
            company_name = metadata.get('company_name', 'Unknown')
            
            print(f"\n🏷️ [{i+1}/{len(companies_to_process)}] Reclassifying: {company_name}")
            
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
                    id=match.id,
                    set_metadata=updated_metadata
                )
                
                successful_classifications += 1
                saas_status = "SaaS" if classification_result['is_saas'] else "Non-SaaS"
                confidence = round(classification_result['confidence'] * 100)
                
                print(f"   ✅ {classification_result['category']} ({saas_status}) - {confidence}% confidence")
                
            else:
                print(f"   ❌ Classification failed")
                
        except Exception as e:
            print(f"   ❌ Error reclassifying {company_name}: {e}")
    
    print(f"\n🎉 Reclassification Complete!")
    print(f"   Successfully reclassified: {successful_classifications}/{len(companies_to_process)}")
    print(f"   Success rate: {round(successful_classifications/len(companies_to_process)*100, 1)}%")

if __name__ == "__main__":
    main()