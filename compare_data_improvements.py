#!/usr/bin/env python3
"""
Compare data improvements before and after reprocessing companies.
This script analyzes current data completeness and then reprocesses companies to show improvements.
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

class DataImprovementAnalyzer:
    """Analyze and compare data improvements before/after reprocessing"""
    
    def __init__(self):
        config = CompanyIntelligenceConfig()
        self.pipeline = TheodoreIntelligencePipeline(
            config=config,
            pinecone_api_key=os.getenv('PINECONE_API_KEY'),
            pinecone_environment=os.getenv('PINECONE_ENVIRONMENT'),
            pinecone_index=os.getenv('PINECONE_INDEX_NAME')
        )
        
        # Key fields to analyze for completeness
        self.key_fields = [
            'company_name', 'website', 'industry', 'business_model', 'company_size',
            'company_stage', 'founding_year', 'location', 'employee_count_range',
            'company_description', 'value_proposition', 'target_market', 'company_culture',
            'key_services', 'products_services_offered', 'pain_points', 'competitive_advantages',
            'tech_stack', 'tech_sophistication', 'has_chat_widget', 'has_forms',
            'funding_status', 'funding_stage_detailed', 'has_job_listings', 'job_listings_count',
            'leadership_team', 'key_decision_makers', 'awards', 'certifications', 'partnerships',
            'contact_info', 'social_media', 'recent_news', 'recent_news_events'
        ]
    
    def analyze_company_completeness(self, company_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze completeness of a single company's data"""
        total_fields = len(self.key_fields)
        filled_fields = 0
        empty_fields = []
        filled_fields_list = []
        
        for field in self.key_fields:
            value = company_metadata.get(field)
            is_filled = self._is_field_filled(value)
            
            if is_filled:
                filled_fields += 1
                filled_fields_list.append(field)
            else:
                empty_fields.append(field)
        
        return {
            'total_fields': total_fields,
            'filled_fields': filled_fields,
            'empty_fields': len(empty_fields),
            'completeness_percentage': (filled_fields / total_fields) * 100,
            'filled_field_names': filled_fields_list,
            'empty_field_names': empty_fields
        }
    
    def _is_field_filled(self, value: Any) -> bool:
        """Check if a field has meaningful data"""
        if value is None:
            return False
        
        if isinstance(value, str):
            return value.strip() != '' and value.lower() not in ['unknown', 'not specified', 'n/a', 'none']
        
        if isinstance(value, (list, dict)):
            return len(value) > 0
        
        if isinstance(value, bool):
            return True  # Booleans are always considered filled
        
        if isinstance(value, (int, float)):
            return value > 0
        
        return bool(value)
    
    def get_current_state(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get current state of companies in database"""
        print(f"📊 Analyzing current data completeness for top {limit} companies...")
        
        companies = self.pipeline.pinecone_client.find_companies_by_filters({}, top_k=limit)
        current_state = []
        
        for i, company in enumerate(companies[:limit], 1):
            metadata = company.get('metadata', {})
            company_name = metadata.get('company_name', f'Company_{i}')
            website = metadata.get('website', 'No website')
            
            analysis = self.analyze_company_completeness(metadata)
            
            current_state.append({
                'company_id': company.get('company_id', ''),
                'company_name': company_name,
                'website': website,
                'before_analysis': analysis,
                'before_metadata': metadata.copy()
            })
            
            print(f"{i:2d}. {company_name}")
            print(f"    Completeness: {analysis['completeness_percentage']:.1f}% ({analysis['filled_fields']}/{analysis['total_fields']} fields)")
            print(f"    Website: {website}")
        
        return current_state
    
    def reprocess_companies(self, companies_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Reprocess companies and capture new data"""
        print(f"\n🔄 Reprocessing {len(companies_data)} companies...")
        
        for i, company_data in enumerate(companies_data, 1):
            company_name = company_data['company_name']
            website = company_data['website']
            
            print(f"\n{i:2d}. Processing {company_name}...")
            
            try:
                # Reprocess the company
                new_company_data = self.pipeline.process_single_company(company_name, website)
                
                # Get updated data from database
                updated_company = self.pipeline.pinecone_client.find_company_by_name(company_name)
                if updated_company:
                    updated_metadata = updated_company.__dict__ if hasattr(updated_company, '__dict__') else {}
                    # Convert datetime objects to strings for analysis
                    for key, value in updated_metadata.items():
                        if isinstance(value, datetime):
                            updated_metadata[key] = value.isoformat()
                    
                    analysis = self.analyze_company_completeness(updated_metadata)
                    company_data['after_analysis'] = analysis
                    company_data['after_metadata'] = updated_metadata
                    
                    print(f"    ✅ Reprocessed - New completeness: {analysis['completeness_percentage']:.1f}%")
                else:
                    print(f"    ❌ Could not find updated data for {company_name}")
                    company_data['after_analysis'] = company_data['before_analysis']
                    company_data['after_metadata'] = company_data['before_metadata']
                    
            except Exception as e:
                print(f"    ❌ Error processing {company_name}: {str(e)}")
                company_data['after_analysis'] = company_data['before_analysis']
                company_data['after_metadata'] = company_data['before_metadata']
        
        return companies_data
    
    def generate_comparison_report(self, companies_data: List[Dict[str, Any]]) -> str:
        """Generate detailed comparison report"""
        print(f"\n📋 Generating comparison report...")
        
        report = []
        report.append("=" * 80)
        report.append("DATA IMPROVEMENT ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Companies analyzed: {len(companies_data)}")
        report.append("")
        
        # Overall statistics
        total_before = sum(c['before_analysis']['filled_fields'] for c in companies_data)
        total_after = sum(c['after_analysis']['filled_fields'] for c in companies_data)
        total_possible = len(companies_data) * len(self.key_fields)
        
        avg_before = (total_before / len(companies_data)) if companies_data else 0
        avg_after = (total_after / len(companies_data)) if companies_data else 0
        
        report.append("OVERALL STATISTICS:")
        report.append(f"  Average fields filled before: {avg_before:.1f}/{len(self.key_fields)} ({(avg_before/len(self.key_fields)*100):.1f}%)")
        report.append(f"  Average fields filled after:  {avg_after:.1f}/{len(self.key_fields)} ({(avg_after/len(self.key_fields)*100):.1f}%)")
        report.append(f"  Improvement: +{avg_after - avg_before:.1f} fields per company ({((avg_after - avg_before)/len(self.key_fields)*100):+.1f}%)")
        report.append("")
        
        # Individual company analysis
        report.append("INDIVIDUAL COMPANY ANALYSIS:")
        report.append("-" * 80)
        
        for i, company in enumerate(companies_data, 1):
            name = company['company_name']
            before = company['before_analysis']
            after = company['after_analysis']
            
            improvement = after['filled_fields'] - before['filled_fields']
            improvement_pct = after['completeness_percentage'] - before['completeness_percentage']
            
            report.append(f"{i:2d}. {name}")
            report.append(f"    Before: {before['filled_fields']:2d}/{before['total_fields']} fields ({before['completeness_percentage']:5.1f}%)")
            report.append(f"    After:  {after['filled_fields']:2d}/{after['total_fields']} fields ({after['completeness_percentage']:5.1f}%)")
            report.append(f"    Change: {improvement:+2d} fields ({improvement_pct:+5.1f}%)")
            
            # Show newly filled fields
            new_fields = set(after['filled_field_names']) - set(before['filled_field_names'])
            if new_fields:
                report.append(f"    New fields: {', '.join(sorted(new_fields))}")
            
            report.append("")
        
        # Field-by-field analysis
        report.append("FIELD-BY-FIELD IMPROVEMENT ANALYSIS:")
        report.append("-" * 80)
        
        field_improvements = {}
        for field in self.key_fields:
            before_count = sum(1 for c in companies_data if field in c['before_analysis']['filled_field_names'])
            after_count = sum(1 for c in companies_data if field in c['after_analysis']['filled_field_names'])
            improvement = after_count - before_count
            field_improvements[field] = {
                'before': before_count,
                'after': after_count,
                'improvement': improvement
            }
        
        # Sort by improvement
        sorted_fields = sorted(field_improvements.items(), key=lambda x: x[1]['improvement'], reverse=True)
        
        for field, stats in sorted_fields[:15]:  # Top 15 improvements
            if stats['improvement'] > 0:
                report.append(f"  {field:25} : {stats['before']:2d} → {stats['after']:2d} (+{stats['improvement']})")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_detailed_results(self, companies_data: List[Dict[str, Any]], filename: str = None):
        """Save detailed results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"data_improvement_analysis_{timestamp}.json"
        
        # Prepare data for JSON serialization
        json_data = {
            'analysis_date': datetime.now().isoformat(),
            'companies_analyzed': len(companies_data),
            'companies': companies_data
        }
        
        with open(filename, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        print(f"💾 Detailed results saved to: {filename}")
        return filename

def main():
    """Main execution function"""
    print("🚀 Starting Data Improvement Analysis...")
    print("=" * 60)
    
    analyzer = DataImprovementAnalyzer()
    
    # Step 1: Get current state
    current_companies = analyzer.get_current_state(limit=10)
    
    # Step 2: Reprocess companies
    updated_companies = analyzer.reprocess_companies(current_companies)
    
    # Step 3: Generate report
    report = analyzer.generate_comparison_report(updated_companies)
    print("\n" + report)
    
    # Step 4: Save detailed results
    results_file = analyzer.save_detailed_results(updated_companies)
    
    print(f"\n✅ Analysis complete! Check {results_file} for detailed data.")

if __name__ == "__main__":
    main()