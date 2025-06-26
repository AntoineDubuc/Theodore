#!/usr/bin/env python3
"""
Simplified 4-Model Comparison Test: Nova Pro, Nova Lite, Gemini Pro, Gemini Flash
Uses sample content to test AI models directly without scraping complexity
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

class Simple4ModelTester:
    """Simplified 4-model comparison using sample content"""
    
    def __init__(self):
        # Sample company content for testing
        self.sample_content = {
            "Procurify": """
            Procurify is a comprehensive procurement and spend management platform designed to help organizations 
            streamline their purchasing processes. The company offers a cloud-based solution that enables businesses 
            to manage purchase orders, invoices, budgets, and supplier relationships in one centralized platform.
            
            Key features include automated approval workflows, real-time budget tracking, supplier management,
            and detailed analytics and reporting. Procurify serves mid-market and enterprise customers across
            various industries including healthcare, education, manufacturing, and technology.
            
            The platform integrates with popular accounting systems like QuickBooks, NetSuite, and Sage,
            making it easy for companies to adopt without disrupting existing workflows. Procurify was founded
            in 2013 and is headquartered in Vancouver, Canada, with a growing customer base across North America.
            """,
            
            "Stripe": """
            Stripe is a leading financial technology company that provides payment processing services for 
            internet businesses. The company offers a comprehensive suite of APIs and tools that enable 
            businesses to accept and manage online payments across various channels and geographies.
            
            Stripe's platform handles everything from payment processing to fraud prevention, subscription
            billing, and marketplace payments. The company serves businesses of all sizes, from startups
            to large enterprises, including notable customers like Amazon, Google, Microsoft, and Shopify.
            
            Founded in 2010 by brothers Patrick and John Collison, Stripe is headquartered in San Francisco
            and has expanded globally with offices in multiple countries. The company has raised significant
            funding and achieved a valuation of over $95 billion, making it one of the most valuable
            private fintech companies in the world.
            """
        }
        
        # Define all models to test
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
                "cost_per_1k_tokens": 0.00006,  # $0.06 per 1M tokens (13x cheaper!)
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
                "cost_per_1k_tokens": 0.000075,  # $0.075 per 1M tokens (16x cheaper!)
                "client_type": "gemini",
                "color": "🟡"
            }
        }
        
        # Test prompt
        self.test_prompt = """
        Analyze this company based on the provided content and return a JSON response with:
        
        1. business_model: Primary revenue model (B2B SaaS, marketplace, etc.)
        2. target_market: Who they serve (SMB, enterprise, consumers, etc.)
        3. competitive_advantages: Top 3 key differentiators
        4. company_stage: startup, growth, or mature
        5. technology_sophistication: score from 1-10
        
        Company: {company_name}
        Content: {content}
        
        Return only valid JSON with these exact keys.
        """
        
        self.results = {
            "test_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "models_tested": len(self.models_to_test),
                "companies_tested": len(self.sample_content)
            },
            "model_results": {},
            "cost_analysis": {},
            "performance_analysis": {},
            "accuracy_analysis": {}
        }
    
    async def test_all_models(self):
        """Test all models with all companies"""
        
        print("🧪 SIMPLIFIED 4-MODEL AI COMPARISON TEST")
        print("="*80)
        print("🔵 Amazon Nova Pro   | 🟦 Amazon Nova Lite")
        print("🟢 Gemini 2.5 Pro   | 🟡 Gemini 2.5 Flash")
        print("="*80)
        
        for company_name, content in self.sample_content.items():
            print(f"\n🏢 Testing: {company_name}")
            print("-" * 60)
            
            # Format prompt for this company
            formatted_prompt = self.test_prompt.format(
                company_name=company_name,
                content=content
            )
            
            company_results = {}
            
            # Test each model
            for model_key, model_config in self.models_to_test.items():
                print(f"{model_config['color']} Testing {model_config['name']}...")
                
                if model_config['client_type'] == 'bedrock':
                    result = await self.test_bedrock_model(formatted_prompt, model_config, company_name)
                elif model_config['client_type'] == 'gemini':
                    result = await self.test_gemini_model(formatted_prompt, model_config, company_name)
                
                company_results[model_key] = result
                
                # Small delay between requests
                await asyncio.sleep(2)
            
            self.results["model_results"][company_name] = company_results
            print(f"\n✅ Completed testing for {company_name}")
        
        # Generate analysis
        self.analyze_results()
        
        return self.results
    
    async def test_bedrock_model(self, prompt: str, model_config: Dict, company_name: str) -> Dict:
        """Test with Bedrock models (Nova)"""
        
        start_time = time.time()
        result = {
            "model": model_config["name"],
            "model_id": model_config["model_id"],
            "company": company_name,
            "success": False,
            "response": None,
            "tokens_used": 0,
            "cost": 0.0,
            "response_time": 0.0,
            "error": None,
            "json_valid": False
        }
        
        try:
            # Import Bedrock client and config
            import sys
            sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))
            from bedrock_client import BedrockClient
            from models import CompanyIntelligenceConfig
            
            # Create minimal config for testing
            config = CompanyIntelligenceConfig()
            client = BedrockClient(config)
            
            # Make request
            response = await asyncio.to_thread(
                client.analyze_content,
                prompt
            )
            
            result["response_time"] = time.time() - start_time
            
            if response:
                result["success"] = True
                result["response"] = response
                
                # Calculate cost
                estimated_tokens = len(prompt.split()) + len(response.split())
                result["tokens_used"] = estimated_tokens
                result["cost"] = (estimated_tokens / 1000) * model_config["cost_per_1k_tokens"]
                
                # Check JSON validity
                result["json_valid"] = self.is_valid_json(response)
                
                print(f"   ✅ Success: {estimated_tokens} tokens, ${result['cost']:.6f}, {result['response_time']:.1f}s, JSON: {result['json_valid']}")
            else:
                result["error"] = "No response received"
                print("   ❌ No response received")
                
        except Exception as e:
            result["error"] = str(e)
            result["response_time"] = time.time() - start_time
            print(f"   ❌ Error: {e}")
        
        return result
    
    async def test_gemini_model(self, prompt: str, model_config: Dict, company_name: str) -> Dict:
        """Test with Gemini models"""
        
        start_time = time.time()
        result = {
            "model": model_config["name"],
            "model_id": model_config["model_id"],
            "company": company_name,
            "success": False,
            "response": None,
            "tokens_used": 0,
            "cost": 0.0,
            "response_time": 0.0,
            "error": None,
            "json_valid": False
        }
        
        try:
            # Import Gemini client and config
            import sys
            sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))
            from gemini_client import GeminiClient
            from models import CompanyIntelligenceConfig
            
            # Create minimal config for testing
            config = CompanyIntelligenceConfig()
            client = GeminiClient(config)
            
            # Make request
            response = await asyncio.to_thread(
                client.analyze_content,
                prompt
            )
            
            result["response_time"] = time.time() - start_time
            
            if response:
                result["success"] = True
                result["response"] = response
                
                # Calculate cost
                estimated_tokens = len(prompt.split()) + len(response.split())
                result["tokens_used"] = estimated_tokens
                result["cost"] = (estimated_tokens / 1000) * model_config["cost_per_1k_tokens"]
                
                # Check JSON validity
                result["json_valid"] = self.is_valid_json(response)
                
                print(f"   ✅ Success: {estimated_tokens} tokens, ${result['cost']:.6f}, {result['response_time']:.1f}s, JSON: {result['json_valid']}")
            else:
                result["error"] = "No response received"
                print("   ❌ No response received")
                
        except Exception as e:
            result["error"] = str(e)
            result["response_time"] = time.time() - start_time
            print(f"   ❌ Error: {e}")
        
        return result
    
    def is_valid_json(self, response: str) -> bool:
        """Check if response contains valid JSON"""
        try:
            import re
            json_matches = re.findall(r'\{.*\}', response, re.DOTALL)
            if json_matches:
                json.loads(json_matches[0])
                return True
            return False
        except:
            return False
    
    def analyze_results(self):
        """Analyze test results across all models"""
        
        # Initialize analysis
        for model_key in self.models_to_test.keys():
            self.results["cost_analysis"][model_key] = {
                "total_cost": 0.0,
                "total_tokens": 0,
                "successful_requests": 0
            }
            self.results["performance_analysis"][model_key] = {
                "avg_response_time": 0.0,
                "successful_requests": 0,
                "errors": 0
            }
            self.results["accuracy_analysis"][model_key] = {
                "json_valid_count": 0,
                "total_requests": 0
            }
        
        # Aggregate results
        for company_name, company_results in self.results["model_results"].items():
            for model_key, result in company_results.items():
                
                # Cost analysis
                if result["success"]:
                    self.results["cost_analysis"][model_key]["total_cost"] += result["cost"]
                    self.results["cost_analysis"][model_key]["total_tokens"] += result["tokens_used"]
                    self.results["cost_analysis"][model_key]["successful_requests"] += 1
                    
                    # Performance analysis
                    self.results["performance_analysis"][model_key]["avg_response_time"] += result["response_time"]
                    self.results["performance_analysis"][model_key]["successful_requests"] += 1
                else:
                    self.results["performance_analysis"][model_key]["errors"] += 1
                
                # Accuracy analysis
                self.results["accuracy_analysis"][model_key]["total_requests"] += 1
                if result["json_valid"]:
                    self.results["accuracy_analysis"][model_key]["json_valid_count"] += 1
        
        # Calculate averages
        for model_key in self.models_to_test.keys():
            successful = self.results["performance_analysis"][model_key]["successful_requests"]
            if successful > 0:
                self.results["performance_analysis"][model_key]["avg_response_time"] /= successful
    
    def print_summary(self):
        """Print comprehensive test summary"""
        
        print(f"\n" + "="*80)
        print("📊 4-MODEL AI COMPARISON - FINAL RESULTS")
        print("="*80)
        
        # Cost rankings
        cost_ranking = sorted(
            self.models_to_test.keys(),
            key=lambda m: self.results["cost_analysis"][m]["total_cost"]
        )
        
        # Performance rankings
        perf_ranking = sorted(
            self.models_to_test.keys(),
            key=lambda m: self.results["performance_analysis"][m]["avg_response_time"]
        )
        
        # Accuracy rankings
        acc_ranking = sorted(
            self.models_to_test.keys(),
            key=lambda m: (self.results["accuracy_analysis"][m]["json_valid_count"] / 
                          max(self.results["accuracy_analysis"][m]["total_requests"], 1)),
            reverse=True
        )
        
        print(f"\n🎯 MODEL PERFORMANCE:")
        for model_key in self.models_to_test.keys():
            model_name = self.models_to_test[model_key]["name"]
            color = self.models_to_test[model_key]["color"]
            total_cost = self.results["cost_analysis"][model_key]["total_cost"]
            avg_time = self.results["performance_analysis"][model_key]["avg_response_time"]
            json_valid = self.results["accuracy_analysis"][model_key]["json_valid_count"]
            total_req = self.results["accuracy_analysis"][model_key]["total_requests"]
            
            print(f"   {color} {model_name}:")
            print(f"      💰 Total Cost: ${total_cost:.6f}")
            print(f"      ⚡ Avg Speed: {avg_time:.1f}s")
            print(f"      🎯 JSON Success: {json_valid}/{total_req}")
        
        print(f"\n🏆 RANKINGS:")
        print(f"   💰 Cost (cheapest first): {' > '.join([self.models_to_test[m]['name'] for m in cost_ranking])}")
        print(f"   ⚡ Speed (fastest first): {' > '.join([self.models_to_test[m]['name'] for m in perf_ranking])}")
        print(f"   🎯 Accuracy (best first): {' > '.join([self.models_to_test[m]['name'] for m in acc_ranking])}")
        
        # Recommendations
        print(f"\n🎯 RECOMMENDATIONS:")
        cost_winner = cost_ranking[0]
        speed_winner = perf_ranking[0]
        accuracy_winner = acc_ranking[0]
        
        print(f"   💰 Best Cost: {self.models_to_test[cost_winner]['name']} - ${self.results['cost_analysis'][cost_winner]['total_cost']:.6f}")
        print(f"   ⚡ Best Speed: {self.models_to_test[speed_winner]['name']} - {self.results['performance_analysis'][speed_winner]['avg_response_time']:.1f}s")
        print(f"   🎯 Best Accuracy: {self.models_to_test[accuracy_winner]['name']} - {self.results['accuracy_analysis'][accuracy_winner]['json_valid_count']}/{self.results['accuracy_analysis'][accuracy_winner]['total_requests']} JSON success")
        
        # Overall recommendation
        if cost_winner == accuracy_winner:
            print(f"   🌟 STRONGLY RECOMMEND: {self.models_to_test[cost_winner]['name']} - Best cost AND accuracy!")
        elif cost_winner in acc_ranking[:2]:
            print(f"   ✅ RECOMMEND: {self.models_to_test[cost_winner]['name']} - Best cost with good accuracy")
        else:
            print(f"   ⚖️ BALANCED CHOICE: {self.models_to_test[cost_winner]['name']} for cost, {self.models_to_test[accuracy_winner]['name']} for accuracy")
    
    def save_results(self, filename: str = None):
        """Save detailed test results"""
        
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"simple_4model_comparison_{timestamp}.json"
        
        filepath = Path(__file__).parent / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filepath}")
        return filepath


async def main():
    """Main test execution"""
    
    print("🚀 SIMPLIFIED 4-MODEL AI COMPARISON")
    print("="*60)
    print("Testing Nova Pro, Nova Lite, Gemini Pro, Gemini Flash")
    print("Using sample company content for direct model comparison")
    print(f"\n⏱️ Estimated completion time: 2-3 minutes")
    
    # Initialize tester
    tester = Simple4ModelTester()
    
    try:
        # Run comparison
        results = await tester.test_all_models()
        
        # Print summary
        tester.print_summary()
        
        # Save results
        results_file = tester.save_results()
        
        print(f"\n🎉 4-model comparison test completed successfully!")
        print(f"📄 Detailed results: {results_file}")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())