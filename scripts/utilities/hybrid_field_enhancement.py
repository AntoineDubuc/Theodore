#!/usr/bin/env python3
"""
Hybrid Field Enhancement - Additive approach
1. Pattern matching first (fast, free)
2. LLM enhancement for missing fields (targeted AI usage)
3. Specialized re-scraping last resort (comprehensive but expensive)
"""

import os
import sys
from datetime import datetime
import json

# Add project root and src to path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def main():
    print("🔄 Hybrid Field Enhancement (Additive Approach)")
    print("=" * 60)
    
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Import Theodore components
        from src.main_pipeline import TheodoreIntelligencePipeline
        from src.models import CompanyIntelligenceConfig
        from src.enhanced_field_extractor import EnhancedFieldExtractor
        from src.bedrock_client import BedrockClient
        
        # Initialize components
        config = CompanyIntelligenceConfig()
        pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME')
        )
        
        extractor = EnhancedFieldExtractor()
        bedrock_client = BedrockClient(config)
        print("✅ Theodore pipeline, extractor, and AI client initialized")
        
        # Fetch companies with missing data
        print("\n📊 Fetching companies with missing critical fields...")
        query_result = pipeline.pinecone_client.index.query(
            vector=[0.0] * 1536,
            top_k=1000,
            include_metadata=True,
            include_values=False
        )
        
        # Identify enhancement candidates
        enhancement_candidates = []
        
        for match in query_result.matches:
            metadata = match.metadata or {}
            company_name = metadata.get('company_name', 'Unknown')
            
            # Check for missing critical fields
            missing_fields = []
            if not metadata.get('founding_year'):
                missing_fields.append('founding_year')
            if not metadata.get('location'):
                missing_fields.append('location')  
            if not metadata.get('leadership_team'):
                missing_fields.append('leadership_team')
            if not metadata.get('contact_info') or metadata.get('contact_info') == '':
                missing_fields.append('contact_info')
            if not metadata.get('employee_count_range'):
                missing_fields.append('employee_count_range')
            
            if missing_fields:
                enhancement_candidates.append({
                    'id': match.id,
                    'name': company_name,
                    'metadata': metadata,
                    'missing_fields': missing_fields,
                    'raw_content': metadata.get('raw_content', ''),
                    'company_description': metadata.get('company_description', ''),
                    'ai_summary': metadata.get('ai_summary', '')
                })
        
        print(f"📈 Enhancement Analysis:")
        print(f"   Total companies: {len(query_result.matches)}")
        print(f"   Companies needing enhancement: {len(enhancement_candidates)}")
        
        if not enhancement_candidates:
            print("✅ All companies have complete critical field data!")
            return
        
        # Process enhancement candidates
        batch_size = min(10, len(enhancement_candidates))
        companies_to_process = enhancement_candidates[:batch_size]
        
        print(f"\n🔄 Processing {len(companies_to_process)} companies with hybrid approach...")
        
        # Track improvements
        phase_stats = {
            'pattern_matching': {'total': 0, 'successful_fields': 0},
            'llm_enhancement': {'total': 0, 'successful_fields': 0, 'api_calls': 0},
            'companies_enhanced': 0
        }
        
        for i, company_info in enumerate(companies_to_process):
            company_name = company_info['name']
            metadata = company_info['metadata']
            missing_fields = company_info['missing_fields']
            raw_content = company_info['raw_content']
            
            print(f"\n[{i+1}/{len(companies_to_process)}] 🔄 Enhancing: {company_name}")
            print(f"   Missing fields: {', '.join(missing_fields)}")
            
            try:
                updated_metadata = metadata.copy()
                fields_found_this_company = []
                
                # PHASE 1: Pattern Matching Enhancement (Fast & Free)
                print(f"   📋 Phase 1: Pattern matching on existing content...")
                pattern_fields_found = []
                
                if raw_content:
                    enhanced_data = extractor.enhance_company_data(metadata, raw_content)
                    
                    for field in missing_fields:
                        if field in enhanced_data and enhanced_data[field] and not metadata.get(field):
                            updated_metadata[field] = enhanced_data[field]
                            pattern_fields_found.append(field)
                            fields_found_this_company.append(f"{field} (pattern)")
                            phase_stats['pattern_matching']['successful_fields'] += 1
                
                phase_stats['pattern_matching']['total'] += len(missing_fields)
                
                if pattern_fields_found:
                    print(f"      ✅ Pattern matching found: {', '.join(pattern_fields_found)}")
                else:
                    print(f"      ⚠️ Pattern matching: No extractable data")
                
                # PHASE 2: LLM Enhancement (Targeted AI for remaining fields)
                remaining_fields = [f for f in missing_fields if f not in pattern_fields_found]
                
                if remaining_fields and (raw_content or metadata.get('company_description') or metadata.get('ai_summary')):
                    print(f"   🤖 Phase 2: AI enhancement for remaining fields: {', '.join(remaining_fields)}")
                    
                    # Prepare content for AI analysis
                    ai_content = []
                    if metadata.get('company_description'):
                        ai_content.append(f"Description: {metadata['company_description']}")
                    if metadata.get('ai_summary'):
                        ai_content.append(f"Summary: {metadata['ai_summary']}")
                    if raw_content:
                        ai_content.append(f"Content: {raw_content[:1500]}")  # Limit content length
                    
                    if ai_content:
                        # Create targeted AI prompt
                        prompt = create_targeted_extraction_prompt(company_name, remaining_fields, '\\n\\n'.join(ai_content))
                        
                        try:
                            ai_response = bedrock_client.generate_text(prompt, max_tokens=300)
                            phase_stats['llm_enhancement']['api_calls'] += 1
                            
                            if ai_response:
                                ai_extracted_fields = parse_ai_response(ai_response, remaining_fields)
                                
                                for field, value in ai_extracted_fields.items():
                                    if value and str(value).lower() not in ['not found', 'unknown', 'n/a', 'none']:
                                        updated_metadata[field] = value
                                        fields_found_this_company.append(f"{field} (AI)")
                                        phase_stats['llm_enhancement']['successful_fields'] += 1
                                
                                if ai_extracted_fields:
                                    print(f"      ✅ AI enhancement found: {', '.join(ai_extracted_fields.keys())}")
                                else:
                                    print(f"      ⚠️ AI enhancement: No additional fields extracted")
                            else:
                                print(f"      ❌ AI enhancement: No response from model")
                                
                        except Exception as e:
                            print(f"      ❌ AI enhancement error: {e}")
                
                phase_stats['llm_enhancement']['total'] += len(remaining_fields)
                
                # Update if any fields were found
                if fields_found_this_company:
                    # Add enhancement metadata
                    updated_metadata['hybrid_enhancement_timestamp'] = datetime.now().isoformat()
                    updated_metadata['enhanced_fields'] = fields_found_this_company
                    updated_metadata['enhancement_method'] = 'hybrid_pattern_ai'
                    
                    # Update in Pinecone
                    pipeline.pinecone_client.index.update(
                        id=company_info['id'],
                        set_metadata=updated_metadata
                    )
                    
                    phase_stats['companies_enhanced'] += 1
                    print(f"   ✅ Enhanced with: {', '.join(fields_found_this_company)}")
                    
                    # Show extracted values (truncated)
                    for field_desc in fields_found_this_company:
                        field = field_desc.split(' (')[0]
                        value = updated_metadata.get(field)
                        if isinstance(value, dict):
                            display_value = f"{{{', '.join(list(value.keys())[:3])}}}"
                        elif isinstance(value, list):
                            display_value = f"[{', '.join(str(v)[:30] for v in value[:2])}{'...' if len(value) > 2 else ''}]"
                        else:
                            display_value = str(value)[:50] + ('...' if len(str(value)) > 50 else '')
                        print(f"      {field}: {display_value}")
                else:
                    print(f"   ⚠️ No additional fields could be extracted")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Print comprehensive summary
        print(f"\n🎉 Hybrid Enhancement Summary:")
        print(f"   Companies processed: {len(companies_to_process)}")
        print(f"   Companies enhanced: {phase_stats['companies_enhanced']}")
        print(f"   Success rate: {round(phase_stats['companies_enhanced']/len(companies_to_process)*100, 1)}%")
        
        print(f"\n📊 Method Effectiveness:")
        pattern_success_rate = (phase_stats['pattern_matching']['successful_fields'] / max(phase_stats['pattern_matching']['total'], 1)) * 100
        llm_success_rate = (phase_stats['llm_enhancement']['successful_fields'] / max(phase_stats['llm_enhancement']['total'], 1)) * 100
        
        print(f"   Pattern Matching: {phase_stats['pattern_matching']['successful_fields']}/{phase_stats['pattern_matching']['total']} fields ({pattern_success_rate:.1f}%)")
        print(f"   LLM Enhancement: {phase_stats['llm_enhancement']['successful_fields']}/{phase_stats['llm_enhancement']['total']} fields ({llm_success_rate:.1f}%)")
        print(f"   AI API calls made: {phase_stats['llm_enhancement']['api_calls']}")
        
        print(f"\n💡 Next Steps:")
        if phase_stats['companies_enhanced'] < len(companies_to_process) * 0.7:
            print("   - Consider Phase 3: Specialized re-scraping for remaining companies")
            print("   - Target specific page types (/about, /team, /contact) for missing fields")
        else:
            print("   - Hybrid approach was highly effective!")
            print("   - Consider running on remaining companies in the database")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def create_targeted_extraction_prompt(company_name: str, missing_fields, content: str) -> str:
    """Create a targeted AI prompt for specific missing fields"""
    
    field_descriptions = {
        'founding_year': 'founding year (4-digit year when company was established)',
        'location': 'headquarters location (city, state/country)',
        'leadership_team': 'leadership team (CEO, founders, executives with names and titles)',
        'contact_info': 'contact information (email, phone, address)',
        'employee_count_range': 'company size (employee count or range like "51-200")'
    }
    
    requested_fields = [field_descriptions.get(field, field) for field in missing_fields]
    
    prompt = f"""Analyze this company information and extract ONLY the following specific fields:

Company: {company_name}
Content: {content}

Extract these fields (respond "Not found" if information is not available):
{chr(10).join(f"- {field}" for field in requested_fields)}

Format your response exactly as:
founding_year: [4-digit year or Not found]
location: [City, State/Country or Not found]
leadership_team: [CEO Name - Title, Founder Name - Title, etc. or Not found]
contact_info: [email@company.com, +1-555-123-4567, address or Not found]
employee_count_range: [number range like "51-200" or Not found]

Only include fields that were requested above. Be factual and concise."""

    return prompt

def parse_ai_response(ai_response: str, requested_fields):
    """Parse AI response and extract field values"""
    extracted = {}
    
    for line in ai_response.split('\n'):
        line = line.strip()
        if ':' in line:
            field_key, field_value = line.split(':', 1)
            field_key = field_key.strip().lower()
            field_value = field_value.strip()
            
            # Map response keys to our field names
            field_mapping = {
                'founding_year': 'founding_year',
                'location': 'location',
                'leadership_team': 'leadership_team', 
                'contact_info': 'contact_info',
                'employee_count_range': 'employee_count_range'
            }
            
            mapped_field = field_mapping.get(field_key)
            if mapped_field in requested_fields and field_value.lower() not in ['not found', 'unknown', 'n/a']:
                # Process specific field types
                if mapped_field == 'founding_year':
                    try:
                        year = int(field_value)
                        if 1800 <= year <= datetime.now().year:
                            extracted[mapped_field] = year
                    except ValueError:
                        pass
                elif mapped_field == 'leadership_team':
                    # Split leadership into list
                    if ',' in field_value:
                        leaders = [leader.strip() for leader in field_value.split(',')]
                        extracted[mapped_field] = leaders[:5]  # Limit to 5 leaders
                    else:
                        extracted[mapped_field] = [field_value]
                elif mapped_field == 'contact_info':
                    # Parse contact info into dict
                    contact_dict = {}
                    if '@' in field_value:
                        # Extract email
                        import re
                        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', field_value)
                        if email_match:
                            contact_dict['email'] = email_match.group()
                    if any(char.isdigit() for char in field_value):
                        # Has phone number or address
                        contact_dict['details'] = field_value
                    
                    if contact_dict:
                        extracted[mapped_field] = json.dumps(contact_dict)
                else:
                    extracted[mapped_field] = field_value
    
    return extracted

if __name__ == "__main__":
    main()