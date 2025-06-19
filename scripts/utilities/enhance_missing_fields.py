#!/usr/bin/env python3
"""
Enhance companies with missing critical business fields
Focuses on founding_year, location, contact_info, leadership_team
"""

import os
import sys
from datetime import datetime

# Add project root and src to path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def main():
    print("🔍 Enhanced Field Extraction for Missing Data")
    print("=" * 60)
    
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Import Theodore components
        from src.main_pipeline import TheodoreIntelligencePipeline
        from src.models import CompanyIntelligenceConfig
        from src.enhanced_field_extractor import EnhancedFieldExtractor
        
        # Initialize components
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME')
        )
        
        extractor = EnhancedFieldExtractor()
        print("✅ Theodore pipeline and extractor initialized")
        
        # Fetch all companies from Pinecone
        print("\n📊 Fetching companies with missing data...")
        query_result = pipeline.pinecone_client.index.query(
            vector=[0.0] * 1536,
            top_k=1000,
            include_metadata=True,
            include_values=False
        )
        
        # Identify companies with missing critical fields
        companies_needing_enhancement = []
        
        for match in query_result.matches:
            metadata = match.metadata or {}
            company_name = metadata.get('company_name', 'Unknown')
            
            missing_fields = []
            if not metadata.get('founding_year'):
                missing_fields.append('founding_year')
            if not metadata.get('location'):
                missing_fields.append('location')
            if not metadata.get('leadership_team'):
                missing_fields.append('leadership_team')
            if not metadata.get('contact_info'):
                missing_fields.append('contact_info')
            if not metadata.get('employee_count_range'):
                missing_fields.append('employee_count_range')
            
            if missing_fields:
                companies_needing_enhancement.append({
                    'id': match.id,
                    'name': company_name,
                    'metadata': metadata,
                    'missing_fields': missing_fields,
                    'raw_content': metadata.get('raw_content', '')
                })
        
        print(f"📈 Analysis Results:")
        print(f"   Total companies: {len(query_result.matches)}")
        print(f"   Companies needing enhancement: {len(companies_needing_enhancement)}")
        
        if not companies_needing_enhancement:
            print("✅ All companies have complete field data!")
            return
        
        # Process companies for enhancement
        batch_size = min(10, len(companies_needing_enhancement))
        companies_to_process = companies_needing_enhancement[:batch_size]
        
        print(f"\n🔍 Processing {len(companies_to_process)} companies for field enhancement...")
        
        successful_enhancements = 0
        field_improvements = {
            'founding_year': 0,
            'location': 0,
            'leadership_team': 0,
            'contact_info': 0,
            'employee_count_range': 0
        }
        
        for i, company_info in enumerate(companies_to_process):
            company_name = company_info['name']
            metadata = company_info['metadata']
            missing_fields = company_info['missing_fields']
            raw_content = company_info['raw_content']
            
            print(f"\n[{i+1}/{len(companies_to_process)}] 🔍 Enhancing: {company_name}")
            print(f"   Missing fields: {', '.join(missing_fields)}")
            
            try:
                # Use enhanced field extractor
                enhanced_data = extractor.enhance_company_data(metadata, raw_content)
                
                # Check what was improved
                improvements_made = []
                updated_metadata = metadata.copy()
                
                for field in missing_fields:
                    if field in enhanced_data and enhanced_data[field] and not metadata.get(field):
                        updated_metadata[field] = enhanced_data[field]
                        improvements_made.append(field)
                        field_improvements[field] += 1
                
                if improvements_made:
                    # Add enhancement timestamp
                    updated_metadata['field_enhancement_timestamp'] = datetime.now().isoformat()
                    updated_metadata['enhanced_fields'] = improvements_made
                    
                    # Update in Pinecone
                    pipeline.pinecone_client.index.update(
                        id=company_info['id'],
                        set_metadata=updated_metadata
                    )
                    
                    successful_enhancements += 1
                    print(f"   ✅ Enhanced fields: {', '.join(improvements_made)}")
                    
                    # Show what was extracted
                    for field in improvements_made:
                        value = enhanced_data[field]
                        if isinstance(value, list):
                            print(f"     {field}: {', '.join(value[:2])}{'...' if len(value) > 2 else ''}")
                        elif isinstance(value, dict):
                            print(f"     {field}: {list(value.keys())}")
                        else:
                            display_value = str(value)[:50] + '...' if len(str(value)) > 50 else str(value)
                            print(f"     {field}: {display_value}")
                else:
                    print(f"   ⚠️ No extractable data found in raw content")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print(f"\n🎉 Enhancement Summary:")
        print(f"   Companies processed: {len(companies_to_process)}")
        print(f"   Companies enhanced: {successful_enhancements}")
        print(f"   Success rate: {round(successful_enhancements/len(companies_to_process)*100, 1)}%")
        
        print(f"\n📊 Field Improvement Breakdown:")
        for field, count in field_improvements.items():
            if count > 0:
                print(f"   {field}: +{count} companies")
        
        print(f"\n💡 Recommendations:")
        if field_improvements['founding_year'] == 0:
            print("   - Consider targeted scraping of 'About' and 'History' pages for founding years")
        if field_improvements['location'] == 0:
            print("   - Focus on 'Contact' and footer sections for headquarters information")
        if field_improvements['leadership_team'] == 0:
            print("   - Scrape 'Team', 'Leadership', and 'About' pages for executive information")
        if field_improvements['contact_info'] == 0:
            print("   - Target 'Contact Us' pages and footer sections for contact details")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()