#!/usr/bin/env python3
"""
Test David's Business Model Framework Integration
Verifies the framework works end-to-end with Theodore's pipeline
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, 'src')

from dotenv import load_dotenv
load_dotenv()

# Import Theodore components
from concurrent_intelligent_scraper import ConcurrentIntelligentScraperSync
from models import CompanyData
from business_model_framework_prompts import validate_framework_output

class FrameworkIntegrationTester:
    """Test the complete Business Model Framework integration"""
    
    def __init__(self):
        self.scraper = ConcurrentIntelligentScraperSync()
        
    async def test_single_company(self, company_name: str, website: str) -> Dict[str, Any]:
        """Test framework integration with a single company"""
        print(f"\n🧪 TESTING: {company_name} ({website})")
        print("=" * 60)
        
        try:
            # Create company data
            company_data = CompanyData(
                name=company_name,
                website=website
            )
            
            # Run the full intelligent scraping pipeline
            print("🔍 Running intelligent scraping pipeline...")
            result = await self.scraper.scrape_company_intelligent(
                company_data=company_data,
                job_id=f"framework_test_{company_name.lower().replace(' ', '_')}"
            )
            
            if not result or result.scrape_status != "success":
                return {
                    "company": company_name,
                    "status": "failed",
                    "error": "Scraping failed"
                }
            
            # Check if framework was generated
            framework_output = result.business_model_framework
            
            print(f"\n📊 RESULTS:")
            print(f"Status: {result.scrape_status}")
            print(f"Industry: {result.industry}")
            print(f"Business Model: {result.business_model}")
            print(f"Target Market: {result.target_market}")
            print(f"Value Proposition: {result.value_proposition}")
            print(f"Framework Output: {framework_output}")
            
            # Validate framework output
            if framework_output:
                validation = validate_framework_output(framework_output)
                print(f"\n🔍 FRAMEWORK VALIDATION:")
                print(f"Valid: {'✅' if validation['valid'] else '❌'}")
                print(f"Quality Score: {validation['quality_score']:.2f}")
                print(f"Word Count: {validation['word_count']}")
                if validation['errors']:
                    print(f"Errors: {', '.join(validation['errors'])}")
                if validation['warnings']:
                    print(f"Warnings: {', '.join(validation['warnings'])}")
                
                return {
                    "company": company_name,
                    "website": website,
                    "status": "success",
                    "scraping_results": {
                        "industry": result.industry,
                        "business_model": result.business_model,
                        "target_market": result.target_market,
                        "value_proposition": result.value_proposition,
                        "scrape_duration": result.crawl_duration
                    },
                    "framework_results": {
                        "output": framework_output,
                        "validation": validation
                    }
                }
            else:
                return {
                    "company": company_name,
                    "website": website,
                    "status": "partial",
                    "error": "Framework not generated",
                    "scraping_results": {
                        "industry": result.industry,
                        "business_model": result.business_model,
                        "target_market": result.target_market
                    }
                }
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return {
                "company": company_name,
                "website": website,
                "status": "failed",
                "error": str(e)
            }
    
    async def run_integration_test(self, test_companies: list) -> Dict[str, Any]:
        """Run complete integration test"""
        print("🚀 STARTING BUSINESS MODEL FRAMEWORK INTEGRATION TEST")
        print("=" * 80)
        print(f"Testing {len(test_companies)} companies\n")
        
        results = []
        start_time = datetime.now()
        
        for i, company in enumerate(test_companies, 1):
            print(f"\n[{i}/{len(test_companies)}] Testing: {company['name']}")
            
            result = await self.test_single_company(
                company_name=company['name'],
                website=company['website']
            )
            
            results.append(result)
            
            # Brief summary
            if result['status'] == 'success':
                framework = result.get('framework_results', {}).get('output', 'N/A')
                quality = result.get('framework_results', {}).get('validation', {}).get('quality_score', 0)
                print(f"✅ SUCCESS - Quality: {quality:.2f} - Framework: {framework[:100]}...")
            elif result['status'] == 'partial':
                print(f"⚠️ PARTIAL - Scraping OK, Framework failed")
            else:
                print(f"❌ FAILED - {result.get('error', 'Unknown error')}")
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Calculate statistics
        successful = [r for r in results if r['status'] == 'success']
        partial = [r for r in results if r['status'] == 'partial']
        failed = [r for r in results if r['status'] == 'failed']
        
        framework_generated = len([r for r in results if r.get('framework_results', {}).get('output')])
        avg_quality = sum(r.get('framework_results', {}).get('validation', {}).get('quality_score', 0) 
                         for r in successful) / len(successful) if successful else 0
        
        summary = {
            "test_timestamp": start_time.isoformat(),
            "total_companies": len(test_companies),
            "successful": len(successful),
            "partial": len(partial),
            "failed": len(failed),
            "framework_generation_rate": framework_generated / len(test_companies) * 100,
            "average_quality_score": avg_quality,
            "total_test_time": total_time,
            "average_time_per_company": total_time / len(test_companies),
            "results": results
        }
        
        return summary

def display_test_summary(summary: Dict[str, Any]):
    """Display formatted test summary"""
    print("\n" + "=" * 80)
    print("📊 BUSINESS MODEL FRAMEWORK INTEGRATION TEST SUMMARY")
    print("=" * 80)
    print(f"Test Date: {summary['test_timestamp']}")
    print(f"Total Companies: {summary['total_companies']}")
    print(f"Successful: {summary['successful']}")
    print(f"Partial Success: {summary['partial']}")
    print(f"Failed: {summary['failed']}")
    print(f"Success Rate: {(summary['successful'] / summary['total_companies'] * 100):.1f}%")
    print(f"Framework Generation Rate: {summary['framework_generation_rate']:.1f}%")
    print(f"Average Quality Score: {summary['average_quality_score']:.2f}")
    print(f"Total Test Time: {summary['total_test_time']:.1f}s")
    print(f"Average Time/Company: {summary['average_time_per_company']:.1f}s")
    print()
    
    print("🎯 FRAMEWORK OUTPUTS:")
    print("-" * 50)
    for result in summary['results']:
        if result['status'] == 'success' and result.get('framework_results', {}).get('output'):
            framework = result['framework_results']['output']
            quality = result['framework_results']['validation']['quality_score']
            print(f"Company: {result['company']}")
            print(f"Quality: {quality:.2f}")
            print(f"Output: {framework}")
            print()
    
    print("❌ ISSUES:")
    print("-" * 20)
    for result in summary['results']:
        if result['status'] != 'success':
            print(f"Company: {result['company']} - Status: {result['status']} - Error: {result.get('error', 'N/A')}")
    print()

async def main():
    """Run the integration test"""
    
    # Test companies - selected for diverse business models
    test_companies = [
        {"name": "Stripe", "website": "https://stripe.com"},
        {"name": "Notion", "website": "https://notion.so"},
        {"name": "Figma", "website": "https://figma.com"}
    ]
    
    tester = FrameworkIntegrationTester()
    
    try:
        # Run the integration test
        summary = await tester.run_integration_test(test_companies)
        
        # Display results
        display_test_summary(summary)
        
        # Save results to file
        output_file = f"framework_integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"📁 Test results saved to: {output_file}")
        
        # Shutdown scraper
        tester.scraper.shutdown()
        
        return summary
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        return None

if __name__ == "__main__":
    # Run with asyncio
    summary = asyncio.run(main())
    
    if summary:
        success_rate = summary['successful'] / summary['total_companies'] * 100
        framework_rate = summary['framework_generation_rate']
        
        print(f"\n🎉 INTEGRATION TEST COMPLETE")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Framework Generation: {framework_rate:.1f}%")
        print(f"Average Quality: {summary['average_quality_score']:.2f}")
        
        if success_rate >= 80 and framework_rate >= 80:
            print("✅ INTEGRATION SUCCESSFUL - Ready for production!")
        elif success_rate >= 60:
            print("⚠️ PARTIAL SUCCESS - Some refinement needed")
        else:
            print("❌ INTEGRATION NEEDS WORK - Significant issues found")
    else:
        print("❌ INTEGRATION TEST FAILED")