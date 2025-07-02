#!/usr/bin/env python3
"""
Field Extraction Analysis - Before vs After Enhancement
Analyze field extraction success rates across all CompanyData fields
"""

import asyncio
import sys
import os
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models import CompanyData, CompanyIntelligenceConfig
from intelligent_company_scraper import IntelligentCompanyScraper

def analyze_field_extraction(company_data: CompanyData) -> Dict[str, Any]:
    """Analyze field extraction success for a CompanyData instance"""
    
    # All fields in CompanyData model
    all_fields = {
        # Basic info (4 fields)
        'name': company_data.name,
        'website': company_data.website,
        'industry': company_data.industry,
        'business_model': company_data.business_model,
        
        # Company details (8 fields)
        'company_size': company_data.company_size,
        'company_description': company_data.company_description,
        'value_proposition': company_data.value_proposition,
        'founding_year': company_data.founding_year,
        'location': company_data.location,
        'employee_count_range': company_data.employee_count_range,
        'company_culture': company_data.company_culture,
        'funding_status': company_data.funding_status,
        
        # Business intelligence (8 fields)
        'tech_stack': company_data.tech_stack,
        'pain_points': company_data.pain_points,
        'key_services': company_data.key_services,
        'competitive_advantages': company_data.competitive_advantages,
        'target_market': company_data.target_market,
        'business_model_framework': company_data.business_model_framework,
        'products_services_offered': company_data.products_services_offered,
        'certifications': company_data.certifications,
        
        # Contact & team (6 fields)
        'contact_info': company_data.contact_info,
        'social_media': company_data.social_media,
        'leadership_team': company_data.leadership_team,
        'key_decision_makers': company_data.key_decision_makers,
        'partnerships': company_data.partnerships,
        'awards': company_data.awards,
        
        # Technology features (2 fields)
        'has_chat_widget': company_data.has_chat_widget,
        'has_forms': company_data.has_forms,
        
        # Job information (4 fields)
        'has_job_listings': company_data.has_job_listings,
        'job_listings_count': company_data.job_listings_count,
        'job_listings': company_data.job_listings,
        'job_listings_details': company_data.job_listings_details,
        
        # News & marketing (3 fields)
        'recent_news': company_data.recent_news,
        'recent_news_events': company_data.recent_news_events,
        'sales_marketing_tools': company_data.sales_marketing_tools,
        
        # Classification (6 fields)
        'saas_classification': company_data.saas_classification,
        'classification_confidence': company_data.classification_confidence,
        'classification_justification': company_data.classification_justification,
        'is_saas': company_data.is_saas,
        'funding_stage_detailed': company_data.funding_stage_detailed,
        'business_model_type': company_data.business_model_type,
        
        # Similarity metrics (6 fields) 
        'company_stage': company_data.company_stage,
        'tech_sophistication': company_data.tech_sophistication,
        'geographic_scope': company_data.geographic_scope,
        'decision_maker_type': company_data.decision_maker_type,
        'sales_complexity': company_data.sales_complexity,
        'stage_confidence': company_data.stage_confidence,
        
        # Crawling metrics (3 fields)
        'pages_crawled': company_data.pages_crawled,
        'crawl_depth': company_data.crawl_depth,
        'scraped_urls': company_data.scraped_urls,
    }
    
    # Count successful extractions
    successful_fields = 0
    failed_fields = 0
    field_details = {}
    
    for field_name, field_value in all_fields.items():
        extracted = False
        
        if field_value is not None:
            if isinstance(field_value, str) and field_value.strip():
                extracted = True
            elif isinstance(field_value, (list, dict)) and len(field_value) > 0:
                extracted = True
            elif isinstance(field_value, (int, float)) and field_value > 0:
                extracted = True
            elif isinstance(field_value, bool):
                extracted = True  # Booleans count as extracted regardless of value
        
        if extracted:
            successful_fields += 1
        else:
            failed_fields += 1
            
        field_details[field_name] = {
            'extracted': extracted,
            'value_type': type(field_value).__name__,
            'has_content': bool(field_value) if field_value is not None else False
        }
    
    total_fields = len(all_fields)
    success_rate = successful_fields / total_fields if total_fields > 0 else 0
    
    return {
        'total_fields': total_fields,
        'successful_fields': successful_fields,
        'failed_fields': failed_fields,
        'success_rate': success_rate,
        'field_details': field_details,
        'key_extractions': {
            'basic_info': sum(1 for field in ['industry', 'business_model', 'company_description', 'founding_year'] 
                            if field_details[field]['extracted']),
            'business_intelligence': sum(1 for field in ['pain_points', 'key_services', 'competitive_advantages', 'target_market'] 
                                       if field_details[field]['extracted']),
            'contact_team': sum(1 for field in ['contact_info', 'leadership_team', 'social_media'] 
                              if field_details[field]['extracted']),
            'technology': sum(1 for field in ['tech_stack', 'has_chat_widget', 'has_forms'] 
                            if field_details[field]['extracted']),
        }
    }

async def test_field_extraction_rates():
    """Test field extraction with enhanced crawling"""
    print("🔬 FIELD EXTRACTION ANALYSIS - Enhanced Crawling")
    print("=" * 60)
    print("Analyzing field extraction success rates across CompanyData model")
    print("Total fields to extract: 50+ comprehensive business intelligence fields")
    print("=" * 60)
    
    # Test companies
    test_companies = [
        {'name': 'Anthropic', 'website': 'https://anthropic.com'},
        {'name': 'Stripe', 'website': 'https://stripe.com'},
        {'name': 'Airbnb', 'website': 'https://airbnb.com'}
    ]
    
    config = CompanyIntelligenceConfig()
    scraper = IntelligentCompanyScraper(config)
    
    results = []
    
    for i, company in enumerate(test_companies, 1):
        print(f"\n🔬 FIELD EXTRACTION TEST {i}/3: {company['name']}")
        print(f"🌐 Website: {company['website']}")
        
        # Create company data
        company_data = CompanyData(name=company['name'], website=company['website'])
        
        start_time = time.time()
        
        try:
            # Run enhanced scraping with timeout
            result_data = await asyncio.wait_for(
                scraper.scrape_company_intelligent(company_data),
                timeout=180  # 3 minute timeout
            )
            
            processing_time = time.time() - start_time
            
            # Analyze field extraction
            field_analysis = analyze_field_extraction(result_data)
            field_analysis['company'] = company
            field_analysis['processing_time'] = processing_time
            field_analysis['success'] = True
            
            results.append(field_analysis)
            
            print(f"✅ Processing complete: {processing_time:.1f}s")
            print(f"📊 Field extraction: {field_analysis['successful_fields']}/{field_analysis['total_fields']} ({field_analysis['success_rate']:.1%})")
            print(f"🎯 Key categories:")
            print(f"   • Basic info: {field_analysis['key_extractions']['basic_info']}/4 fields")
            print(f"   • Business intelligence: {field_analysis['key_extractions']['business_intelligence']}/4 fields")
            print(f"   • Contact & team: {field_analysis['key_extractions']['contact_team']}/3 fields")
            print(f"   • Technology: {field_analysis['key_extractions']['technology']}/3 fields")
            
        except asyncio.TimeoutError:
            processing_time = time.time() - start_time
            print(f"⏰ Timeout after {processing_time:.1f}s")
            results.append({
                'company': company,
                'success': False,
                'error': 'Timeout',
                'processing_time': processing_time,
                'total_fields': 50,
                'successful_fields': 0,
                'success_rate': 0.0
            })
            
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"❌ Error: {e}")
            results.append({
                'company': company,
                'success': False,
                'error': str(e),
                'processing_time': processing_time,
                'total_fields': 50,
                'successful_fields': 0,
                'success_rate': 0.0
            })
        
        if i < len(test_companies):
            print("⏳ Waiting 5 seconds...")
            await asyncio.sleep(5)
    
    # Generate field extraction report
    generate_field_extraction_report(results)
    
    return results

def generate_field_extraction_report(results: List[Dict[str, Any]]):
    """Generate comprehensive field extraction report"""
    print("\n" + "=" * 80)
    print("📊 FIELD EXTRACTION SUCCESS ANALYSIS")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Calculate aggregate metrics
    successful_tests = [r for r in results if r.get('success', False)]
    
    if successful_tests:
        avg_success_rate = sum(r['success_rate'] for r in successful_tests) / len(successful_tests)
        avg_fields_extracted = sum(r['successful_fields'] for r in successful_tests) / len(successful_tests)
        total_fields = successful_tests[0]['total_fields'] if successful_tests else 50
        
        print(f"\n📈 ENHANCED CRAWLING FIELD EXTRACTION RESULTS:")
        print(f"   • Average success rate: {avg_success_rate:.1%}")
        print(f"   • Average fields extracted: {avg_fields_extracted:.1f}/{total_fields}")
        print(f"   • Processing success rate: {len(successful_tests)}/{len(results)}")
    
    # Before vs After comparison
    print(f"\n📊 BEFORE vs AFTER FIELD EXTRACTION:")
    print(f"   BEFORE (Pre-Enhancement):")
    print(f"   • Success rate: 0% (no data extracted)")
    print(f"   • Fields extracted: 0/50+ fields") 
    print(f"   • Error: 'No links discovered during crawling'")
    
    if successful_tests:
        print(f"   AFTER (Enhanced Crawling):")
        print(f"   • Success rate: {avg_success_rate:.1%}")
        print(f"   • Fields extracted: {avg_fields_extracted:.1f}/50+ fields")
        print(f"   • Improvement: +{avg_success_rate*100:.1f}% field extraction rate")
        print(f"   • Field coverage: {avg_fields_extracted/total_fields:.1%} of all available fields")
    
    # Company-by-company breakdown
    print(f"\n📋 DETAILED FIELD EXTRACTION BY COMPANY:")
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        company_name = result['company']['name']
        print(f"\n{i}. {company_name}")
        
        if result.get('success', False):
            success_rate = result['success_rate']
            fields_extracted = result['successful_fields']
            total_fields = result['total_fields']
            
            print(f"   📊 Overall: {fields_extracted}/{total_fields} fields ({success_rate:.1%})")
            
            if 'key_extractions' in result:
                key_ext = result['key_extractions']
                print(f"   📈 Category breakdown:")
                print(f"      • Basic info: {key_ext['basic_info']}/4 fields ({key_ext['basic_info']/4:.1%})")
                print(f"      • Business intelligence: {key_ext['business_intelligence']}/4 fields ({key_ext['business_intelligence']/4:.1%})")
                print(f"      • Contact & team: {key_ext['contact_team']}/3 fields ({key_ext['contact_team']/3:.1%})")
                print(f"      • Technology: {key_ext['technology']}/3 fields ({key_ext['technology']/3:.1%})")
            
            print(f"   ⏱️  Processing time: {result['processing_time']:.1f}s")
            
        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
            print(f"   ⏱️  Time: {result['processing_time']:.1f}s")
    
    # Field extraction impact assessment
    if successful_tests:
        # Calculate improvement metrics
        avg_basic_info = sum(r.get('key_extractions', {}).get('basic_info', 0) for r in successful_tests) / len(successful_tests)
        avg_business_intel = sum(r.get('key_extractions', {}).get('business_intelligence', 0) for r in successful_tests) / len(successful_tests)
        avg_contact_team = sum(r.get('key_extractions', {}).get('contact_team', 0) for r in successful_tests) / len(successful_tests)
        
        print(f"\n🎯 FIELD CATEGORY PERFORMANCE:")
        print(f"   • Basic company info: {avg_basic_info:.1f}/4 ({avg_basic_info/4:.1%} success)")
        print(f"   • Business intelligence: {avg_business_intel:.1f}/4 ({avg_business_intel/4:.1%} success)")
        print(f"   • Contact & team data: {avg_contact_team:.1f}/3 ({avg_contact_team/3:.1%} success)")
        
        # Overall impact assessment
        if avg_success_rate > 0.6:
            impact = "🚀 EXCELLENT"
        elif avg_success_rate > 0.4:
            impact = "✅ GOOD"
        elif avg_success_rate > 0.2:
            impact = "⚠️ MODERATE"
        else:
            impact = "❌ NEEDS IMPROVEMENT"
            
        print(f"\n📈 FIELD EXTRACTION IMPACT: {impact}")
        print(f"   Enhanced crawling achieves {avg_success_rate:.1%} field extraction success")
        print(f"   vs 0% with pre-enhancement system")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"field_extraction_analysis_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed analysis saved: {filename}")
    print("=" * 80)
    print("🔬 Field extraction analysis complete!")

if __name__ == "__main__":
    asyncio.run(test_field_extraction_rates())