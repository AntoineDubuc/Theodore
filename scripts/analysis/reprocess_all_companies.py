#!/usr/bin/env python3
"""
Reprocess all 10 companies with enhanced extraction and compare before/after results.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

sys.path.append('.')
from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Load environment
load_dotenv()

def reprocess_and_compare():
    """Reprocess all companies and show detailed before/after comparison"""
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    # All critical fields we want to track
    critical_fields = [
        'founding_year', 'location', 'employee_count_range', 'company_description',
        'value_proposition', 'target_market', 'tech_stack', 'competitive_advantages',
        'leadership_team', 'contact_info', 'social_media', 'key_services',
        'products_services_offered', 'pain_points', 'company_culture',
        'funding_status', 'partnerships', 'awards', 'recent_news'
    ]
    
    def is_filled(value):
        """Check if a field has meaningful data"""
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip() != '' and value.lower() not in ['unknown', 'not specified', 'n/a', 'none']
        if isinstance(value, (list, dict)):
            return len(value) > 0
        if isinstance(value, bool):
            return True
        if isinstance(value, (int, float)):
            return value > 0
        return bool(value)
    
    def analyze_completeness(metadata):
        """Analyze field completeness"""
        filled_fields = []
        empty_fields = []
        
        for field in critical_fields:
            value = metadata.get(field)
            if is_filled(value):
                filled_fields.append(field)
            else:
                empty_fields.append(field)
        
        return {
            'filled_count': len(filled_fields),
            'empty_count': len(empty_fields),
            'completeness': (len(filled_fields) / len(critical_fields)) * 100,
            'filled_fields': filled_fields,
            'empty_fields': empty_fields
        }
    
    # Get all companies
    companies = pipeline.pinecone_client.find_companies_by_filters({}, top_k=15)
    
    print("=" * 80)
    print("REPROCESSING ALL COMPANIES WITH ENHANCED EXTRACTION")
    print("=" * 80)
    print(f"Found {len(companies)} companies to reprocess")
    print(f"Tracking {len(critical_fields)} critical fields")
    print()
    
    results = []
    
    for i, company in enumerate(companies[:10], 1):  # Process first 10
        metadata = company.get('metadata', {})
        company_name = metadata.get('company_name', f'Company_{i}')
        website = metadata.get('website', 'No website')
        
        print(f"\n{'='*60}")
        print(f"{i:2d}. PROCESSING: {company_name}")
        print(f"{'='*60}")
        print(f"Website: {website}")
        
        # Analyze BEFORE state
        before_analysis = analyze_completeness(metadata)
        print(f"\n📊 BEFORE - Completeness: {before_analysis['completeness']:.1f}% ({before_analysis['filled_count']}/{len(critical_fields)} fields)")
        
        if before_analysis['filled_fields']:
            print(f"✅ Had: {', '.join(before_analysis['filled_fields'][:5])}{'...' if len(before_analysis['filled_fields']) > 5 else ''}")
        
        # Reprocess the company
        try:
            print(f"\n🔄 Reprocessing {company_name}...")
            
            # Extract website URL properly
            if website and website != 'No website':
                website_url = website
            else:
                website_url = f"https://{company_name.lower().replace(' ', '').replace('.com', '')}.com"
            
            # Reprocess with enhanced extraction
            updated_company = pipeline.process_single_company(company_name, website_url)
            
            # Get the updated data from database
            fresh_company = pipeline.pinecone_client.find_company_by_name(company_name)
            
            if fresh_company:
                updated_metadata = fresh_company.__dict__ if hasattr(fresh_company, '__dict__') else {}
                
                # Clean up datetime objects for analysis
                for key, value in updated_metadata.items():
                    if hasattr(value, 'isoformat'):  # datetime object
                        updated_metadata[key] = value.isoformat()
                
                # Analyze AFTER state
                after_analysis = analyze_completeness(updated_metadata)
                improvement = after_analysis['filled_count'] - before_analysis['filled_count']
                
                print(f"✅ AFTER  - Completeness: {after_analysis['completeness']:.1f}% ({after_analysis['filled_count']}/{len(critical_fields)} fields)")
                print(f"📈 IMPROVEMENT: {improvement:+d} fields ({after_analysis['completeness'] - before_analysis['completeness']:+.1f}%)")
                
                # Show newly filled fields
                new_fields = set(after_analysis['filled_fields']) - set(before_analysis['filled_fields'])
                if new_fields:
                    print(f"🆕 NEW FIELDS: {', '.join(sorted(new_fields))}")
                    
                    # Show specific valuable new data
                    valuable_new = []
                    for field in ['leadership_team', 'founding_year', 'location', 'contact_info']:
                        if field in new_fields:
                            value = updated_metadata.get(field)
                            if field == 'leadership_team' and isinstance(value, list):
                                valuable_new.append(f"Leadership: {', '.join(value[:2])}")
                            elif field == 'founding_year':
                                valuable_new.append(f"Founded: {value}")
                            elif field == 'location':
                                valuable_new.append(f"Location: {value}")
                            elif field == 'contact_info' and isinstance(value, dict):
                                if value.get('email'):
                                    valuable_new.append(f"Email: {value['email']}")
                    
                    if valuable_new:
                        print(f"💎 KEY DATA: {' | '.join(valuable_new)}")
                else:
                    print(f"❌ No new fields extracted")
                
                # Store results
                results.append({
                    'company_name': company_name,
                    'website': website,
                    'before': before_analysis,
                    'after': after_analysis,
                    'improvement': improvement,
                    'new_fields': list(new_fields),
                    'sample_data': {
                        'leadership_team': updated_metadata.get('leadership_team'),
                        'founding_year': updated_metadata.get('founding_year'),
                        'location': updated_metadata.get('location'),
                        'contact_info': updated_metadata.get('contact_info'),
                        'social_media': updated_metadata.get('social_media')
                    }
                })
                
        except Exception as e:
            print(f"❌ Error processing {company_name}: {e}")
            results.append({
                'company_name': company_name,
                'website': website,
                'before': before_analysis,
                'after': before_analysis,  # No change due to error
                'improvement': 0,
                'new_fields': [],
                'error': str(e)
            })
    
    # Generate comprehensive summary
    print(f"\n\n{'='*80}")
    print("COMPREHENSIVE IMPROVEMENT SUMMARY")
    print(f"{'='*80}")
    
    # Overall statistics
    total_improvements = sum(r['improvement'] for r in results if 'error' not in r)
    successful_companies = len([r for r in results if 'error' not in r and r['improvement'] > 0])
    avg_before = sum(r['before']['completeness'] for r in results) / len(results)
    avg_after = sum(r['after']['completeness'] for r in results) / len(results)
    
    print(f"📊 OVERALL RESULTS:")
    print(f"   Companies processed: {len(results)}")
    print(f"   Companies improved: {successful_companies}")
    print(f"   Total new fields: {total_improvements}")
    print(f"   Average completeness: {avg_before:.1f}% → {avg_after:.1f}% ({avg_after-avg_before:+.1f}%)")
    
    # Field-by-field success rates
    field_improvements = {}
    for field in critical_fields:
        before_count = sum(1 for r in results if field in r['before']['filled_fields'])
        after_count = sum(1 for r in results if field in r['after']['filled_fields'])
        improvement = after_count - before_count
        field_improvements[field] = {
            'before': before_count,
            'after': after_count,
            'improvement': improvement,
            'success_rate': (after_count / len(results)) * 100
        }
    
    print(f"\n🏆 BIGGEST IMPROVEMENTS:")
    sorted_improvements = sorted(field_improvements.items(), key=lambda x: x[1]['improvement'], reverse=True)
    for field, stats in sorted_improvements[:8]:
        if stats['improvement'] > 0:
            print(f"   {field:25}: {stats['before']} → {stats['after']} (+{stats['improvement']}) - {stats['success_rate']:.0f}% success")
    
    print(f"\n❌ STILL CHALLENGING:")
    for field, stats in sorted_improvements[-5:]:
        if stats['after'] < len(results) * 0.5:  # Less than 50% success
            print(f"   {field:25}: {stats['success_rate']:.0f}% success rate ({stats['after']}/{len(results)} companies)")
    
    # Show specific examples of extracted data
    print(f"\n💎 SAMPLE EXTRACTED DATA:")
    for result in results[:3]:  # Show first 3 companies
        if 'error' not in result and result['improvement'] > 0:
            print(f"\n   {result['company_name']}:")
            sample = result['sample_data']
            if sample['leadership_team']:
                print(f"     👥 Leadership: {sample['leadership_team']}")
            if sample['founding_year']:
                print(f"     📅 Founded: {sample['founding_year']}")
            if sample['location']:
                print(f"     📍 Location: {sample['location']}")
            if sample['contact_info'] and isinstance(sample['contact_info'], dict):
                if sample['contact_info'].get('email'):
                    print(f"     📧 Email: {sample['contact_info']['email']}")
    
    # Save detailed results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"enhanced_extraction_results_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump({
            'analysis_date': datetime.now().isoformat(),
            'companies_processed': len(results),
            'critical_fields': critical_fields,
            'summary': {
                'total_improvements': total_improvements,
                'avg_before': avg_before,
                'avg_after': avg_after,
                'successful_companies': successful_companies
            },
            'results': results,
            'field_improvements': field_improvements
        }, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {filename}")
    print("=" * 80)

if __name__ == "__main__":
    reprocess_and_compare()