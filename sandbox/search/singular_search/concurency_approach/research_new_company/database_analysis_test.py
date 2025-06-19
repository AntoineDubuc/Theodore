#!/usr/bin/env python3
"""
Database Analysis Test
Detailed analysis of existing companies and their classifications
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
    from src.models import CompanyIntelligenceConfig
    from src.pinecone_client import PineconeClient
    print("✅ Successfully imported Theodore components")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

def analyze_database():
    """Analyze the current database state"""
    
    print("🧪 THEODORE DATABASE ANALYSIS")
    print("=" * 60)
    print("📅 Analysis Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    try:
        # Initialize client
        config = CompanyIntelligenceConfig(
            output_format="json",
            use_ai_analysis=True,
            max_pages=10,
            aws_region="us-east-1",
            bedrock_analysis_model="amazon.nova-pro-v1:0"
        )
        
        pinecone_api_key = os.getenv('PINECONE_API_KEY')
        pinecone_index = os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        
        if not pinecone_api_key:
            print("❌ PINECONE_API_KEY environment variable not found")
            return False
        
        pinecone_client = PineconeClient(
            config=config,
            api_key=pinecone_api_key,
            environment="gcp-starter",
            index_name=pinecone_index
        )
        
        # Get all companies
        print("📊 Retrieving all companies...")
        all_companies = pinecone_client.find_companies_by_filters(filters={}, top_k=1000)
        total_companies = len(all_companies)
        
        print(f"✅ Found {total_companies} companies in database")
        print()
        
        # Detailed analysis
        print("📋 DETAILED COMPANY ANALYSIS")
        print("-" * 40)
        
        classified_companies = []
        unclassified_companies = []
        
        for i, company in enumerate(all_companies, 1):
            metadata = company.get('metadata', {})
            company_name = metadata.get('company_name', f'Unknown_{i}')
            saas_classification = metadata.get('saas_classification')
            is_saas = metadata.get('is_saas')
            confidence = metadata.get('classification_confidence')
            
            print(f"{i:2d}. {company_name}")
            
            if saas_classification and saas_classification != "Unclassified":
                print(f"    🏷️  Classification: {saas_classification}")
                print(f"    📊 Type: {'SaaS' if is_saas else 'Non-SaaS'}")
                if confidence is not None:
                    print(f"    📈 Confidence: {confidence:.2f}")
                classified_companies.append(company_name)
            else:
                print(f"    ❌ No classification")
                unclassified_companies.append(company_name)
            
            print()
        
        # Summary
        print("=" * 60)
        print("📊 CLASSIFICATION SUMMARY")
        print("=" * 60)
        
        classified_count = len(classified_companies)
        unclassified_count = len(unclassified_companies)
        coverage_percentage = classified_count / total_companies * 100 if total_companies > 0 else 0
        
        print(f"Total Companies: {total_companies}")
        print(f"Classified: {classified_count} ({coverage_percentage:.1f}%)")
        print(f"Unclassified: {unclassified_count}")
        print()
        
        print("✅ CLASSIFIED COMPANIES:")
        for company in classified_companies:
            print(f"   • {company}")
        
        print(f"\n❌ UNCLASSIFIED COMPANIES:")
        for company in unclassified_companies:
            print(f"   • {company}")
        
        # Category distribution
        print(f"\n🏷️ CATEGORY DISTRIBUTION:")
        categories = {}
        saas_count = 0
        non_saas_count = 0
        
        for company in all_companies:
            metadata = company.get('metadata', {})
            saas_classification = metadata.get('saas_classification')
            is_saas = metadata.get('is_saas')
            
            if saas_classification and saas_classification != "Unclassified":
                categories[saas_classification] = categories.get(saas_classification, 0) + 1
                
                if is_saas:
                    saas_count += 1
                else:
                    non_saas_count += 1
        
        print(f"   SaaS Companies: {saas_count}")
        print(f"   Non-SaaS Companies: {non_saas_count}")
        print()
        
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"   {category}: {count} companies")
        
        print(f"\n🎯 ASSESSMENT FOR TESTING:")
        
        if classified_count >= 10:
            print("✅ GOOD: Sufficient classified companies for testing")
            print("✅ Can proceed with classification retrieval tests")
        elif classified_count >= 5:
            print("⚠️ MODERATE: Some classified companies available")
            print("⚠️ Limited test scope but can proceed")
        else:
            print("❌ LOW: Very few classified companies")
            print("❌ Should classify more companies before comprehensive testing")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    analyze_database()