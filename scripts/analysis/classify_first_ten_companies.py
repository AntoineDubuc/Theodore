#!/usr/bin/env python3
"""
Classify first 10 companies from Theodore database with real AI
Add columns: Company Name;URL;Classification;Justification
"""

import sys
import os
from datetime import datetime
import csv

# Add src to path
sys.path.insert(0, 'src')

from models import CompanyData, SaaSCategory, ClassificationResult, CompanyIntelligenceConfig
from classification.saas_classifier import SaaSBusinessModelClassifier
from bedrock_client import BedrockClient
from pinecone_client import PineconeClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def initialize_clients():
    """Initialize Bedrock and Pinecone clients"""
    print("🔧 Initializing Theodore clients...")
    
    try:
        # Initialize Bedrock with config
        config = CompanyIntelligenceConfig()
        bedrock_client = BedrockClient(config)
        print(f"   ✅ Bedrock client initialized ({config.bedrock_analysis_model})")
        
        # Initialize classifier
        classifier = SaaSBusinessModelClassifier(bedrock_client)
        print(f"   ✅ Classifier initialized")
        
        # Initialize Pinecone with config
        pinecone_client = PineconeClient(
            config=config,
            api_key=os.getenv('PINECONE_API_KEY'),
            environment=os.getenv('PINECONE_ENVIRONMENT', 'us-east-1'),
            index_name=os.getenv('PINECONE_INDEX_NAME', 'theodore-companies')
        )
        print(f"   ✅ Pinecone client initialized")
        
        return classifier, pinecone_client, config
        
    except Exception as e:
        print(f"   ❌ Failed to initialize clients: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None


def _ensure_list(value):
    """Convert string or other value to list if needed"""
    if isinstance(value, list):
        return value
    elif isinstance(value, str):
        # Try to parse as comma-separated string
        if ',' in value:
            return [item.strip() for item in value.split(',')]
        else:
            return [value] if value else []
    else:
        return [] if value is None else [str(value)]


def get_first_ten_companies(pinecone_client):
    """Get first 10 companies from database"""
    print("📋 Fetching first 10 companies from database...")
    
    try:
        # Query for companies with good data
        query_result = pinecone_client.index.query(
            vector=[0.0] * 1536,  # Dummy vector for metadata query
            top_k=20,  # Get more to filter for quality
            include_metadata=True,
            include_values=False
        )
        
        companies = []
        for match in query_result.matches:
            metadata = match.metadata
            
            # Extract company name from multiple sources
            def extract_name_from_website(website):
                """Extract company name from website URL"""
                if not website:
                    return "Unknown"
                import re
                # Remove protocol and www
                domain = re.sub(r'https?://(www\.)?', '', website)
                # Get domain name without TLD
                name = domain.split('.')[0]
                # Capitalize first letter
                return name.capitalize()
            
            company_name = (
                metadata.get('company_name') or 
                metadata.get('name') or
                extract_name_from_website(metadata.get('website', ''))
            )
            
            # Only include companies with sufficient data
            if company_name and metadata.get('website'):
                company = CompanyData(
                    id=match.id,
                    name=company_name,
                    website=metadata.get('website', ''),
                    ai_summary=metadata.get('ai_summary', ''),
                    value_proposition=metadata.get('value_proposition', ''),
                    company_description=metadata.get('company_description', ''),
                    industry=metadata.get('industry', ''),
                    products_services_offered=_ensure_list(metadata.get('products_services_offered', [])),
                    # Check existing classification
                    saas_classification=metadata.get('saas_classification'),
                    classification_confidence=metadata.get('classification_confidence'),
                    classification_justification=metadata.get('classification_justification'),
                    is_saas=metadata.get('is_saas')
                )
                companies.append(company)
                
                if len(companies) >= 10:
                    break
        
        print(f"   ✅ Found {len(companies)} companies with sufficient data")
        for i, company in enumerate(companies, 1):
            classification_status = "✅ Already classified" if company.saas_classification else "⏳ Needs classification"
            print(f"   {i:2}. {company.name:25} - {classification_status}")
        
        return companies[:10]
        
    except Exception as e:
        print(f"   ❌ Error fetching companies: {e}")
        return []


def classify_company_if_needed(classifier, company):
    """Classify company if not already classified"""
    
    # Check if already classified
    if company.saas_classification and company.classification_justification:
        print(f"   ℹ️  Already classified as: {company.saas_classification}")
        return True
    
    print(f"   🤖 Classifying with real AI...")
    
    try:
        # Perform real classification
        start_time = datetime.now()
        result = classifier.classify_company(company)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        # Update company with classification
        company.saas_classification = result.category.value
        company.classification_confidence = result.confidence
        company.classification_justification = result.justification
        company.classification_timestamp = result.timestamp
        company.is_saas = result.is_saas
        
        print(f"   ✅ Classified as: {result.category.value} ({result.confidence:.2f} confidence)")
        print(f"   ⏱️  Processing time: {processing_time:.2f}s")
        print(f"   📝 Justification: {result.justification[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Classification failed: {e}")
        return False


def update_company_in_database(pinecone_client, company):
    """Update company with classification in Pinecone"""
    
    try:
        # Prepare metadata update
        metadata_update = {
            'saas_classification': company.saas_classification,
            'classification_confidence': company.classification_confidence,
            'classification_justification': company.classification_justification,
            'classification_timestamp': company.classification_timestamp.isoformat() if company.classification_timestamp else None,
            'is_saas': company.is_saas,
            'classification_model_version': 'v1.0'
        }
        
        # Update in Pinecone (keeping existing vector)
        pinecone_client.index.update(
            id=company.id,
            set_metadata=metadata_update
        )
        
        print(f"   ✅ Updated in database")
        return True
        
    except Exception as e:
        print(f"   ❌ Database update failed: {e}")
        return False


def export_to_csv(companies, filename="theodore_classifications.csv"):
    """Export companies to CSV with required format"""
    print(f"📊 Exporting to CSV: {filename}")
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            # Use semicolon delimiter as specified
            writer = csv.writer(csvfile, delimiter=';')
            
            # Write header
            writer.writerow(['Company Name', 'URL', 'Classification', 'Justification'])
            
            # Write company data
            for company in companies:
                writer.writerow([
                    company.name,
                    company.website,
                    company.saas_classification or 'Unclassified',
                    company.classification_justification or 'No justification available'
                ])
        
        print(f"   ✅ Exported {len(companies)} companies to {filename}")
        return True
        
    except Exception as e:
        print(f"   ❌ Export failed: {e}")
        return False


def print_classification_summary(companies):
    """Print summary of classifications"""
    print("\n📊 CLASSIFICATION SUMMARY")
    print("=" * 60)
    
    # Count classifications
    saas_count = sum(1 for c in companies if c.is_saas)
    non_saas_count = sum(1 for c in companies if c.is_saas == False)
    unclassified_count = sum(1 for c in companies if c.is_saas is None)
    
    print(f"📈 Total companies: {len(companies)}")
    print(f"✅ SaaS companies: {saas_count}")
    print(f"🏢 Non-SaaS companies: {non_saas_count}")
    print(f"❓ Unclassified: {unclassified_count}")
    
    # Show categories
    categories = {}
    for company in companies:
        if company.saas_classification:
            categories[company.saas_classification] = categories.get(company.saas_classification, 0) + 1
    
    print(f"\n🏷️ Categories found:")
    for category, count in categories.items():
        print(f"   {category}: {count} companies")
    
    # Show average confidence
    confidences = [c.classification_confidence for c in companies if c.classification_confidence]
    if confidences:
        avg_confidence = sum(confidences) / len(confidences)
        print(f"\n📊 Average confidence: {avg_confidence:.2f}")


def main():
    """Main classification workflow"""
    print("🚀 CLASSIFYING FIRST 10 COMPANIES FROM THEODORE DATABASE")
    print("=" * 60)
    
    # Initialize clients
    classifier, pinecone_client, config = initialize_clients()
    if not classifier or not pinecone_client:
        print("❌ Failed to initialize clients")
        return False
    
    # Get companies
    companies = get_first_ten_companies(pinecone_client)
    if not companies:
        print("❌ No companies found")
        return False
    
    # Process each company
    print(f"\n🔬 PROCESSING {len(companies)} COMPANIES")
    print("=" * 60)
    
    successful_classifications = 0
    successful_updates = 0
    
    for i, company in enumerate(companies, 1):
        print(f"\n📦 Processing {i}/{len(companies)}: {company.name}")
        print(f"   🌐 Website: {company.website}")
        print(f"   🏢 Industry: {company.industry or 'Unknown'}")
        
        # Classify if needed
        if classify_company_if_needed(classifier, company):
            successful_classifications += 1
            
            # Update in database
            if update_company_in_database(pinecone_client, company):
                successful_updates += 1
        
        # Rate limiting
        if i < len(companies):
            print(f"   💤 Waiting 2 seconds...")
            import time
            time.sleep(2)
    
    # Export results
    print(f"\n📊 EXPORTING RESULTS")
    print("=" * 60)
    export_to_csv(companies)
    
    # Print summary
    print_classification_summary(companies)
    
    # Final results
    print(f"\n🎉 CLASSIFICATION COMPLETE!")
    print(f"   ✅ Classifications: {successful_classifications}/{len(companies)}")
    print(f"   ✅ Database updates: {successful_updates}/{len(companies)}")
    print(f"   📄 CSV exported: theodore_classifications.csv")
    
    if successful_classifications == len(companies):
        print("✅ All companies successfully classified!")
        return True
    else:
        print("⚠️ Some companies failed classification")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)