#!/usr/bin/env python3
"""
Hybrid Spreadsheet 4-Model Test
Uses real companies from spreadsheet with sample content for immediate testing
Creates Excel results with multiple tabs
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

class HybridSpreadsheet4ModelTester:
    """4-model comparison using real companies from spreadsheet with sample content"""
    
    def __init__(self):
        # Google Sheets info
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
        
        # Sample content templates for different company types
        self.content_templates = {
            "saas": """
            {company_name} is a leading software-as-a-service company that provides cloud-based solutions 
            to help businesses streamline their operations. Our platform offers comprehensive features including 
            automated workflows, real-time analytics, and seamless integrations with popular business tools.
            
            Founded in {year}, {company_name} serves {market} customers across various industries including 
            technology, healthcare, finance, and manufacturing. Our innovative approach combines advanced AI 
            technology with user-friendly interfaces to deliver exceptional value to our clients.
            
            Key features include: dashboard analytics, automated reporting, API integrations, enterprise security,
            multi-tenant architecture, and 24/7 customer support. We offer flexible pricing models including
            subscription tiers and usage-based billing to meet diverse customer needs.
            """,
            
            "fintech": """
            {company_name} is a financial technology company revolutionizing {market} financial services through 
            innovative digital solutions. Our platform leverages cutting-edge technology to provide secure, 
            efficient, and user-friendly financial products and services.
            
            Since our founding in {year}, we have focused on democratizing access to financial services and 
            enabling businesses and consumers to make smarter financial decisions. Our technology stack includes
            machine learning algorithms, blockchain infrastructure, and advanced security protocols.
            
            We offer services including digital payments, lending solutions, wealth management, regulatory compliance,
            fraud detection, and real-time transaction processing. Our API-first approach enables seamless 
            integration with existing financial systems and third-party platforms.
            """,
            
            "healthcare": """
            {company_name} is a healthcare technology company dedicated to improving patient outcomes and 
            streamlining healthcare operations. Our digital health platform connects patients, providers, 
            and healthcare systems through innovative technology solutions.
            
            Established in {year}, {company_name} addresses critical challenges in {market} healthcare delivery 
            including care coordination, patient engagement, and operational efficiency. Our HIPAA-compliant 
            platform ensures the highest standards of data security and privacy.
            
            Our solutions include electronic health records, telemedicine capabilities, patient portals, 
            clinical decision support, population health management, and healthcare analytics. We serve 
            hospitals, clinics, physician practices, and healthcare networks of all sizes.
            """,
            
            "enterprise": """
            {company_name} provides enterprise-grade technology solutions designed to help large organizations 
            optimize their operations and accelerate digital transformation. Our comprehensive platform offers 
            scalable, secure, and integrated solutions for complex business requirements.
            
            Since {year}, {company_name} has been a trusted partner for {market} enterprises seeking to modernize 
            their technology infrastructure and improve operational efficiency. Our solutions are designed for 
            high-volume, mission-critical environments with enterprise-grade security and compliance.
            
            Key capabilities include enterprise resource planning, customer relationship management, supply chain 
            optimization, business intelligence, workforce management, and cloud infrastructure services. We offer 
            both on-premises and cloud deployment options with comprehensive support and professional services.
            """
        }
        
        # Research prompt for analysis
        self.test_prompt = """
        Analyze this company based on the provided information and return a JSON response with:
        
        1. business_model: Primary revenue model (B2B SaaS, B2C, marketplace, consulting, etc.)
        2. target_market: Who they serve (SMB, enterprise, consumers, specific industries)
        3. competitive_advantages: Top 3 key differentiators or value propositions
        4. company_stage: startup, growth, or mature
        5. technology_sophistication: score from 1-10 based on technical complexity
        6. industry_sector: Primary industry (fintech, healthcare, SaaS, etc.)
        
        Company: {company_name}
        Website: {website}
        Employee Count: {employee_count}
        Description: {description}
        Technologies: {technologies}
        
        Content: {content}
        
        Return only valid JSON with these exact keys.
        """
        
        self.test_companies = []
        self.results = {
            "test_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "sheet_id": self.sheet_id,
                "models_tested": len(self.models_to_test),
                "companies_tested": 0,
                "note": "Using hybrid approach with real company data + sample content for immediate testing"
            },
            "companies": [],
            "model_performance": {},
            "rankings": {},
            "recommendation": {}
        }
    
    def extract_domain_from_url(self, url: str) -> str:
        """Extract clean domain from URL"""
        if not url:
            return ""
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
    
    def load_companies_from_csv(self) -> List[Dict]:
        """Load companies from local CSV"""
        
        print("📊 Loading companies from local CSV...")
        
        try:
            local_csv = Path(__file__).parent.parent.parent / 'data' / '2025 Survey Respondents Summary May 20.csv'
            df = pd.read_csv(local_csv)
            
            print(f"✅ Loaded {len(df)} rows from CSV")
            
            companies = []
            for _, row in df.iterrows():
                try:
                    company_name = str(row.get('Company', '')).strip()
                    url = str(row.get('URL', '')).strip()
                    
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
                    continue
            
            print(f"✅ Successfully processed {len(companies)} valid companies")
            return companies
            
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return []
    
    def classify_company_type(self, company: Dict) -> str:
        """Classify company type based on description and technologies"""
        
        description = company.get('description', '').lower()
        technologies = company.get('technologies', '').lower()
        name = company.get('name', '').lower()
        
        # Simple classification logic
        if any(word in description or word in technologies for word in ['fintech', 'payment', 'financial', 'lending', 'banking']):
            return "fintech"
        elif any(word in description or word in technologies for word in ['health', 'medical', 'hospital', 'patient', 'clinical']):
            return "healthcare"
        elif any(word in description or word in technologies for word in ['enterprise', 'erp', 'corporation', 'large']):
            return "enterprise"
        else:
            return "saas"
    
    def generate_sample_content(self, company: Dict) -> str:
        """Generate realistic sample content for a company"""
        
        company_type = self.classify_company_type(company)
        template = self.content_templates.get(company_type, self.content_templates["saas"])
        
        # Determine market type
        if 'b2b' in company.get('description', '').lower():
            market = "business"
        elif any(word in company.get('description', '').lower() for word in ['enterprise', 'corporate']):
            market = "enterprise"
        else:
            market = "mid-market"
        
        # Generate a reasonable founding year
        year = random.choice(range(2010, 2022))
        
        return template.format(
            company_name=company['name'],
            market=market,
            year=year
        )
    
    def select_random_companies(self, companies: List[Dict], count: int = 10) -> List[Dict]:
        """Select random companies for testing"""
        
        valid_companies = [c for c in companies if c['domain'] and len(c['domain']) > 3]
        
        if len(valid_companies) < count:
            print(f"⚠️ Only {len(valid_companies)} valid companies available, using all")
            return valid_companies
        
        selected = random.sample(valid_companies, count)
        
        print(f"🎲 Selected {len(selected)} random companies for testing:")
        for i, company in enumerate(selected, 1):
            print(f"   {i}. {company['name']} ({company['domain']}) - {company['employee_count']} employees")
        
        return selected
    
    async def test_company_with_all_models(self, company: Dict[str, str]) -> Dict[str, Any]:
        """Test a single company with all 4 models"""
        
        print(f"\n🏢 Testing: {company['name']} ({company['domain']})")
        print("="*80)
        
        # Generate sample content for this company
        sample_content = self.generate_sample_content(company)
        
        company_result = {
            "company": company,
            "timestamp": datetime.utcnow().isoformat(),
            "sample_content_length": len(sample_content),
            "model_results": {}
        }
        
        # Format prompt with company data
        formatted_prompt = self.test_prompt.format(
            company_name=company['name'],
            website=company['url'],
            employee_count=company['employee_count'],
            description=company['description'][:500],  # Limit description length
            technologies=company['technologies'][:200],  # Limit technologies length
            content=sample_content
        )
        
        print(f"📝 Generated {len(sample_content)} characters of sample content")
        print(f"🎯 Company type classified as: {self.classify_company_type(company)}")
        
        # Test each model
        for model_key, model_config in self.models_to_test.items():
            print(f"\n{model_config['color']} Testing with {model_config['name']}...")
            
            if model_config['client_type'] == 'bedrock':
                result = await self.test_bedrock_model(formatted_prompt, model_config, company['name'])
            elif model_config['client_type'] == 'gemini':
                result = await self.test_gemini_model(formatted_prompt, model_config, company['name'])
            
            company_result["model_results"][model_key] = result
            
            # Small delay between requests
            await asyncio.sleep(2)
        
        return company_result
    
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
            "json_valid": False,
            "response_length": 0
        }
        
        try:
            import sys
            sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))
            from bedrock_client import BedrockClient
            from models import CompanyIntelligenceConfig
            
            config = CompanyIntelligenceConfig()
            client = BedrockClient(config)
            
            response = await asyncio.to_thread(client.analyze_content, prompt)
            
            result["response_time"] = time.time() - start_time
            
            if response:
                result["success"] = True
                result["response"] = response
                result["response_length"] = len(response)
                
                estimated_tokens = len(prompt.split()) + len(response.split())
                result["tokens_used"] = estimated_tokens
                result["cost"] = (estimated_tokens / 1000) * model_config["cost_per_1k_tokens"]
                
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
            "json_valid": False,
            "response_length": 0
        }
        
        try:
            import sys
            sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))
            from gemini_client import GeminiClient
            from models import CompanyIntelligenceConfig
            
            config = CompanyIntelligenceConfig()
            client = GeminiClient(config)
            
            response = await asyncio.to_thread(client.analyze_content, prompt)
            
            result["response_time"] = time.time() - start_time
            
            if response:
                result["success"] = True
                result["response"] = response
                result["response_length"] = len(response)
                
                estimated_tokens = len(prompt.split()) + len(response.split())
                result["tokens_used"] = estimated_tokens
                result["cost"] = (estimated_tokens / 1000) * model_config["cost_per_1k_tokens"]
                
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
    
    async def run_full_test(self) -> Dict[str, Any]:
        """Run the complete hybrid test"""
        
        print("🧪 HYBRID SPREADSHEET 4-MODEL AI COMPARISON TEST")
        print("="*80)
        print("🔵 Amazon Nova Pro   | 🟦 Amazon Nova Lite")
        print("🟢 Gemini 2.5 Pro   | 🟡 Gemini 2.5 Flash")
        print("="*80)
        print(f"📊 Using real company data from spreadsheet + sample content")
        print(f"🎯 Testing comprehensive business model analysis")
        
        # Load companies
        all_companies = self.load_companies_from_csv()
        if not all_companies:
            print("❌ No companies loaded. Exiting.")
            return self.results
        
        # Select 10 random companies
        self.test_companies = self.select_random_companies(all_companies, 10)
        self.results["test_metadata"]["companies_tested"] = len(self.test_companies)
        
        print(f"\n⏱️ Estimated time: {len(self.test_companies) * 2} minutes")
        print(f"🎯 Total comparisons: {len(self.test_companies) * len(self.models_to_test)}")
        
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
            
            if model_key in company_result["model_results"]:
                result = company_result["model_results"][model_key]
                
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
                perf["json_success_rate"] = perf["json_success_count"] / perf["total_requests"] if perf["total_requests"] > 0 else 0
        
        # Generate rankings
        models = list(self.models_to_test.keys())
        
        cost_ranking = sorted(models, key=lambda m: self.results["model_performance"][m].get("total_cost", float('inf')))
        speed_ranking = sorted(models, key=lambda m: self.results["model_performance"][m].get("avg_response_time", float('inf')))
        accuracy_ranking = sorted(models, key=lambda m: self.results["model_performance"][m].get("json_success_rate", 0), reverse=True)
        
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
        print("📊 HYBRID SPREADSHEET 4-MODEL AI COMPARISON - FINAL RESULTS")
        print("="*80)
        
        # Model performance
        print(f"\n🎯 MODEL PERFORMANCE:")
        for model_key, model_config in self.models_to_test.items():
            perf = self.results["model_performance"][model_key]
            json_rate = perf.get("json_success_rate", 0)
            print(f"   {model_config['color']} {model_config['name']}:")
            print(f"      💰 Total Cost: ${perf['total_cost']:.6f}")
            print(f"      ⚡ Avg Speed: {perf['avg_response_time']:.1f}s")
            print(f"      🎯 JSON Success: {perf['json_success_count']}/{perf['total_requests']} ({json_rate:.1%})")
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
            filename = f"hybrid_4_model_comparison_{timestamp}.xlsx"
        
        filepath = Path(__file__).parent / filename
        
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                
                # Tab 1: Executive Summary
                summary_data = []
                for model_key, model_config in self.models_to_test.items():
                    perf = self.results["model_performance"][model_key]
                    json_rate = perf.get("json_success_rate", 0)
                    summary_data.append({
                        "Model": model_config["name"],
                        "Total Cost": f"${perf['total_cost']:.6f}",
                        "Cost per Company": f"${perf['total_cost'] / len(self.test_companies):.6f}",
                        "Avg Response Time": f"{perf['avg_response_time']:.1f}s",
                        "JSON Success Rate": f"{json_rate:.1%}",
                        "Overall Success": f"{perf['successful_requests']}/{perf['total_requests']}",
                        "Model Pricing": f"${model_config['cost_per_1k_tokens']:.6f}/1K tokens"
                    })
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name="Executive Summary", index=False)
                
                # Tab 2: Company Details
                company_details = []
                for company_result in self.results["companies"]:
                    company = company_result["company"]
                    company_details.append({
                        "Company Name": company["name"],
                        "Website": company["url"],
                        "Domain": company["domain"],
                        "Employee Count": company["employee_count"],
                        "Source Row": company["source_row"],
                        "Sample Content Length": company_result["sample_content_length"],
                        "Description Preview": company["description"][:100] + "..." if len(company["description"]) > 100 else company["description"],
                        "Key Technologies": company["technologies"][:100] + "..." if len(company["technologies"]) > 100 else company["technologies"]
                    })
                
                companies_df = pd.DataFrame(company_details)
                companies_df.to_excel(writer, sheet_name="Companies Tested", index=False)
                
                # Tab 3: Detailed Model Results
                detailed_results = []
                for company_result in self.results["companies"]:
                    company = company_result["company"]
                    for model_key, result in company_result["model_results"].items():
                        detailed_results.append({
                            "Company": company["name"],
                            "Model": self.models_to_test[model_key]["name"],
                            "Success": result["success"],
                            "Cost": f"${result['cost']:.6f}",
                            "Response Time": f"{result['response_time']:.1f}s",
                            "Tokens Used": result["tokens_used"],
                            "JSON Valid": result["json_valid"],
                            "Response Length": result["response_length"],
                            "Error": result.get("error", "")[:100] if result.get("error") else ""
                        })
                
                detailed_df = pd.DataFrame(detailed_results)
                detailed_df.to_excel(writer, sheet_name="Detailed Results", index=False)
                
                # Tab 4: Cost Comparison
                cost_analysis = []
                for model_key, model_config in self.models_to_test.items():
                    perf = self.results["model_performance"][model_key]
                    cost_analysis.append({
                        "Model": model_config["name"],
                        "Model ID": model_config["model_id"],
                        "Cost per 1K Tokens": f"${model_config['cost_per_1k_tokens']:.6f}",
                        "Total Tokens": perf["total_tokens"],
                        "Total Cost": f"${perf['total_cost']:.6f}",
                        "Cost per Company": f"${perf['total_cost'] / len(self.test_companies):.6f}",
                        "Cost Efficiency Rank": self.results["rankings"]["cost_efficiency"].index(model_key) + 1
                    })
                
                cost_df = pd.DataFrame(cost_analysis)
                cost_df.to_excel(writer, sheet_name="Cost Analysis", index=False)
                
                # Tab 5: Performance Analysis
                performance_data = []
                for model_key, model_config in self.models_to_test.items():
                    perf = self.results["model_performance"][model_key]
                    json_rate = perf.get("json_success_rate", 0)
                    performance_data.append({
                        "Model": model_config["name"],
                        "Avg Response Time": f"{perf['avg_response_time']:.1f}s",
                        "Speed Rank": self.results["rankings"]["speed"].index(model_key) + 1,
                        "JSON Success Count": perf["json_success_count"],
                        "JSON Success Rate": f"{json_rate:.1%}",
                        "Accuracy Rank": self.results["rankings"]["accuracy"].index(model_key) + 1,
                        "Successful Requests": perf["successful_requests"],
                        "Failed Requests": perf["failed_requests"],
                        "Total Requests": perf["total_requests"]
                    })
                
                performance_df = pd.DataFrame(performance_data)
                performance_df.to_excel(writer, sheet_name="Performance Analysis", index=False)
                
                # Tab 6: Recommendations
                recommendations_data = []
                for category, recommendation in self.results["recommendation"].items():
                    recommendations_data.append({
                        "Category": category.replace('_', ' ').title(),
                        "Recommendation": recommendation
                    })
                
                # Add test metadata
                recommendations_data.extend([
                    {"Category": "Test Date", "Recommendation": self.results["test_metadata"]["timestamp"]},
                    {"Category": "Companies Tested", "Recommendation": str(self.results["test_metadata"]["companies_tested"])},
                    {"Category": "Models Tested", "Recommendation": str(self.results["test_metadata"]["models_tested"])},
                    {"Category": "Total Comparisons", "Recommendation": str(len(self.test_companies) * len(self.models_to_test))},
                    {"Category": "Note", "Recommendation": self.results["test_metadata"]["note"]}
                ])
                
                recommendations_df = pd.DataFrame(recommendations_data)
                recommendations_df.to_excel(writer, sheet_name="Recommendations", index=False)
            
            print(f"\n💾 Comprehensive Excel report saved to: {filepath}")
            print(f"📊 Report includes 6 tabs: Executive Summary, Companies, Detailed Results, Cost Analysis, Performance, Recommendations")
            return filepath
            
        except Exception as e:
            print(f"❌ Error saving Excel file: {e}")
            return None
    
    def save_json_results(self, filename: str = None):
        """Save results as JSON for further analysis"""
        
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"hybrid_4_model_raw_{timestamp}.json"
        
        filepath = Path(__file__).parent / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"💾 Raw JSON results saved to: {filepath}")
        return filepath


async def main():
    """Main test execution"""
    
    print("🚀 HYBRID SPREADSHEET 4-MODEL AI COMPARISON")
    print("="*60)
    print("📊 Using real companies from David's survey spreadsheet")
    print("🧪 Testing Nova Pro, Nova Lite, Gemini Pro, Gemini Flash")
    print("📝 Generating realistic sample content for each company")
    print(f"\n⏱️ Estimated completion time: 20-30 minutes")
    
    # Initialize tester
    tester = HybridSpreadsheet4ModelTester()
    
    try:
        # Run complete test
        results = await tester.run_full_test()
        
        # Print comprehensive summary
        tester.print_comprehensive_summary()
        
        # Save results to Excel
        excel_file = tester.save_results_to_excel()
        
        # Save raw JSON
        json_file = tester.save_json_results()
        
        print(f"\n🎉 Hybrid 4-model comparison completed successfully!")
        print(f"📊 Excel report: {excel_file}")
        print(f"📄 JSON data: {json_file}")
        
        print(f"\n📈 KEY INSIGHTS:")
        print(f"   • Tested {len(tester.test_companies)} real companies from survey data")
        print(f"   • Generated realistic sample content for each company type")
        print(f"   • Comprehensive cost, speed, and accuracy analysis")
        print(f"   • Ready for presentation to stakeholders")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Test interrupted by user")
        tester.save_results_to_excel("hybrid_4_model_interrupted")
        tester.save_json_results("hybrid_4_model_interrupted")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())