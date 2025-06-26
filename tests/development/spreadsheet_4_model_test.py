#!/usr/bin/env python3
"""
Spreadsheet 4-Model Comparison Test
Reads 10 random companies from Google Sheets, runs 4-model AI comparison, and writes results to new tab
"""

import os
import json
import time
import asyncio
import random
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import re

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

class Spreadsheet4ModelTester:
    """4-model comparison using real companies from Google Sheets with Theodore scraper"""
    
    def __init__(self):
        # Google Sheets URL
        self.sheet_url = "https://docs.google.com/spreadsheets/d/1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk/edit?gid=81910028#gid=81910028"
        self.sheet_id = "1dD1pw9yJzRPFnZRRKGldCJpc29fGmK0vQ-g5sBG-bZk"
        
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
        
        # Research prompts for analysis
        self.research_prompts = {
            "business_model": """
            Analyze this company's business model based on the scraped content. Return a JSON response with:
            
            1. business_model: Primary revenue model (B2B SaaS, B2C, marketplace, consulting, etc.)
            2. target_market: Who they serve (SMB, enterprise, consumers, healthcare, fintech, etc.)
            3. competitive_advantages: Top 3 key differentiators or unique value propositions
            4. company_stage: startup, growth, or mature
            5. technology_sophistication: score from 1-10 based on technical complexity
            6. industry_sector: Primary industry (healthcare, fintech, logistics, etc.)
            
            Company: {company_name}
            Website: {website}
            
            Content: {content}
            
            Return only valid JSON with these exact keys.
            """,
            
            "sales_intelligence": """
            Extract sales and marketing intelligence from this company's website content. Return JSON with:
            
            1. pain_points: Top 3 business problems they solve for customers
            2. key_services: Main products/services offered
            3. pricing_model: How they charge (subscription, usage, one-time, consulting, etc.)
            4. target_customers: Specific customer types or industries they serve
            5. sales_signals: Indicators of sales readiness (hiring, funding, partnerships, etc.)
            6. contact_approach: Best way to reach them (leadership team, sales team, partnerships)
            
            Company: {company_name}
            Content: {content}
            
            Return only valid JSON.
            """,
            
            "technology_assessment": """
            Assess the technical sophistication and approach of this company. Return JSON with:
            
            1. tech_stack: Technologies mentioned or inferred (programming languages, platforms, etc.)
            2. engineering_approach: How they build products (cloud-native, AI/ML, APIs, etc.)
            3. technical_complexity: Simple, moderate, or advanced
            4. innovation_level: Score 1-10 for technical innovation
            5. developer_focus: Whether they target developers/technical buyers
            6. integration_capabilities: APIs, partnerships, third-party integrations mentioned
            
            Company: {company_name}
            Content: {content}
            
            Return only valid JSON.
            """
        }
        
        self.test_companies = []
        self.results = {
            "test_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "sheet_url": self.sheet_url,
                "models_tested": len(self.models_to_test),
                "prompts_tested": len(self.research_prompts),
                "companies_tested": 0
            },
            "companies": [],
            "model_performance": {},
            "cost_analysis": {},
            "accuracy_analysis": {},
            "speed_analysis": {}
        }
    
    def extract_domain_from_url(self, url: str) -> str:
        """Extract clean domain from URL"""
        if not url:
            return ""
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
    
    def load_companies_from_sheet(self) -> List[Dict]:
        """Load companies from Google Sheets"""
        
        print("📊 Loading companies from Google Sheets...")
        
        try:
            # Convert Google Sheets URL to CSV export URL
            csv_url = f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/export?format=csv&gid=81910028"
            
            # Load the data
            df = pd.read_csv(csv_url)
            
            print(f"✅ Loaded {len(df)} companies from spreadsheet")
            print(f"📋 Columns: {list(df.columns)}")
            
            companies = []
            for _, row in df.iterrows():
                try:
                    company_name = str(row.get('Company', '')).strip()
                    url = str(row.get('URL', '')).strip()
                    
                    # Skip empty rows
                    if not company_name or company_name == 'nan' or not url or url == 'nan':
                        continue
                    
                    domain = self.extract_domain_from_url(url)
                    if not domain:
                        continue
                    
                    company = {
                        'name': company_name,
                        'url': url,
                        'domain': domain,
                        'employee_count': str(row.get('Emp Count', 'Not Specified')),
                        'description': str(row.get('Customer Problem & Solution (≈100 words)', '')),
                        'technologies': str(row.get('Key Technologies', '')),
                        'source_row': int(row.get('Unnamed: 0', 0)) if pd.notna(row.get('Unnamed: 0')) else 0
                    }
                    
                    companies.append(company)
                    
                except Exception as e:
                    print(f"⚠️ Error processing row: {e}")
                    continue
            
            print(f"✅ Successfully processed {len(companies)} valid companies")
            return companies
            
        except Exception as e:
            print(f"❌ Error loading from Google Sheets: {e}")
            print("🔄 Falling back to local CSV...")
            
            # Fallback to local CSV
            try:
                local_csv = Path(__file__).parent.parent.parent / 'data' / '2025 Survey Respondents Summary May 20.csv'
                df = pd.read_csv(local_csv)
                
                companies = []
                for _, row in df.iterrows():
                    try:
                        company_name = str(row.get('Company', '')).strip()
                        url = str(row.get('URL', '')).strip()
                        
                        if not company_name or not url:
                            continue
                        
                        domain = self.extract_domain_from_url(url)
                        if not domain:
                            continue
                        
                        company = {
                            'name': company_name,
                            'url': url,
                            'domain': domain,
                            'employee_count': str(row.get('Emp Count', 'Not Specified')),
                            'description': str(row.get('Customer Problem & Solution (≈100 words)', '')),
                            'technologies': str(row.get('Key Technologies', '')),
                            'source_row': int(row.iloc[0]) if pd.notna(row.iloc[0]) else 0
                        }
                        
                        companies.append(company)
                        
                    except Exception as e:
                        continue
                
                print(f"✅ Loaded {len(companies)} companies from local CSV")
                return companies
                
            except Exception as e:
                print(f"❌ Error loading local CSV: {e}")
                return []
    
    def select_random_companies(self, companies: List[Dict], count: int = 10) -> List[Dict]:
        """Select random companies for testing"""
        
        # Filter companies with valid domains
        valid_companies = [c for c in companies if c['domain'] and len(c['domain']) > 3]
        
        if len(valid_companies) < count:
            print(f"⚠️ Only {len(valid_companies)} valid companies available, using all")
            return valid_companies
        
        selected = random.sample(valid_companies, count)
        
        print(f"🎲 Selected {len(selected)} random companies for testing:")
        for i, company in enumerate(selected, 1):
            print(f"   {i}. {company['name']} ({company['domain']})")
        
        return selected
    
    async def scrape_company_content(self, company: Dict[str, str]) -> Optional[str]:
        """Scrape company content using Theodore's intelligent scraper"""
        
        try:
            # Import Theodore's scraper
            import sys
            sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))
            
            from intelligent_company_scraper import IntelligentCompanyScraperSync
            from models import CompanyIntelligenceConfig, CompanyData
            
            # Configure scraper for faster testing
            config = CompanyIntelligenceConfig(
                company_name=company['name'],
                company_domain=company['domain'],
                max_pages_to_scrape=10,  # Reduced for speed
                timeout_seconds=30
            )
            
            scraper = IntelligentCompanyScraperSync(config)
            
            print(f"🔍 Scraping {company['name']} ({company['domain']})...")
            
            # Create CompanyData object
            company_data = CompanyData(
                name=company['name'],
                website=f"https://{company['domain']}"
            )
            
            scraping_result = scraper.scrape_company(company_data, timeout=45)
            
            # Handle both dict and object returns
            if isinstance(scraping_result, dict):
                if scraping_result.get('success') and scraping_result.get('aggregated_content'):
                    content = scraping_result['aggregated_content']
                    print(f"   ✅ Scraped {len(content)} characters")
                    return content
                else:
                    print(f"   ❌ Scraping failed: {scraping_result.get('error', 'Unknown error')}")
                    return None
            else:
                # Handle CompanyData object
                if (hasattr(scraping_result, 'success') and scraping_result.success and 
                    hasattr(scraping_result, 'aggregated_content') and scraping_result.aggregated_content):
                    content = scraping_result.aggregated_content
                    print(f"   ✅ Scraped {len(content)} characters")
                    return content
                else:
                    error_msg = getattr(scraping_result, 'error_message', 'Unknown error')
                    print(f"   ❌ Scraping failed: {error_msg}")
                    return None
                
        except Exception as e:
            print(f"   ❌ Scraping error: {e}")
            return None
    
    async def test_company_with_all_models(self, company: Dict[str, str]) -> Dict[str, Any]:
        """Test a single company with all 4 models and 3 prompts"""
        
        print(f"\n🏢 Testing: {company['name']} ({company['domain']})")
        print("="*80)
        
        company_result = {
            "company": company,
            "timestamp": datetime.utcnow().isoformat(),
            "scraped_content": None,
            "model_results": {model_key: {} for model_key in self.models_to_test.keys()},
            "prompt_comparisons": {}
        }
        
        # Step 1: Scrape company content
        scraped_content = await self.scrape_company_content(company)
        company_result["scraped_content"] = {
            "content_length": len(scraped_content) if scraped_content else 0,
            "scraping_success": scraped_content is not None
        }
        
        if not scraped_content:
            print(f"❌ Failed to scrape content for {company['name']}")
            return company_result
        
        # Step 2: Test each prompt with all models
        for prompt_name, prompt_template in self.research_prompts.items():
            print(f"\n📋 Testing prompt: {prompt_name}")
            print("-" * 60)
            
            # Format prompt with company data
            formatted_prompt = prompt_template.format(
                company_name=company['name'],
                website=company['url'],
                content=scraped_content[:8000]  # Limit content length
            )
            
            prompt_results = {}
            
            # Test each model
            for model_key, model_config in self.models_to_test.items():
                print(f"{model_config['color']} Testing with {model_config['name']}...")
                
                if model_config['client_type'] == 'bedrock':
                    result = await self.test_bedrock_model(formatted_prompt, model_config, company['name'], prompt_name)
                elif model_config['client_type'] == 'gemini':
                    result = await self.test_gemini_model(formatted_prompt, model_config, company['name'], prompt_name)
                
                prompt_results[model_key] = result
                company_result["model_results"][model_key][prompt_name] = result
                
                # Small delay between requests
                await asyncio.sleep(2)
            
            # Compare results for this prompt
            company_result["prompt_comparisons"][prompt_name] = self.compare_prompt_across_models(prompt_results, prompt_name)
            
            # Longer delay between prompts
            await asyncio.sleep(3)
        
        return company_result
    
    async def test_bedrock_model(self, prompt: str, model_config: Dict, company_name: str, prompt_type: str) -> Dict:
        """Test with Bedrock models (Nova)"""
        
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
            "response_length": 0
        }
        
        try:
            # Import Bedrock client
            import sys
            sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))
            from bedrock_client import BedrockClient
            from models import CompanyIntelligenceConfig
            
            config = CompanyIntelligenceConfig()
            client = BedrockClient(config)
            
            # Make request
            response = await asyncio.to_thread(client.analyze_content, prompt)
            
            result["response_time"] = time.time() - start_time
            
            if response:
                result["success"] = True
                result["response"] = response
                result["response_length"] = len(response)
                
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
    
    async def test_gemini_model(self, prompt: str, model_config: Dict, company_name: str, prompt_type: str) -> Dict:
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
            "response_length": 0
        }
        
        try:
            # Import Gemini client
            import sys
            sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))
            from gemini_client import GeminiClient
            from models import CompanyIntelligenceConfig
            
            config = CompanyIntelligenceConfig()
            client = GeminiClient(config)
            
            # Make request
            response = await asyncio.to_thread(client.analyze_content, prompt)
            
            result["response_time"] = time.time() - start_time
            
            if response:
                result["success"] = True
                result["response"] = response
                result["response_length"] = len(response)
                
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
    
    def compare_prompt_across_models(self, prompt_results: Dict, prompt_name: str) -> Dict:
        """Compare results from all 4 models for a specific prompt"""
        
        successful_models = {k: v for k, v in prompt_results.items() if v["success"]}
        
        if not successful_models:
            return {"prompt": prompt_name, "successful_models": 0, "comparison": "No successful responses"}
        
        # Find best performers
        cost_ranking = sorted(successful_models.items(), key=lambda x: x[1]["cost"])
        speed_ranking = sorted(successful_models.items(), key=lambda x: x[1]["response_time"])
        json_ranking = sorted(successful_models.items(), key=lambda x: x[1]["json_valid"], reverse=True)
        
        return {
            "prompt": prompt_name,
            "successful_models": len(successful_models),
            "cost_winner": cost_ranking[0][0] if cost_ranking else None,
            "speed_winner": speed_ranking[0][0] if speed_ranking else None,
            "json_winner": json_ranking[0][0] if json_ranking else None,
            "cost_range": {
                "cheapest": cost_ranking[0][1]["cost"] if cost_ranking else 0,
                "most_expensive": cost_ranking[-1][1]["cost"] if cost_ranking else 0
            },
            "detailed_results": {k: {
                "cost": v["cost"],
                "speed": v["response_time"],
                "json_valid": v["json_valid"],
                "response_length": v["response_length"]
            } for k, v in successful_models.items()}
        }
    
    async def run_full_test(self) -> Dict[str, Any]:
        """Run the complete spreadsheet 4-model comparison test"""
        
        print("🧪 SPREADSHEET 4-MODEL AI COMPARISON TEST")
        print("="*80)
        print("🔵 Amazon Nova Pro   | 🟦 Amazon Nova Lite")
        print("🟢 Gemini 2.5 Pro   | 🟡 Gemini 2.5 Flash")
        print("="*80)
        print(f"📊 Using Theodore's intelligent scraper + 3 research prompts per company")
        print(f"🎯 Testing business model, sales intelligence, and technology assessment")
        
        # Load companies from spreadsheet
        all_companies = self.load_companies_from_sheet()
        if not all_companies:
            print("❌ No companies loaded. Exiting.")
            return self.results
        
        # Select 10 random companies
        self.test_companies = self.select_random_companies(all_companies, 10)
        self.results["test_metadata"]["companies_tested"] = len(self.test_companies)
        
        print(f"\n⏱️ Estimated time: {len(self.test_companies) * len(self.research_prompts) * 2} minutes")
        print(f"🎯 Total comparisons: {len(self.test_companies) * len(self.research_prompts) * len(self.models_to_test)}")
        
        # Test each company
        for i, company in enumerate(self.test_companies, 1):
            print(f"\n[{i}/{len(self.test_companies)}] Processing {company['name']}...")
            
            try:
                company_result = await self.test_company_with_all_models(company)
                self.results["companies"].append(company_result)
                
                # Update running totals
                self.update_running_totals(company_result)
                
                # Show progress
                self.print_progress_summary(i)
                
            except Exception as e:
                print(f"❌ Failed to test {company['name']}: {e}")
                continue
        
        # Generate final analysis
        self.generate_final_analysis()
        
        return self.results
    
    def update_running_totals(self, company_result: Dict[str, Any]):
        """Update running totals for analysis"""
        
        for model_key in self.models_to_test.keys():
            if model_key not in self.results["model_performance"]:
                self.results["model_performance"][model_key] = {
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "avg_response_time": 0.0,
                    "json_success_count": 0,
                    "total_requests": 0
                }
            
            for prompt_name in self.research_prompts.keys():
                if prompt_name in company_result["model_results"][model_key]:
                    result = company_result["model_results"][model_key][prompt_name]
                    
                    perf = self.results["model_performance"][model_key]
                    perf["total_requests"] += 1
                    
                    if result["success"]:
                        perf["total_cost"] += result["cost"]
                        perf["total_tokens"] += result["tokens_used"]
                        perf["successful_requests"] += 1
                        perf["avg_response_time"] += result["response_time"]
                        
                        if result["json_valid"]:
                            perf["json_success_count"] += 1
                    else:
                        perf["failed_requests"] += 1
    
    def print_progress_summary(self, companies_completed: int):
        """Print progress summary after each company"""
        
        print(f"\n📊 PROGRESS SUMMARY ({companies_completed}/{len(self.test_companies)} companies)")
        print("-" * 70)
        
        for model_key, model_config in self.models_to_test.items():
            perf = self.results["model_performance"].get(model_key, {})
            cost = perf.get("total_cost", 0)
            successes = perf.get("successful_requests", 0)
            failures = perf.get("failed_requests", 0)
            json_success = perf.get("json_success_count", 0)
            
            print(f"{model_config['color']} {model_config['name']}: ${cost:.4f} | {successes} success | {failures} fail | {json_success} JSON")
    
    def generate_final_analysis(self):
        """Generate comprehensive final analysis"""
        
        # Calculate averages and rankings
        for model_key, perf in self.results["model_performance"].items():
            if perf["successful_requests"] > 0:
                perf["avg_response_time"] /= perf["successful_requests"]
                perf["avg_cost_per_request"] = perf["total_cost"] / perf["successful_requests"]
                perf["json_success_rate"] = perf["json_success_count"] / perf["total_requests"]
        
        # Generate rankings
        models = list(self.models_to_test.keys())
        
        # Cost ranking (lower is better)
        cost_ranking = sorted(models, key=lambda m: self.results["model_performance"][m].get("total_cost", float('inf')))
        
        # Speed ranking (lower is better)
        speed_ranking = sorted(models, key=lambda m: self.results["model_performance"][m].get("avg_response_time", float('inf')))
        
        # Accuracy ranking (higher is better)
        accuracy_ranking = sorted(models, 
                                key=lambda m: self.results["model_performance"][m].get("json_success_rate", 0), 
                                reverse=True)
        
        self.results["rankings"] = {
            "cost_efficiency": cost_ranking,
            "speed": speed_ranking,
            "accuracy": accuracy_ranking
        }
        
        # Generate recommendation
        self.results["recommendation"] = self.generate_recommendation()
    
    def generate_recommendation(self) -> Dict[str, str]:
        """Generate final recommendations"""
        
        rankings = self.results["rankings"]
        cost_winner = rankings["cost_efficiency"][0]
        speed_winner = rankings["speed"][0]
        accuracy_winner = rankings["accuracy"][0]
        
        cost_winner_name = self.models_to_test[cost_winner]["name"]
        speed_winner_name = self.models_to_test[speed_winner]["name"]
        accuracy_winner_name = self.models_to_test[accuracy_winner]["name"]
        
        recommendations = {
            "cost_efficiency": f"{cost_winner_name} - Lowest total cost",
            "speed": f"{speed_winner_name} - Fastest average response time",
            "accuracy": f"{accuracy_winner_name} - Highest JSON success rate"
        }
        
        # Overall recommendation
        if cost_winner == accuracy_winner:
            recommendations["overall"] = f"STRONGLY RECOMMEND {cost_winner_name} - Best cost AND accuracy"
        elif cost_winner in rankings["accuracy"][:2]:
            recommendations["overall"] = f"RECOMMEND {cost_winner_name} - Best cost with good accuracy"
        else:
            recommendations["overall"] = f"BALANCED CHOICE - Cost: {cost_winner_name}, Accuracy: {accuracy_winner_name}"
        
        return recommendations
    
    def print_comprehensive_summary(self):
        """Print comprehensive test summary"""
        
        print(f"\n" + "="*80)
        print("📊 SPREADSHEET 4-MODEL AI COMPARISON - FINAL RESULTS")
        print("="*80)
        
        # Model performance
        print(f"\n🎯 MODEL PERFORMANCE:")
        for model_key, model_config in self.models_to_test.items():
            perf = self.results["model_performance"][model_key]
            print(f"   {model_config['color']} {model_config['name']}:")
            print(f"      💰 Total Cost: ${perf['total_cost']:.6f}")
            print(f"      ⚡ Avg Speed: {perf['avg_response_time']:.1f}s")
            print(f"      🎯 JSON Success: {perf['json_success_count']}/{perf['total_requests']} ({perf['json_success_rate']:.1%})")
            print(f"      ✅ Success Rate: {perf['successful_requests']}/{perf['total_requests']}")
        
        # Rankings
        print(f"\n🏆 RANKINGS:")
        print(f"   💰 Cost (cheapest): {' > '.join([self.models_to_test[m]['name'] for m in self.results['rankings']['cost_efficiency']])}")
        print(f"   ⚡ Speed (fastest): {' > '.join([self.models_to_test[m]['name'] for m in self.results['rankings']['speed']])}")
        print(f"   🎯 Accuracy (best): {' > '.join([self.models_to_test[m]['name'] for m in self.results['rankings']['accuracy']])}")
        
        # Recommendations
        print(f"\n🎯 RECOMMENDATIONS:")
        for category, recommendation in self.results["recommendation"].items():
            print(f"   {category.replace('_', ' ').title()}: {recommendation}")
    
    def save_results_to_excel(self, filename: str = None):
        """Save detailed results to Excel with multiple tabs"""
        
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"4_model_comparison_results_{timestamp}.xlsx"
        
        filepath = Path(__file__).parent / filename
        
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                
                # Tab 1: Summary
                summary_data = []
                for model_key, model_config in self.models_to_test.items():
                    perf = self.results["model_performance"][model_key]
                    summary_data.append({
                        "Model": model_config["name"],
                        "Total Cost": f"${perf['total_cost']:.6f}",
                        "Avg Response Time": f"{perf['avg_response_time']:.1f}s",
                        "JSON Success Rate": f"{perf['json_success_rate']:.1%}",
                        "Success Rate": f"{perf['successful_requests']}/{perf['total_requests']}",
                        "Cost per 1K Tokens": f"${model_config['cost_per_1k_tokens']:.6f}"
                    })
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name="Summary", index=False)
                
                # Tab 2: Company Details
                company_details = []
                for company_result in self.results["companies"]:
                    company = company_result["company"]
                    company_details.append({
                        "Company Name": company["name"],
                        "Domain": company["domain"],
                        "Employee Count": company["employee_count"],
                        "Scraping Success": company_result["scraped_content"]["scraping_success"],
                        "Content Length": company_result["scraped_content"]["content_length"]
                    })
                
                companies_df = pd.DataFrame(company_details)
                companies_df.to_excel(writer, sheet_name="Companies Tested", index=False)
                
                # Tab 3: Detailed Results
                detailed_results = []
                for company_result in self.results["companies"]:
                    company = company_result["company"]
                    for model_key in self.models_to_test.keys():
                        for prompt_name in self.research_prompts.keys():
                            if prompt_name in company_result["model_results"][model_key]:
                                result = company_result["model_results"][model_key][prompt_name]
                                detailed_results.append({
                                    "Company": company["name"],
                                    "Model": self.models_to_test[model_key]["name"],
                                    "Prompt": prompt_name,
                                    "Success": result["success"],
                                    "Cost": f"${result['cost']:.6f}",
                                    "Response Time": f"{result['response_time']:.1f}s",
                                    "Tokens Used": result["tokens_used"],
                                    "JSON Valid": result["json_valid"],
                                    "Response Length": result["response_length"],
                                    "Error": result.get("error", "")
                                })
                
                detailed_df = pd.DataFrame(detailed_results)
                detailed_df.to_excel(writer, sheet_name="Detailed Results", index=False)
                
                # Tab 4: Cost Analysis
                cost_analysis = []
                for model_key, model_config in self.models_to_test.items():
                    perf = self.results["model_performance"][model_key]
                    cost_analysis.append({
                        "Model": model_config["name"],
                        "Cost per 1K Tokens": f"${model_config['cost_per_1k_tokens']:.6f}",
                        "Total Tokens": perf["total_tokens"],
                        "Total Cost": f"${perf['total_cost']:.6f}",
                        "Avg Cost per Request": f"${perf.get('avg_cost_per_request', 0):.6f}",
                        "Cost per Company": f"${perf['total_cost'] / len(self.test_companies):.6f}"
                    })
                
                cost_df = pd.DataFrame(cost_analysis)
                cost_df.to_excel(writer, sheet_name="Cost Analysis", index=False)
            
            print(f"\n💾 Detailed results saved to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error saving Excel file: {e}")
            return None
    
    def save_json_results(self, filename: str = None):
        """Save results as JSON for further analysis"""
        
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"4_model_comparison_raw_{timestamp}.json"
        
        filepath = Path(__file__).parent / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"💾 Raw JSON results saved to: {filepath}")
        return filepath


async def main():
    """Main test execution"""
    
    print("🚀 SPREADSHEET 4-MODEL AI COMPARISON")
    print("="*60)
    print("📊 Reading companies from Google Sheets")
    print("🧪 Testing Nova Pro, Nova Lite, Gemini Pro, Gemini Flash")
    print("🔍 Using Theodore's intelligent scraper")
    print(f"\n⏱️ Estimated completion time: 60-90 minutes")
    
    # Initialize tester
    tester = Spreadsheet4ModelTester()
    
    try:
        # Run complete test
        results = await tester.run_full_test()
        
        # Print comprehensive summary
        tester.print_comprehensive_summary()
        
        # Save results to Excel
        excel_file = tester.save_results_to_excel()
        
        # Save raw JSON
        json_file = tester.save_json_results()
        
        print(f"\n🎉 Spreadsheet 4-model comparison completed successfully!")
        print(f"📊 Excel results: {excel_file}")
        print(f"📄 JSON results: {json_file}")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Test interrupted by user")
        tester.save_results_to_excel("4_model_comparison_interrupted")
        tester.save_json_results("4_model_comparison_interrupted")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Install required packages if not available
    try:
        import pandas as pd
        import openpyxl
    except ImportError:
        print("📦 Installing required packages...")
        import subprocess
        subprocess.run(["pip", "install", "pandas", "openpyxl"])
        import pandas as pd
        import openpyxl
    
    asyncio.run(main())