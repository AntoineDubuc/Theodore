#!/usr/bin/env python3
"""
Phase 4 Integrated Classification Test - Option B Validation
Tests combining content aggregation + SaaS classification in single LLM call
"""

import sys
import os
import time
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Add Theodore root to path
sys.path.append('/Users/antoinedubuc/Desktop/AI_Goodies/Theodore')
sys.path.append('/Users/antoinedubuc/Desktop/AI_Goodies/Theodore/sandbox/search/singular_search/concurency_approach/concurency_and_rate_limiting_tests')

try:
    # Import our rate-limited solution
    from rate_limited_gemini_solution import RateLimitedTheodoreLLMManager, LLMTask, LLMResult
    from rate_limited_gemini_solution import safe_json_parse
    print("✅ Successfully imported rate-limited solution")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("ℹ️ This test requires the rate_limited_gemini_solution.py file from concurency_and_rate_limiting_tests")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class IntegratedTestResult:
    """Result structure for integrated classification test"""
    company_name: str
    processing_time: float
    prompt_tokens: int
    response_tokens: int
    success: bool
    
    # Business Intelligence Results
    business_intelligence: Dict[str, Any] = None
    bi_quality_score: float = 0.0
    
    # Classification Results  
    classification_result: Dict[str, Any] = None
    classification_accuracy: str = "unknown"  # "correct", "incorrect", "ambiguous"
    
    # Technical Metrics
    response_parsing_success: bool = False
    error_message: Optional[str] = None

class Phase4IntegratedClassificationTester:
    """
    Tests whether Phase 4 can handle both content aggregation and 
    SaaS classification in a single LLM call (Option B)
    """
    
    def __init__(self):
        # Initialize rate-limited LLM manager
        self.llm_manager = RateLimitedTheodoreLLMManager(
            max_workers=1,
            requests_per_minute=8
        )
        
        # SaaS Taxonomy for classification (59 categories)
        self.saas_taxonomy = self._get_59_category_taxonomy()
        
        # Test companies with known classifications
        self.test_companies = self._get_test_company_scenarios()
    
    def _get_59_category_taxonomy(self) -> str:
        """Complete 59-category SaaS taxonomy for classification"""
        return """
SaaS VERTICALS (26 categories):
- AdTech: Advertising technology platforms
- AssetManagement: Asset and property management software
- Billing: Billing and subscription management
- Bio/LS: Biotechnology and life sciences software
- CollabTech: Collaboration and communication tools
- Data/BI/Analytics: Data analysis and business intelligence
- DevOps/CloudInfra: Development operations and cloud infrastructure
- E-commerce & Retail: Online commerce platforms
- EdTech: Educational technology
- Enertech: Energy technology solutions
- FinTech: Financial technology services
- GovTech: Government technology solutions
- HRTech: Human resources technology
- HealthTech: Healthcare technology (non-pharma)
- Identity & Access Management (IAM): Security and access control
- InsureTech: Insurance technology
- LawTech: Legal technology solutions
- LeisureTech: Entertainment and leisure technology
- Manufacturing/AgTech/IoT: Industrial and agricultural tech
- Martech & CRM: Marketing technology and customer relations
- MediaTech: Media and content technology
- PropTech: Property and real estate technology
- Risk/Audit/Governance: Compliance and risk management
- Social / Community / Non Profit: Social impact platforms
- Supply Chain & Logistics: Supply chain management
- TranspoTech: Transportation technology

NON-SaaS CATEGORIES (17 categories):
- Advertising & Media Services: Traditional advertising agencies
- Biopharma R&D: Pharmaceutical research and development
- Combo HW & SW: Hardware and software combination products
- Education: Traditional educational institutions
- Energy: Traditional energy companies
- Financial Services: Traditional banks and financial institutions
- Healthcare Services: Healthcare providers and services
- Industry Consulting Services: Management and industry consulting
- Insurance: Traditional insurance companies
- IT Consulting Services: Technology consulting and services
- Logistics Services: Traditional logistics and shipping
- Manufacturing: Traditional manufacturing companies
- Non-Profit: Non-profit organizations
- Retail: Traditional retail businesses
- Sports: Sports organizations and teams
- Travel & Leisure: Traditional travel and hospitality
- Wholesale Distribution & Supply: Distribution and supply companies

SPECIAL CATEGORY:
- Unclassified: Cannot be definitively classified
"""
    
    def _get_test_company_scenarios(self) -> List[Dict[str, Any]]:
        """Test companies with expected classifications"""
        return [
            {
                "name": "Stripe",
                "website": "https://stripe.com",
                "scenario": "Clear SaaS - FinTech",
                "expected_classification": "FinTech",
                "expected_is_saas": True,
                "content": "Stripe is a financial technology company that offers payment processing software and APIs for e-commerce websites and mobile applications. The company provides a suite of tools for online businesses including payment processing, subscription management, marketplace functionality, and fraud prevention. Stripe serves millions of businesses worldwide including Amazon, Google, Microsoft, and Shopify. The platform handles billions of dollars in transactions annually and is used by companies of all sizes from startups to Fortune 500 enterprises. Stripe's mission is to increase the GDP of the internet by providing infrastructure for online commerce."
            },
            {
                "name": "Linear",
                "website": "https://linear.app", 
                "scenario": "Clear SaaS - Project Management",
                "expected_classification": "CollabTech",
                "expected_is_saas": True,
                "content": "Linear is a modern issue tracking and project management tool built for high-performance teams. The company focuses on providing a fast, streamlined workflow for software development teams, emphasizing speed and efficiency. Linear offers real-time collaboration, keyboard shortcuts, and integrations with popular development tools, designed specifically for engineering teams at technology companies who need efficient project tracking. The platform integrates with GitHub, Slack, Figma, and other development tools popular with engineering teams."
            },
            {
                "name": "Tesla",
                "website": "https://tesla.com",
                "scenario": "Clear Non-SaaS - Manufacturing",
                "expected_classification": "Manufacturing",
                "expected_is_saas": False,
                "content": "Tesla is an electric vehicle and clean energy company based in Austin, Texas. Tesla designs and manufactures electric cars, battery energy storage systems, solar panels, and related products and services. The company operates multiple Gigafactories for vehicle and battery production and has a global network of Supercharger stations. Tesla also develops autonomous driving technology and operates an energy generation and storage business. The company manufactures the Model S, Model 3, Model X, Model Y vehicles and the Cybertruck."
            },
            {
                "name": "Deloitte",
                "website": "https://deloitte.com",
                "scenario": "Clear Non-SaaS - Consulting",
                "expected_classification": "Industry Consulting Services",
                "expected_is_saas": False,
                "content": "Deloitte is a multinational professional services network providing audit, consulting, financial advisory, risk advisory, tax, and related services. The company serves clients in more than 150 countries and territories with approximately 415,000 professionals worldwide. Deloitte provides consulting services across strategy, operations, technology, and human capital to help organizations solve complex business challenges. The firm works with 85% of Fortune 500 companies and offers industry-specific expertise across sectors including technology, financial services, healthcare, and government."
            },
            {
                "name": "Hybrid Solutions Inc",
                "website": "https://hybridsolutions.example",
                "scenario": "Ambiguous - Hybrid Business Model",
                "expected_classification": "Unclassified",
                "expected_is_saas": None,
                "content": "Hybrid Solutions Inc provides a combination of software licensing, professional services, and hardware solutions for enterprise clients. The company offers both on-premise software installations and cloud-based SaaS solutions depending on client needs. Revenue comes from software licenses, subscription fees, consulting services, and hardware sales. The business model varies by customer segment with some clients using purely SaaS offerings while others prefer traditional licensing with professional services support."
            }
        ]
    
    def start(self):
        """Start the rate-limited LLM manager"""
        self.llm_manager.start()
        logger.info("🚀 Rate-limited LLM manager started")
    
    def shutdown(self):
        """Shutdown the rate-limited LLM manager"""
        self.llm_manager.shutdown()
        logger.info("🛑 Rate-limited LLM manager shutdown")
    
    def create_integrated_phase4_prompt(self, company_name: str, extracted_content: str) -> str:
        """
        Create the integrated prompt combining content aggregation + classification
        """
        
        prompt = f"""You are an expert business analyst. Perform TWO tasks in a single analysis:

TASK 1: BUSINESS INTELLIGENCE EXTRACTION
Analyze the website content for {company_name} and extract comprehensive business intelligence.

TASK 2: BUSINESS MODEL CLASSIFICATION  
Classify {company_name} using the 59-category taxonomy below.

COMPANY TO ANALYZE:
Company Name: {company_name}
Website Content: {extracted_content}

=== TASK 1: BUSINESS INTELLIGENCE EXTRACTION ===

Extract structured business intelligence including:
- Company overview and value proposition
- Business model (B2B/B2C/B2B2C) and target market
- Key products/services and competitive advantages
- Company size indicators and maturity stage
- Sales-relevant insights and market context

=== TASK 2: BUSINESS MODEL CLASSIFICATION ===

CLASSIFICATION TAXONOMY:
{self.saas_taxonomy}

CLASSIFICATION INSTRUCTIONS:
1. Analyze the company's business model based on the provided content
2. Choose the single best-fit category from the 59 options above
3. Determine if this is a SaaS (Software as a Service) or Non-SaaS company
4. Provide confidence score (0.0-1.0) based on available evidence
5. Provide one-sentence justification citing specific evidence

=== OUTPUT FORMAT ===

Return your analysis in this exact JSON structure:

{{
  "business_intelligence": {{
    "company_description": "2-3 paragraph comprehensive business summary",
    "industry": "Primary industry classification",
    "business_model": "B2B|B2C|B2B2C|Marketplace",
    "target_market": "Primary customer segments",
    "key_services": ["service1", "service2", "service3"],
    "competitive_advantages": ["advantage1", "advantage2"],
    "company_size": "startup|small|medium|large|enterprise",
    "value_proposition": "Core value proposition and unique selling points",
    "market_context": "Industry position and competitive landscape"
  }},
  "saas_classification": {{
    "category": "Exact category name from taxonomy above",
    "is_saas": true/false,
    "confidence": 0.85,
    "justification": "One-sentence explanation citing specific evidence from the content",
    "model_version": "integrated_v1.0"
  }}
}}

IMPORTANT: 
- Use exact category names from the taxonomy
- Base classification on actual business model, not just industry
- Confidence should reflect quality of available evidence
- Ensure both business intelligence and classification are comprehensive
"""
        
        return prompt
    
    def test_single_company_integrated_analysis(self, test_company: Dict[str, Any]) -> IntegratedTestResult:
        """Test integrated analysis on a single company"""
        
        logger.info(f"🧪 Testing integrated analysis: {test_company['name']}")
        start_time = time.time()
        
        # Create integrated prompt
        prompt = self.create_integrated_phase4_prompt(
            test_company["name"],
            test_company["content"]
        )
        
        # Calculate prompt size
        prompt_tokens = len(prompt) // 4  # Rough token estimate
        logger.info(f"📊 Prompt size: ~{prompt_tokens} tokens")
        
        # Create LLM task
        task = LLMTask(
            task_id=f"integrated_test_{test_company['name']}_{int(time.time())}",
            prompt=prompt,
            context={"company_name": test_company["name"], "test_scenario": test_company["scenario"]}
        )
        
        # Process with rate limiting
        try:
            llm_result = self.llm_manager.worker_pool.process_task(task)
            processing_time = time.time() - start_time
            
            if llm_result.success:
                # Parse the integrated response
                parsed_result = safe_json_parse(llm_result.response, fallback_value={})
                
                if parsed_result and "business_intelligence" in parsed_result and "saas_classification" in parsed_result:
                    # Successful parsing of integrated response
                    
                    # Evaluate classification accuracy
                    classification_accuracy = self._evaluate_classification_accuracy(
                        parsed_result["saas_classification"],
                        test_company
                    )
                    
                    # Evaluate business intelligence quality
                    bi_quality = self._evaluate_business_intelligence_quality(
                        parsed_result["business_intelligence"]
                    )
                    
                    return IntegratedTestResult(
                        company_name=test_company["name"],
                        processing_time=processing_time,
                        prompt_tokens=prompt_tokens,
                        response_tokens=len(llm_result.response) // 4,
                        success=True,
                        business_intelligence=parsed_result["business_intelligence"],
                        bi_quality_score=bi_quality,
                        classification_result=parsed_result["saas_classification"],
                        classification_accuracy=classification_accuracy,
                        response_parsing_success=True
                    )
                    
                else:
                    # Parsing failed
                    return IntegratedTestResult(
                        company_name=test_company["name"],
                        processing_time=processing_time,
                        prompt_tokens=prompt_tokens,
                        response_tokens=len(llm_result.response) // 4,
                        success=False,
                        response_parsing_success=False,
                        error_message="Failed to parse integrated JSON response"
                    )
            
            else:
                # LLM call failed
                return IntegratedTestResult(
                    company_name=test_company["name"],
                    processing_time=processing_time,
                    prompt_tokens=prompt_tokens,
                    response_tokens=0,
                    success=False,
                    error_message=f"LLM call failed: {llm_result.error}"
                )
                
        except Exception as e:
            return IntegratedTestResult(
                company_name=test_company["name"],
                processing_time=time.time() - start_time,
                prompt_tokens=prompt_tokens,
                response_tokens=0,
                success=False,
                error_message=f"Exception during processing: {str(e)}"
            )
    
    def _evaluate_classification_accuracy(self, classification_result: Dict, test_company: Dict) -> str:
        """Evaluate classification accuracy against expected results"""
        
        if not classification_result:
            return "failed"
        
        actual_category = classification_result.get("category", "")
        actual_is_saas = classification_result.get("is_saas", None)
        
        expected_category = test_company["expected_classification"]
        expected_is_saas = test_company["expected_is_saas"]
        
        # Check SaaS/Non-SaaS classification
        saas_correct = actual_is_saas == expected_is_saas
        
        # Check category classification
        category_correct = actual_category == expected_category
        
        if saas_correct and category_correct:
            return "correct"
        elif saas_correct:
            return "partially_correct"  # Right SaaS/Non-SaaS, wrong category
        elif expected_is_saas is None:  # Ambiguous case
            return "ambiguous"
        else:
            return "incorrect"
    
    def _evaluate_business_intelligence_quality(self, bi_result: Dict) -> float:
        """Evaluate business intelligence extraction quality (0.0-1.0)"""
        
        if not bi_result:
            return 0.0
        
        # Check required fields presence and quality
        required_fields = [
            "company_description", "industry", "business_model", 
            "target_market", "key_services", "value_proposition"
        ]
        
        quality_score = 0.0
        for field in required_fields:
            value = bi_result.get(field, "")
            if value and len(str(value).strip()) > 10:  # Minimum quality threshold
                quality_score += 1.0
        
        return quality_score / len(required_fields)
    
    def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run the complete test suite for integrated Phase 4"""
        
        print("🧪 PHASE 4 INTEGRATED CLASSIFICATION TEST SUITE")
        print("=" * 80)
        print("🎯 Testing: Content Aggregation + SaaS Classification in Single LLM Call")
        print("📅 Test Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print()
        
        test_results = []
        
        for i, test_company in enumerate(self.test_companies, 1):
            print(f"📋 TEST {i}/{len(self.test_companies)}: {test_company['name']}")
            print(f"   Scenario: {test_company['scenario']}")
            print(f"   Expected: {test_company['expected_classification']} ({'SaaS' if test_company['expected_is_saas'] else 'Non-SaaS' if test_company['expected_is_saas'] is not None else 'Ambiguous'})")
            print("-" * 60)
            
            result = self.test_single_company_integrated_analysis(test_company)
            test_results.append(result)
            
            # Display results
            if result.success:
                print(f"✅ SUCCESS: Processing completed in {result.processing_time:.2f}s")
                print(f"📊 Tokens: {result.prompt_tokens} prompt → {result.response_tokens} response")
                
                if result.response_parsing_success:
                    print(f"🎯 Classification: {result.classification_result.get('category', 'N/A')}")
                    print(f"🏷️ SaaS Type: {'SaaS' if result.classification_result.get('is_saas') else 'Non-SaaS'}")
                    print(f"📈 Confidence: {result.classification_result.get('confidence', 0):.2f}")
                    print(f"✔️ Accuracy: {result.classification_accuracy}")
                    print(f"📄 BI Quality: {result.bi_quality_score:.2f}")
                    
                    # Show justification
                    justification = result.classification_result.get('justification', 'N/A')
                    print(f"💭 Justification: {justification}")
                else:
                    print("❌ Response parsing failed")
            else:
                print(f"❌ FAILED: {result.error_message}")
            
            print()
            
            # Rate limiting pause
            if i < len(self.test_companies):
                print("⏳ Pausing for rate limiting...")
                time.sleep(8)  # 8 requests per minute = 7.5s between requests
                print()
        
        # Generate summary report
        return self._generate_test_summary(test_results)
    
    def _generate_test_summary(self, test_results: List[IntegratedTestResult]) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        
        successful_tests = [r for r in test_results if r.success]
        successful_parsing = [r for r in successful_tests if r.response_parsing_success]
        
        # Classification accuracy analysis
        accuracy_counts = {}
        for result in successful_parsing:
            acc = result.classification_accuracy
            accuracy_counts[acc] = accuracy_counts.get(acc, 0) + 1
        
        # Performance metrics
        avg_processing_time = sum(r.processing_time for r in successful_tests) / len(successful_tests) if successful_tests else 0
        avg_prompt_tokens = sum(r.prompt_tokens for r in test_results) / len(test_results)
        avg_response_tokens = sum(r.response_tokens for r in successful_tests) / len(successful_tests) if successful_tests else 0
        avg_bi_quality = sum(r.bi_quality_score for r in successful_parsing) / len(successful_parsing) if successful_parsing else 0
        
        summary = {
            "test_execution": {
                "total_tests": len(test_results),
                "successful_tests": len(successful_tests),
                "parsing_success": len(successful_parsing),
                "success_rate": len(successful_tests) / len(test_results) * 100,
                "parsing_rate": len(successful_parsing) / len(successful_tests) * 100 if successful_tests else 0
            },
            "classification_accuracy": {
                "accuracy_distribution": accuracy_counts,
                "correct_classifications": accuracy_counts.get("correct", 0),
                "accuracy_rate": accuracy_counts.get("correct", 0) / len(successful_parsing) * 100 if successful_parsing else 0
            },
            "performance_metrics": {
                "avg_processing_time": avg_processing_time,
                "avg_prompt_tokens": avg_prompt_tokens,
                "avg_response_tokens": avg_response_tokens,
                "avg_bi_quality": avg_bi_quality
            }
        }
        
        # Print summary
        print("=" * 80)
        print("📊 INTEGRATED CLASSIFICATION TEST SUMMARY")
        print("=" * 80)
        
        print(f"🎯 TEST EXECUTION:")
        print(f"   Total Tests: {summary['test_execution']['total_tests']}")
        print(f"   Successful: {summary['test_execution']['successful_tests']} ({summary['test_execution']['success_rate']:.1f}%)")
        print(f"   Response Parsing: {summary['test_execution']['parsing_success']} ({summary['test_execution']['parsing_rate']:.1f}%)")
        
        print(f"\n🏷️ CLASSIFICATION ACCURACY:")
        for acc_type, count in accuracy_counts.items():
            print(f"   {acc_type.title()}: {count}")
        print(f"   Overall Accuracy: {summary['classification_accuracy']['accuracy_rate']:.1f}%")
        
        print(f"\n⚡ PERFORMANCE METRICS:")
        print(f"   Avg Processing Time: {summary['performance_metrics']['avg_processing_time']:.2f}s")
        print(f"   Avg Prompt Tokens: {summary['performance_metrics']['avg_prompt_tokens']:.0f}")
        print(f"   Avg Response Tokens: {summary['performance_metrics']['avg_response_tokens']:.0f}")
        print(f"   Avg BI Quality: {summary['performance_metrics']['avg_bi_quality']:.2f}")
        
        # Option B Viability Assessment
        print(f"\n🎯 OPTION B VIABILITY ASSESSMENT:")
        
        viable = (
            summary['test_execution']['success_rate'] >= 80 and
            summary['classification_accuracy']['accuracy_rate'] >= 85 and
            summary['performance_metrics']['avg_processing_time'] <= 15 and
            summary['performance_metrics']['avg_bi_quality'] >= 0.8
        )
        
        print(f"   Option B Viable: {'✅ YES' if viable else '❌ NO'}")
        
        if viable:
            print("   ✅ High success rate, accurate classifications, good performance")
            print("   ✅ RECOMMENDATION: Proceed with integrated Phase 4 approach")
        else:
            print("   ❌ Performance or accuracy concerns detected")
            print("   ❌ RECOMMENDATION: Consider separate Phase 5 classification call (Option A)")
        
        return summary

def run_phase4_integration_test():
    """Main test execution function"""
    
    tester = Phase4IntegratedClassificationTester()
    
    try:
        tester.start()
        summary = tester.run_comprehensive_test_suite()
        return summary
        
    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        tester.shutdown()

if __name__ == "__main__":
    print("🚀 Starting Phase 4 Integrated Classification Test (Option B)")
    print("🎯 Objective: Validate combining content aggregation + SaaS classification")
    print()
    
    summary = run_phase4_integration_test()
    
    if summary:
        print("\n🏁 Test completed successfully!")
        print("📄 Review results above to determine Option B viability")
    else:
        print("\n💥 Test execution failed - check logs for details")