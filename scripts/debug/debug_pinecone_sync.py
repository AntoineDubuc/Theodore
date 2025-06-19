#!/usr/bin/env python3
"""
Debug script to investigate Pinecone synchronization issues
"""

import os
import sys
from datetime import datetime

# Add project root and src to path
project_root = os.path.join(os.path.dirname(__file__), '.')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def main():
    print("🔍 Pinecone Synchronization Debug")
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
        
        # Query raw Pinecone data
        print("\n🔍 Querying raw Pinecone data...")
        query_result = pipeline.pinecone_client.index.query(
            vector=[0.0] * 1536,
            top_k=1000,
            include_metadata=True,
            include_values=False
        )
        
        # Analyze classification status
        total_companies = len(query_result.matches)
        classified_count = 0
        classification_stats = {}
        confidence_stats = {"high": 0, "medium": 0, "low": 0}
        saas_count = 0
        
        print(f"\n📊 Analyzing {total_companies} companies from Pinecone...")
        
        recent_updates = []
        
        for i, match in enumerate(query_result.matches):
            metadata = match.metadata or {}
            company_name = metadata.get('company_name', 'Unknown')
            
            # Check classification
            is_classified = metadata.get('saas_classification') is not None
            if is_classified:
                classified_count += 1
                category = metadata.get('saas_classification', 'Unknown')
                classification_stats[category] = classification_stats.get(category, 0) + 1
                
                # Check SaaS status
                if metadata.get('is_saas'):
                    saas_count += 1
                
                # Check confidence
                confidence = metadata.get('classification_confidence', 0)
                if confidence >= 0.8:
                    confidence_stats["high"] += 1
                elif confidence >= 0.6:
                    confidence_stats["medium"] += 1
                else:
                    confidence_stats["low"] += 1
                
                # Check for recent updates
                timestamp = metadata.get('classification_timestamp')
                if timestamp:
                    try:
                        from datetime import datetime
                        update_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        if (datetime.now().astimezone() - update_time.astimezone()).total_seconds() < 3600:  # Last hour
                            recent_updates.append({
                                'company': company_name,
                                'category': category,
                                'timestamp': timestamp,
                                'is_saas': metadata.get('is_saas', False)
                            })
                    except Exception as e:
                        pass
                
                print(f"  ✅ [{i+1:2d}] {company_name:<20} - {category} ({'SaaS' if metadata.get('is_saas') else 'Non-SaaS'}) - {confidence:.1f}")
            else:
                print(f"  ❌ [{i+1:2d}] {company_name:<20} - Not classified")
        
        # Calculate statistics
        classification_percentage = round((classified_count / total_companies) * 100, 1)
        saas_percentage = round((saas_count / total_companies) * 100, 1)
        
        print(f"\n📈 Raw Pinecone Statistics:")
        print(f"   Total Companies: {total_companies}")
        print(f"   Classified: {classified_count} ({classification_percentage}%)")
        print(f"   Unclassified: {total_companies - classified_count}")
        print(f"   SaaS Companies: {saas_count} ({saas_percentage}%)")
        print(f"   Non-SaaS Companies: {classified_count - saas_count}")
        
        print(f"\n📊 Category Breakdown:")
        for category, count in sorted(classification_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"   {category}: {count}")
        
        print(f"\n🎯 Confidence Distribution:")
        for level, count in confidence_stats.items():
            print(f"   {level.title()}: {count}")
        
        if recent_updates:
            print(f"\n🕒 Recent Updates (last hour):")
            for update in recent_updates:
                print(f"   • {update['company']}: {update['category']} ({'SaaS' if update['is_saas'] else 'Non-SaaS'}) at {update['timestamp']}")
        
        # Test API endpoint for comparison
        print(f"\n🌐 Testing API endpoint...")
        import requests
        try:
            response = requests.get('http://localhost:5002/api/classification/stats')
            if response.status_code == 200:
                api_data = response.json()
                print(f"   API Total Companies: {api_data.get('total_companies')}")
                print(f"   API Classified: {api_data.get('classified_companies')} ({api_data.get('classification_percentage')}%)")
                print(f"   API SaaS: {api_data.get('saas_companies')} ({api_data.get('saas_percentage')}%)")
                
                # Compare results
                print(f"\n⚖️  Comparison:")
                print(f"   Pinecone vs API Classified: {classified_count} vs {api_data.get('classified_companies')}")
                print(f"   Pinecone vs API Percentage: {classification_percentage}% vs {api_data.get('classification_percentage')}%")
                
                if classified_count != api_data.get('classified_companies'):
                    print(f"   🚨 MISMATCH DETECTED! Pinecone has {classified_count - api_data.get('classified_companies')} more classified companies")
                else:
                    print(f"   ✅ Data matches between Pinecone and API")
            else:
                print(f"   ❌ API request failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ API test failed: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()