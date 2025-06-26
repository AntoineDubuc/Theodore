#!/usr/bin/env python3
"""
4-Model Comparison Test: Nova Pro, Nova Lite, Gemini Pro, Gemini Flash
Comprehensive A/B testing for cost, accuracy, and performance comparison
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

class FourModelComparisonTester:
    """Comprehensive 4-model comparison framework"""
    
    def __init__(self):
        """Initialize the 4-model comparison tester"""
        
        # Test companies for consistent comparison (reduced for initial test)
        self.test_companies = [
            {"name": "Procurify", "domain": "procurify.com"},
            {"name": "Stripe", "domain": "stripe.com"}
        ]
        
        # Define all models to test with accurate pricing
        self.models_to_test = {
            "nova_pro": {
                "name": "Amazon Nova Pro",
                "model_id": "amazon.nova-pro-v1:0",
                "cost_per_1k_tokens": 0.0008,  # $0.80 per 1M tokens
                "client_type": "bedrock",
                "color": "🔵"
            },
            "nova_lite": {
                "name": "Amazon Nova Lite", 
                "model_id": "amazon.nova-lite-v1:0",
                "cost_per_1k_tokens": 0.00006,  # $0.06 per 1M tokens (13x cheaper than Nova Pro!)
                "client_type": "bedrock",
                "color": "🟦"
            },
            "gemini_pro": {
                "name": "Gemini 2.5 Pro",
                "model_id": "gemini-2.5-pro", 
                "cost_per_1k_tokens": 0.00125,  # $1.25 per 1M tokens
                "client_type": "gemini",
                "color": "🟢"
            },
            "gemini_flash": {
                "name": "Gemini 2.5 Flash",
                "model_id": "gemini-2.5-flash",
                "cost_per_1k_tokens": 0.000075,  # $0.075 per 1M tokens (16x cheaper than Gemini Pro!)
                "client_type": "gemini",
                "color": "🟡"
            }
        }
        
        # Standard research prompts for consistent testing
        self.research_prompts = {
            "business_model": """
            Analyze the business model of {company_name} ({domain}). Based on the scraped content, provide a structured analysis:
            
            1. Primary business model (B2B SaaS, B2C, Marketplace, etc.)
            2. Revenue streams (subscription, transaction fees, advertising, etc.)
            3. Target market and customer segments
            4. Competitive positioning and value proposition
            5. Company stage (startup, growth, mature)
            
            Return as JSON with these exact keys: business_model, revenue_streams, target_market, positioning, company_stage.
            """,
            
            "technical_assessment": """
            Assess the technical sophistication of {company_name} ({domain}) based on the content:
            
            1. Technology stack indicators
            2. Engineering capabilities and approach
            3. Product complexity and technical differentiation
            4. Developer community engagement
            5. Technical innovation level (score 1-10)
            
            Return as JSON with keys: tech_stack, engineering_capabilities, product_complexity, developer_engagement, innovation_score.
            """,
            
            "market_analysis": """
            Analyze {company_name} ({domain}) from a market perspective:
            
            1. Market size and opportunity
            2. Competitive landscape position
            3. Growth indicators and market traction
            4. Industry trends and company alignment
            5. Investment attractiveness (score 1-10)
            
            Return as JSON with keys: market_size, competitive_position, growth_indicators, industry_alignment, investment_score.
            """
        }
        
        self.results = {
            "test_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "test_companies": len(self.test_companies),
                "prompts_tested": len(self.research_prompts),
                "models_tested": len(self.models_to_test),
                "total_comparisons": len(self.test_companies) * len(self.research_prompts) * len(self.models_to_test),
                "models": {k: v["name"] for k, v in self.models_to_test.items()}
            },
            "company_results": [],
            "cost_analysis": {model_key: {
                "total_tokens": 0, 
                "total_cost": 0.0, 
                "avg_cost_per_company": 0.0,
                "cost_per_1k_tokens": self.models_to_test[model_key]["cost_per_1k_tokens"]
            } for model_key in self.models_to_test.keys()},
            "accuracy_analysis": {model_key: {
                "structured_responses": 0, 
                "json_valid": 0, 
                "completeness_score": 0.0,
                "avg_response_length": 0.0
            } for model_key in self.models_to_test.keys()},
            "performance_analysis": {model_key: {
                "avg_response_time": 0.0, 
                "timeouts": 0, 
                "errors": 0,
                "successful_requests": 0
            } for model_key in self.models_to_test.keys()}
        }
    
    async def test_company_with_all_models(self, company: Dict[str, str]) -> Dict[str, Any]:
        """Test a single company with all 4 models"""
        
        print(f"\n🏢 Testing: {company['name']} ({company['domain']})")
        print("="*80)
        
        company_result = {
            "company": company,
            "timestamp": datetime.utcnow().isoformat(),
            "scraped_content": None,
            "model_results": {model_key: {} for model_key in self.models_to_test.keys()},
            "prompt_comparisons": {}
        }
        
        # Step 1: Scrape company content (same input for all models)
        scraped_content = await self.scrape_company_content(company)
        company_result["scraped_content"] = {
            "content_length": len(scraped_content) if scraped_content else 0,
            "scraping_success": scraped_content is not None
        }
        
        if not scraped_content:
            print(f"❌ Failed to scrape content for {company['name']}")
            return company_result
        
        print(f"✅ Scraped {len(scraped_content)} characters of content")
        
        # Step 2: Test each prompt with all 4 models
        for prompt_name, prompt_template in self.research_prompts.items():
            print(f"\n📋 Testing prompt: {prompt_name}")
            print("-" * 60)
            
            # Format prompt with company data
            formatted_prompt = prompt_template.format(
                company_name=company['name'],
                domain=company['domain']
            )
            full_prompt = f"{formatted_prompt}\n\nCompany Content:\n{scraped_content[:8000]}"
            
            prompt_results = {}
            
            # Test each model
            for model_key, model_config in self.models_to_test.items():
                print(f"{model_config['color']} Testing with {model_config['name']}...")
                
                if model_config['client_type'] == 'bedrock':
                    result = await self.test_with_bedrock_model(
                        full_prompt, model_config, company['name'], prompt_name
                    )
                elif model_config['client_type'] == 'gemini':
                    result = await self.test_with_gemini_model(
                        full_prompt, model_config, company['name'], prompt_name
                    )
                
                prompt_results[model_key] = result
                
                # Store in company results
                if prompt_name not in company_result["model_results"][model_key]:
                    company_result["model_results"][model_key][prompt_name] = result
                
                # Small delay between model requests
                await asyncio.sleep(1)
            
            # Compare all models for this prompt
            company_result["prompt_comparisons"][prompt_name] = self.compare_prompt_across_models(prompt_results, prompt_name)
            
            # Longer delay between prompts
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
                max_pages_to_scrape=15,  # Reduced for faster testing
                timeout_seconds=25
            )
            
            scraper = IntelligentCompanyScraperSync(config)
            
            print(f"🔍 Scraping {company['name']}...")
            
            # Create a temporary CompanyData object
            from models import CompanyData
            temp_company_data = CompanyData(
                name=company['name'],
                website=f"https://{company['domain']}"
            )
            
            scraping_result = scraper.scrape_company(temp_company_data)
            
            # Handle both dict and object returns from scraper
            if isinstance(scraping_result, dict):
                if scraping_result.get('success') and scraping_result.get('aggregated_content'):
                    return scraping_result['aggregated_content']
                else:
                    print(f"❌ Scraping failed: {scraping_result.get('error', 'Unknown error')}")
                    return None
            else:
                # Handle CompanyData object
                if hasattr(scraping_result, 'success') and scraping_result.success and hasattr(scraping_result, 'aggregated_content') and scraping_result.aggregated_content:
                    return scraping_result.aggregated_content
                else:
                    error_msg = getattr(scraping_result, 'error_message', 'Unknown error')
                    print(f"❌ Scraping failed: {error_msg}")
                    return None
                
        except Exception as e:
            print(f"❌ Scraping error: {e}")
            return None
    
    async def test_with_bedrock_model(self, prompt: str, model_config: Dict, company_name: str, prompt_type: str) -> Dict[str, Any]:
        """Test with Nova models via Bedrock"""
        
        start_time = time.time()
        result = {
            "model": model_config["name"],
            "model_id": model_config["model_id"],
            "prompt_type": prompt_type,
            "company": company_name,
            "success": False,
            "response": None,
            "tokens_used": 0,
            "cost": 0.0,
            "response_time": 0.0,
            "error": None,
            "json_valid": False,
            "completeness_score": 0.0,
            "response_length": 0
        }
        
        try:
            # Import Nova client
            import sys
            sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))
            from bedrock_client import BedrockClient
            
            client = BedrockClient()
            
            # Make request with specific model
            response = await asyncio.to_thread(
                client.analyze_with_bedrock,
                prompt,
                model_id=model_config["model_id"],
                max_tokens=4000
            )
            
            result["response_time"] = time.time() - start_time
            
            if response:
                result["success"] = True
                result["response"] = response
                result["response_length"] = len(response)
                
                # Calculate tokens and cost
                estimated_tokens = len(prompt.split()) + len(response.split())
                result["tokens_used"] = estimated_tokens
                result["cost"] = estimated_tokens * model_config["cost_per_1k_tokens"]
                
                # Assess response quality
                result["json_valid"] = self.is_valid_json_response(response)
                result["completeness_score"] = self.assess_response_completeness(response, prompt_type)
                
                print(f"   ✅ Success: {estimated_tokens} tokens, ${result['cost']:.6f}, {result['response_time']:.1f}s")
            else:
                result["error"] = f"No response from {model_config['name']}"
                print(f"   ❌ No response received")
                
        except Exception as e:
            result["error"] = str(e)
            result["response_time"] = time.time() - start_time
            print(f"   ❌ Error: {e}")
        
        return result
    
    async def test_with_gemini_model(self, prompt: str, model_config: Dict, company_name: str, prompt_type: str) -> Dict[str, Any]:
        """Test with Gemini models"""
        
        start_time = time.time()
        result = {
            "model": model_config["name"],
            "model_id": model_config["model_id"],
            "prompt_type": prompt_type,
            "company": company_name,
            "success": False,
            "response": None,
            "tokens_used": 0,
            "cost": 0.0,
            "response_time": 0.0,
            "error": None,
            "json_valid": False,
            "completeness_score": 0.0,
            "response_length": 0
        }
        
        try:
            # Import Gemini client
            import sys
            sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))
            from gemini_client import GeminiClient
            
            client = GeminiClient()
            
            # Make request with specific model
            response = await asyncio.to_thread(
                client.analyze_with_gemini,
                prompt,
                model_name=model_config["model_id"]
            )
            
            result["response_time"] = time.time() - start_time
            
            if response:
                result["success"] = True
                result["response"] = response
                result["response_length"] = len(response)
                
                # Calculate tokens and cost
                estimated_tokens = len(prompt.split()) + len(response.split())
                result["tokens_used"] = estimated_tokens
                result["cost"] = estimated_tokens * model_config["cost_per_1k_tokens"]
                
                # Assess response quality
                result["json_valid"] = self.is_valid_json_response(response)
                result["completeness_score"] = self.assess_response_completeness(response, prompt_type)
                
                print(f"   ✅ Success: {estimated_tokens} tokens, ${result['cost']:.6f}, {result['response_time']:.1f}s")
            else:
                result["error"] = f"No response from {model_config['name']}"
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
    
    def compare_prompt_across_models(self, prompt_results: Dict, prompt_name: str) -> Dict:
        """Compare results from all 4 models for a specific prompt"""
        
        successful_models = {k: v for k, v in prompt_results.items() if v["success"]}
        
        if not successful_models:
            return {"prompt": prompt_name, "successful_models": 0, "comparison": "No successful responses"}
        
        # Find best performers
        cost_ranking = sorted(successful_models.items(), key=lambda x: x[1]["cost"])
        accuracy_ranking = sorted(successful_models.items(), key=lambda x: x[1]["completeness_score"], reverse=True)
        speed_ranking = sorted(successful_models.items(), key=lambda x: x[1]["response_time"])
        
        return {
            "prompt": prompt_name,
            "successful_models": len(successful_models),
            "cost_winner": cost_ranking[0][0] if cost_ranking else None,
            "accuracy_winner": accuracy_ranking[0][0] if accuracy_ranking else None,
            "speed_winner": speed_ranking[0][0] if speed_ranking else None,
            "cost_range": {
                "cheapest": cost_ranking[0][1]["cost"] if cost_ranking else 0,
                "most_expensive": cost_ranking[-1][1]["cost"] if cost_ranking else 0
            },
            "accuracy_range": {
                "highest": accuracy_ranking[0][1]["completeness_score"] if accuracy_ranking else 0,
                "lowest": accuracy_ranking[-1][1]["completeness_score"] if accuracy_ranking else 0
            },
            "detailed_results": {k: {
                "cost": v["cost"],
                "accuracy": v["completeness_score"], 
                "speed": v["response_time"],
                "json_valid": v["json_valid"]
            } for k, v in successful_models.items()}
        }
    
    async def run_full_comparison(self) -> Dict[str, Any]:
        """Run the complete 4-model comparison test"""
        
        print("🧪 4-MODEL AI COMPARISON TEST")
        print("="*80)
        print("🔵 Amazon Nova Pro   | 🟦 Amazon Nova Lite")
        print("🟢 Gemini 2.5 Pro   | 🟡 Gemini 2.5 Flash")
        print("="*80)
        print(f"📊 Testing {len(self.test_companies)} companies with {len(self.research_prompts)} prompts each")
        print(f"🎯 Total comparisons: {len(self.test_companies) * len(self.research_prompts) * len(self.models_to_test)}")
        print(f"⏱️ Estimated time: {len(self.test_companies) * len(self.research_prompts) * 2} minutes")
        
        # Test each company
        for i, company in enumerate(self.test_companies, 1):
            print(f"\n[{i}/{len(self.test_companies)}] Processing {company['name']}...")
            
            try:
                company_result = await self.test_company_with_all_models(company)
                self.results["company_results"].append(company_result)
                
                # Update running totals
                self.update_running_totals(company_result)
                
                # Save intermediate results
                if i % 2 == 0:  # Save every 2 companies
                    self.save_intermediate_results(f"4model_comparison_partial_{i}")
                
                # Show progress summary
                self.print_progress_summary(i)
                
            except Exception as e:
                print(f"❌ Failed to test {company['name']}: {e}")
                continue
        
        # Generate final analysis
        self.generate_final_analysis()
        
        return self.results
    
    def update_running_totals(self, company_result: Dict[str, Any]):
        """Update running cost and performance totals"""
        
        for model_key in self.models_to_test.keys():
            for prompt_name in self.research_prompts.keys():
                if prompt_name in company_result["model_results"][model_key]:
                    result = company_result["model_results"][model_key][prompt_name]
                    
                    if result["success"]:
                        # Update cost analysis
                        self.results["cost_analysis"][model_key]["total_tokens"] += result["tokens_used"]
                        self.results["cost_analysis"][model_key]["total_cost"] += result["cost"]
                        
                        # Update accuracy analysis
                        if result["json_valid"]:
                            self.results["accuracy_analysis"][model_key]["json_valid"] += 1
                        
                        self.results["accuracy_analysis"][model_key]["completeness_score"] += result["completeness_score"]
                        self.results["accuracy_analysis"][model_key]["avg_response_length"] += result["response_length"]
                        self.results["accuracy_analysis"][model_key]["structured_responses"] += 1
                        
                        # Update performance analysis
                        self.results["performance_analysis"][model_key]["avg_response_time"] += result["response_time"]
                        self.results["performance_analysis"][model_key]["successful_requests"] += 1
                    else:
                        self.results["performance_analysis"][model_key]["errors"] += 1
    
    def print_progress_summary(self, companies_completed: int):
        """Print progress summary after each company"""
        
        print(f"\n📊 PROGRESS SUMMARY ({companies_completed}/{len(self.test_companies)} companies)")
        print("-" * 60)
        
        for model_key, model_config in self.models_to_test.items():
            cost = self.results["cost_analysis"][model_key]["total_cost"]
            successes = self.results["performance_analysis"][model_key]["successful_requests"]
            errors = self.results["performance_analysis"][model_key]["errors"]
            
            print(f"{model_config['color']} {model_config['name']}: ${cost:.4f} | {successes} success | {errors} errors")
    
    def generate_final_analysis(self):
        """Generate comprehensive final analysis"""
        
        # Calculate averages for each model
        for model_key in self.models_to_test.keys():
            successful_requests = self.results["performance_analysis"][model_key]["successful_requests"]
            
            if successful_requests > 0:
                # Cost averages
                self.results["cost_analysis"][model_key]["avg_cost_per_company"] = \
                    self.results["cost_analysis"][model_key]["total_cost"] / len(self.test_companies)
                
                # Accuracy averages
                self.results["accuracy_analysis"][model_key]["completeness_score"] /= successful_requests
                self.results["accuracy_analysis"][model_key]["avg_response_length"] /= successful_requests
                
                # Performance averages
                self.results["performance_analysis"][model_key]["avg_response_time"] /= successful_requests
        
        # Generate rankings
        models = list(self.models_to_test.keys())
        
        # Cost ranking (lower is better)
        cost_ranking = sorted(models, key=lambda m: self.results["cost_analysis"][m]["total_cost"])
        
        # Accuracy ranking (higher is better)
        accuracy_ranking = sorted(models, 
                                key=lambda m: self.results["accuracy_analysis"][m]["completeness_score"], 
                                reverse=True)
        
        # Speed ranking (lower is better)
        speed_ranking = sorted(models, 
                             key=lambda m: self.results["performance_analysis"][m]["avg_response_time"])
        
        self.results["rankings"] = {
            "cost_efficiency": cost_ranking,
            "accuracy": accuracy_ranking,
            "speed": speed_ranking
        }
        
        # Generate overall recommendation
        self.results["recommendation"] = self.generate_overall_recommendation()
    
    def generate_overall_recommendation(self) -> Dict[str, str]:
        """Generate overall recommendations based on test results"""
        
        recommendations = {}
        
        # Cost winner
        cost_winner = self.results["rankings"]["cost_efficiency"][0]
        cost_winner_name = self.models_to_test[cost_winner]["name"]
        cost_savings = ((self.results["cost_analysis"][self.results["rankings"]["cost_efficiency"][-1]]["total_cost"] - 
                        self.results["cost_analysis"][cost_winner]["total_cost"]) / 
                       max(self.results["cost_analysis"][self.results["rankings"]["cost_efficiency"][-1]]["total_cost"], 0.001)) * 100
        
        recommendations["cost_efficiency"] = f"{cost_winner_name} - {cost_savings:.1f}% cheaper than most expensive"
        
        # Accuracy winner
        accuracy_winner = self.results["rankings"]["accuracy"][0]
        accuracy_winner_name = self.models_to_test[accuracy_winner]["name"]
        accuracy_score = self.results["accuracy_analysis"][accuracy_winner]["completeness_score"]
        
        recommendations["accuracy"] = f"{accuracy_winner_name} - {accuracy_score:.2f} completeness score"
        
        # Speed winner
        speed_winner = self.results["rankings"]["speed"][0]
        speed_winner_name = self.models_to_test[speed_winner]["name"]
        speed_time = self.results["performance_analysis"][speed_winner]["avg_response_time"]
        
        recommendations["speed"] = f"{speed_winner_name} - {speed_time:.1f}s average response time"
        
        # Overall recommendation
        if cost_winner == accuracy_winner:
            recommendations["overall"] = f"STRONGLY RECOMMEND {cost_winner_name} - Best cost AND accuracy"
        elif cost_winner in self.results["rankings"]["accuracy"][:2]:
            recommendations["overall"] = f"RECOMMEND {cost_winner_name} - Best cost with good accuracy"
        else:
            recommendations["overall"] = f"BALANCED CHOICE NEEDED - Cost leader: {cost_winner_name}, Accuracy leader: {accuracy_winner_name}"
        
        return recommendations
    
    def save_results(self, filename: str = None):
        """Save detailed test results"""
        
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"4model_comparison_{timestamp}.json"
        
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
    
    def print_comprehensive_summary(self):
        """Print comprehensive test summary"""
        
        print(f"\n" + "="*80)
        print("📊 4-MODEL AI COMPARISON - FINAL RESULTS")
        print("="*80)
        
        # Model overview
        print(f"\n🎯 MODELS TESTED:")
        for model_key, model_config in self.models_to_test.items():
            total_cost = self.results["cost_analysis"][model_key]["total_cost"]
            avg_accuracy = self.results["accuracy_analysis"][model_key]["completeness_score"]
            avg_speed = self.results["performance_analysis"][model_key]["avg_response_time"]
            
            print(f"   {model_config['color']} {model_config['name']}")
            print(f"      💰 Total Cost: ${total_cost:.6f}")
            print(f"      🎯 Avg Accuracy: {avg_accuracy:.2f}")
            print(f"      ⚡ Avg Speed: {avg_speed:.1f}s")
        
        # Rankings
        print(f"\n🏆 RANKINGS:")
        print(f"   💰 Cost Efficiency: {' > '.join([self.models_to_test[m]['name'] for m in self.results['rankings']['cost_efficiency']])}")
        print(f"   🎯 Accuracy: {' > '.join([self.models_to_test[m]['name'] for m in self.results['rankings']['accuracy']])}")
        print(f"   ⚡ Speed: {' > '.join([self.models_to_test[m]['name'] for m in self.results['rankings']['speed']])}")
        
        # Cost comparison
        print(f"\n💰 COST ANALYSIS:")
        cheapest = self.results["rankings"]["cost_efficiency"][0]
        most_expensive = self.results["rankings"]["cost_efficiency"][-1]
        
        cheapest_cost = self.results["cost_analysis"][cheapest]["total_cost"]
        expensive_cost = self.results["cost_analysis"][most_expensive]["total_cost"]
        savings_ratio = expensive_cost / max(cheapest_cost, 0.000001)
        
        print(f"   🥇 Cheapest: {self.models_to_test[cheapest]['name']} - ${cheapest_cost:.6f}")
        print(f"   💸 Most Expensive: {self.models_to_test[most_expensive]['name']} - ${expensive_cost:.6f}")
        print(f"   📊 Cost Difference: {savings_ratio:.1f}x more expensive")
        
        # Recommendations
        print(f"\n🎯 RECOMMENDATIONS:")
        for category, recommendation in self.results["recommendation"].items():
            print(f"   {category.title().replace('_', ' ')}: {recommendation}")


async def main():
    """Main test execution"""
    
    print("🚀 4-MODEL AI COMPARISON FRAMEWORK")
    print("="*60)
    print("Testing Nova Pro, Nova Lite, Gemini Pro, Gemini Flash")
    print("Real-world cost, accuracy, and performance comparison")
    print(f"\n⏱️ Estimated completion time: 90-120 minutes")
    
    # Confirm execution
    print(f"\nThis test will:")
    print(f"✅ Test 10 companies with 4 different AI models")
    print(f"✅ Use 3 research prompts per company (120 total API calls)")
    print(f"✅ Measure cost, accuracy, speed, and response quality")
    print(f"✅ Generate detailed comparison reports")
    print(f"✅ Provide concrete recommendations for Theodore")
    
    # Initialize tester
    tester = FourModelComparisonTester()
    
    try:
        # Run complete comparison
        results = await tester.run_full_comparison()
        
        # Print comprehensive summary
        tester.print_comprehensive_summary()
        
        # Save results
        results_file = tester.save_results()
        
        print(f"\n🎉 4-model comparison test completed successfully!")
        print(f"📄 Detailed results: {results_file}")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Test interrupted by user")
        tester.save_results("4model_comparison_interrupted")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())