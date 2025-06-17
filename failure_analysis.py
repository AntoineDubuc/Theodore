#!/usr/bin/env python3
"""
Analyze where we consistently fail to extract data.
"""

import os
import sys
from typing import Dict, Any, List

sys.path.append('.')
from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Load environment
load_dotenv()

def analyze_extraction_failures():
    """Analyze where we consistently fail to extract data"""
    
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    # Get all companies
    companies = pipeline.pinecone_client.find_companies_by_filters({}, top_k=15)
    
    print("=" * 80)
    print("EXTRACTION FAILURE ANALYSIS")
    print("=" * 80)
    print(f"Analyzing {len(companies)} companies for consistent extraction failures")
    print()
    
    # Critical fields that should be extractable from most company websites
    critical_fields = {
        'founding_year': 'Company founding date',
        'location': 'Headquarters/main office location',
        'employee_count_range': 'Company size/employee count',
        'company_description': 'What the company does',
        'value_proposition': 'Key value offered to customers',
        'contact_info': 'Contact details (email, phone)',
        'social_media': 'Social media presence',
        'leadership_team': 'Key executives/founders',
        'key_services': 'Main products/services offered',
        'competitive_advantages': 'What makes them unique',
        'company_culture': 'Company values/culture',
        'tech_stack': 'Technologies they use',
        'funding_status': 'Investment/funding information',
        'awards': 'Recognition/achievements',
        'certifications': 'Industry certifications',
        'partnerships': 'Key business partnerships',
        'recent_news': 'Latest company news',
        'pain_points': 'Problems they solve'
    }
    
    def is_filled(value):
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip() != '' and value.lower() not in ['unknown', 'not specified', 'n/a', 'none', 'null']
        if isinstance(value, (list, dict)):
            return len(value) > 0
        if isinstance(value, bool):
            return True
        return bool(value)
    
    # Analyze extraction success rates
    field_stats = {}
    company_data = []
    
    for company in companies:
        metadata = company.get('metadata', {})
        company_name = metadata.get('company_name', 'Unknown')
        website = metadata.get('website', 'No website')
        
        company_fields = {}
        for field in critical_fields.keys():
            value = metadata.get(field)
            is_extracted = is_filled(value)
            company_fields[field] = is_extracted
            
            if field not in field_stats:
                field_stats[field] = {'success': 0, 'fail': 0, 'examples': []}
            
            if is_extracted:
                field_stats[field]['success'] += 1
                if len(field_stats[field]['examples']) < 3:
                    field_stats[field]['examples'].append((company_name, str(value)[:50]))
            else:
                field_stats[field]['fail'] += 1
        
        company_data.append({
            'name': company_name,
            'website': website,
            'fields': company_fields
        })
    
    # Calculate failure rates
    total_companies = len(companies)
    field_failure_rates = []
    
    for field, stats in field_stats.items():
        failure_rate = (stats['fail'] / total_companies) * 100
        success_rate = (stats['success'] / total_companies) * 100
        
        field_failure_rates.append({
            'field': field,
            'failure_rate': failure_rate,
            'success_rate': success_rate,
            'success_count': stats['success'],
            'fail_count': stats['fail'],
            'examples': stats['examples']
        })
    
    # Sort by failure rate (highest first)
    field_failure_rates.sort(key=lambda x: x['failure_rate'], reverse=True)
    
    print("🔴 CRITICAL EXTRACTION FAILURES (Worst performing fields):")
    print("=" * 80)
    
    worst_fields = [f for f in field_failure_rates if f['failure_rate'] >= 80]
    
    for field_data in worst_fields:
        field = field_data['field']
        failure_rate = field_data['failure_rate']
        success_count = field_data['success_count']
        
        print(f"\n❌ {field.replace('_', ' ').title()}")
        print(f"   Failure Rate: {failure_rate:.1f}% ({field_data['fail_count']}/{total_companies} companies)")
        print(f"   Description: {critical_fields[field]}")
        
        if field_data['examples']:
            print(f"   ✅ Rare successes: {', '.join([ex[0] for ex in field_data['examples']])}")
        else:
            print(f"   ❌ No successful extractions found")
    
    print(f"\n\n🟡 MODERATE FAILURES (50-80% failure rate):")
    print("=" * 50)
    
    moderate_fields = [f for f in field_failure_rates if 50 <= f['failure_rate'] < 80]
    
    for field_data in moderate_fields:
        field = field_data['field']
        failure_rate = field_data['failure_rate']
        success_rate = field_data['success_rate']
        
        print(f"⚠️  {field.replace('_', ' ').title()}: {failure_rate:.1f}% fail / {success_rate:.1f}% success")
    
    print(f"\n\n🟢 SUCCESS STORIES (< 50% failure rate):")
    print("=" * 50)
    
    success_fields = [f for f in field_failure_rates if f['failure_rate'] < 50]
    
    for field_data in success_fields:
        field = field_data['field']
        failure_rate = field_data['failure_rate']
        success_rate = field_data['success_rate']
        
        print(f"✅ {field.replace('_', ' ').title()}: {success_rate:.1f}% success / {failure_rate:.1f}% fail")
    
    # Analyze patterns in failures
    print(f"\n\n🔍 FAILURE PATTERN ANALYSIS:")
    print("=" * 80)
    
    # Companies with most failures
    company_failure_counts = []
    for company in company_data:
        failure_count = sum(1 for extracted in company['fields'].values() if not extracted)
        failure_rate = (failure_count / len(critical_fields)) * 100
        
        company_failure_counts.append({
            'name': company['name'],
            'website': company['website'],
            'failure_count': failure_count,
            'failure_rate': failure_rate
        })
    
    company_failure_counts.sort(key=lambda x: x['failure_rate'], reverse=True)
    
    print("Companies with highest extraction failure rates:")
    for company in company_failure_counts[:5]:
        print(f"• {company['name']}: {company['failure_rate']:.1f}% failure ({company['failure_count']}/{len(critical_fields)} fields missing)")
        print(f"  Website: {company['website']}")
    
    # Root cause analysis
    print(f"\n\n🎯 ROOT CAUSE ANALYSIS:")
    print("=" * 80)
    
    print("Most likely reasons for extraction failures:")
    print()
    
    print("1. 🏢 CORPORATE DATA LOCATIONS:")
    print("   • Founding year: Often in 'About Us' > 'History' or 'Our Story' sections")
    print("   • Location: May be in footer, contact page, or legal disclaimers")
    print("   • Employee count: Usually in company overview, LinkedIn, or job pages")
    print()
    
    print("2. 📞 CONTACT INFORMATION:")
    print("   • Contact info: Often requires parsing contact forms or 'Contact Us' pages")
    print("   • Social media: Links may be in footer or separate social media sections")
    print()
    
    print("3. 💼 BUSINESS INTELLIGENCE:")
    print("   • Value proposition: Scattered across homepage, about page, marketing copy")
    print("   • Competitive advantages: May require analysis of multiple pages")
    print("   • Company culture: Often in careers page or about section")
    print()
    
    print("4. 🔧 TECHNICAL CHALLENGES:")
    print("   • JavaScript-heavy sites: Content may not be in initial HTML")
    print("   • Dynamic content: Loaded after page render")
    print("   • Complex navigation: Information buried in subpages")
    print()
    
    print("5. 📈 IMPROVEMENT OPPORTUNITIES:")
    print("   • Better page selection: Target specific page types (about, contact, careers)")
    print("   • Enhanced prompts: More specific extraction instructions")
    print("   • Multi-page analysis: Combine data from multiple pages")
    print("   • Structured data parsing: Look for JSON-LD, microdata")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    analyze_extraction_failures()