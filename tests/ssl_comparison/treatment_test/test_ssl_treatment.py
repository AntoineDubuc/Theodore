#!/usr/bin/env python3
"""
SSL Comparison Treatment Test
Tests Theodore system with SSL fixes applied in isolated scope using real companies from Google Sheets dataset
"""

import json
import time
import requests
import sys
import os
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

# Import SSL configuration
from ssl_config import apply_ssl_fixes_for_treatment

# Add Theodore's src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

class SSLTreatmentTest:
    """
    Treatment test for SSL comparison - tests Theodore with SSL fixes applied
    """
    
    def __init__(self):
        self.base_url = "http://localhost:5002"
        self.results = []
        self.test_start_time = datetime.utcnow()
        self.companies = []
        self.ssl_fixer = None
        
    def load_test_companies(self) -> List[Dict]:
        """Load companies from the generated company list"""
        
        # First check if company data has been generated
        company_file = Path(__file__).parent.parent / "test_data" / "company_list.json"
        
        if not company_file.exists():
            print("❌ company_list.json not found!")
            print("📋 Please run the data fetcher first:")
            print("   cd tests/ssl_comparison/test_data")
            print("   python fetch_companies.py 8")
            sys.exit(1)
            
        with open(company_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Check if this is the placeholder or real data
        if "note" in data and "instructions" in data:
            print("❌ Company data has not been generated yet!")
            print("📋 Please run the data fetcher first:")
            print("   cd tests/ssl_comparison/test_data") 
            print("   python fetch_companies.py 8")
            sys.exit(1)
            
        companies = data.get("test_companies", [])
        
        if not companies:
            print("❌ No companies found in company_list.json")
            sys.exit(1)
            
        print(f"✅ Loaded {len(companies)} companies for treatment testing")
        return companies
        
    def check_theodore_status(self) -> bool:
        """Check if Theodore is running and accessible"""
        
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            if response.status_code == 200:
                print("✅ Theodore is running and accessible")
                return True
            else:
                print(f"⚠️  Theodore responded with status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to Theodore - is it running?")
            print("🚀 Please start Theodore: python app.py")
            return False
        except Exception as e:
            print(f"❌ Error checking Theodore status: {str(e)}")
            return False
            
    def setup_ssl_fixes(self):
        """Apply SSL fixes for the treatment test"""
        
        print("\n🔧 Setting up SSL fixes for treatment test...")
        print("=" * 50)
        
        try:
            self.ssl_fixer = apply_ssl_fixes_for_treatment()
            print("✅ SSL fixes applied successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to apply SSL fixes: {str(e)}")
            print("⚠️  Proceeding without SSL fixes - test may show false results")
            return False
            
    def test_company(self, company: Dict) -> Dict[str, Any]:
        """
        Test a single company through Theodore's API (with SSL fixes applied)
        """
        
        company_name = company.get("name", "Unknown")
        website = company.get("website", "")
        
        print(f"\n🧪 TREATMENT TEST: {company_name}")
        print(f"🌐 Website: {website}")
        print(f"🔒 SSL fixes: {'Applied' if self.ssl_fixer else 'Not applied'}")
        
        test_start = time.time()
        
        result = {
            "company_name": company_name,
            "website": website,
            "domain": company.get("domain", ""),
            "test_type": "treatment",
            "test_timestamp": datetime.utcnow().isoformat(),
            "source_row": company.get("source_row", "unknown"),
            "ssl_fixes_applied": bool(self.ssl_fixer),
            "success": False,
            "ssl_errors": [],
            "link_discovery": {
                "links_discovered": 0,
                "discovery_method": "unknown",
                "ssl_failures": []
            },
            "page_selection": {
                "method_used": "unknown",
                "llm_success": False,
                "heuristic_fallback": False,
                "pages_selected": 0
            },
            "content_extraction": {
                "pages_attempted": 0,
                "pages_successful": 0,
                "total_content_chars": 0
            },
            "processing_metrics": {
                "processing_time_seconds": 0,
                "total_cost_usd": 0.0,
                "error_messages": []
            }
        }
        
        try:
            # Use Theodore's process-company API endpoint
            api_url = f"{self.base_url}/api/process-company"
            
            payload = {
                "company_name": company_name,
                "website": website
            }
            
            print(f"📡 Calling Theodore API: {api_url}")
            
            # Make the API call with timeout
            response = requests.post(
                api_url,
                json=payload,
                timeout=60,  # 60 second timeout
                headers={"Content-Type": "application/json"}
            )
            
            processing_time = time.time() - test_start
            result["processing_metrics"]["processing_time_seconds"] = round(processing_time, 2)
            
            if response.status_code == 200:
                api_result = response.json()
                
                # Extract metrics from Theodore's response
                if api_result.get("success"):
                    result["success"] = True
                    
                    # Extract company data if available
                    company_data = api_result.get("company_data", {})
                    
                    # Analyze scraped pages for link discovery metrics
                    scraped_urls = company_data.get("scraped_urls", [])
                    result["link_discovery"]["links_discovered"] = len(scraped_urls)
                    
                    if len(scraped_urls) > 0:
                        result["page_selection"]["pages_selected"] = len(scraped_urls)
                        result["content_extraction"]["pages_attempted"] = len(scraped_urls)
                        
                        # Check for successful content extraction
                        ai_summary = company_data.get("ai_summary", "")
                        if ai_summary and len(ai_summary) > 100:
                            result["content_extraction"]["pages_successful"] = len(scraped_urls)
                            result["content_extraction"]["total_content_chars"] = len(ai_summary)
                        
                        # Determine page selection method
                        if len(scraped_urls) > 5:
                            result["page_selection"]["method_used"] = "llm"
                            result["page_selection"]["llm_success"] = True
                            result["link_discovery"]["discovery_method"] = "llm_enhanced"
                        else:
                            result["page_selection"]["method_used"] = "heuristic"
                            result["page_selection"]["heuristic_fallback"] = True
                            result["link_discovery"]["discovery_method"] = "heuristic"
                    else:
                        # No pages found - may still be SSL issues despite fixes
                        result["link_discovery"]["ssl_failures"].append("No URLs discovered despite SSL fixes")
                        result["page_selection"]["method_used"] = "none"
                        result["page_selection"]["heuristic_fallback"] = True
                        result["link_discovery"]["discovery_method"] = "failed"
                        
                    # Extract cost information
                    result["processing_metrics"]["total_cost_usd"] = company_data.get("total_cost_usd", 0.0)
                    
                    print(f"✅ SUCCESS: {len(scraped_urls)} pages, {len(ai_summary) if ai_summary else 0} chars summary")
                    
                else:
                    # API call succeeded but processing failed
                    error_msg = api_result.get("error", "Unknown processing error")
                    result["processing_metrics"]["error_messages"].append(error_msg)
                    
                    # Check for SSL-related errors (should be reduced with fixes)
                    if "ssl" in error_msg.lower() or "certificate" in error_msg.lower():
                        result["ssl_errors"].append(error_msg)
                        result["link_discovery"]["ssl_failures"].append(error_msg)
                        print(f"⚠️  SSL ERROR DESPITE FIXES: {error_msg}")
                    else:
                        print(f"❌ NON-SSL PROCESSING ERROR: {error_msg}")
                    
            else:
                # HTTP error
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                result["processing_metrics"]["error_messages"].append(error_msg)
                print(f"❌ API ERROR: {error_msg}")
                
        except requests.exceptions.Timeout:
            error_msg = "Request timeout after 60 seconds"
            result["processing_metrics"]["error_messages"].append(error_msg)
            result["processing_metrics"]["processing_time_seconds"] = 60
            print(f"⏰ TIMEOUT: {error_msg}")
            
        except requests.exceptions.ConnectionError:
            error_msg = "Connection error - Theodore may not be running"
            result["processing_metrics"]["error_messages"].append(error_msg)
            print(f"🔌 CONNECTION ERROR: {error_msg}")
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            result["processing_metrics"]["error_messages"].append(error_msg)
            print(f"💥 ERROR: {error_msg}")
        
        print(f"⏱️  Processing time: {result['processing_metrics']['processing_time_seconds']}s")
        return result
        
    def run_treatment_test(self):
        """Run the complete treatment test"""
        
        print("🧪 SSL COMPARISON - TREATMENT TEST")
        print("=" * 60)
        print("Testing Theodore system WITH SSL fixes applied")
        print("Using real companies from 6000+ company Google Sheets dataset")
        print("=" * 60)
        
        # Load test companies
        self.companies = self.load_test_companies()
        
        # Check Theodore status
        if not self.check_theodore_status():
            sys.exit(1)
            
        # Apply SSL fixes
        ssl_success = self.setup_ssl_fixes()
        if not ssl_success:
            print("⚠️  Continuing with test despite SSL setup issues...")
            
        print(f"\n🚀 Starting treatment test with {len(self.companies)} companies...")
        
        # Test each company
        for i, company in enumerate(self.companies, 1):
            print(f"\n📊 Progress: {i}/{len(self.companies)}")
            result = self.test_company(company)
            self.results.append(result)
            
            # Brief pause between companies
            if i < len(self.companies):
                print("⏳ Waiting 3 seconds before next company...")
                time.sleep(3)
        
        # Generate summary and save results
        self.generate_summary()
        self.save_results()
        
    def generate_summary(self):
        """Generate summary statistics for the treatment test"""
        
        total_companies = len(self.results)
        successful_companies = sum(1 for r in self.results if r["success"])
        
        # Link discovery metrics
        companies_with_links = sum(1 for r in self.results if r["link_discovery"]["links_discovered"] > 0)
        total_links = sum(r["link_discovery"]["links_discovered"] for r in self.results)
        avg_links = total_links / total_companies if total_companies > 0 else 0
        
        # Page selection metrics
        llm_successes = sum(1 for r in self.results if r["page_selection"]["llm_success"])
        heuristic_fallbacks = sum(1 for r in self.results if r["page_selection"]["heuristic_fallback"])
        
        # Content extraction metrics
        total_pages_attempted = sum(r["content_extraction"]["pages_attempted"] for r in self.results)
        total_pages_successful = sum(r["content_extraction"]["pages_successful"] for r in self.results)
        
        # Processing metrics
        total_processing_time = sum(r["processing_metrics"]["processing_time_seconds"] for r in self.results)
        avg_processing_time = total_processing_time / total_companies if total_companies > 0 else 0
        
        # SSL error metrics
        companies_with_ssl_errors = sum(1 for r in self.results if r["ssl_errors"])
        
        summary = {
            "test_metadata": {
                "test_type": "treatment",
                "test_start_time": self.test_start_time.isoformat(),
                "test_end_time": datetime.utcnow().isoformat(),
                "total_companies_tested": total_companies,
                "theodore_base_url": self.base_url,
                "ssl_fixes_applied": bool(self.ssl_fixer)
            },
            "overall_metrics": {
                "overall_success_rate": successful_companies / total_companies if total_companies > 0 else 0,
                "companies_successful": successful_companies,
                "companies_failed": total_companies - successful_companies
            },
            "link_discovery_metrics": {
                "link_discovery_success_rate": companies_with_links / total_companies if total_companies > 0 else 0,
                "companies_with_links": companies_with_links,
                "companies_without_links": total_companies - companies_with_links,
                "total_links_discovered": total_links,
                "average_links_per_company": round(avg_links, 1)
            },
            "page_selection_metrics": {
                "llm_success_rate": llm_successes / total_companies if total_companies > 0 else 0,
                "heuristic_fallback_rate": heuristic_fallbacks / total_companies if total_companies > 0 else 0,
                "llm_successes": llm_successes,
                "heuristic_fallbacks": heuristic_fallbacks
            },
            "content_extraction_metrics": {
                "content_extraction_success_rate": total_pages_successful / total_pages_attempted if total_pages_attempted > 0 else 0,
                "pages_attempted": total_pages_attempted,
                "pages_successful": total_pages_successful,
                "pages_failed": total_pages_attempted - total_pages_successful
            },
            "performance_metrics": {
                "average_processing_time_seconds": round(avg_processing_time, 1),
                "total_processing_time_seconds": round(total_processing_time, 1)
            },
            "ssl_metrics": {
                "ssl_error_rate": companies_with_ssl_errors / total_companies if total_companies > 0 else 0,
                "companies_with_ssl_errors": companies_with_ssl_errors,
                "companies_without_ssl_errors": total_companies - companies_with_ssl_errors
            }
        }
        
        print("\n" + "=" * 60)
        print("📊 TREATMENT TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Overall Success Rate: {summary['overall_metrics']['overall_success_rate']:.1%}")
        print(f"🔍 Link Discovery Success: {summary['link_discovery_metrics']['link_discovery_success_rate']:.1%}")
        print(f"📄 Average Links Found: {summary['link_discovery_metrics']['average_links_per_company']}")
        print(f"🧠 LLM Page Selection Success: {summary['page_selection_metrics']['llm_success_rate']:.1%}")
        print(f"📋 Heuristic Fallback Rate: {summary['page_selection_metrics']['heuristic_fallback_rate']:.1%}")
        print(f"📝 Content Extraction Success: {summary['content_extraction_metrics']['content_extraction_success_rate']:.1%}")
        print(f"🔒 SSL Error Rate: {summary['ssl_metrics']['ssl_error_rate']:.1%}")
        print(f"⏱️  Average Processing Time: {summary['performance_metrics']['average_processing_time_seconds']}s")
        
        self.summary = summary
        
    def save_results(self):
        """Save detailed results and summary to files"""
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results
        results_file = Path(__file__).parent / "treatment_results" / f"treatment_detailed_{timestamp}.json"
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": self.summary,
                "detailed_results": self.results
            }, f, indent=2, ensure_ascii=False)
            
        # Save summary only
        summary_file = Path(__file__).parent / "treatment_results" / f"treatment_summary_{timestamp}.json"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(self.summary, f, indent=2, ensure_ascii=False)
            
        # Create latest symlinks
        latest_detailed = Path(__file__).parent / "treatment_results" / "latest_detailed.json"
        latest_summary = Path(__file__).parent / "treatment_results" / "latest_summary.json"
        
        if latest_detailed.exists():
            latest_detailed.unlink()
        if latest_summary.exists():
            latest_summary.unlink()
            
        latest_detailed.symlink_to(results_file.name)
        latest_summary.symlink_to(summary_file.name)
        
        print(f"\n💾 Results saved:")
        print(f"   📄 Detailed: {results_file}")
        print(f"   📊 Summary: {summary_file}")
        print(f"   🔗 Latest: {latest_summary}")
        
    def cleanup(self):
        """Clean up SSL fixes after test completion"""
        
        if self.ssl_fixer:
            print("\n🔄 Cleaning up SSL fixes...")
            self.ssl_fixer.restore_ssl_settings()

def main():
    """Main execution function"""
    
    tester = None
    try:
        tester = SSLTreatmentTest()
        tester.run_treatment_test()
        
        print("\n" + "=" * 60)
        print("✅ TREATMENT TEST COMPLETED SUCCESSFULLY")
        print("📋 Next step: Generate comparison report")
        print("   cd ../analysis")
        print("   python generate_comparison_report.py")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        if tester:
            tester.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        if tester:
            tester.cleanup()
        sys.exit(1)
    finally:
        if tester:
            tester.cleanup()

if __name__ == "__main__":
    main()