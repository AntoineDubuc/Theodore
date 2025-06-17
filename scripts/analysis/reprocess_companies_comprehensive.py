#!/usr/bin/env python3
"""
Comprehensive company reprocessing script for Theodore.
This will reprocess all 10 companies and provide detailed before/after comparison.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any

sys.path.append('.')
from dotenv import load_dotenv
from src.models import CompanyIntelligenceConfig
from src.main_pipeline import TheodoreIntelligencePipeline

# Load environment
load_dotenv()

def safe_get_field(data: Dict, field: str, default: Any = None) -> Any:
    """Safely get field from company data"""
    if isinstance(data, dict):
        return data.get(field, default)
    return getattr(data, field, default) if hasattr(data, field) else default

def format_field_value(value: Any) -> str:
    """Format field value for display"""
    if value is None:
        return "None"
    elif isinstance(value, list):
        if not value:
            return "[]"
        return f"[{len(value)} items]: {', '.join(str(v)[:50] for v in value[:3])}{'...' if len(value) > 3 else ''}"
    elif isinstance(value, dict):
        if not value:
            return "{}"
        return f"{{keys: {list(value.keys())[:3]}{'...' if len(value) > 3 else ''}}}"
    elif isinstance(value, str):
        if not value.strip():
            return "Empty"
        return f"'{value[:100]}{'...' if len(value) > 100 else ''}'"
    else:
        return str(value)

def get_companies_from_database(pipeline) -> List[Dict]:
    """Get all companies from Pinecone database"""
    try:
        # Query all vectors with a high limit
        query_result = pipeline.pinecone_client.index.query(
            vector=[0.0] * 1536,  # Dummy vector
            top_k=50,  # Get all companies
            include_metadata=True,
            include_values=False
        )
        
        companies = []
        for match in query_result.matches:
            companies.append({
                'id': match.id,
                'name': match.metadata.get('company_name', 'Unknown'),
                'website': match.metadata.get('website', ''),
                'metadata': match.metadata
            })
        
        print(f"✅ Retrieved {len(companies)} companies from database")
        return companies
        
    except Exception as e:
        print(f"❌ Error retrieving companies: {e}")
        return []

def analyze_field_coverage(companies: List[Dict], field_name: str) -> Dict:
    """Analyze coverage of a specific field across companies"""
    total = len(companies)
    populated = 0
    empty = 0
    none_values = 0
    
    for company in companies:
        value = safe_get_field(company['metadata'], field_name)
        if value is None:
            none_values += 1
        elif isinstance(value, (list, dict)) and not value:
            empty += 1
        elif isinstance(value, str) and not value.strip():
            empty += 1
        else:
            populated += 1
    
    return {
        'total': total,
        'populated': populated,
        'empty': empty,
        'none_values': none_values,
        'coverage_rate': (populated / total * 100) if total > 0 else 0
    }

def comprehensive_reprocessing():
    """Main reprocessing function"""
    print("=" * 80)
    print("COMPREHENSIVE COMPANY REPROCESSING - THEODORE")
    print("=" * 80)
    
    # Initialize pipeline
    config = CompanyIntelligenceConfig()
    pipeline = TheodoreIntelligencePipeline(
        config=config,
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
        pinecone_index=os.getenv('PINECONE_INDEX_NAME')
    )
    
    # Step 1: Get current state of all companies
    print("\n📊 STEP 1: ANALYZING CURRENT DATABASE STATE")
    print("-" * 50)
    
    companies_before = get_companies_from_database(pipeline)
    if not companies_before:
        print("❌ No companies found in database. Exiting.")
        return
    
    print(f"Found {len(companies_before)} companies in database:")
    for i, company in enumerate(companies_before, 1):
        print(f"  {i}. {company['name']} ({company['website']})")
    
    # Analyze field coverage BEFORE reprocessing
    critical_fields = [
        'products_services_offered', 'job_listings_count', 'job_listings', 
        'job_listings_details', 'leadership_team', 'location', 'founding_year',
        'company_culture', 'partnerships', 'contact_info', 'value_proposition'
    ]
    
    print(f"\n📈 FIELD COVERAGE ANALYSIS - BEFORE REPROCESSING")
    print("-" * 50)
    coverage_before = {}
    for field in critical_fields:
        coverage = analyze_field_coverage(companies_before, field)
        coverage_before[field] = coverage
        print(f"{field:25} | {coverage['populated']:2}/{coverage['total']:2} populated ({coverage['coverage_rate']:5.1f}%)")
    
    # Step 2: Reprocess each company
    print(f"\n🔄 STEP 2: REPROCESSING ALL {len(companies_before)} COMPANIES")
    print("-" * 50)
    
    reprocessing_results = []
    
    for i, company in enumerate(companies_before, 1):
        print(f"\n🔄 [{i}/{len(companies_before)}] Reprocessing: {company['name']}")
        
        try:
            # Reprocess the company
            updated_company = pipeline.process_single_company(
                company['name'], 
                company['website']
            )
            
            if updated_company:
                print(f"   ✅ Successfully reprocessed {company['name']}")
                print(f"   📊 Scrape status: {updated_company.scrape_status}")
                print(f"   📝 Job listings: {updated_company.job_listings_count or 0} openings")
                print(f"   🏢 Products/Services: {len(updated_company.products_services_offered or [])} items")
                
                reprocessing_results.append({
                    'company': company,
                    'status': 'success',
                    'updated_data': updated_company,
                    'error': None
                })
            else:
                print(f"   ⚠️ Reprocessing returned None for {company['name']}")
                reprocessing_results.append({
                    'company': company,
                    'status': 'failed',
                    'updated_data': None,
                    'error': 'Reprocessing returned None'
                })
                
        except Exception as e:
            print(f"   ❌ Error reprocessing {company['name']}: {e}")
            reprocessing_results.append({
                'company': company,
                'status': 'error',
                'updated_data': None,
                'error': str(e)
            })
    
    # Step 3: Get updated state and compare
    print(f"\n📊 STEP 3: ANALYZING UPDATED DATABASE STATE")
    print("-" * 50)
    
    companies_after = get_companies_from_database(pipeline)
    
    print(f"\n📈 FIELD COVERAGE ANALYSIS - AFTER REPROCESSING")
    print("-" * 50)
    coverage_after = {}
    for field in critical_fields:
        coverage = analyze_field_coverage(companies_after, field)
        coverage_after[field] = coverage
        before_rate = coverage_before[field]['coverage_rate']
        after_rate = coverage['coverage_rate']
        improvement = after_rate - before_rate
        
        status = "📈" if improvement > 0 else "📉" if improvement < 0 else "➡️"
        print(f"{field:25} | {coverage['populated']:2}/{coverage['total']:2} populated ({coverage['coverage_rate']:5.1f}%) {status} {improvement:+5.1f}%")
    
    # Step 4: Detailed comparison report
    print(f"\n📋 STEP 4: DETAILED IMPROVEMENT ANALYSIS")
    print("=" * 80)
    
    successful_reprocessing = [r for r in reprocessing_results if r['status'] == 'success']
    failed_reprocessing = [r for r in reprocessing_results if r['status'] != 'success']
    
    print(f"📊 REPROCESSING SUMMARY:")
    print(f"   ✅ Successful: {len(successful_reprocessing)}/{len(companies_before)}")
    print(f"   ❌ Failed: {len(failed_reprocessing)}/{len(companies_before)}")
    print(f"   📈 Success Rate: {len(successful_reprocessing)/len(companies_before)*100:.1f}%")
    
    if failed_reprocessing:
        print(f"\n❌ FAILED COMPANIES:")
        for result in failed_reprocessing:
            print(f"   • {result['company']['name']}: {result['error']}")
    
    # Calculate overall improvement
    total_improvements = sum(1 for field in critical_fields 
                           if coverage_after[field]['coverage_rate'] > coverage_before[field]['coverage_rate'])
    
    print(f"\n📈 OVERALL IMPROVEMENTS:")
    print(f"   🎯 Fields Improved: {total_improvements}/{len(critical_fields)}")
    
    # Show biggest improvements
    improvements = [(field, coverage_after[field]['coverage_rate'] - coverage_before[field]['coverage_rate']) 
                   for field in critical_fields]
    improvements.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n🏆 TOP IMPROVEMENTS:")
    for field, improvement in improvements[:5]:
        if improvement > 0:
            before_count = coverage_before[field]['populated']
            after_count = coverage_after[field]['populated']
            print(f"   • {field}: +{improvement:.1f}% ({before_count} → {after_count} companies)")
    
    # Step 5: Sample detailed data comparison
    print(f"\n🔍 STEP 5: SAMPLE DETAILED DATA EXAMPLES")
    print("-" * 50)
    
    # Show detailed examples for first 3 companies
    for i, company_after in enumerate(companies_after[:3]):
        company_before = next((c for c in companies_before if c['id'] == company_after['id']), None)
        if not company_before:
            continue
            
        print(f"\n📋 DETAILED COMPARISON - {company_after['name']}")
        print("-" * 40)
        
        for field in critical_fields[:6]:  # Show first 6 fields
            before_val = safe_get_field(company_before['metadata'], field)
            after_val = safe_get_field(company_after['metadata'], field)
            
            before_str = format_field_value(before_val)
            after_str = format_field_value(after_val)
            
            if before_str != after_str:
                print(f"  {field}:")
                print(f"    Before: {before_str}")
                print(f"    After:  {after_str}")
            else:
                print(f"  {field}: No change ({before_str})")
    
    print(f"\n🎉 COMPREHENSIVE REPROCESSING COMPLETE!")
    print(f"   📊 Total companies processed: {len(companies_before)}")
    print(f"   ✅ Successful updates: {len(successful_reprocessing)}")
    print(f"   📈 Fields improved: {total_improvements}")
    print(f"   🎯 Check the web interface at http://localhost:5002 to see updated data!")
    
    return {
        'companies_before': companies_before,
        'companies_after': companies_after,
        'coverage_before': coverage_before,
        'coverage_after': coverage_after,
        'reprocessing_results': reprocessing_results,
        'successful_count': len(successful_reprocessing),
        'total_improvements': total_improvements
    }

if __name__ == "__main__":
    results = comprehensive_reprocessing()