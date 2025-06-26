#!/usr/bin/env python3
"""
Nova Pro vs Gemini 2.5 Pro Comparison Test
Real-world A/B test with 10 companies to compare cost, accuracy, and performance
"""

import os
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Load environment variables
def load_env():
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    value = value.strip('"\'')
                    os.environ[key] = value

load_env()

class ModelComparisonTester:
    """Multi-model comparison framework: Nova Pro, Nova Lite, Gemini Pro, Gemini Flash"""
    
    def __init__(self):
        """Initialize the comparison tester"""
        
        # Test companies for consistent comparison
        self.test_companies = [
            {"name": "Procurify", "domain": "procurify.com"},
            {"name": "Stripe", "domain": "stripe.com"},
            {"name": "Shopify", "domain": "shopify.com"},
            {"name": "Slack", "domain": "slack.com"},
            {"name": "Notion", "domain": "notion.so"},
            {"name": "Figma", "domain": "figma.com"},
            {"name": "Zoom", "domain": "zoom.us"},
            {"name": "Dropbox", "domain": "dropbox.com"},
            {"name": "Atlassian", "domain": "atlassian.com"},
            {"name": "GitLab", "domain": "gitlab.com"}
        ]
        
        # Standard research prompts for consistent testing
        self.research_prompts = {
            "business_model": """
            Analyze the business model of {company_name} ({domain}). Based on the scraped content, determine:
            
            1. Primary business model (B2B SaaS, B2C, Marketplace, etc.)
            2. Revenue streams (subscription, transaction fees, advertising, etc.)
            3. Target market and customer segments
            4. Competitive positioning and value proposition
            5. Company stage (startup, growth, mature)
            
            Provide a structured analysis in JSON format.
            """,
            
            "technical_assessment": """
            Assess the technical sophistication of {company_name} ({domain}) based on the content:
            
            1. Technology stack indicators
            2. Engineering capabilities and approach
            3. Product complexity and technical differentiation
            4. Developer community engagement
            5. Technical innovation level (1-10 scale)
            
            Provide technical intelligence in JSON format.
            """,
            
            "market_analysis": """
            Analyze {company_name} ({domain}) from a market perspective:
            
            1. Market size and opportunity
            2. Competitive landscape position
            3. Growth indicators and market traction
            4. Industry trends and company alignment
            5. Investment attractiveness (1-10 scale)
            
            Return market intelligence in JSON format.
            """
        }
        
        # Define all models to test
        self.models_to_test = {
            "nova_pro": {
                "name": "Amazon Nova Pro",
                "model_id": "amazon.nova-pro-v1:0",
                "cost_per_1k_tokens": 0.0008,  # $0.80 per 1M tokens
                "client_type": "bedrock"
            },
            "nova_lite": {
                "name": "Amazon Nova Lite", 
                "model_id": "amazon.nova-lite-v1:0",
                "cost_per_1k_tokens": 0.00006,  # $0.06 per 1M tokens
                "client_type": "bedrock"
            },
            "gemini_pro": {
                "name": "Gemini 2.5 Pro",
                "model_id": "gemini-2.5-pro", 
                "cost_per_1k_tokens": 0.00125,  # $1.25 per 1M tokens
                "client_type": "gemini"
            },
            "gemini_flash": {
                "name": "Gemini 2.5 Flash",
                "model_id": "gemini-2.5-flash",
                "cost_per_1k_tokens": 0.000075,  # $0.075 per 1M tokens
                "client_type": "gemini"
            }
        }
        
        self.results = {
            "test_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "test_companies": len(self.test_companies),
                "prompts_tested": len(self.research_prompts),
                "models_tested": len(self.models_to_test),
                "total_comparisons": len(self.test_companies) * len(self.research_prompts) * len(self.models_to_test)
            },
            "company_results": [],
            "cost_analysis": {model_key: {"total_tokens": 0, "total_cost": 0.0, "avg_cost_per_company": 0.0} 
                           for model_key in self.models_to_test.keys()},
            "accuracy_analysis": {model_key: {"structured_responses": 0, "json_valid": 0, "completeness_score": 0.0} 
                                for model_key in self.models_to_test.keys()},
            "performance_analysis": {model_key: {"avg_response_time": 0.0, "timeouts": 0, "errors": 0} 
                                   for model_key in self.models_to_test.keys()}
        }
    
    async def test_company_with_all_models(self, company: Dict[str, str]) -> Dict[str, Any]:
        """Test a single company with all 4 models: Nova Pro, Nova Lite, Gemini Pro, Gemini Flash"""
        
        print(f"\n🏢 Testing: {company['name']} ({company['domain']})")
        print("="*60)
        
        company_result = {
            "company": company,
            "timestamp": datetime.utcnow().isoformat(),
            "scraped_content": None,
            "model_results": {model_key: {} for model_key in self.models_to_test.keys()},
            "comparisons": {}
        }
        
        # Step 1: Scrape company content (same input for both models)
        scraped_content = await self.scrape_company_content(company)
        company_result["scraped_content"] = {
            "content_length": len(scraped_content) if scraped_content else 0,
            "scraping_success": scraped_content is not None
        }
        
        if not scraped_content:
            print(f"❌ Failed to scrape content for {company['name']}")
            return company_result
        
        print(f"✅ Scraped {len(scraped_content)} characters of content")
        
        # Step 2: Test each prompt with both models
        for prompt_name, prompt_template in self.research_prompts.items():
            print(f"\n📋 Testing prompt: {prompt_name}")
            
            # Format prompt with company data
            formatted_prompt = prompt_template.format(
                company_name=company['name'],
                domain=company['domain']
            )
            full_prompt = f"{formatted_prompt}\n\nCompany Content:\n{scraped_content[:8000]}"
            
            # Test Nova Pro
            print("🔵 Testing with Nova Pro...")
            nova_result = await self.test_with_nova_pro(full_prompt, company['name'], prompt_name)
            company_result["nova_results"][prompt_name] = nova_result
            
            # Wait between requests
            await asyncio.sleep(2)
            
            # Test Gemini Pro
            print("🟢 Testing with Gemini 2.5 Pro...")
            gemini_result = await self.test_with_gemini_pro(full_prompt, company['name'], prompt_name)
            company_result["gemini_results"][prompt_name] = gemini_result
            
            # Compare results
            comparison = self.compare_prompt_results(nova_result, gemini_result, prompt_name)
            company_result["comparison"][prompt_name] = comparison
            
            # Wait between prompts
            await asyncio.sleep(3)
        
        return company_result
    
    async def scrape_company_content(self, company: Dict[str, str]) -> Optional[str]:
        """Scrape company content using Theodore's existing scraper"""
        
        try:
            # Import Theodore's scraper
            import sys
            sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))
            
            from intelligent_company_scraper import IntelligentCompanyScraperSync
            from models import CompanyIntelligenceConfig
            
            # Configure scraper
            config = CompanyIntelligenceConfig(
                company_name=company['name'],
                company_domain=company['domain'],
                max_pages_to_scrape=20,  # Reduced for faster testing
                timeout_seconds=30
            )
            
            scraper = IntelligentCompanyScraperSync()
            
            print(f"🔍 Scraping {company['name']}...")
            scraping_result = scraper.scrape_company_sync(config)
            
            if scraping_result.success and scraping_result.aggregated_content:
                return scraping_result.aggregated_content
            else:
                print(f"❌ Scraping failed: {scraping_result.error_message}")
                return None
                
        except Exception as e:
            print(f"❌ Scraping error: {e}")
            return None
    
    async def test_with_nova_pro(self, prompt: str, company_name: str, prompt_type: str) -> Dict[str, Any]:
        """Test with Nova Pro model"""
        
        start_time = time.time()
        result = {
            "model": "amazon.nova-pro-v1:0",
            "prompt_type": prompt_type,
            "company": company_name,
            "success": False,
            "response": None,
            "tokens_used": 0,
            "cost": 0.0,
            "response_time": 0.0,
            "error": None,
            "json_valid": False,
            "completeness_score": 0.0
        }
        
        try:
            # Import Nova client
            import sys
            sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))
            from bedrock_client import BedrockClient
            
            client = BedrockClient()
            
            # Make request
            response = await asyncio.to_thread(
                client.analyze_with_bedrock,
                prompt,
                max_tokens=4000
            )
            
            result["response_time"] = time.time() - start_time
            
            if response:
                result["success"] = True
                result["response"] = response
                
                # Estimate tokens and cost (Nova Pro pricing)
                estimated_tokens = len(prompt.split()) + len(response.split())
                result["tokens_used"] = estimated_tokens
                result["cost"] = estimated_tokens * 0.0008 / 1000  # Nova Pro: $0.80 per 1M tokens
                
                # Assess response quality
                result["json_valid"] = self.is_valid_json_response(response)
                result["completeness_score"] = self.assess_response_completeness(response, prompt_type)
                
                print(f"   ✅ Success: {estimated_tokens} tokens, ${result['cost']:.4f}")
            else:
                result["error"] = "No response from Nova Pro"
                print(f"   ❌ No response received")
                
        except Exception as e:
            result["error"] = str(e)
            result["response_time"] = time.time() - start_time
            print(f"   ❌ Error: {e}")
        
        return result
    
    async def test_with_gemini_pro(self, prompt: str, company_name: str, prompt_type: str) -> Dict[str, Any]:
        """Test with Gemini 2.5 Pro model"""
        
        start_time = time.time()
        result = {
            "model": "gemini-2.5-pro",
            "prompt_type": prompt_type,
            "company": company_name,
            "success": False,
            "response": None,
            "tokens_used": 0,
            "cost": 0.0,
            "response_time": 0.0,
            "error": None,
            "json_valid": False,
            "completeness_score": 0.0
        }
        
        try:
            # Import Gemini client
            import sys
            sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))
            from gemini_client import GeminiClient
            
            client = GeminiClient()
            
            # Make request
            response = await asyncio.to_thread(
                client.analyze_with_gemini,
                prompt,
                model_name="gemini-2.5-pro"
            )
            
            result["response_time"] = time.time() - start_time
            
            if response:
                result["success"] = True
                result["response"] = response
                
                # Estimate tokens and cost (Gemini Pro pricing)
                estimated_tokens = len(prompt.split()) + len(response.split())
                result["tokens_used"] = estimated_tokens
                result["cost"] = estimated_tokens * 0.00125 / 1000  # Gemini Pro: $1.25 per 1M tokens
                
                # Assess response quality
                result["json_valid"] = self.is_valid_json_response(response)
                result["completeness_score"] = self.assess_response_completeness(response, prompt_type)
                
                print(f"   ✅ Success: {estimated_tokens} tokens, ${result['cost']:.4f}")
            else:
                result["error"] = "No response from Gemini Pro"
                print(f"   ❌ No response received")
                
        except Exception as e:
            result["error"] = str(e)
            result["response_time"] = time.time() - start_time
            print(f"   ❌ Error: {e}")
        
        return result
    
    def is_valid_json_response(self, response: str) -> bool:
        """Check if response contains valid JSON"""
        try:
            # Look for JSON in the response
            import re
            json_matches = re.findall(r'\{.*\}', response, re.DOTALL)
            if json_matches:
                json.loads(json_matches[0])
                return True
            return False
        except:
            return False
    
    def assess_response_completeness(self, response: str, prompt_type: str) -> float:
        """Assess how complete the response is based on prompt requirements"""
        
        completeness_score = 0.0
        
        # Basic completeness checks
        if len(response) > 100:
            completeness_score += 0.2
        
        if self.is_valid_json_response(response):
            completeness_score += 0.3
        
        # Prompt-specific checks
        if prompt_type == "business_model":
            required_elements = ["business model", "revenue", "customer", "market", "stage"]
        elif prompt_type == "technical_assessment":
            required_elements = ["technology", "engineering", "technical", "innovation", "developer"]
        elif prompt_type == "market_analysis":
            required_elements = ["market", "competitive", "growth", "industry", "investment"]
        else:
            required_elements = []
        
        # Check for required elements
        response_lower = response.lower()
        found_elements = sum(1 for element in required_elements if element in response_lower)
        
        if required_elements:
            completeness_score += 0.5 * (found_elements / len(required_elements))
        
        return min(completeness_score, 1.0)
    
    def compare_prompt_results(self, nova_result: Dict, gemini_result: Dict, prompt_name: str) -> Dict:
        """Compare results from Nova and Gemini for a specific prompt"""
        
        return {
            "prompt": prompt_name,
            "both_successful": nova_result["success"] and gemini_result["success"],
            "cost_comparison": {
                "nova_cost": nova_result["cost"],
                "gemini_cost": gemini_result["cost"],
                "cost_difference": nova_result["cost"] - gemini_result["cost"],
                "nova_cheaper": nova_result["cost"] < gemini_result["cost"]
            },
            "performance_comparison": {
                "nova_time": nova_result["response_time"],
                "gemini_time": gemini_result["response_time"],
                "time_difference": nova_result["response_time"] - gemini_result["response_time"],
                "nova_faster": nova_result["response_time"] < gemini_result["response_time"]
            },
            "accuracy_comparison": {
                "nova_json_valid": nova_result["json_valid"],
                "gemini_json_valid": gemini_result["json_valid"],
                "nova_completeness": nova_result["completeness_score"],
                "gemini_completeness": gemini_result["completeness_score"],
                "nova_more_complete": nova_result["completeness_score"] > gemini_result["completeness_score"]
            }
        }
    
    async def run_full_comparison(self) -> Dict[str, Any]:
        """Run the complete A/B comparison test"""
        
        print("🧪 NOVA PRO vs GEMINI 2.5 PRO COMPARISON TEST")
        print("="*80)
        print(f"📊 Testing {len(self.test_companies)} companies with {len(self.research_prompts)} prompts each")
        print(f"🎯 Total comparisons: {len(self.test_companies) * len(self.research_prompts)}")
        print(f"⏱️ Estimated time: {len(self.test_companies) * len(self.research_prompts) * 2} minutes")
        
        # Test each company
        for i, company in enumerate(self.test_companies, 1):
            print(f"\n[{i}/{len(self.test_companies)}] Processing {company['name']}...")
            
            try:
                company_result = await self.test_company_with_both_models(company)
                self.results["company_results"].append(company_result)
                
                # Update running totals
                self.update_running_totals(company_result)
                
                # Save intermediate results
                if i % 3 == 0:  # Save every 3 companies
                    self.save_intermediate_results(f"comparison_results_partial_{i}")
                
            except Exception as e:
                print(f"❌ Failed to test {company['name']}: {e}")
                continue
        
        # Generate final analysis
        self.generate_final_analysis()
        
        return self.results
    
    def update_running_totals(self, company_result: Dict[str, Any]):
        """Update running cost and performance totals"""
        
        for prompt_name in self.research_prompts.keys():
            # Nova totals
            if prompt_name in company_result["nova_results"]:
                nova = company_result["nova_results"][prompt_name]
                if nova["success"]:
                    self.results["cost_analysis"]["nova_pro"]["total_tokens"] += nova["tokens_used"]
                    self.results["cost_analysis"]["nova_pro"]["total_cost"] += nova["cost"]
                    
                    if nova["json_valid"]:
                        self.results["accuracy_analysis"]["nova_pro"]["json_valid"] += 1
                    
                    self.results["accuracy_analysis"]["nova_pro"]["completeness_score"] += nova["completeness_score"]
                    self.results["performance_analysis"]["nova_pro"]["avg_response_time"] += nova["response_time"]
                    
                    if nova["success"]:
                        self.results["accuracy_analysis"]["nova_pro"]["structured_responses"] += 1
                else:
                    self.results["performance_analysis"]["nova_pro"]["errors"] += 1
            
            # Gemini totals
            if prompt_name in company_result["gemini_results"]:
                gemini = company_result["gemini_results"][prompt_name]
                if gemini["success"]:
                    self.results["cost_analysis"]["gemini_pro"]["total_tokens"] += gemini["tokens_used"]
                    self.results["cost_analysis"]["gemini_pro"]["total_cost"] += gemini["cost"]
                    
                    if gemini["json_valid"]:
                        self.results["accuracy_analysis"]["gemini_pro"]["json_valid"] += 1
                    
                    self.results["accuracy_analysis"]["gemini_pro"]["completeness_score"] += gemini["completeness_score"]
                    self.results["performance_analysis"]["gemini_pro"]["avg_response_time"] += gemini["response_time"]
                    
                    if gemini["success"]:
                        self.results["accuracy_analysis"]["gemini_pro"]["structured_responses"] += 1
                else:
                    self.results["performance_analysis"]["gemini_pro"]["errors"] += 1
    
    def generate_final_analysis(self):
        """Generate comprehensive final analysis"""
        
        total_comparisons = len(self.test_companies) * len(self.research_prompts)
        
        # Calculate averages
        nova_responses = self.results["accuracy_analysis"]["nova_pro"]["structured_responses"]
        gemini_responses = self.results["accuracy_analysis"]["gemini_pro"]["structured_responses"]
        
        if nova_responses > 0:
            self.results["cost_analysis"]["nova_pro"]["avg_cost_per_company"] = \
                self.results["cost_analysis"]["nova_pro"]["total_cost"] / len(self.test_companies)
            
            self.results["accuracy_analysis"]["nova_pro"]["completeness_score"] /= nova_responses
            self.results["performance_analysis"]["nova_pro"]["avg_response_time"] /= nova_responses
        
        if gemini_responses > 0:
            self.results["cost_analysis"]["gemini_pro"]["avg_cost_per_company"] = \
                self.results["cost_analysis"]["gemini_pro"]["total_cost"] / len(self.test_companies)
            
            self.results["accuracy_analysis"]["gemini_pro"]["completeness_score"] /= gemini_responses
            self.results["performance_analysis"]["gemini_pro"]["avg_response_time"] /= gemini_responses
        
        # Generate summary
        self.results["summary"] = {
            "winner_cost": "nova_pro" if self.results["cost_analysis"]["nova_pro"]["total_cost"] < 
                          self.results["cost_analysis"]["gemini_pro"]["total_cost"] else "gemini_pro",
            "winner_accuracy": "nova_pro" if self.results["accuracy_analysis"]["nova_pro"]["completeness_score"] > 
                              self.results["accuracy_analysis"]["gemini_pro"]["completeness_score"] else "gemini_pro",
            "winner_performance": "nova_pro" if self.results["performance_analysis"]["nova_pro"]["avg_response_time"] < 
                                 self.results["performance_analysis"]["gemini_pro"]["avg_response_time"] else "gemini_pro",
            "cost_savings_percentage": abs(
                (self.results["cost_analysis"]["nova_pro"]["total_cost"] - 
                 self.results["cost_analysis"]["gemini_pro"]["total_cost"]) / 
                max(self.results["cost_analysis"]["gemini_pro"]["total_cost"], 0.001) * 100
            ),
            "recommendation": self.generate_recommendation()
        }
    
    def generate_recommendation(self) -> str:
        """Generate final recommendation based on test results"""
        
        nova_cost = self.results["cost_analysis"]["nova_pro"]["total_cost"]
        gemini_cost = self.results["cost_analysis"]["gemini_pro"]["total_cost"]
        
        nova_accuracy = self.results["accuracy_analysis"]["nova_pro"]["completeness_score"]
        gemini_accuracy = self.results["accuracy_analysis"]["gemini_pro"]["completeness_score"]
        
        if nova_cost < gemini_cost * 0.8 and nova_accuracy > 0.7:
            return "STRONGLY_RECOMMEND_NOVA"
        elif nova_cost < gemini_cost and nova_accuracy >= gemini_accuracy * 0.9:
            return "RECOMMEND_NOVA"
        elif gemini_accuracy > nova_accuracy * 1.2:
            return "RECOMMEND_GEMINI_FOR_ACCURACY"
        elif nova_cost < gemini_cost * 0.9:
            return "RECOMMEND_NOVA_FOR_COST"
        else:
            return "NEUTRAL_BOTH_VIABLE"
    
    def save_results(self, filename: str = None):
        """Save detailed test results"""
        
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"nova_vs_gemini_comparison_{timestamp}.json"
        
        filepath = Path(__file__).parent / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filepath}")
        return filepath
    
    def save_intermediate_results(self, filename: str):
        """Save intermediate results during long test"""
        filepath = Path(__file__).parent / f"{filename}.json"
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
    
    def print_summary(self):
        """Print comprehensive test summary"""
        
        print(f"\n" + "="*80)
        print("📊 NOVA PRO vs GEMINI 2.5 PRO - FINAL RESULTS")
        print("="*80)
        
        # Cost Analysis
        print(f"\n💰 COST ANALYSIS:")
        print(f"   Nova Pro Total: ${self.results['cost_analysis']['nova_pro']['total_cost']:.4f}")
        print(f"   Gemini Pro Total: ${self.results['cost_analysis']['gemini_pro']['total_cost']:.4f}")
        print(f"   Cost Difference: {self.results['summary']['cost_savings_percentage']:.1f}%")
        print(f"   Winner: {self.results['summary']['winner_cost'].replace('_', ' ').title()}")
        
        # Accuracy Analysis
        print(f"\n🎯 ACCURACY ANALYSIS:")
        print(f"   Nova Pro Completeness: {self.results['accuracy_analysis']['nova_pro']['completeness_score']:.2f}")
        print(f"   Gemini Pro Completeness: {self.results['accuracy_analysis']['gemini_pro']['completeness_score']:.2f}")
        print(f"   Winner: {self.results['summary']['winner_accuracy'].replace('_', ' ').title()}")
        
        # Performance Analysis
        print(f"\n⚡ PERFORMANCE ANALYSIS:")
        print(f"   Nova Pro Avg Time: {self.results['performance_analysis']['nova_pro']['avg_response_time']:.2f}s")
        print(f"   Gemini Pro Avg Time: {self.results['performance_analysis']['gemini_pro']['avg_response_time']:.2f}s")
        print(f"   Winner: {self.results['summary']['winner_performance'].replace('_', ' ').title()}")
        
        # Final Recommendation
        print(f"\n🎯 FINAL RECOMMENDATION:")
        recommendation = self.results['summary']['recommendation']
        if recommendation == "STRONGLY_RECOMMEND_NOVA":
            print("   ✅ STRONGLY RECOMMEND NOVA PRO")
            print("   💡 Significant cost savings with good accuracy")
        elif recommendation == "RECOMMEND_NOVA":
            print("   ✅ RECOMMEND NOVA PRO")
            print("   💡 Better cost efficiency with comparable accuracy")
        elif recommendation == "RECOMMEND_GEMINI_FOR_ACCURACY":
            print("   ✅ RECOMMEND GEMINI PRO")
            print("   💡 Superior accuracy justifies higher cost")
        elif recommendation == "RECOMMEND_NOVA_FOR_COST":
            print("   ✅ RECOMMEND NOVA PRO FOR COST SAVINGS")
            print("   💡 Good cost savings, acceptable accuracy")
        else:
            print("   🤝 BOTH MODELS VIABLE")
            print("   💡 Choose based on specific priorities")


async def main():
    """Main test execution"""
    
    print("🧪 NOVA PRO vs GEMINI 2.5 PRO COMPARISON")
    print("="*50)
    print("This test will:")
    print("✅ Test 10 companies with both models")
    print("✅ Use 3 different research prompts per company")  
    print("✅ Measure cost, accuracy, and performance")
    print("✅ Generate comparative recommendations")
    print(f"\n⏱️ Estimated completion time: 60-90 minutes")
    
    # Initialize tester
    tester = ModelComparisonTester()
    
    try:
        # Run complete comparison
        results = await tester.run_full_comparison()
        
        # Print summary
        tester.print_summary()
        
        # Save results
        results_file = tester.save_results()
        
        print(f"\n🎉 Comparison test completed successfully!")
        print(f"📄 Detailed results: {results_file}")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Test interrupted by user")
        tester.save_results("nova_vs_gemini_interrupted")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())