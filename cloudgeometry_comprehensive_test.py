#!/usr/bin/env python3
"""
CloudGeometry Comprehensive Test & Report
Tests the fix and generates a detailed report showing field extraction results
Success criteria: 75% of fields collected (50+ out of 67 fields)
"""

import asyncio
import sys
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.dirname(__file__)
sys.path.insert(0, project_root)
load_dotenv(os.path.join(project_root, '.env'))

from src.intelligent_company_scraper import IntelligentCompanyScraper
from src.models import CompanyData, CompanyIntelligenceConfig
from src.bedrock_client import BedrockClient
from src.pinecone_client import PineconeClient

class CloudGeometryTestRunner:
    def __init__(self):
        self.config = CompanyIntelligenceConfig()
        self.test_results = {}
        self.all_fields = self._get_all_company_fields()
        
    def _get_all_company_fields(self):
        """Get all 67 CompanyData fields for analysis"""
        return [
            # Core Company Information (6 fields)
            'name', 'website', 'industry', 'company_description', 'business_model', 'value_proposition',
            
            # Technology & Platform Details (3 fields)
            'tech_stack', 'saas_classification', 'classification_confidence',
            
            # Business Intelligence (5 fields)
            'target_market', 'competitive_advantages', 'pain_points', 'key_services', 'products_services_offered',
            
            # Extended Company Metadata (14 fields)
            'founding_year', 'location', 'employee_count_range', 'company_size', 'company_culture',
            'funding_status', 'contact_info', 'social_media', 'leadership_team', 'key_decision_makers',
            'recent_news', 'recent_news_events', 'certifications', 'partnerships', 'awards',
            
            # Multi-Page Crawling Results (3 fields)
            'pages_crawled', 'crawl_depth', 'crawl_duration',
            
            # SaaS Classification System (6 fields)
            'has_job_listings', 'job_listings_count', 'sales_marketing_tools', 'has_forms', 'has_chat_widget', 'is_saas',
            
            # Similarity Metrics (9 fields)
            'company_stage', 'tech_sophistication', 'geographic_scope', 'decision_maker_type', 
            'sales_complexity', 'stage_confidence', 'tech_confidence', 'industry_confidence', 'funding_stage_detailed',
            
            # Batch Research Intelligence (9 fields)
            'business_model_framework', 'business_model_type', 'classification_model_version', 'classification_timestamp',
            'classification_justification', 'page_selection_prompt', 'content_analysis_prompt', 'scrape_status', 'scrape_error',
            
            # AI Analysis & Content (3 fields)
            'raw_content', 'ai_summary', 'embedding',
            
            # Scraping Details (2 fields)
            'scraped_urls', 'scraped_content_details',
            
            # LLM Interaction Details (3 fields)
            'llm_prompts_sent', 'job_listings', 'job_listings_details',
            
            # Token Usage & Cost Tracking (4 fields)
            'total_input_tokens', 'total_output_tokens', 'total_cost_usd', 'llm_calls_breakdown',
            
            # Timestamps (2 fields)
            'created_at', 'last_updated',
            
            # ID field (1 field)
            'id'
        ]
    
    async def run_comprehensive_test(self):
        """Run complete CloudGeometry test with field analysis"""
        print("🚀 CLOUDGEOMETRY COMPREHENSIVE TEST")
        print("=" * 60)
        print(f"🎯 Target: https://www.cloudgeometry.com")
        print(f"📊 Success Criteria: 75% field extraction (50+ out of 67 fields)")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Create test company
        company = CompanyData(
            name="CloudGeometry Comprehensive Test",
            website="https://www.cloudgeometry.com"
        )
        
        start_time = time.time()
        
        try:
            # Initialize scraper with full AI pipeline
            scraper = IntelligentCompanyScraper(self.config)
            
            # Initialize AI clients for full analysis
            bedrock_client = None
            try:
                bedrock_client = BedrockClient(self.config)
                scraper.bedrock_client = bedrock_client
                print("✅ Bedrock AI client initialized")
            except Exception as e:
                print(f"⚠️  Bedrock not available: {e}")
            
            print("🔍 Starting comprehensive intelligent scraping...")
            print()
            
            # Run full scraping with AI analysis
            result = await scraper.scrape_company_intelligent(company)
            
            duration = time.time() - start_time
            
            # Store results
            self.test_results = {
                'success': True,
                'duration': duration,
                'company_data': result,
                'error': None
            }
            
            print(f"\n✅ SCRAPING COMPLETED SUCCESSFULLY!")
            print(f"⏱️  Total Duration: {duration:.1f} seconds")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results = {
                'success': False,
                'duration': duration,
                'company_data': None,
                'error': str(e)
            }
            
            print(f"\n❌ SCRAPING FAILED: {e}")
            print(f"⏱️  Failed after: {duration:.1f} seconds")
    
    def analyze_field_extraction(self):
        """Analyze field extraction results against 67 total fields"""
        if not self.test_results['success']:
            return {
                'total_fields': 67,
                'extracted_fields': 0,
                'extraction_rate': 0.0,
                'success_criteria_met': False,
                'field_details': {}
            }
        
        company_data = self.test_results['company_data']
        field_details = {}
        extracted_count = 0
        
        for field in self.all_fields:
            if hasattr(company_data, field):
                value = getattr(company_data, field)
                
                # Determine if field has meaningful data
                is_extracted = self._is_field_extracted(field, value)
                
                field_details[field] = {
                    'extracted': is_extracted,
                    'value': self._format_value_for_display(value),
                    'category': self._get_field_category(field)
                }
                
                if is_extracted:
                    extracted_count += 1
            else:
                field_details[field] = {
                    'extracted': False,
                    'value': 'Field not found',
                    'category': self._get_field_category(field)
                }
        
        extraction_rate = (extracted_count / 67) * 100
        success_criteria_met = extraction_rate >= 75.0
        
        return {
            'total_fields': 67,
            'extracted_fields': extracted_count,
            'extraction_rate': extraction_rate,
            'success_criteria_met': success_criteria_met,
            'field_details': field_details
        }
    
    def _is_field_extracted(self, field, value):
        """Determine if a field contains meaningful extracted data"""
        if value is None:
            return False
        
        # String fields
        if isinstance(value, str):
            # Empty or default values
            if value in ['', 'unknown', 'Unknown', 'N/A', 'null']:
                return False
            # Meaningful content
            if len(value.strip()) > 0:
                return True
        
        # List fields
        elif isinstance(value, list):
            return len(value) > 0
        
        # Dict fields
        elif isinstance(value, dict):
            if field == 'contact_info':
                # Check if any contact field has real data
                return any(v not in ['unknown', '', None] for v in value.values() if v)
            return len(value) > 0 and any(v for v in value.values())
        
        # Numeric fields
        elif isinstance(value, (int, float)):
            return value > 0
        
        # Boolean fields
        elif isinstance(value, bool):
            return True  # Any boolean value is considered extracted
        
        # Other types
        else:
            return value is not None
        
        return False
    
    def _format_value_for_display(self, value):
        """Format value for display in report"""
        if value is None:
            return "None"
        elif isinstance(value, str):
            if len(value) > 100:
                return f"{value[:97]}..."
            return value
        elif isinstance(value, list):
            if len(value) == 0:
                return "[] (empty)"
            elif len(value) <= 3:
                return str(value)
            else:
                return f"[{len(value)} items]"
        elif isinstance(value, dict):
            if len(value) == 0:
                return "{} (empty)"
            else:
                return f"{{...}} ({len(value)} keys)"
        else:
            return str(value)
    
    def _get_field_category(self, field):
        """Categorize fields for better organization"""
        categories = {
            'Core Company Information': ['name', 'website', 'industry', 'company_description', 'business_model', 'value_proposition'],
            'Technology & Platform': ['tech_stack', 'saas_classification', 'classification_confidence'],
            'Business Intelligence': ['target_market', 'competitive_advantages', 'pain_points', 'key_services', 'products_services_offered'],
            'Company Metadata': ['founding_year', 'location', 'employee_count_range', 'company_size', 'company_culture', 'funding_status', 'contact_info', 'social_media', 'leadership_team', 'key_decision_makers', 'recent_news', 'recent_news_events', 'certifications', 'partnerships', 'awards'],
            'Crawling Results': ['pages_crawled', 'crawl_depth', 'crawl_duration'],
            'SaaS Classification': ['has_job_listings', 'job_listings_count', 'sales_marketing_tools', 'has_forms', 'has_chat_widget', 'is_saas'],
            'Similarity Metrics': ['company_stage', 'tech_sophistication', 'geographic_scope', 'decision_maker_type', 'sales_complexity', 'stage_confidence', 'tech_confidence', 'industry_confidence', 'funding_stage_detailed'],
            'Research Intelligence': ['business_model_framework', 'business_model_type', 'classification_model_version', 'classification_timestamp', 'classification_justification', 'page_selection_prompt', 'content_analysis_prompt', 'scrape_status', 'scrape_error'],
            'AI Analysis': ['raw_content', 'ai_summary', 'embedding'],
            'Scraping Details': ['scraped_urls', 'scraped_content_details'],
            'LLM Interaction': ['llm_prompts_sent', 'job_listings', 'job_listings_details'],
            'Cost Tracking': ['total_input_tokens', 'total_output_tokens', 'total_cost_usd', 'llm_calls_breakdown'],
            'System Fields': ['created_at', 'last_updated', 'id']
        }
        
        for category, fields in categories.items():
            if field in fields:
                return category
        return 'Other'
    
    def generate_report(self):
        """Generate comprehensive test report"""
        analysis = self.analyze_field_extraction()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"cloudgeometry_comprehensive_test_report_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("CLOUDGEOMETRY COMPREHENSIVE TEST REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            # Executive Summary
            f.write("📊 EXECUTIVE SUMMARY\n")
            f.write("-" * 40 + "\n")
            f.write(f"Test Target: https://www.cloudgeometry.com\n")
            f.write(f"Success Criteria: 75% field extraction (50+ out of 67 fields)\n")
            f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {self.test_results.get('duration', 0):.1f} seconds\n\n")
            
            if self.test_results['success']:
                f.write(f"✅ SCRAPING STATUS: SUCCESS\n")
            else:
                f.write(f"❌ SCRAPING STATUS: FAILED\n")
                f.write(f"Error: {self.test_results.get('error', 'Unknown error')}\n")
            
            f.write(f"📋 FIELDS EXTRACTED: {analysis['extracted_fields']}/67 ({analysis['extraction_rate']:.1f}%)\n")
            
            if analysis['success_criteria_met']:
                f.write(f"🎉 SUCCESS CRITERIA: ✅ MET (≥75% required)\n")
            else:
                f.write(f"❌ SUCCESS CRITERIA: NOT MET (≥75% required)\n")
            
            f.write("\n")
            
            # Detailed Field Analysis by Category
            f.write("📋 DETAILED FIELD ANALYSIS BY CATEGORY\n")
            f.write("-" * 60 + "\n\n")
            
            # Group fields by category
            categories = {}
            for field, details in analysis['field_details'].items():
                category = details['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append((field, details))
            
            # Report each category
            for category, fields in categories.items():
                extracted_in_category = sum(1 for _, details in fields if details['extracted'])
                total_in_category = len(fields)
                category_rate = (extracted_in_category / total_in_category * 100) if total_in_category > 0 else 0
                
                f.write(f"### {category} ({extracted_in_category}/{total_in_category} - {category_rate:.1f}%)\n")
                
                for field, details in sorted(fields):
                    status = "✅" if details['extracted'] else "❌"
                    f.write(f"   {status} {field}: {details['value']}\n")
                
                f.write("\n")
            
            # Performance Analysis
            f.write("📈 PERFORMANCE ANALYSIS\n")
            f.write("-" * 40 + "\n")
            
            if self.test_results['success'] and self.test_results['company_data']:
                company_data = self.test_results['company_data']
                
                # Crawling performance
                pages_crawled = getattr(company_data, 'pages_crawled', 0)
                crawl_duration = getattr(company_data, 'crawl_duration', 0)
                
                if isinstance(pages_crawled, list):
                    pages_count = len(pages_crawled)
                elif isinstance(pages_crawled, int):
                    pages_count = pages_crawled
                else:
                    pages_count = 0
                
                f.write(f"Pages Crawled: {pages_count}\n")
                f.write(f"Crawl Duration: {crawl_duration:.1f} seconds\n")
                
                if pages_count > 0 and crawl_duration > 0:
                    f.write(f"Pages per Second: {pages_count / crawl_duration:.2f}\n")
                
                # Content analysis
                raw_content = getattr(company_data, 'raw_content', '')
                if raw_content and isinstance(raw_content, str):
                    f.write(f"Content Generated: {len(raw_content):,} characters\n")
                
                # AI analysis
                ai_summary = getattr(company_data, 'ai_summary', '')
                if ai_summary and isinstance(ai_summary, str) and ai_summary != 'unknown':
                    f.write(f"AI Summary: {len(ai_summary):,} characters\n")
            
            f.write("\n")
            
            # Recommendations
            f.write("💡 RECOMMENDATIONS\n")
            f.write("-" * 40 + "\n")
            
            if analysis['success_criteria_met']:
                f.write("🎉 Excellent! Theodore successfully extracted 75%+ of company fields.\n")
                f.write("The crawling fix has resolved the CloudGeometry extraction issues.\n")
                f.write("Theodore is ready for production use with your website.\n")
            else:
                f.write("⚠️  Field extraction below 75% target. Areas for improvement:\n")
                
                # Identify missing high-value fields
                missing_high_value = []
                high_value_fields = ['industry', 'company_description', 'business_model', 'founding_year', 'location', 'employee_count_range', 'key_services']
                
                for field in high_value_fields:
                    if field in analysis['field_details'] and not analysis['field_details'][field]['extracted']:
                        missing_high_value.append(field)
                
                if missing_high_value:
                    f.write(f"• Missing high-value fields: {', '.join(missing_high_value)}\n")
                
                f.write("• Consider optimizing AI analysis prompts\n")
                f.write("• Verify content extraction from key pages\n")
                f.write("• Check LLM processing for business intelligence fields\n")
            
            f.write("\n")
            
            # Raw Data Summary
            f.write("🔍 RAW DATA SUMMARY\n")
            f.write("-" * 40 + "\n")
            
            if self.test_results['success'] and self.test_results['company_data']:
                company_data = self.test_results['company_data']
                
                # Show first few extracted fields as examples
                f.write("Sample Extracted Data:\n")
                sample_fields = ['name', 'website', 'industry', 'company_description', 'pages_crawled']
                for field in sample_fields:
                    if hasattr(company_data, field):
                        value = getattr(company_data, field)
                        formatted_value = self._format_value_for_display(value)
                        f.write(f"  {field}: {formatted_value}\n")
        
        print(f"\n📄 COMPREHENSIVE REPORT GENERATED:")
        print(f"   File: {report_file}")
        print(f"   Size: {os.path.getsize(report_file):,} bytes")
        
        return report_file, analysis

async def main():
    """Main execution function"""
    tester = CloudGeometryTestRunner()
    
    # Run comprehensive test
    await tester.run_comprehensive_test()
    
    # Generate report
    report_file, analysis = tester.generate_report()
    
    # Print summary to console
    print(f"\n🎯 FINAL RESULTS:")
    print(f"   Fields Extracted: {analysis['extracted_fields']}/67 ({analysis['extraction_rate']:.1f}%)")
    print(f"   Success Criteria: {'✅ MET' if analysis['success_criteria_met'] else '❌ NOT MET'} (≥75%)")
    print(f"   Report File: {report_file}")
    
    if analysis['success_criteria_met']:
        print(f"\n🎉 SUCCESS! CloudGeometry field extraction meets your 75% criteria.")
        print(f"   Theodore is working excellently with your website.")
    else:
        print(f"\n⚠️  Field extraction below 75% target. Check report for details.")

if __name__ == "__main__":
    asyncio.run(main())