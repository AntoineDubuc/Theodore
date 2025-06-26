#!/usr/bin/env python3
"""
AI Model Comparison using Theodore's Web API
Tests multiple AI models by calling the actual web application endpoints
"""

import requests
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Any

class APIModelComparison:
    """Test multiple AI models via Theodore's web API"""
    
    def __init__(self, base_url: str = "http://localhost:5002"):
        self.base_url = base_url
        self.companies = [
            "scitara.com",
            "viseven.com", 
            "3dsbiovia.com",
            "agmednet.com",
            "aitiabio.com",
            "aizon.ai",
            "certara.com",
            "chemify.io",
            "citeline.com",
            "clinicalresearch.io",
            "dotcompliance.com"
        ]
        
        # Model configurations to test
        self.models = {
            "gemini_2_5_flash": {
                "GEMINI_MODEL": "gemini-2.5-flash",
                "BEDROCK_ANALYSIS_MODEL": "us.amazon.nova-pro-v1:0",
                "description": "Gemini 2.5 Flash - Fast, efficient model"
            },
            "gemini_2_5_pro": {
                "GEMINI_MODEL": "gemini-2.5-pro", 
                "BEDROCK_ANALYSIS_MODEL": "us.amazon.nova-pro-v1:0",
                "description": "Gemini 2.5 Pro - Advanced reasoning model"
            },
            "nova_pro": {
                "GEMINI_MODEL": "gemini-2.5-flash",
                "BEDROCK_ANALYSIS_MODEL": "us.amazon.nova-pro-v1:0",
                "description": "Amazon Nova Pro - High-performance model"
            },
            "nova_micro": {
                "GEMINI_MODEL": "gemini-2.5-flash",
                "BEDROCK_ANALYSIS_MODEL": "us.amazon.nova-micro-v1:0",
                "description": "Amazon Nova Micro - Lightweight model"
            },
            "nova_nano": {
                "GEMINI_MODEL": "gemini-2.5-flash",
                "BEDROCK_ANALYSIS_MODEL": "us.amazon.nova-nano-v1:0", 
                "description": "Amazon Nova Nano - Ultra-lightweight model"
            }
        }
        
        self.results = {}
        
    def check_app_status(self) -> bool:
        """Check if Theodore web app is running"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def start_research(self, company_url: str) -> str:
        """Start research for a company and return job_id"""
        try:
            payload = {
                "company_name": company_url.replace('https://', '').replace('http://', '').replace('www.', ''),
                "website": company_url
            }
            
            response = requests.post(
                f"{self.base_url}/api/research/start",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('job_id')
            else:
                print(f"❌ Failed to start research: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error starting research: {str(e)}")
            return None
    
    def wait_for_completion(self, job_id: str, timeout: int = 120) -> Dict[str, Any]:
        """Wait for research to complete and return results"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/api/research/progress/{job_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    
                    if status == 'completed':
                        print(f"✅ Research completed in {time.time() - start_time:.1f}s")
                        return data
                    elif status == 'failed':
                        print(f"❌ Research failed: {data.get('error')}")
                        return {'status': 'failed', 'error': data.get('error')}
                    else:
                        print(f"⏳ Status: {status} - {data.get('message', '')}")
                        time.sleep(3)
                else:
                    print(f"❌ Error checking progress: {response.status_code}")
                    time.sleep(3)
                    
            except Exception as e:
                print(f"❌ Error waiting for completion: {str(e)}")
                time.sleep(3)
        
        print(f"⏰ Timeout waiting for research completion")
        return {'status': 'timeout'}
    
    def test_company_with_model(self, company_url: str, model_name: str, model_config: Dict[str, str]) -> Dict[str, Any]:
        """Test a single company with a specific model configuration"""
        print(f"\n🔍 Testing {company_url} with {model_name}")
        
        start_time = time.time()
        
        try:
            # Start the research
            job_id = self.start_research(company_url)
            if not job_id:
                return {
                    "model": model_name,
                    "company_url": company_url,
                    "success": False,
                    "error": "Failed to start research",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            print(f"📋 Started research job: {job_id}")
            
            # Wait for completion
            result = self.wait_for_completion(job_id)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            if result.get('status') == 'completed':
                # Extract company data from result
                company_data = result.get('company_data', {})
                
                # Calculate extraction quality
                quality_metrics = self.calculate_extraction_quality(company_data)
                
                return {
                    "model": model_name,
                    "model_description": model_config["description"],
                    "company_url": company_url,
                    "job_id": job_id,
                    "processing_time_seconds": round(processing_time, 2),
                    "success": True,
                    "timestamp": datetime.utcnow().isoformat(),
                    "extraction_quality": quality_metrics,
                    "extracted_data": {
                        "company_name": company_data.get('name'),
                        "company_description": company_data.get('company_description'),
                        "industry": company_data.get('industry'),
                        "business_model": company_data.get('business_model'),
                        "company_size": company_data.get('company_size'),
                        "target_market": company_data.get('target_market'),
                        "founding_year": company_data.get('founding_year'),
                        "location": company_data.get('location'),
                        "employee_count_range": company_data.get('employee_count_range'),
                        "funding_status": company_data.get('funding_status'),
                        "tech_stack": company_data.get('tech_stack', []),
                        "key_services": company_data.get('key_services', []),
                        "competitive_advantages": company_data.get('competitive_advantages', []),
                        "leadership_team": company_data.get('leadership_team', []),
                        "pages_crawled": company_data.get('pages_crawled', []),
                        "ai_summary": (company_data.get('ai_summary') or '')[:500]  # Truncate
                    }
                }
            else:
                return {
                    "model": model_name,
                    "company_url": company_url,
                    "success": False,
                    "error": result.get('error', 'Unknown error'),
                    "processing_time_seconds": round(processing_time, 2),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "model": model_name,
                "company_url": company_url,
                "success": False,
                "error": str(e),
                "processing_time_seconds": round(time.time() - start_time, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def calculate_extraction_quality(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate quality metrics for extracted data"""
        key_fields = [
            'name', 'company_description', 'industry', 'business_model',
            'company_size', 'target_market', 'founding_year', 'location', 
            'employee_count_range', 'funding_status', 'tech_stack', 
            'key_services', 'competitive_advantages', 'leadership_team'
        ]
        
        populated_fields = 0
        field_details = {}
        
        for field in key_fields:
            value = company_data.get(field)
            is_populated = False
            
            if value:
                if isinstance(value, str) and len(value.strip()) > 0:
                    is_populated = True
                elif isinstance(value, list) and len(value) > 0:
                    is_populated = True
                elif isinstance(value, (int, float)) and value is not None:
                    is_populated = True
            
            if is_populated:
                populated_fields += 1
            
            field_details[field] = {
                "populated": is_populated,
                "value_type": type(value).__name__,
                "value_length": len(value) if isinstance(value, (str, list)) else None
            }
        
        coverage_percentage = (populated_fields / len(key_fields)) * 100
        
        return {
            "total_key_fields": len(key_fields),
            "populated_fields": populated_fields,
            "coverage_percentage": round(coverage_percentage, 1),
            "pages_scraped": len(company_data.get('pages_crawled', [])),
            "has_ai_summary": bool(company_data.get('ai_summary')),
            "field_details": field_details
        }
    
    def run_comparison(self):
        """Run the full comparison test"""
        print("🤖 Theodore AI Model Comparison (API Mode)")
        print("=" * 60)
        
        # Check if app is running
        if not self.check_app_status():
            print("❌ Theodore web app is not running at http://localhost:5002")
            print("Please start the app with: python3 app.py")
            return None
        
        print("✅ Theodore web app is running")
        print(f"📊 Testing {len(self.companies)} companies with {len(self.models)} models")
        
        # Test first 2 companies only for speed
        test_companies = self.companies[:2]  
        
        for company_url in test_companies:
            print(f"\n🏢 --- Testing company: {company_url} ---")
            company_results = {}
            
            for model_name, model_config in self.models.items():
                result = self.test_company_with_model(company_url, model_name, model_config)
                company_results[model_name] = result
                
                if result['success']:
                    print(f"✅ {model_name}: {result['extraction_quality']['coverage_percentage']}% coverage in {result['processing_time_seconds']}s")
                else:
                    print(f"❌ {model_name}: Failed - {result.get('error', 'Unknown error')}")
                
                # Delay between model tests
                time.sleep(5)
            
            self.results[company_url] = company_results
            
            # Longer delay between companies
            time.sleep(10)
        
        print(f"\n✅ Comparison test completed")
        return self.results

def main():
    """Main execution function"""
    comparison = APIModelComparison()
    
    try:
        # Run the comparison
        results = comparison.run_comparison()
        
        if results:
            # Save results
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = f"docs/analysis/api_model_comparison_results_{timestamp}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
            
            print(f"\n📁 Results saved to: {output_file}")
            
            # Quick summary
            print("\n📈 Quick Summary:")
            for company_url, company_results in results.items():
                print(f"\n🏢 {company_url}:")
                for model_name, result in company_results.items():
                    if result.get('success'):
                        coverage = result.get('extraction_quality', {}).get('coverage_percentage', 0)
                        time_taken = result.get('processing_time_seconds', 0)
                        print(f"  {model_name}: {coverage:.1f}% coverage, {time_taken:.1f}s")
                    else:
                        print(f"  {model_name}: Failed")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    main()